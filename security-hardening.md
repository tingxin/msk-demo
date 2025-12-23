# Docker 容器安全加固建议

## 立即采取的措施

### 1. 网络安全
```bash
# 限制容器只监听本地接口
docker run -p 127.0.0.1:8080:8080 your-image

# 或使用防火墙规则限制访问
iptables -A INPUT -p tcp --dport 8080 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP
```

### 2. 应用层防护
```python
# 在应用中添加请求验证
from urllib.parse import urlparse

def validate_request(request_path):
    # 阻止类加载器攻击
    if 'class.module.classLoader' in request_path:
        return False
    
    # 阻止代理请求
    parsed = urlparse(request_path)
    if parsed.netloc and parsed.netloc != 'localhost':
        return False
    
    return True
```

### 3. 容器安全配置
```dockerfile
# 使用非root用户
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# 限制容器权限
# docker run --read-only --tmpfs /tmp your-image
```

## 监控和日志

### 1. 增强日志记录
```python
import logging
import json
from datetime import datetime

def log_security_event(ip, request, status):
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'ip': ip,
        'request': request,
        'status': status,
        'threat_level': classify_threat(request)
    }
    logging.warning(f"SECURITY_EVENT: {json.dumps(event)}")

def classify_threat(request):
    threats = {
        'class.module.classLoader': 'HIGH',
        'http://' in request: 'MEDIUM',
        'SSH-2.0': 'MEDIUM'
    }
    
    for pattern, level in threats.items():
        if pattern in request:
            return level
    return 'LOW'
```

### 2. 实时监控脚本
```bash
#!/bin/bash
# monitor-attacks.sh

tail -f /var/log/app.log | while read line; do
    if echo "$line" | grep -E "(class\.module\.classLoader|SSH-2\.0|http://)" > /dev/null; then
        echo "ALERT: Potential attack detected at $(date)"
        echo "$line"
        # 可以发送告警到监控系统
    fi
done
```

## AWS 环境特定建议

### 1. 使用 AWS WAF
```yaml
# cloudformation template
Resources:
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Rules:
        - Name: BlockJavaAttacks
          Statement:
            ByteMatchStatement:
              SearchString: "class.module.classLoader"
              FieldToMatch:
                UriPath: {}
          Action:
            Block: {}
```

### 2. VPC 安全组配置
```bash
# 只允许特定IP访问
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 8080 \
  --cidr 10.0.0.0/8
```

### 3. 使用 EKS 网络策略
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-external-access
spec:
  podSelector:
    matchLabels:
      app: your-app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: allowed-namespace
```

## 应急响应

### 1. 立即隔离
```bash
# 停止容器
docker stop container-id

# 检查是否有持久化攻击
docker exec container-id find / -name "*.jsp" -o -name "*.war" -newer /tmp/attack-time
```

### 2. 取证分析
```bash
# 导出容器文件系统
docker export container-id > compromised-container.tar

# 分析网络连接
netstat -tulpn | grep :8080
```

### 3. 重新部署
```bash
# 使用加固后的镜像重新部署
docker build -t your-app:secure .
docker run --read-only --tmpfs /tmp -p 127.0.0.1:8080:8080 your-app:secure
```