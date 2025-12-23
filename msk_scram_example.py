#!/usr/bin/env python3
"""
AWS MSK SCRAM-SHA-512 认证示例
简化版本，专门用于 SCRAM-SHA-512 认证
"""

from msk_producer import MSKProducer, MSKConfig
import json
import time


def create_scram_config(bootstrap_servers: str, username: str, password: str, topic: str) -> MSKConfig:
    """创建 SCRAM-SHA-512 配置"""
    return MSKConfig(
        bootstrap_servers=bootstrap_servers,
        topic_name=topic,
        username=username,
        password=password,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        region="us-east-2"
    )


def send_user_events():
    """发送用户事件数据示例"""
    
    # MSK 集群配置
    config = create_scram_config(
        bootstrap_servers="b-1.your-cluster.xxxxx.kafka.us-east-2.amazonaws.com:9096,b-2.your-cluster.xxxxx.kafka.us-east-2.amazonaws.com:9096",
        username="kafka-user",
        password="your-secure-password",
        topic="user-events"
    )
    
    producer = MSKProducer(config)
    
    try:
        if not producer.connect():
            print("❌ 连接 MSK 失败")
            return
            
        print("✅ 成功连接到 MSK 集群")
        
        # 用户行为事件数据
        events = [
            {
                "event_type": "login",
                "user_id": "user_001",
                "timestamp": int(time.time() * 1000),
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            {
                "event_type": "page_view",
                "user_id": "user_001", 
                "page": "/dashboard",
                "timestamp": int(time.time() * 1000),
                "session_id": "sess_12345"
            },
            {
                "event_type": "purchase",
                "user_id": "user_002",
                "product_id": "prod_789",
                "amount": 99.99,
                "currency": "USD",
                "timestamp": int(time.time() * 1000)
            }
        ]
        
        # 发送事件
        success_count = 0
        for event in events:
            if producer.send_message(event, key=event["user_id"]):
                success_count += 1
                print(f"✅ 发送事件: {event['event_type']} - 用户: {event['user_id']}")
            else:
                print(f"❌ 发送失败: {event['event_type']}")
                
        print(f"\n📊 发送统计: {success_count}/{len(events)} 条消息成功")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {str(e)}")
    finally:
        producer.close()


def send_application_logs():
    """发送应用日志示例"""
    
    config = create_scram_config(
        bootstrap_servers="b-1.your-cluster.xxxxx.kafka.us-east-2.amazonaws.com:9096",
        username="log-producer",
        password="log-password",
        topic="application-logs"
    )
    
    producer = MSKProducer(config)
    
    try:
        if not producer.connect():
            print("❌ 连接 MSK 失败")
            return
            
        print("✅ 成功连接到 MSK 集群")
        
        # 应用日志数据
        logs = []
        log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        services = ["user-service", "order-service", "payment-service"]
        
        for i in range(20):
            log = {
                "timestamp": int(time.time() * 1000) + i,
                "level": log_levels[i % len(log_levels)],
                "service": services[i % len(services)],
                "message": f"处理请求 #{i+1}",
                "request_id": f"req_{i+1:03d}",
                "duration_ms": 50 + (i * 10) % 200
            }
            logs.append(log)
            
        # 批量发送日志
        success_count = producer.send_batch_messages(logs, batch_size=5)
        print(f"\n📊 日志发送统计: {success_count}/{len(logs)} 条消息成功")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {str(e)}")
    finally:
        producer.close()


def test_connection():
    """测试连接功能"""
    
    print("🔧 测试 MSK SCRAM-SHA-512 连接...")
    
    # 请替换为你的实际配置
    config = create_scram_config(
        bootstrap_servers="your-msk-cluster:9096",
        username="test-user",
        password="test-password",
        topic="test-topic"
    )
    
    producer = MSKProducer(config)
    
    try:
        if producer.connect():
            print("✅ 连接测试成功")
            
            # 发送测试消息
            test_msg = {
                "test": True,
                "message": "Hello MSK with SCRAM-SHA-512!",
                "timestamp": int(time.time() * 1000)
            }
            
            if producer.send_message(test_msg, key="test"):
                print("✅ 测试消息发送成功")
            else:
                print("❌ 测试消息发送失败")
        else:
            print("❌ 连接测试失败")
            
    except Exception as e:
        print(f"❌ 连接测试出错: {str(e)}")
    finally:
        producer.close()


if __name__ == "__main__":
    print("AWS MSK SCRAM-SHA-512 认证示例")
    print("=" * 40)
    
    while True:
        print("\n选择操作:")
        print("1. 测试连接")
        print("2. 发送用户事件")
        print("3. 发送应用日志")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            test_connection()
        elif choice == "2":
            send_user_events()
        elif choice == "3":
            send_application_logs()
        elif choice == "4":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")