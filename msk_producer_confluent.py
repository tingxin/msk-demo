#!/usr/bin/env python3
"""
AWS MSK Producer - 使用 confluent-kafka 库
更稳定的替代方案，解决 kafka-python 依赖问题
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from confluent_kafka import Producer
from confluent_kafka.error import KafkaError, KafkaException


@dataclass
class MSKConfig:
    """MSK 连接配置"""
    bootstrap_servers: str
    topic_name: str
    username: str
    password: str
    security_protocol: str = "SASL_SSL"
    sasl_mechanism: str = "SCRAM-SHA-512"
    region: str = "us-east-1"


class MSKProducer:
    """AWS MSK 生产者类 - 使用 confluent-kafka"""
    
    def __init__(self, config: MSKConfig):
        self.config = config
        self.producer = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _get_producer_config(self) -> Dict[str, Any]:
        """获取 Kafka Producer 配置"""
        config = {
            'bootstrap.servers': self.config.bootstrap_servers,
            'acks': 'all',
            'retries': 3,
            'retry.backoff.ms': 1000,
            'request.timeout.ms': 30000,
            'delivery.timeout.ms': 60000,
        }
        
        # 根据安全协议配置认证
        if self.config.security_protocol == "SASL_SSL":
            config.update({
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': self.config.sasl_mechanism,
            })
            
            # SASL/SCRAM 认证
            if self.config.sasl_mechanism == "SCRAM-SHA-512":
                if not (self.config.username and self.config.password):
                    raise ValueError("SCRAM-SHA-512 需要用户名和密码")
                config['sasl.username'] = self.config.username
                config['sasl.password'] = self.config.password
                
        elif self.config.security_protocol == "PLAINTEXT":
            config['security.protocol'] = 'PLAINTEXT'
            
        elif self.config.security_protocol == "SASL_PLAINTEXT":
            config.update({
                'security.protocol': 'SASL_PLAINTEXT',
                'sasl.mechanism': 'SCRAM-SHA-512',
                'sasl.username': self.config.username,
                'sasl.password': self.config.password,
            })
            
        return config
    
    def connect(self) -> bool:
        """连接到 MSK 集群"""
        try:
            producer_config = self._get_producer_config()
            self.producer = Producer(producer_config)
            
            self.logger.info(f"成功连接到 MSK 集群: {self.config.bootstrap_servers}")
            return True
                
        except Exception as e:
            self.logger.error(f"连接 MSK 失败: {str(e)}")
            return False
    
    def _delivery_callback(self, err, msg):
        """消息发送回调函数"""
        if err is not None:
            self.logger.error(f"消息发送失败: {err}")
        else:
            self.logger.info(
                f"消息发送成功 - Topic: {msg.topic()}, "
                f"Partition: {msg.partition()}, "
                f"Offset: {msg.offset()}"
            )
    
    def send_message(self, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """发送消息到 MSK"""
        if not self.producer:
            self.logger.error("Producer 未初始化，请先调用 connect()")
            return False
            
        try:
            # 添加时间戳
            message['timestamp'] = int(time.time() * 1000)
            
            # 序列化消息
            message_json = json.dumps(message)
            key_bytes = key.encode('utf-8') if key else None
            
            # 发送消息
            self.producer.produce(
                topic=self.config.topic_name,
                value=message_json.encode('utf-8'),
                key=key_bytes,
                callback=self._delivery_callback
            )
            
            # 等待发送完成
            self.producer.flush(timeout=10)
            return True
            
        except KafkaException as e:
            self.logger.error(f"Kafka 错误: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            return False
    
    def send_batch_messages(self, messages: list, batch_size: int = 100) -> int:
        """批量发送消息"""
        if not self.producer:
            self.logger.error("Producer 未初始化，请先调用 connect()")
            return 0
            
        success_count = 0
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            for idx, message in enumerate(batch):
                key = f"batch_{i//batch_size}_{idx}"
                
                try:
                    # 添加时间戳
                    message['timestamp'] = int(time.time() * 1000)
                    
                    # 序列化消息
                    message_json = json.dumps(message)
                    
                    # 发送消息（异步）
                    self.producer.produce(
                        topic=self.config.topic_name,
                        value=message_json.encode('utf-8'),
                        key=key.encode('utf-8')
                    )
                    success_count += 1
                    
                except Exception as e:
                    self.logger.error(f"发送消息失败: {str(e)}")
                    
            # 批次间暂停
            time.sleep(0.1)
            
        # 确保所有消息都发送完成
        self.producer.flush()
        
        self.logger.info(f"批量发送完成: {success_count}/{len(messages)} 条消息成功")
        return success_count
    
    def close(self):
        """关闭 Producer"""
        if self.producer:
            self.producer.flush()
            self.logger.info("MSK Producer 已关闭")


def main():
    """主函数 - 使用示例"""
    
    # 配置 MSK 连接信息 - 使用 SCRAM-SHA-512 认证
    msk_config = MSKConfig(
        bootstrap_servers="b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196,b-2-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196",
        topic_name="test-topic",
        username="demo",
        password="Demo1234",
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        region="us-east-2"
    )
    
    # 创建生产者
    producer = MSKProducer(msk_config)
    
    try:
        # 连接到 MSK
        if not producer.connect():
            print("连接失败，退出程序")
            return
            
        # 发送单条消息
        test_message = {
            "user_id": "12345",
            "event_type": "page_view",
            "page": "/home",
            "user_agent": "Mozilla/5.0...",
            "ip_address": "192.168.1.100"
        }
        
        success = producer.send_message(test_message, key="user_12345")
        if success:
            print("单条消息发送成功")
            
        # 批量发送消息
        batch_messages = []
        for i in range(10):
            message = {
                "user_id": f"user_{i}",
                "event_type": "click",
                "button": f"button_{i}",
                "session_id": f"session_{i//3}"  # 每3个用户共享一个session
            }
            batch_messages.append(message)
            
        success_count = producer.send_batch_messages(batch_messages)
        print(f"批量发送完成: {success_count} 条消息")
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        producer.close()


if __name__ == "__main__":
    main()