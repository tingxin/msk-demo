#!/bin/bash

# AWS MSK 公共访问完整配置脚本
# 解决 allow.everyone.if.no.acl.found 配置问题

set -e

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <cluster-arn>"
    echo "示例: $0 arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3"
    exit 1
fi

CLUSTER_ARN="$1"

echo "=== AWS MSK 公共访问配置脚本 ==="
echo "集群 ARN: $CLUSTER_ARN"
echo ""

# 获取集群信息
echo "1. 获取集群信息..."
CURRENT_VERSION=$(aws kafka describe-cluster \
    --cluster-arn "$CLUSTER_ARN" \
    --query 'ClusterInfo.CurrentVersion' \
    --output text)

CLUSTER_STATE=$(aws kafka describe-cluster \
    --cluster-arn "$CLUSTER_ARN" \
    --query 'ClusterInfo.State' \
    --output text)

echo "   集群版本: $CURRENT_VERSION"
echo "   集群状态: $CLUSTER_STATE"

if [ "$CLUSTER_STATE" != "ACTIVE" ]; then
    echo "❌ 错误: 集群状态不是 ACTIVE，无法进行配置更新"
    exit 1
fi

# 检查当前配置
echo ""
echo "2. 检查当前集群配置..."
CURRENT_CONFIG_ARN=$(aws kafka describe-cluster \
    --cluster-arn "$CLUSTER_ARN" \
    --query 'ClusterInfo.CurrentBrokerSoftwareInfo.ConfigurationArn' \
    --output text)

echo "   当前配置 ARN: $CURRENT_CONFIG_ARN"

# 创建新的配置
echo ""
echo "3. 创建支持公共访问的新配置..."

# 生成配置文件
cat > msk-public-config.properties << 'EOF'
# MSK 公共访问必需配置
allow.everyone.if.no.acl.found=false

# 其他推荐的安全配置
auto.create.topics.enable=false
delete.topic.enable=false
log.retention.hours=168
num.partitions=3
default.replication.factor=3
min.insync.replicas=2

# 性能优化配置
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
EOF

echo "   配置文件内容:"
cat msk-public-config.properties

# 创建配置
CONFIG_NAME="msk-public-access-config-$(date +%Y%m%d-%H%M%S)"
echo ""
echo "4. 创建新配置: $CONFIG_NAME"

NEW_CONFIG_ARN=$(aws kafka create-configuration \
    --name "$CONFIG_NAME" \
    --description "MSK configuration for public access with security settings" \
    --kafka-versions "2.8.1" "3.3.2" "3.4.0" "3.5.1" "3.6.0" "3.7.x" "3.8.x" \
    --server-properties fileb://msk-public-config.properties \
    --query 'Arn' \
    --output text)

echo "   新配置 ARN: $NEW_CONFIG_ARN"

# 等待配置创建完成
echo ""
echo "5. 等待配置创建完成..."
while true; do
    CONFIG_STATE=$(aws kafka describe-configuration \
        --arn "$NEW_CONFIG_ARN" \
        --query 'State' \
        --output text)
    
    echo "   配置状态: $CONFIG_STATE"
    
    if [ "$CONFIG_STATE" = "ACTIVE" ]; then
        break
    elif [ "$CONFIG_STATE" = "DELETE_FAILED" ] || [ "$CONFIG_STATE" = "DELETING" ]; then
        echo "❌ 配置创建失败"
        exit 1
    fi
    
    sleep 10
done

# 更新集群配置
echo ""
echo "6. 更新集群配置..."
aws kafka update-cluster-configuration \
    --cluster-arn "$CLUSTER_ARN" \
    --current-version "$CURRENT_VERSION" \
    --configuration-info "Arn=$NEW_CONFIG_ARN,Revision=1"

echo "   配置更新请求已提交"

# 等待配置更新完成
echo ""
echo "7. 等待集群配置更新完成..."
echo "   这可能需要 10-15 分钟，请耐心等待..."

while true; do
    CLUSTER_STATE=$(aws kafka describe-cluster \
        --cluster-arn "$CLUSTER_ARN" \
        --query 'ClusterInfo.State' \
        --output text)
    
    echo "   集群状态: $CLUSTER_STATE ($(date))"
    
    if [ "$CLUSTER_STATE" = "ACTIVE" ]; then
        # 检查配置是否已更新
        UPDATED_CONFIG_ARN=$(aws kafka describe-cluster \
            --cluster-arn "$CLUSTER_ARN" \
            --query 'ClusterInfo.CurrentBrokerSoftwareInfo.ConfigurationArn' \
            --output text)
        
        if [ "$UPDATED_CONFIG_ARN" = "$NEW_CONFIG_ARN" ]; then
            echo "   ✅ 集群配置更新完成"
            break
        fi
    elif [ "$CLUSTER_STATE" = "FAILED" ]; then
        echo "❌ 集群配置更新失败"
        exit 1
    fi
    
    sleep 30
done

# 获取新的集群版本
echo ""
echo "8. 获取更新后的集群版本..."
NEW_CLUSTER_VERSION=$(aws kafka describe-cluster \
    --cluster-arn "$CLUSTER_ARN" \
    --query 'ClusterInfo.CurrentVersion' \
    --output text)

echo "   新集群版本: $NEW_CLUSTER_VERSION"

# 启用公共访问
echo ""
echo "9. 启用公共访问..."
aws kafka update-connectivity \
    --cluster-arn "$CLUSTER_ARN" \
    --current-version "$NEW_CLUSTER_VERSION" \
    --connectivity-info '{
        "PublicAccess": {
            "Type": "SERVICE_PROVIDED_EIPS"
        }
    }'

echo "   公共访问启用请求已提交"

# 等待公共访问配置完成
echo ""
echo "10. 等待公共访问配置完成..."
echo "    这可能需要 5-10 分钟..."

while true; do
    CLUSTER_STATE=$(aws kafka describe-cluster \
        --cluster-arn "$CLUSTER_ARN" \
        --query 'ClusterInfo.State' \
        --output text)
    
    echo "    集群状态: $CLUSTER_STATE ($(date))"
    
    if [ "$CLUSTER_STATE" = "ACTIVE" ]; then
        # 检查公共访问是否已启用
        PUBLIC_ACCESS_TYPE=$(aws kafka describe-cluster \
            --cluster-arn "$CLUSTER_ARN" \
            --query 'ClusterInfo.BrokerNodeGroupInfo.ConnectivityInfo.PublicAccess.Type' \
            --output text)
        
        if [ "$PUBLIC_ACCESS_TYPE" = "SERVICE_PROVIDED_EIPS" ]; then
            echo "    ✅ 公共访问配置完成"
            break
        fi
    elif [ "$CLUSTER_STATE" = "FAILED" ]; then
        echo "❌ 公共访问配置失败"
        exit 1
    fi
    
    sleep 30
done

# 获取公共端点
echo ""
echo "11. 获取公共访问端点..."
aws kafka get-bootstrap-brokers --cluster-arn "$CLUSTER_ARN"

echo ""
echo "🎉 MSK 公共访问配置完成！"
echo ""
echo "重要提醒:"
echo "1. 公共访问已启用，请确保配置了适当的安全组规则"
echo "2. 建议配置 SASL/SCRAM 或 IAM 身份验证"
echo "3. 定期审查访问日志和安全配置"
echo ""
echo "清理临时文件..."
rm -f msk-public-config.properties

echo "脚本执行完成！"