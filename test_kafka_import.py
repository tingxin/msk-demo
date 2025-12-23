#!/usr/bin/env python3
"""
测试 Kafka 库导入的脚本
"""

import sys


def test_kafka_python():
    """测试 kafka-python 库"""
    try:
        from kafka import KafkaProducer
        from kafka.errors import KafkaError
        print("✅ kafka-python 导入成功")
        return True
    except ImportError as e:
        print(f"❌ kafka-python 导入失败: {e}")
        return False


def test_confluent_kafka():
    """测试 confluent-kafka 库"""
    try:
        from confluent_kafka import Producer
        from confluent_kafka.error import KafkaError, KafkaException
        print("✅ confluent-kafka 导入成功")
        return True
    except ImportError as e:
        print(f"❌ confluent-kafka 导入失败: {e}")
        return False


def test_other_dependencies():
    """测试其他依赖"""
    try:
        import boto3
        print("✅ boto3 导入成功")
    except ImportError as e:
        print(f"❌ boto3 导入失败: {e}")
        return False
    
    try:
        import json
        import time
        import logging
        from typing import Dict, Any, Optional
        from dataclasses import dataclass
        print("✅ 标准库导入成功")
    except ImportError as e:
        print(f"❌ 标准库导入失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("Kafka 库导入测试")
    print("=" * 30)
    
    print(f"Python 版本: {sys.version}")
    print()
    
    # 测试其他依赖
    print("测试基础依赖:")
    other_ok = test_other_dependencies()
    print()
    
    # 测试 Kafka 库
    print("测试 Kafka 库:")
    kafka_python_ok = test_kafka_python()
    confluent_kafka_ok = test_confluent_kafka()
    print()
    
    # 给出建议
    print("建议:")
    if confluent_kafka_ok:
        print("🎉 推荐使用 confluent-kafka 版本:")
        print("   python3 msk_producer_confluent.py")
    elif kafka_python_ok:
        print("🎉 可以使用 kafka-python 版本:")
        print("   python3 msk_producer.py")
    else:
        print("❌ 需要安装 Kafka 库:")
        print("   pip3 install confluent-kafka==2.3.0  # 推荐")
        print("   或")
        print("   python3 fix_kafka_dependencies.py   # 修复 kafka-python")
    
    if not other_ok:
        print("❌ 需要安装基础依赖:")
        print("   pip3 install boto3==1.34.0")


if __name__ == "__main__":
    main()