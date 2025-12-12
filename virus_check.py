#!/usr/bin/env python3
"""
VirusTotal API 扫描脚本
用于检查 exe 文件的病毒检测结果
"""

import os
import hashlib
import time
import requests
import json

def get_file_hash(file_path):
    """计算文件的 SHA256 哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 分块读取文件以处理大文件
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def check_virustotal(api_key, file_path):
    """
    使用 VirusTotal API 检查文件
    需要注册 VirusTotal 账号获取免费的 API key
    """
    file_hash = get_file_hash(file_path)
    print(f"文件 SHA256: {file_hash}")
    
    # VirusTotal API URL
    url = f"https://www.virustotal.com/vtapi/v2/file/report"
    
    params = {
        'apikey': api_key,
        'resource': file_hash
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            
            if result['response_code'] == 1:
                # 文件已经在 VirusTotal 数据库中
                print(f"\n检测结果 (共 {result['total']} 个杀毒引擎):")
                print(f"检出威胁: {result['posititives']}")
                print(f"扫描日期: {result['scan_date']}")
                print(f"预链接: {result['permalink']}")
                
                print("\n详细检测结果:")
                for engine, scan_result in result['scans'].items():
                    status = scan_result['result']
                    if status == 'Clean' or status is None:
                        print(f"✓ {engine}: 清洁")
                    else:
                        print(f"✗ {engine}: {status}")
                        
                return result['posititives']
            else:
                print("文件尚未被扫描，请手动上传到 VirusTotal")
                return -1
        else:
            print(f"API 请求失败: {response.status_code}")
            return -1
            
    except Exception as e:
        print(f"检查失败: {e}")
        return -1

def upload_to_virustotal(api_key, file_path):
    """
    上传文件到 VirusTotal 进行扫描
    """
    url = "https://www.virustotal.com/vtapi/v2/file/scan"
    
    params = {'apikey': api_key}
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(url, files=files, params=params)
            
        if response.status_code == 200:
            result = response.json()
            print(f"文件上传成功！")
            print(f"扫描ID: {result['scan_id']}")
            print(f"预链接: {result['permalink']}")
            print("扫描进行中，请稍后再次检查结果")
            return True
        else:
            print(f"上传失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"上传失败: {e}")
        return False

def main():
    print("VirusTotal 文件扫描工具")
    print("="*40)
    
    # 配置
    exe_path = "dist/Windows_C_Drive_Cleaner/Windows_C_Drive_Cleaner.exe"
    
    if not os.path.exists(exe_path):
        print(f"错误: 找不到文件 {exe_path}")
        print("请先运行 build_anti_virus.py 构建程序")
        return
    
    # API Key - 请替换为您自己的 VirusTotal API Key
    # 注册地址: https://www.virustotal.com/gui/join-us
    api_key = input("请输入您的 VirusTotal API Key (或按回车跳过): ").strip()
    
    if not api_key:
        print("\n跳过 VirusTotal 检查")
        print("您可以:")
        print("1. 手动访问 https://www.virustotal.com 上传文件")
        print("2. 注册免费账号获取 API Key")
        print("3. 直接使用程序，遇到误报时添加到杀毒软件白名单")
        return
    
    print(f"\n检查文件: {exe_path}")
    
    # 首先尝试检查现有结果
    detections = check_virustotal(api_key, exe_path)
    
    if detections == -1:
        # 文件未找到，询问是否上传
        choice = input("\n文件未在 VirusTotal 数据库中，是否上传扫描？(y/n): ").lower()
        if choice == 'y':
            upload_to_virustotal(api_key, exe_path)
            print("\n上传完成，请等待 1-2 分钟后再次运行此脚本查看结果")

if __name__ == "__main__":
    main()