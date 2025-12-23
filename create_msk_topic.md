# AWS MSK Topic 创建指南

## 方法 1: 使用 AWS CLI 创建 Topic

### 前提条件
- 安装 AWS CLI
- 配置适当的 IAM 权限
- 获取 MSK 集群 ARN

### 创建 Topic
```bash
# 获取集群 ARN
aws kafka list-clusters --query 'ClusterInfoList[*].[ClusterName,ClusterArn]' --output table

# 创建 Topic (需要集群支持 auto.create.topics.enable=true)
# 注意：MSK 默认不支持通过 AWS CLI 直接创建 Topic
```

## 方法 2: 使用 Kafka 客户端工具创建 Topic

### 安装 Kafka 客户端
```bash
# 下载 Kafka
wget https://downloads.apache.org/kafka/2.8.1/kafka_2.13-2.8.1.tgz
tar -xzf kafka_2.13-2.8.1.tgz
cd kafka_2.13-2.8.1
```

### 创建客户端配置文件
```bash
# 创建 client.properties 文件
cat > client.properties << EOF
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="demo" password="your-password";
EOF
```

### 创建 Topic
```bash
# 创建 Topic
./bin/kafka-topics.sh --create \
    --bootstrap-server b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196 \
    --command-config client.properties \
    --topic test-topic \
    --partitions 3 \
    --replication-factor 2

# 列出所有 Topic
./bin/kafka-topics.sh --list \
    --bootstrap-server b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196 \
    --command-config client.properties

# 查看 Topic 详情
./bin/kafka-topics.sh --describe \
    --bootstrap-server b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196 \
    --command-config client.properties \
    --topic test-topic
```

## 方法 3: 使用 Python 脚本创建 Topic

### 创建 Topic 脚本
```python
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaError

def create_topic():
    # 配置
    config = {
        'bootstrap.servers': 'b-1-public.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9196',
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'SCRAM-SHA-512',
        'sasl.username': 'demo',
        'sasl.password': 'your-password'
    }
    
    # 创建管理客户端
    admin_client = AdminClient(config)
    
    # 定义新 Topic
    topic_list = [NewTopic(
        topic="test-topic",
        num_partitions=3,
        replication_factor=2
    )]
    
    # 创建 Topic
    fs = admin_client.create_topics(topic_list)
    
    # 等待结果
    for topic, f in fs.items():
        try:
            f.result()  # 等待操作完成
            print(f"Topic {topic} 创建成功")
        except Exception as e:
            print(f"创建 Topic {topic} 失败: {e}")

if __name__ == "__main__":
    create_topic()
```

## 方法 4: 通过 AWS MSK 控制台

1. 登录 AWS 控制台
2. 进入 MSK 服务
3. 选择你的集群
4. 在 "Topics" 标签页中点击 "Create topic"
5. 填写 Topic 名称和配置
6. 点击创建

## 权限问题解决

### 检查 SCRAM 用户权限
```bash
# 列出 SCRAM 用户
aws kafka list-scram-secrets \
    --cluster-arn arn:aws:kafka:us-east-2:123456789012:cluster/test/xxxxx

# 检查用户是否有创建 Topic 的权限
```

### 为用户添加权限 (需要管理员权限)
```bash
# 使用 Kafka ACL 添加权限
./bin/kafka-acls.sh --authorizer-properties zookeeper.connect=localhost:2181 \
    --add --allow-principal User:demo \
    --operation Create --topic test-topic

# 或者给用户所有 Topic 的权限
./bin/kafka-acls.sh --authorizer-properties zookeeper.connect=localhost:2181 \
    --add --allow-principal User:demo \
    --operation All --topic '*'
```

## 快速解决方案

### 1. 使用现有 Topic
如果集群中已有其他 Topic，可以先使用现有的进行测试：

```python
# 修改代码中的 topic_name
topic_name = "existing-topic-name"
```

### 2. 请求管理员创建
联系 MSK 集群管理员，请求创建以下 Topic：
- Topic 名称: `test-topic`
- 分区数: 3
- 副本数: 2

### 3. 临时使用自动创建 (如果启用)
某些 MSK 集群配置了自动创建 Topic，第一次发送消息时会自动创建。

## 验证 Topic 创建成功

```bash
# 使用我们的测试脚本验证
python3 msk_connection_test.py
```

创建成功后，应该能看到 Topic 列表中包含 `test-topic`。