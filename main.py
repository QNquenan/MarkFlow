# -*- coding: utf-8 -*-
# @Time    : 2025/6/21 下午6:12
# @Author  : Quenan

import os
from PIL import Image


def check_folder_images(folder_path):
    """
    遍历文件夹及其子文件夹中的所有图片，判断横竖图
    :param folder_path: 图片文件夹路径
    """
    # 支持的图片格式
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}

    results = {
        'horizontal': [],  # 存储横图路径
        'vertical': [],  # 存储竖图路径
        'errors': []  # 存储错误信息
    }

    # 递归遍历文件夹
    for root, _, files in os.walk(folder_path):
        for file in files:
            # 检查文件扩展名
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext not in image_exts:
                continue

            file_path = os.path.join(root, file)

            try:
                with Image.open(file_path) as img:
                    width, height = img.size

                    # 判断横竖图
                    if width >= height:
                        results['horizontal'].append(file_path)
                        print(f"✅ 横图：{file_path} ({width}x{height})")
                    else:
                        results['vertical'].append(file_path)
                        print(f"📏 竖图：{file_path} ({width}x{height})")

            except Exception as e:
                error_msg = f"❌ 处理失败：{file_path} - {str(e)}"
                results['errors'].append(error_msg)
                print(error_msg)

    # 打印统计数据
    print("\n" + "=" * 50)
    print(f"📊 统计结果：共处理 {len(results['horizontal']) + len(results['vertical'])} 张图片")
    print(f"🖼️  横图数量：{len(results['horizontal'])}")
    print(f"🏙️  竖图数量：{len(results['vertical'])}")
    print(f"⚠️  错误数量：{len(results['errors'])}")

    return results


# 使用示例
if __name__ == "__main__":
    folder = r"C:\Users\Administrator\Desktop\临时照片\jpg"  # 替换为你的图片文件夹路径
    results = check_folder_images(folder)