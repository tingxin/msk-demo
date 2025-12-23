#!/bin/bash

# AWS MSK 公共访问启用脚本
# 用法: ./enable-msk-public-access.sh <cluster-arn>

set -e

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <cluster-arn>"
    echo "示例: $0 arn:aws:kafka:us-east-2:515491257789:cluster/test/ba888316-aa4e-4432-a3a5-7a344b68ee8f-3"
    exit 1
fi

CLUSTER_ARN="$1"

echo "正在获取 MSK 集群信息..."

# 获取集群的当前版本
CURRENT_VERSION=$(aws kafka describe-cluster \
    --cluster-arn "$CLUSTER_ARN" \
    --query 'ClusterInfo.CurrentVersion' \
    --output text)

if [ -z "$CURRENT_VERSION" ] || [ "$CURRENT_VERSION" = "None" ]; then
    echo "错误: 无法获取集群版本"
    exit 1
fi

echo "集群当前版本: $CURRENT_VERSION"

# 获取集群状态
CLUSTER_STATE=$(aws kafka describe-cluster \
    --cluster-arn "$CLUSTER_ARN" \
    --query 'ClusterInfo.State' \
    --output text)

echo "集群状态: $CLUSTER_STATE"

if [ "$CLUSTER_STATE" != "ACTIVE" ]; then
    echo "警告: 集群状态不是 ACTIVE，当前状态为 $CLUSTER_STATE"
    echo "只有在 ACTIVE 状态下才能更新连接性配置"
    exit 1
fi

# 检查当前连接性配置
echo "检查当前连接性配置..."
aws kafka describe-cluster \
    --cluster-arn "$CLUSTER_ARN" \
    --query 'ClusterInfo.BrokerNodeGroupInfo.ConnectivityInfo' \
    --output json

echo ""
echo "正在启用公共访问..."

# 更新连接性配置以启用公共访问
aws kafka update-connectivity \
    --cluster-arn "$CLUSTER_ARN" \
    --current-version "$CURRENT_VERSION" \
    --connectivity-info '{
        "PublicAccess": {
            "Type": "SERVICE_PROVIDED_EIPS"
        }
    }'

if [ $? -eq 0 ]; then
    echo "✅ 公共访问配置更新请求已提交成功"
    echo ""
    echo "注意事项:"
    echo "1. 更新过程可能需要几分钟时间"
    echo "2. 可以使用以下命令检查更新状态:"
    echo "   aws kafka describe-cluster --cluster-arn \"$CLUSTER_ARN\" --query 'ClusterInfo.State'"
    echo ""
    echo "3. 更新完成后，可以使用以下命令获取公共端点:"
    echo "   aws kafka get-bootstrap-brokers --cluster-arn \"$CLUSTER_ARN\""
else
    echo "❌ 公共访问配置更新失败"
    exit 1
fi