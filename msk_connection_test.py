#!/usr/bin/env python3
"""
MSK 连接测试工具
用于测试连接和诊断权限问题
"""

from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaError, KafkaException
import json
import time


def create_producer_config(bootstrap_servers, username, password):
    """创建生产者配置"""
    return {
        'bootstrap.servers': bootstrap_servers,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'SCRAM-SHA-512',
        'sasl.username': username,
        'sasl.password': password,
        'acks': 'all',
        'retries': 3,
        'request.timeout.ms': 30000,
    }


def test_connection(bootstrap_servers, username, password):
    """测试基本连接"""
    print("🔧 测试 MSK 连接...")
    
    config = create_producer_config(bootstrap_servers, username, password)
    
    try:
        producer = Producer(config)
        print("✅ Producer 创建成功")
        
        # 获取集群元数据
        metadata = producer.list_topics(timeout=10)
        print(f"✅ 连接成功，发现 {len(metadata.topics)} 个 Topic")
        
        # 列出可用的 Topic
        if metadata.topics:
            print("📋 可用的 Topics:")
            for topic_name in metadata.topics:
                topic = metadata.topics[topic_name]
                print(f"   - {topic_name} ({len(topic.partitions)} 个分区)")
        else:
            print("⚠️  没有发现任何 Topic")
            
        return True, list(metadata.topics.keys())
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False, []


def create_test_topic(bootstrap_servers, username, password, topic_name):
    """创建测试 Topic"""
    print(f"🔧 尝试创建 Topic: {topic_name}")
    
    config = {
        'bootstrap.servers': bootstrap_servers,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'SCRAM-SHA-512',
        'sasl.username': username,
        'sasl.password': password,
    }
    
    try:
        admin_client = AdminClient(config)
        
        # 创建 Topic
        topic_list = [NewTopic(topic_name, num_partitions=3, replication_factor=2)]
        fs = admin_client.create_topics(topic_list)
        
        # 等待创建完成
        for topic, f in fs.items():
            try:
                f.result()  # 等待操作完成
                print(f"✅ Topic '{topic}' 创建成功")
                return True
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"ℹ️  Topic '{topic}' 已存在")
                    return True
                else:
                    print(f"❌ 创建 Topic '{topic}' 失败: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ 创建 Topic 失败: {e}")
        return False


def test_produce_message(bootstrap_servers, username, password, topic_name):
    """测试发送消息"""
    print(f"🔧 测试发送消息到 Topic: {topic_name}")
    
    config = create_producer_config(bootstrap_servers, username, password)
    
    try:
        producer = Producer(config)
        
        # 测试消息
        test_message = {
            "test": True,
            "timestamp": int(time.time() * 1000),
            "message": "Hello MSK!"
        }
        
        # 发送消息
        producer.produce(
            topic=topic_name,
            value=json.dumps(test_message).encode('utf-8'),
            key="test-key".encode('utf-8')
        )
        
        # 等待发送完成
        producer.flush(timeout=10)
        print("✅ 消息发送成功")
        return True
        
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        return False


def main():
    """主函数"""
    print("AWS MSK 连接测试工具")
    print("=" * 40)
    
    # 配置信息 - 请根据实际情况修改
    bootstrap_servers = "b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196,b-2-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196"
    username = "demo"  # 请替换为实际用户名
    password = "Demo1234"  # 请替换为实际密码
    test_topic = "test-topic"
    
    print(f"集群地址: {bootstrap_servers}")
    print(f"用户名: {username}")
    print(f"测试 Topic: {test_topic}")
    print()
    
    # 1. 测试连接
    success, existing_topics = test_connection(bootstrap_servers, username, password)
    if not success:
        print("❌ 连接测试失败，请检查配置")
        return
    
    print()
    
    # 2. 检查或创建测试 Topic
    if test_topic not in existing_topics:
        print(f"⚠️  Topic '{test_topic}' 不存在，尝试创建...")
        if not create_test_topic(bootstrap_servers, username, password, test_topic):
            print("❌ 无法创建 Topic，可能没有权限")
            print("💡 建议:")
            print("   1. 使用现有的 Topic")
            print("   2. 请管理员创建 Topic")
            print("   3. 检查用户权限")
            
            if existing_topics:
                print(f"\n可以尝试使用现有 Topic: {existing_topics[0]}")
                test_topic = existing_topics[0]
            else:
                return
    else:
        print(f"✅ Topic '{test_topic}' 已存在")
    
    print()
    
    # 3. 测试发送消息
    if test_produce_message(bootstrap_servers, username, password, test_topic):
        print("\n🎉 所有测试通过!")
        print(f"✅ 可以使用 Topic: {test_topic}")
        print("\n现在可以在代码中使用:")
        print(f"   topic_name = '{test_topic}'")
        print(f"   username = '{username}'")
        print(f"   password = '{password}'")
    else:
        print("\n❌ 消息发送测试失败")
        print("💡 可能的原因:")
        print("   1. 用户没有写入权限")
        print("   2. Topic 不存在或无权限")
        print("   3. 网络连接问题")


if __name__ == "__main__":
    main()