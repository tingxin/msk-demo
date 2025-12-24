# AWS MSK 公网安全访问配置指南

## 配置流程

### 1. 创建 MSK 集群
- 使用 SASL/SCRAM 认证
- 默认内网访问
- 配置 `allow.everyone.if.no.acl.found=true`（临时设置）

### 2. 创建 SCRAM 用户
```bash
# 创建用户密钥
aws secretsmanager create-secret \
    --name "msk-demo-credentials" \
    --description "MSK SCRAM demo user credentials" \
    --secret-string '{"username":"demo","password":"Demo1234"}'

# 获取密钥 ARN 并关联到集群
SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "msk-demo-credentials" \
    --query 'ARN' \
    --output text)

aws kafka batch-associate-scram-secret \
    --cluster-arn "arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3" \
    --secret-arn-list "$SECRET_ARN"
```

### 3. 使用内网地址创建 Topic
```bash
# 创建客户端配置文件
cat > client.properties << EOF
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="demo" password="Demo1234";
EOF

# 使用内网地址创建 Topic
python3 create_topic.py
```

### 4. 使用内网地址设置用户权限
```bash
# 为 demo 用户添加写入权限
./kafka-acls.sh --bootstrap-server b-1.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9096,b-2.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9096 \
    --command-config client.properties \
    --add --allow-principal User:demo \
    --operation Write --topic "*"

# 添加读取权限
./kafka-acls.sh --bootstrap-server b-1.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9096,b-2.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9096 \
    --command-config client.properties \
    --add --allow-principal User:demo \
    --operation Read --topic "*"

# 添加描述权限
./kafka-acls.sh --bootstrap-server b-1.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9096,b-2.test.ymeaeb.c3.kafka.us-east-2.amazonaws.com:9096 \
    --command-config client.properties \
    --add --allow-principal User:demo \
    --operation Describe --topic "*"
```

### 5. 修改集群配置加固安全
```bash
# 创建安全配置文件
cat > msk-secure-config.properties << EOF
allow.everyone.if.no.acl.found=false
auto.create.topics.enable=false
delete.topic.enable=false
log.retention.hours=168
num.partitions=3
default.replication.factor=2
min.insync.replicas=1
EOF

# 创建新配置
aws kafka create-configuration \
    --name "msk-secure-config-$(date +%Y%m%d-%H%M%S)" \
    --description "MSK secure configuration for public access" \
    --kafka-versions "2.8.1" "3.3.2" "3.4.0" "3.5.1" "3.6.0" "3.7.x" "3.8.x" \
    --server-properties fileb://msk-secure-config.properties

# 获取集群当前版本
CURRENT_VERSION=$(aws kafka describe-cluster \
    --cluster-arn "arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3" \
    --query 'ClusterInfo.CurrentVersion' \
    --output text)

# 更新集群配置
aws kafka update-cluster-configuration \
    --cluster-arn "arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3" \
    --current-version "$CURRENT_VERSION" \
    --configuration-info "Arn=<NEW_CONFIG_ARN>,Revision=1"
```

### 6. 启用公网访问
```bash
# 获取更新后的集群版本
NEW_VERSION=$(aws kafka describe-cluster \
    --cluster-arn "arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3" \
    --query 'ClusterInfo.CurrentVersion' \
    --output text)

# 启用公网访问
aws kafka update-connectivity \
    --cluster-arn "arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3" \
    --current-version "$NEW_VERSION" \
    --connectivity-info '{
        "PublicAccess": {
            "Type": "SERVICE_PROVIDED_EIPS"
        }
    }'
```

### 7. 验证配置
```bash
# 获取公网访问端点
aws kafka get-bootstrap-brokers \
    --cluster-arn "arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3"

# 测试公网访问
python3 msk_producer_confluent.py
```

## 重要说明

- **安全性**: 通过 `allow.everyone.if.no.acl.found=false` 确保只有授权用户可以访问
- **权限管理**: ACL 权限持久化，不会因配置更改而丢失
- **端口区别**: 内网使用 9096，公网使用 9196
- **等待时间**: 配置更新需要 5-15 分钟生效