#!/usr/bin/env python3
"""
AWS MSK 配置示例和使用场景
"""

from msk_producer import MSKProducer, MSKConfig


def example_iam_authentication():
    """使用 IAM 认证的示例（推荐用于生产环境）"""
    config = MSKConfig(
        bootstrap_servers="b-1.your-cluster.xxxxx.kafka.us-east-1.amazonaws.com:9098,b-2.your-cluster.xxxxx.kafka.us-east-1.amazonaws.com:9098",
        topic_name="user-events",
        security_protocol="SASL_SSL",
        sasl_mechanism="AWS_MSK_IAM",
        region="us-east-1"
    )
    
    producer = MSKProducer(config)
    
    if producer.connect():
        # 发送用户行为数据
        event_data = {
            "event_id": "evt_001",
            "user_id": "user_12345",
            "event_type": "purchase",
            "product_id": "prod_789",
            "amount": 99.99,
            "currency": "USD"
        }
        
        producer.send_message(event_data, key=event_data["user_id"])
        producer.close()


def example_scram_authentication():
    """使用 SCRAM-SHA-512 认证的示例"""
    config = MSKConfig(
        bootstrap_servers="b-1.your-cluster.xxxxx.kafka.us-east-1.amazonaws.com:9096",
        topic_name="application-logs",
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        username="kafka-user",
        password="your-secure-password",
        region="us-east-1"
    )
    
    producer = MSKProducer(config)
    
    if producer.connect():
        # 发送应用日志
        log_data = {
            "level": "INFO",
            "service": "user-service",
            "message": "User login successful",
            "user_id": "user_456",
            "request_id": "req_789"
        }
        
        producer.send_message(log_data, key=log_data["service"])
        producer.close()


def example_plaintext():
    """使用 PLAINTEXT 的示例（仅用于开发环境）"""
    config = MSKConfig(
        bootstrap_servers="localhost:9092",  # 本地开发环境
        topic_name="dev-testing",
        security_protocol="PLAINTEXT"
    )
    
    producer = MSKProducer(config)
    
    if producer.connect():
        # 发送测试数据
        test_data = {
            "test_id": "test_001",
            "environment": "development",
            "data": {"key": "value", "number": 42}
        }
        
        producer.send_message(test_data)
        producer.close()


def example_batch_processing():
    """批量处理示例"""
    config = MSKConfig(
        bootstrap_servers="your-msk-cluster.kafka.us-east-1.amazonaws.com:9098",
        topic_name="sensor-data",
        security_protocol="SASL_SSL",
        sasl_mechanism="AWS_MSK_IAM",
        region="us-east-1"
    )
    
    producer = MSKProducer(config)
    
    if producer.connect():
        # 模拟传感器数据
        sensor_data = []
        for i in range(100):
            data = {
                "sensor_id": f"sensor_{i % 10}",
                "temperature": 20 + (i % 30),
                "humidity": 40 + (i % 40),
                "location": f"building_A_floor_{i % 5}"
            }
            sensor_data.append(data)
        
        # 批量发送
        success_count = producer.send_batch_messages(sensor_data, batch_size=20)
        print(f"传感器数据发送完成: {success_count} 条")
        
        producer.close()


if __name__ == "__main__":
    print("选择运行示例:")
    print("1. IAM 认证示例")
    print("2. SCRAM 认证示例") 
    print("3. PLAINTEXT 示例")
    print("4. 批量处理示例")
    
    choice = input("请输入选择 (1-4): ")
    
    if choice == "1":
        example_iam_authentication()
    elif choice == "2":
        example_scram_authentication()
    elif choice == "3":
        example_plaintext()
    elif choice == "4":
        example_batch_processing()
    else:
        print("无效选择")