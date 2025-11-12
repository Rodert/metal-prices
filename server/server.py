#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贵金属价格数据接收和存储服务
提供API接收采集数据并存储到SQLite数据库
"""

from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import json
import logging
import os
from contextlib import contextmanager
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
DATABASE_PATH = os.getenv('DATABASE_PATH', 'metal_prices.db')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

app = Flask(__name__)


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建最新价格表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS latest_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT NOT NULL UNIQUE,
                    product_name TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    current_time TEXT NOT NULL,
                    min_price REAL,
                    max_price REAL,
                    data_timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    deleted_at TEXT,
                    UNIQUE(product_code)
                )
            ''')
            
            # 创建历史记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    current_time TEXT NOT NULL,
                    min_price REAL,
                    max_price REAL,
                    data_timestamp TEXT NOT NULL,
                    collect_timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    deleted_at TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_history_product 
                ON price_history(product_code)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_history_time 
                ON price_history(created_at)
            ''')
            
            # 创建触发器：自动更新 latest_prices 的 updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_latest_prices_timestamp 
                AFTER UPDATE ON latest_prices
                FOR EACH ROW
                BEGIN
                    UPDATE latest_prices 
                    SET updated_at = datetime('now', 'localtime')
                    WHERE id = NEW.id;
                END;
            ''')
            
            # 创建触发器：自动更新 price_history 的 updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_price_history_timestamp 
                AFTER UPDATE ON price_history
                FOR EACH ROW
                BEGIN
                    UPDATE price_history 
                    SET updated_at = datetime('now', 'localtime')
                    WHERE id = NEW.id;
                END;
            ''')
            
            logger.info("数据库初始化完成")
    
    def save_prices(self, prices_data: Dict) -> Dict:
        """
        保存价格数据
        
        Args:
            prices_data: 包含价格列表的字典
            
        Returns:
            保存结果统计
        """
        prices = prices_data.get('prices', [])
        source = prices_data.get('source', 'UNKNOWN')
        collect_time = prices_data.get('collect_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        if not prices:
            raise ValueError("没有价格数据")
        
        success_count = 0
        failed_count = 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for price_info in prices:
                try:
                    product_code = price_info['product_code']
                    product_name = price_info['product_name']
                    current_price = price_info['current_price']
                    current_time = price_info['current_time']
                    min_price = price_info.get('min_price')
                    max_price = price_info.get('max_price')
                    data_timestamp = price_info['data_timestamp']
                    collect_timestamp = price_info.get('collect_timestamp', collect_time)
                    
                    # 插入历史记录（created_at 和 updated_at 由数据库自动设置）
                    cursor.execute('''
                        INSERT INTO price_history (
                            product_code, product_name, current_price, current_time,
                            min_price, max_price, data_timestamp, collect_timestamp,
                            source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product_code, product_name, current_price, current_time,
                        min_price, max_price, data_timestamp, collect_timestamp,
                        source
                    ))
                    
                    # 更新或插入最新价格（created_at 和 updated_at 由数据库自动设置）
                    cursor.execute('''
                        INSERT INTO latest_prices (
                            product_code, product_name, current_price, current_time,
                            min_price, max_price, data_timestamp, source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(product_code) DO UPDATE SET
                            product_name = excluded.product_name,
                            current_price = excluded.current_price,
                            current_time = excluded.current_time,
                            min_price = excluded.min_price,
                            max_price = excluded.max_price,
                            data_timestamp = excluded.data_timestamp,
                            source = excluded.source,
                            updated_at = datetime('now', 'localtime')
                    ''', (
                        product_code, product_name, current_price, current_time,
                        min_price, max_price, data_timestamp, source
                    ))
                    
                    success_count += 1
                    logger.info(f"保存 {product_code} 价格: {current_price}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"保存价格失败: {e}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(prices)
        }
    
    def get_latest_prices(self, product_code: Optional[str] = None) -> List[Dict]:
        """
        获取最新价格
        
        Args:
            product_code: 产品代码，为空则返回所有产品
            
        Returns:
            价格列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if product_code:
                cursor.execute('''
                    SELECT * FROM latest_prices WHERE product_code = ?
                    ORDER BY updated_at DESC
                ''', (product_code,))
            else:
                cursor.execute('''
                    SELECT * FROM latest_prices ORDER BY updated_at DESC
                ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_price_history(
        self, 
        product_code: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取历史价格
        
        Args:
            product_code: 产品代码
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            
        Returns:
            历史价格列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM price_history WHERE 1=1'
            params = []
            
            if product_code:
                query += ' AND product_code = ?'
                params.append(product_code)
            
            if start_time:
                query += ' AND created_at >= ?'
                params.append(start_time)
            
            if end_time:
                query += ' AND created_at <= ?'
                params.append(end_time)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总产品数
            cursor.execute('SELECT COUNT(*) as count FROM latest_prices')
            total_products = cursor.fetchone()['count']
            
            # 历史记录总数
            cursor.execute('SELECT COUNT(*) as count FROM price_history')
            total_history = cursor.fetchone()['count']
            
            # 最新更新时间
            cursor.execute('SELECT MAX(updated_at) as last_update FROM latest_prices')
            last_update = cursor.fetchone()['last_update']
            
            # 各产品记录数
            cursor.execute('''
                SELECT product_code, product_name, COUNT(*) as count 
                FROM price_history 
                GROUP BY product_code 
                ORDER BY count DESC
            ''')
            product_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_products': total_products,
                'total_history_records': total_history,
                'last_update': last_update,
                'product_statistics': product_stats
            }


# 初始化数据库
db = Database()


# ==================== API 路由 ====================

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/prices', methods=['POST'])
def receive_prices():
    """
    接收价格数据
    
    请求体格式:
    {
        "prices": [
            {
                "product_code": "Au99.99",
                "product_name": "黄金99.99",
                "current_price": 530.67,
                "current_time": "10:15",
                "min_price": 528.5,
                "max_price": 532.8,
                "data_timestamp": "2025年11月11日 10:15:52",
                "collect_timestamp": "2025-11-11 10:16:00"
            }
        ],
        "collect_time": "2025-11-11 10:16:00",
        "source": "SGE"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体为空'
            }), 400
        
        # 保存数据
        result = db.save_prices(data)
        
        logger.info(f"接收价格数据: 成功 {result['success']} 条，失败 {result['failed']} 条")
        
        return jsonify({
            'success': True,
            'message': '数据保存成功',
            'result': result
        }), 200
        
    except ValueError as e:
        logger.error(f"数据验证失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"保存数据失败: {e}")
        return jsonify({
            'success': False,
            'error': '服务器内部错误'
        }), 500


@app.route('/api/prices/latest', methods=['GET'])
def get_latest_prices():
    """
    获取最新价格
    
    查询参数:
    - product_code: 产品代码（可选）
    
    示例:
    - GET /api/prices/latest
    - GET /api/prices/latest?product_code=Au99.99
    """
    try:
        product_code = request.args.get('product_code')
        prices = db.get_latest_prices(product_code)
        
        return jsonify({
            'success': True,
            'count': len(prices),
            'data': prices
        }), 200
        
    except Exception as e:
        logger.error(f"查询最新价格失败: {e}")
        return jsonify({
            'success': False,
            'error': '查询失败'
        }), 500


@app.route('/api/prices/history', methods=['GET'])
def get_price_history():
    """
    获取历史价格
    
    查询参数:
    - product_code: 产品代码（可选）
    - start_time: 开始时间，格式 YYYY-MM-DD HH:MM:SS（可选）
    - end_time: 结束时间，格式 YYYY-MM-DD HH:MM:SS（可选）
    - limit: 返回记录数，默认100（可选）
    
    示例:
    - GET /api/prices/history
    - GET /api/prices/history?product_code=Au99.99
    - GET /api/prices/history?product_code=Au99.99&limit=50
    - GET /api/prices/history?start_time=2025-11-11 00:00:00&end_time=2025-11-11 23:59:59
    """
    try:
        product_code = request.args.get('product_code')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        limit = int(request.args.get('limit', 100))
        
        history = db.get_price_history(
            product_code=product_code,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'count': len(history),
            'data': history
        }), 200
        
    except Exception as e:
        logger.error(f"查询历史价格失败: {e}")
        return jsonify({
            'success': False,
            'error': '查询失败'
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    获取统计信息
    
    返回:
    - 总产品数
    - 历史记录总数
    - 最新更新时间
    - 各产品记录数统计
    """
    try:
        stats = db.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'success': False,
            'error': '查询失败'
        }), 500


@app.route('/', methods=['GET'])
def index():
    """API 文档"""
    return jsonify({
        'name': '贵金属价格数据服务',
        'version': '1.0.0',
        'endpoints': {
            'health': {
                'method': 'GET',
                'path': '/health',
                'description': '健康检查'
            },
            'receive_prices': {
                'method': 'POST',
                'path': '/api/prices',
                'description': '接收价格数据'
            },
            'latest_prices': {
                'method': 'GET',
                'path': '/api/prices/latest',
                'description': '获取最新价格',
                'params': ['product_code (可选)']
            },
            'price_history': {
                'method': 'GET',
                'path': '/api/prices/history',
                'description': '获取历史价格',
                'params': ['product_code (可选)', 'start_time (可选)', 'end_time (可选)', 'limit (可选)']
            },
            'statistics': {
                'method': 'GET',
                'path': '/api/statistics',
                'description': '获取统计信息'
            }
        }
    })


if __name__ == '__main__':
    logger.info(f"启动服务: {HOST}:{PORT}")
    logger.info(f"数据库路径: {DATABASE_PATH}")
    app.run(host=HOST, port=PORT, debug=False)
