#!/bin/bash

# 安全地创建 AWS 凭证 Secret

set -e

NAMESPACE="dolphinscheduler"

# AWS 凭证（从环境变量或参数读取）
AWS_ACCESS_KEY_ID="${1:-AKIAXQBNMLW66MU3476K}"
AWS_SECRET_ACCESS_KEY="${2:-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}"

echo "创建 Kubernetes 命名空间..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "创建 AWS 凭证 Secret..."
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id="$AWS_ACCESS_KEY_ID" \
  --from-literal=secret-access-key="$AWS_SECRET_ACCESS_KEY" \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✓ AWS 凭证已安全存储在 Kubernetes Secret 中"
echo "✓ Secret 名称: aws-credentials"
echo "✓ 命名空间: $NAMESPACE"

# 验证 Secret 创建
echo ""
echo "验证 Secret..."
kubectl get secret aws-credentials -n $NAMESPACE -o yaml | grep -E "access-key-id|secret-access-key" | head -2
