# AWS MSK Python Producer 使用指南 (SCRAM-SHA-512 认证)

## 安装依赖

### 方法 1: 使用 confluent-kafka (推荐)

```bash
# 安装 confluent-kafka 版本的依赖
pip3 install -r requirements_confluent.txt

# 或者单独安装
pip3 install confluent-kafka==2.3.0 boto3==1.34.0
```

### 方法 2: 使用 kafka-python (如果遇到问题)

```bash
# 运行修复脚本
python3 fix_kafka_dependencies.py

# 或者手动安装
pip3 install -r requirements.txt
```

## 推荐使用方案

如果遇到 `No module named 'kafka.vendor.six.moves'` 错误，推荐使用 **confluent-kafka** 版本：

```bash
# 使用更稳定的 confluent-kafka 版本
python3 msk_producer_confluent.py
```

## MSK 用户管理

### 创建 SCRAM 用户

```bash
# 使用 AWS CLI 创建 SCRAM 用户
aws kafka create-scram-secret \
    --cluster-arn arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/12345678-1234-1234-1234-123456789012-1 \
    --secret-arn arn:aws:secretsmanager:us-east-1:123456789012:secret:AmazonMSK_my-secret \
    --username kafka-user \
    --password your-secure-password

# 列出现有用户
aws kafka list-scram-secrets \
    --cluster-arn arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/12345678-1234-1234-1234-123456789012-1
```

### 使用 AWS Secrets Manager 管理密码

```bash
# 创建密钥
aws secretsmanager create-secret \
    --name "msk-scram-credentials" \
    --description "MSK SCRAM-SHA-512 用户凭证" \
    --secret-string '{"username":"kafka-user","password":"your-secure-password"}'
```

## MSK 集群信息获取

### 获取 Bootstrap Servers
```bash
# 使用 AWS CLI 获取集群信息
aws kafka describe-cluster --cluster-arn arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/12345678-1234-1234-1234-123456789012-1

# 获取 Bootstrap Brokers
aws kafka get-bootstrap-brokers --cluster-arn arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/12345678-1234-1234-1234-123456789012-1
```

## 使用示例

### 1. 基本使用（SCRAM-SHA-512 认证）- confluent-kafka 版本

```python
from msk_producer_confluent import MSKProducer, MSKConfig

# 配置
config = MSKConfig(
    bootstrap_servers="b-1.your-cluster.xxxxx.kafka.us-east-1.amazonaws.com:9096",
    topic_name="your-topic",
    username="kafka-user",
    password="your-secure-password",
    security_protocol="SASL_SSL",
    sasl_mechanism="SCRAM-SHA-512",
    region="us-east-1"
)

# 创建生产者并发送消息
producer = MSKProducer(config)
if producer.connect():
    message = {"user_id": "123", "action": "login"}
    producer.send_message(message, key="user_123")
    producer.close()
```

### 2. 使用简化示例脚本

```bash
# 推荐：使用 confluent-kafka 版本
python3 msk_producer_confluent.py

# 或者使用 kafka-python 版本
python3 msk_producer.py

# 交互式示例
python3 msk_scram_example.py
```

### 3. 批量发送

```python
messages = [
    {"id": 1, "data": "message 1"},
    {"id": 2, "data": "message 2"},
    {"id": 3, "data": "message 3"}
]

success_count = producer.send_batch_messages(messages, batch_size=10)
```

## MSK 集群端口说明

- **9092**: PLAINTEXT (不加密，不推荐生产使用)
- **9094**: TLS (加密但无认证)
- **9096**: SASL_SSL with SCRAM-SHA-512 (推荐)
- **9098**: SASL_SSL with IAM

## 常见问题

### 1. 连接超时
- 检查安全组是否允许端口 9096
- 确认 MSK 集群状态为 ACTIVE
- 验证 VPC 网络连通性

### 2. SCRAM 认证失败
- 验证用户名密码正确
- 确认用户已在 MSK 集群中创建
- 检查 SCRAM 密钥是否正确关联

### 3. Topic 不存在
```bash
# 使用 Kafka 客户端工具创建 Topic
kafka-topics.sh --create \
    --bootstrap-server your-cluster:9096 \
    --command-config client.properties \
    --topic your-topic \
    --partitions 3 \
    --replication-factor 2
```

### 4. 客户端配置文件示例 (client.properties)
```properties
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="kafka-user" password="your-password";
```

## 运行示例

```bash
# 推荐：使用 confluent-kafka 版本（更稳定）
python3 msk_producer_confluent.py

# 或者使用 kafka-python 版本
python3 msk_producer.py

# 交互式 SCRAM 示例
python3 msk_scram_example.py

# 运行配置示例
python3 msk_config_example.py

# 如果遇到依赖问题，运行修复脚本
python3 fix_kafka_dependencies.py
```

## 故障排除

### 依赖问题解决方案

如果遇到 `No module named 'kafka.vendor.six.moves'` 错误：

1. **推荐方案**：使用 confluent-kafka
```bash
pip3 install confluent-kafka==2.3.0 boto3==1.34.0
python3 msk_producer_confluent.py
```

2. **修复 kafka-python**：
```bash
python3 fix_kafka_dependencies.py
```

3. **手动修复**：
```bash
pip3 uninstall kafka-python -y
pip3 install six==1.16.0
pip3 install kafka-python==2.0.1
```

## SCRAM 用户权限配置

### 创建具有适当权限的 SCRAM 用户

```bash
# 1. 创建 SCRAM 用户
aws kafka put-cluster-policy \
    --cluster-arn arn:aws:kafka:region:account:cluster/cluster-name/cluster-id \
    --policy '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": [
                    "kafka-cluster:Connect",
                    "kafka-cluster:WriteData",
                    "kafka-cluster:ReadData"
                ],
                "Resource": "*"
            }
        ]
    }'

# 2. 为用户分配 Topic 权限
# 这通常通过 Kafka ACL 完成，需要使用 Kafka 管理工具
```