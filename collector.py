#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贵金属价格数据采集脚本
从上海黄金交易所采集实时价格数据并发送到指定接口
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MetalPriceCollector:
    """贵金属价格采集器"""
    
    # 上海黄金交易所API地址
    SGE_API_URL = "https://www.sge.com.cn/graph/quotations"
    
    # 产品代码映射
    PRODUCT_NAMES = {
        "Au99.99": "黄金99.99",
        "Au99.95": "黄金99.95",
        "Au99.5": "黄金99.5",
        "Au100g": "100克金条",
        "iAu99.99": "国际板黄金99.99",
        "iAu100g": "国际板100克金条",
        "iAu99.5": "国际板黄金99.5",
        "Au(T+D)": "黄金延期交收",
        "Au(T+N1)": "黄金远期合约1",
        "Au(T+N2)": "黄金远期合约2",
        "Ag99.99": "白银99.99",
        "Ag(T+D)": "白银延期交收",
        "Pt99.95": "铂金99.95",
        "PGC30g": "铂金金条30克",
        "NYAuTN06": "纽约金06合约",
        "NYAuTN12": "纽约金12合约"
    }
    
    # 默认采集的产品列表
    DEFAULT_PRODUCTS = [
        "Au99.99", "Au99.95", "Au100g",
        "Ag99.99", "Pt99.95"
    ]
    
    def __init__(self, target_api_url: Optional[str] = None):
        """
        初始化采集器
        
        Args:
            target_api_url: 目标接口URL，从环境变量或参数获取
        """
        self.target_api_url = target_api_url or os.getenv("TARGET_API_URL")
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.sge.com.cn',
            'Referer': 'https://www.sge.com.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        })
    
    def fetch_product_data(self, product_code: str) -> Optional[Dict]:
        """
        获取指定产品的价格数据
        
        Args:
            product_code: 产品代码，如 "Au99.99"
            
        Returns:
            产品数据字典，失败返回None
        """
        try:
            logger.info(f"正在获取 {product_code} ({self.PRODUCT_NAMES.get(product_code, product_code)}) 的数据...")
            
            response = self.session.post(
                self.SGE_API_URL,
                data={'instid': product_code},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"成功获取 {product_code} 的数据")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取 {product_code} 数据失败: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析 {product_code} 数据失败: {e}")
            return None
    
    def get_current_price(self, product_data: Dict) -> Optional[Dict]:
        """
        从产品数据中提取当前时刻的价格信息
        
        Args:
            product_data: 产品完整数据
            
        Returns:
            包含当前价格信息的字典
        """
        try:
            times = product_data.get('times', [])
            prices = product_data.get('data', [])
            product_code = product_data.get('heyue', '')
            delay_str = product_data.get('delaystr', '')
            min_price = product_data.get('min')
            max_price = product_data.get('max')
            
            if not times or not prices:
                logger.warning(f"产品 {product_code} 数据为空")
                return None
            
            # 从 delaystr 中提取时间，格式如 "2025年11月11日 10:15:52"
            if not delay_str:
                logger.error(f"{product_code} 缺少 delaystr 时间戳，数据不完整")
                return None
            
            try:
                # 提取时间部分，格式: "10:15:52"
                time_part = delay_str.split(' ')[-1]  # 获取最后一部分
                hour_minute = ':'.join(time_part.split(':')[:2])  # 只取小时:分钟，如 "10:15"
                
                # 在 times 数组中查找对应的时间
                if hour_minute not in times:
                    logger.error(f"{product_code} 在数据中未找到时间 {hour_minute}，数据不完整")
                    return None
                
                index = times.index(hour_minute)
                current_time = hour_minute
                current_price = prices[index]
                logger.info(f"{product_code} 根据时间 {hour_minute} 找到对应价格: {current_price}")
                
            except Exception as e:
                logger.error(f"{product_code} 解析时间失败: {e}")
                return None
            
            result = {
                'product_code': product_code,
                'product_name': self.PRODUCT_NAMES.get(product_code, product_code),
                'current_time': current_time,
                'current_price': float(current_price),
                'min_price': float(min_price) if min_price else None,
                'max_price': float(max_price) if max_price else None,
                'data_timestamp': delay_str,
                'collect_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"{product_code} 当前价格: {current_price} (时间: {current_time})")
            return result
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"提取价格信息失败: {e}")
            return None
    
    def send_to_target_api(self, data: Dict) -> bool:
        """
        将数据发送到目标接口
        
        Args:
            data: 要发送的数据
            
        Returns:
            是否发送成功
        """
        if not self.target_api_url:
            logger.warning("未配置目标API地址，跳过发送")
            logger.info(f"采集到的数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        
        try:
            logger.info(f"正在发送数据到 {self.target_api_url}...")
            
            response = requests.post(
                self.target_api_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"数据发送成功: {response.status_code}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"发送数据失败: {e}")
            return False
    
    def collect_and_send(self, product_codes: Optional[List[str]] = None) -> Dict:
        """
        采集指定产品的数据并发送
        
        Args:
            product_codes: 要采集的产品代码列表，默认使用DEFAULT_PRODUCTS
            
        Returns:
            采集结果统计
        """
        if product_codes is None:
            product_codes = self.DEFAULT_PRODUCTS
        
        logger.info(f"开始采集任务，共 {len(product_codes)} 个产品")
        
        results = {
            'success': [],
            'failed': [],
            'total': len(product_codes),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        all_prices = []
        
        for product_code in product_codes:
            # 获取产品数据
            product_data = self.fetch_product_data(product_code)
            if not product_data:
                results['failed'].append(product_code)
                continue
            
            # 提取当前价格
            price_info = self.get_current_price(product_data)
            if not price_info:
                results['failed'].append(product_code)
                continue
            
            all_prices.append(price_info)
            results['success'].append(product_code)
        
        # 检查是否有失败的产品
        if results['failed']:
            logger.error(f"部分产品采集失败: {', '.join(results['failed'])}")
            logger.warning("由于数据不完整，不发送到目标API")
            return results
        
        # 批量发送数据
        if all_prices:
            payload = {
                'prices': all_prices,
                'collect_time': results['timestamp'],
                'source': 'SGE'
            }
            
            if self.send_to_target_api(payload):
                logger.info(f"采集完成: 成功 {len(results['success'])} 个，失败 {len(results['failed'])} 个")
            else:
                logger.error("数据发送失败")
        else:
            logger.error("没有采集到任何数据，任务失败")
        
        return results


def main():
    """主函数"""
    # 从环境变量读取配置
    target_api_url = os.getenv("TARGET_API_URL")
    products_env = os.getenv("PRODUCTS")
    
    # 解析产品列表
    if products_env:
        product_codes = [p.strip() for p in products_env.split(',') if p.strip()]
    else:
        product_codes = None  # 使用默认列表
    
    # 创建采集器
    collector = MetalPriceCollector(target_api_url=target_api_url)
    
    # 执行采集
    results = collector.collect_and_send(product_codes)
    
    # 输出结果
    logger.info("=" * 50)
    logger.info(f"采集任务完成")
    logger.info(f"总计: {results['total']} 个产品")
    logger.info(f"成功: {len(results['success'])} 个")
    logger.info(f"失败: {len(results['failed'])} 个")
    if results['failed']:
        logger.warning(f"失败的产品: {', '.join(results['failed'])}")
    logger.info("=" * 50)
    
    # 如果有失败的，返回非零退出码
    if results['failed']:
        sys.exit(1)


if __name__ == "__main__":
    main()
