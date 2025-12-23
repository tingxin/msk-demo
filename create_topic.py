#!/usr/bin/env python3
"""
AWS MSK Topic 创建工具
"""

from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource, ConfigSource
from confluent_kafka import KafkaError
import sys
import time


class MSKTopicManager:
    """MSK Topic 管理器"""
    
    def __init__(self, bootstrap_servers: str, username: str, password: str):
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanism': 'SCRAM-SHA-512',
            'sasl.username': username,
            'sasl.password': password
        }
        self.admin_client = AdminClient(self.config)
    
    def list_topics(self):
        """列出所有 Topic"""
        try:
            metadata = self.admin_client.list_topics(timeout=10)
            topics = list(metadata.topics.keys())
            
            print(f"📋 发现 {len(topics)} 个 Topic:")
            for topic in sorted(topics):
                if not topic.startswith('__'):  # 过滤内部 Topic
                    print(f"  - {topic}")
            
            return topics
        except Exception as e:
            print(f"❌ 获取 Topic 列表失败: {e}")
            return []
    
    def topic_exists(self, topic_name: str) -> bool:
        """检查 Topic 是否存在"""
        topics = self.list_topics()
        return topic_name in topics
    
    def create_topic(self, topic_name: str, num_partitions: int = 3, replication_factor: int = 2):
        """创建 Topic"""
        try:
            # 检查 Topic 是否已存在
            if self.topic_exists(topic_name):
                print(f"⚠️  Topic '{topic_name}' 已存在")
                return True
            
            # 创建新 Topic
            topic_list = [NewTopic(
                topic=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )]
            
            print(f"🔧 创建 Topic: {topic_name} (分区: {num_partitions}, 副本: {replication_factor})")
            
            # 执行创建操作
            fs = self.admin_client.create_topics(topic_list)
            
            # 等待结果
            for topic, f in fs.items():
                try:
                    f.result(timeout=30)  # 等待最多30秒
                    print(f"✅ Topic '{topic}' 创建成功")
                    return True
                except Exception as e:
                    print(f"❌ 创建 Topic '{topic}' 失败: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ 创建 Topic 操作失败: {e}")
            return False
    
    def delete_topic(self, topic_name: str):
        """删除 Topic"""
        try:
            if not self.topic_exists(topic_name):
                print(f"⚠️  Topic '{topic_name}' 不存在")
                return True
            
            print(f"🗑️  删除 Topic: {topic_name}")
            
            # 执行删除操作
            fs = self.admin_client.delete_topics([topic_name])
            
            # 等待结果
            for topic, f in fs.items():
                try:
                    f.result(timeout=30)
                    print(f"✅ Topic '{topic}' 删除成功")
                    return True
                except Exception as e:
                    print(f"❌ 删除 Topic '{topic}' 失败: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ 删除 Topic 操作失败: {e}")
            return False
    
    def describe_topic(self, topic_name: str):
        """描述 Topic 详情"""
        try:
            metadata = self.admin_client.list_topics(timeout=10)
            
            if topic_name not in metadata.topics:
                print(f"❌ Topic '{topic_name}' 不存在")
                return
            
            topic_metadata = metadata.topics[topic_name]
            
            print(f"📊 Topic '{topic_name}' 详情:")
            print(f"  分区数: {len(topic_metadata.partitions)}")
            
            for partition_id, partition in topic_metadata.partitions.items():
                print(f"  分区 {partition_id}:")
                print(f"    Leader: {partition.leader}")
                print(f"    副本: {partition.replicas}")
                print(f"    ISR: {partition.isrs}")
                
        except Exception as e:
            print(f"❌ 获取 Topic 详情失败: {e}")


def main():
    """主函数"""
    print("AWS MSK Topic 管理工具")
    print("=" * 40)
    
    # MSK 集群配置
    bootstrap_servers = "b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196,b-2-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196"
    username = "demo"
    password = input("请输入密码: ").strip()
    
    if not password:
        print("❌ 密码不能为空")
        return
    
    # 创建管理器
    manager = MSKTopicManager(bootstrap_servers, username, password)
    
    while True:
        print("\n选择操作:")
        print("1. 列出所有 Topic")
        print("2. 创建 Topic")
        print("3. 删除 Topic")
        print("4. 查看 Topic 详情")
        print("5. 创建测试 Topic (test-topic)")
        print("6. 退出")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == "1":
            print("\n📋 Topic 列表:")
            manager.list_topics()
            
        elif choice == "2":
            topic_name = input("输入 Topic 名称: ").strip()
            if topic_name:
                partitions = input("输入分区数 (默认 3): ").strip()
                partitions = int(partitions) if partitions.isdigit() else 3
                
                replicas = input("输入副本数 (默认 2): ").strip()
                replicas = int(replicas) if replicas.isdigit() else 2
                
                manager.create_topic(topic_name, partitions, replicas)
            else:
                print("❌ Topic 名称不能为空")
                
        elif choice == "3":
            topic_name = input("输入要删除的 Topic 名称: ").strip()
            if topic_name:
                confirm = input(f"确认删除 Topic '{topic_name}'? (y/N): ").strip().lower()
                if confirm == 'y':
                    manager.delete_topic(topic_name)
                else:
                    print("取消删除")
            else:
                print("❌ Topic 名称不能为空")
                
        elif choice == "4":
            topic_name = input("输入 Topic 名称: ").strip()
            if topic_name:
                manager.describe_topic(topic_name)
            else:
                print("❌ Topic 名称不能为空")
                
        elif choice == "5":
            print("\n🔧 创建测试 Topic...")
            success = manager.create_topic("test-topic", 3, 2)
            if success:
                print("✅ 测试 Topic 创建成功，现在可以运行:")
                print("  python3 msk_producer_confluent.py")
                print("  python3 msk_connection_test.py")
                
        elif choice == "6":
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选择，请重试")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")