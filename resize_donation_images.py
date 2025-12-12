#!/usr/bin/env python3
"""
缩放打赏图片到合适的大小
"""

import os
from PIL import Image
from pathlib import Path

def resize_image(input_path, output_path, max_size=200, quality=85):
    """
    缩放图片到指定最大尺寸
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        max_size: 最大边长（像素）
        quality: JPEG质量（1-100）
    """
    try:
        # 打开图片
        img = Image.open(input_path)
        
        # 获取原始尺寸
        original_width, original_height = img.size
        print(f"原始尺寸: {original_width}x{original_height}")
        
        # 计算缩放比例
        if original_width > original_height:
            # 宽度是最大边
            new_width = max_size
            new_height = int(original_height * (max_size / original_width))
        else:
            # 高度是最大边
            new_height = max_size
            new_width = int(original_width * (max_size / original_height))
        
        # 执行缩放
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存图片
        if str(output_path).lower().endswith('.png'):
            resized_img.save(output_path, 'PNG', optimize=True)
        else:
            resized_img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        print(f"缩放后尺寸: {new_width}x{new_height}")
        print(f"保存到: {output_path}")
        
        # 获取文件大小
        original_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        compression_ratio = (1 - new_size / original_size) * 100
        
        print(f"原始大小: {original_size:,} 字节")
        print(f"新大小: {new_size:,} 字节")
        print(f"压缩率: {compression_ratio:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"缩放失败: {e}")
        return False

def main():
    print("缩放打赏图片...")
    print("=" * 40)
    
    # 配置目录
    config_dir = Path("config")
    
    # 要处理的图片文件
    images = [
        ("weichat.png", "weichat_small.png"),
        ("alipay.png", "alipay_small.jpg")
    ]
    
    success_count = 0
    
    for input_name, output_name in images:
        input_path = config_dir / input_name
        output_path = config_dir / output_name
        
        print(f"\n处理 {input_name}:")
        print("-" * 20)
        
        if input_path.exists():
            if resize_image(input_path, output_path):
                success_count += 1
        else:
            print(f"错误: 找不到文件 {input_path}")
    
    print("\n" + "=" * 40)
    print(f"处理完成！成功缩放 {success_count}/{len(images)} 个文件")
    
    if success_count == len(images):
        print("\n缩放后的图片文件:")
        for _, output_name in images:
            output_path = config_dir / output_name
            if output_path.exists():
                size = output_path.stat().st_size
                print(f"  ✓ {output_name} ({size:,} 字节)")
    
    print("\n现在可以更新README.md中的图片路径:")
    for _, output_name in images:
        print(f"  {output_name}")

if __name__ == "__main__":
    try:
        # 检查PIL库是否安装
        from PIL import Image
        main()
    except ImportError:
        print("需要安装Pillow库:")
        print("pip install Pillow")
        print("\n或者手动:")
        print("1. 使用图片编辑软件将图片缩放到200x200像素")
        print("2. 保存到config目录")
        print("3. 命名为weichat_small.png和alipay_small.jpg")