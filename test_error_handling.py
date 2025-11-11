#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试错误处理逻辑
"""

from collector import MetalPriceCollector
import logging

logging.basicConfig(level=logging.INFO)

# 创建采集器实例
collector = MetalPriceCollector()

# 测试1: 正常数据
print("\n=== 测试1: 正常数据 ===")
normal_data = {
    'times': ['10:00', '10:01', '10:02'],
    'data': ['100.0', '101.0', '102.0'],
    'heyue': 'TEST01',
    'delaystr': '2025年11月11日 10:01:30',
    'min': 100,
    'max': 102
}
result = collector.get_current_price(normal_data)
print(f"结果: {result}")

# 测试2: 缺少 delaystr
print("\n=== 测试2: 缺少 delaystr ===")
no_delaystr = {
    'times': ['10:00', '10:01', '10:02'],
    'data': ['100.0', '101.0', '102.0'],
    'heyue': 'TEST02',
    'min': 100,
    'max': 102
}
result = collector.get_current_price(no_delaystr)
print(f"结果: {result}")

# 测试3: 时间不匹配
print("\n=== 测试3: 时间不匹配 ===")
time_mismatch = {
    'times': ['10:00', '10:01', '10:02'],
    'data': ['100.0', '101.0', '102.0'],
    'heyue': 'TEST03',
    'delaystr': '2025年11月11日 10:15:30',  # 10:15 不在 times 中
    'min': 100,
    'max': 102
}
result = collector.get_current_price(time_mismatch)
print(f"结果: {result}")

# 测试4: 空数据
print("\n=== 测试4: 空数据 ===")
empty_data = {
    'times': [],
    'data': [],
    'heyue': 'TEST04',
    'delaystr': '2025年11月11日 10:01:30',
    'min': 100,
    'max': 102
}
result = collector.get_current_price(empty_data)
print(f"结果: {result}")

print("\n=== 所有测试完成 ===")
