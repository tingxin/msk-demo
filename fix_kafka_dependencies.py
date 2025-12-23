#!/usr/bin/env python3
"""
修复 kafka-python 依赖问题的脚本
"""

import subprocess
import sys
import os


def run_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def fix_kafka_dependencies():
    """修复 kafka-python 依赖问题"""
    
    print("🔧 修复 kafka-python 依赖问题...")
    
    # 卸载可能冲突的包
    print("1. 卸载现有的 kafka-python...")
    success, stdout, stderr = run_command("pip3 uninstall kafka-python -y")
    if success:
        print("✅ 成功卸载 kafka-python")
    else:
        print(f"⚠️  卸载警告: {stderr}")
    
    # 安装 six 包
    print("2. 安装 six 包...")
    success, stdout, stderr = run_command("pip3 install six==1.16.0")
    if success:
        print("✅ 成功安装 six")
    else:
        print(f"❌ 安装 six 失败: {stderr}")
        return False
    
    # 重新安装 kafka-python
    print("3. 重新安装 kafka-python...")
    success, stdout, stderr = run_command("pip3 install kafka-python==2.0.1")
    if success:
        print("✅ 成功安装 kafka-python")
    else:
        print(f"❌ 安装 kafka-python 失败: {stderr}")
        return False
    
    # 安装其他依赖
    print("4. 安装其他依赖...")
    success, stdout, stderr = run_command("pip3 install boto3==1.34.0")
    if success:
        print("✅ 成功安装 boto3")
    else:
        print(f"❌ 安装 boto3 失败: {stderr}")
        return False
    
    return True


def test_import():
    """测试导入是否成功"""
    print("\n🧪 测试导入...")
    
    try:
        from kafka import KafkaProducer
        print("✅ kafka.KafkaProducer 导入成功")
    except ImportError as e:
        print(f"❌ kafka.KafkaProducer 导入失败: {e}")
        return False
    
    try:
        import boto3
        print("✅ boto3 导入成功")
    except ImportError as e:
        print(f"❌ boto3 导入失败: {e}")
        return False
    
    try:
        import six
        print("✅ six 导入成功")
    except ImportError as e:
        print(f"❌ six 导入失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("AWS MSK Python 依赖修复工具")
    print("=" * 40)
    
    # 检查 Python 版本
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return
    
    # 修复依赖
    if fix_kafka_dependencies():
        print("\n✅ 依赖修复完成")
        
        # 测试导入
        if test_import():
            print("\n🎉 所有依赖都可以正常导入!")
            print("\n现在可以运行:")
            print("  python3 msk_producer.py")
            print("  python3 msk_scram_example.py")
        else:
            print("\n❌ 导入测试失败，请检查错误信息")
    else:
        print("\n❌ 依赖修复失败")


if __name__ == "__main__":
    main()