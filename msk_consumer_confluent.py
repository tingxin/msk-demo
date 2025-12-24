#!/usr/bin/env python3
"""
AWS MSK Consumer - 使用 confluent-kafka 库
消费 MSK 中的消息
"""

import json
import logging
import time
import signal
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from confluent_kafka import Consumer, KafkaError, KafkaException


@dataclass
class MSKConsumerConfig:
    """MSK Consumer 连接配置"""
    bootstrap_servers: str
    topic_name: str
    group_id: str
    username: str
    password: str
    security_protocol: str = "SASL_SSL"
    sasl_mechanism: str = "SCRAM-SHA-512"
    region: str = "us-east-1"
    auto_offset_reset: str = "earliest"  # earliest, latest


class MSKConsumer:
    """AWS MSK 消费者类 - 使用 confluent-kafka"""
    
    def __init__(self, config: MSKConsumerConfig):
        self.config = config
        self.consumer = None
        self.logger = self._setup_logger()
        self.running = True
        
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
    
    def _get_consumer_config(self) -> Dict[str, Any]:
        """获取 Kafka Consumer 配置"""
        config = {
            'bootstrap.servers': self.config.bootstrap_servers,
            'group.id': self.config.group_id,
            'auto.offset.reset': self.config.auto_offset_reset,
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000,
            'session.timeout.ms': 30000,
            'heartbeat.interval.ms': 10000,
            'max.poll.interval.ms': 300000,
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
            consumer_config = self._get_consumer_config()
            self.consumer = Consumer(consumer_config)
            
            # 订阅 Topic
            self.consumer.subscribe([self.config.topic_name])
            
            self.logger.info(f"成功连接到 MSK 集群: {self.config.bootstrap_servers}")
            self.logger.info(f"订阅 Topic: {self.config.topic_name}, Group: {self.config.group_id}")
            return True
                
        except Exception as e:
            self.logger.error(f"连接 MSK 失败: {str(e)}")
            return False
    
    def process_message(self, message: Dict[str, Any]) -> bool:
        """处理消息的业务逻辑 - 可以重写此方法"""
        try:
            # 默认处理逻辑：打印消息内容
            self.logger.info(f"处理消息: {json.dumps(message, indent=2, ensure_ascii=False)}")
            
            # 在这里添加你的业务逻辑
            # 例如：保存到数据库、调用API、发送通知等
            
            return True
        except Exception as e:
            self.logger.error(f"处理消息失败: {str(e)}")
            return False
    
    def consume_messages(self, timeout: float = 1.0) -> None:
        """消费消息"""
        if not self.consumer:
            self.logger.error("Consumer 未初始化，请先调用 connect()")
            return
            
        self.logger.info("开始消费消息...")
        message_count = 0
        
        try:
            while self.running:
                msg = self.consumer.poll(timeout=timeout)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # 到达分区末尾
                        self.logger.info(f"到达分区末尾: {msg.topic()}[{msg.partition()}] at offset {msg.offset()}")
                    else:
                        self.logger.error(f"Consumer 错误: {msg.error()}")
                    continue
                
                try:
                    # 解析消息
                    message_value = msg.value().decode('utf-8')
                    message_data = json.loads(message_value)
                    
                    # 添加元数据
                    message_data['_kafka_metadata'] = {
                        'topic': msg.topic(),
                        'partition': msg.partition(),
                        'offset': msg.offset(),
                        'key': msg.key().decode('utf-8') if msg.key() else None,
                        'timestamp': msg.timestamp()[1] if msg.timestamp()[1] > 0 else None
                    }
                    
                    # 处理消息
                    if self.process_message(message_data):
                        message_count += 1
                        if message_count % 100 == 0:
                            self.logger.info(f"已处理 {message_count} 条消息")
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON 解析失败: {str(e)}, 原始消息: {msg.value()}")
                except Exception as e:
                    self.logger.error(f"处理消息时出错: {str(e)}")
                    
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，停止消费...")
        except Exception as e:
            self.logger.error(f"消费过程中出错: {str(e)}")
        finally:
            self.logger.info(f"总共处理了 {message_count} 条消息")
    
    def consume_batch_messages(self, batch_size: int = 10, timeout: float = 1.0) -> None:
        """批量消费消息"""
        if not self.consumer:
            self.logger.error("Consumer 未初始化，请先调用 connect()")
            return
            
        self.logger.info(f"开始批量消费消息，批次大小: {batch_size}")
        message_count = 0
        
        try:
            while self.running:
                messages = self.consumer.consume(num_messages=batch_size, timeout=timeout)
                
                if not messages:
                    continue
                
                batch_data = []
                
                for msg in messages:
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            self.logger.info(f"到达分区末尾: {msg.topic()}[{msg.partition()}] at offset {msg.offset()}")
                        else:
                            self.logger.error(f"Consumer 错误: {msg.error()}")
                        continue
                    
                    try:
                        # 解析消息
                        message_value = msg.value().decode('utf-8')
                        message_data = json.loads(message_value)
                        
                        # 添加元数据
                        message_data['_kafka_metadata'] = {
                            'topic': msg.topic(),
                            'partition': msg.partition(),
                            'offset': msg.offset(),
                            'key': msg.key().decode('utf-8') if msg.key() else None,
                            'timestamp': msg.timestamp()[1] if msg.timestamp()[1] > 0 else None
                        }
                        
                        batch_data.append(message_data)
                        
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON 解析失败: {str(e)}")
                    except Exception as e:
                        self.logger.error(f"处理消息时出错: {str(e)}")
                
                # 批量处理消息
                if batch_data:
                    if self.process_batch_messages(batch_data):
                        message_count += len(batch_data)
                        self.logger.info(f"批量处理了 {len(batch_data)} 条消息，总计: {message_count}")
                    
                    # 手动提交偏移量
                    self.consumer.commit()
                    
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，停止消费...")
        except Exception as e:
            self.logger.error(f"批量消费过程中出错: {str(e)}")
        finally:
            self.logger.info(f"总共处理了 {message_count} 条消息")
    
    def process_batch_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """批量处理消息的业务逻辑 - 可以重写此方法"""
        try:
            self.logger.info(f"批量处理 {len(messages)} 条消息")
            
            # 默认处理逻辑：打印消息摘要
            for i, message in enumerate(messages):
                metadata = message.get('_kafka_metadata', {})
                self.logger.info(
                    f"消息 {i+1}: Topic={metadata.get('topic')}, "
                    f"Partition={metadata.get('partition')}, "
                    f"Offset={metadata.get('offset')}, "
                    f"Key={metadata.get('key')}"
                )
            
            # 在这里添加批量处理的业务逻辑
            # 例如：批量插入数据库、批量调用API等
            
            return True
        except Exception as e:
            self.logger.error(f"批量处理消息失败: {str(e)}")
            return False
    
    def get_topic_metadata(self) -> Optional[Dict[str, Any]]:
        """获取 Topic 元数据"""
        if not self.consumer:
            self.logger.error("Consumer 未初始化")
            return None
            
        try:
            metadata = self.consumer.list_topics(topic=self.config.topic_name, timeout=10)
            topic_metadata = metadata.topics.get(self.config.topic_name)
            
            if topic_metadata:
                return {
                    'topic': self.config.topic_name,
                    'partitions': len(topic_metadata.partitions),
                    'partition_details': {
                        partition_id: {
                            'leader': partition.leader,
                            'replicas': partition.replicas,
                            'isrs': partition.isrs
                        }
                        for partition_id, partition in topic_metadata.partitions.items()
                    }
                }
            return None
            
        except Exception as e:
            self.logger.error(f"获取 Topic 元数据失败: {str(e)}")
            return None
    
    def stop(self):
        """停止消费"""
        self.running = False
        self.logger.info("停止消费信号已发送")
    
    def close(self):
        """关闭 Consumer"""
        if self.consumer:
            self.consumer.close()
            self.logger.info("MSK Consumer 已关闭")


def signal_handler(signum, frame):
    """信号处理器"""
    print("\n收到停止信号，正在关闭...")
    global consumer_instance
    if consumer_instance:
        consumer_instance.stop()


def main():
    """主函数 - 使用示例"""
    global consumer_instance
    
    # 配置 MSK Consumer 连接信息
    consumer_config = MSKConsumerConfig(
        bootstrap_servers="b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196,b-2-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196",
        topic_name="test-topic",
        group_id="demo-consumer-group",
        username="demo",
        password="Demo1234",
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        region="us-east-2",
        auto_offset_reset="earliest"  # 从最早的消息开始消费
    )
    
    # 创建消费者
    consumer_instance = MSKConsumer(consumer_config)
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 连接到 MSK
        if not consumer_instance.connect():
            print("连接失败，退出程序")
            return
            
        # 获取 Topic 元数据
        metadata = consumer_instance.get_topic_metadata()
        if metadata:
            print(f"Topic 信息: {json.dumps(metadata, indent=2)}")
            
        print("开始消费消息... (按 Ctrl+C 停止)")
        
        # 选择消费模式
        mode = input("选择消费模式 (1: 单条消费, 2: 批量消费): ").strip()
        
        if mode == "2":
            batch_size = input("输入批次大小 (默认 10): ").strip()
            batch_size = int(batch_size) if batch_size.isdigit() else 10
            consumer_instance.consume_batch_messages(batch_size=batch_size)
        else:
            consumer_instance.consume_messages()
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        consumer_instance.close()


if __name__ == "__main__":
    consumer_instance = None
    main()