# -*- coding: utf-8 -*-
# @Time    : 2025/6/21 下午6:12
# @Author  : Quenan

import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk, ImageOps
import os
import numpy as np
from pathlib import Path
import threading


class SmartLogoApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("智能Logo添加工具")
        self.geometry("900x700")
        self.image_paths = []
        self.photo_refs = []  # 防止图像被垃圾回收
        self.white_logo_path = None
        self.black_logo_path = None
        self.output_dir = ""  # 输出目录

        # 颜色阈值设置
        self.light_threshold = 180  # 浅色区域亮度阈值
        self.dark_threshold = 120  # 深色区域亮度阈值

        self.create_widgets()

    def create_widgets(self):
        # 主布局分左右两栏
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左侧面板 - 图片列表和操作区
        left_frame = tk.LabelFrame(main_frame, text="图片管理")
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # 右侧面板 - 操作和结果
        right_frame = tk.LabelFrame(main_frame, text="操作与结果")
        right_frame.pack(side="right", fill="both", padx=5, pady=5)

        # ======= 左侧面板内容 =======
        # 拖拽区域
        drop_frame = tk.LabelFrame(left_frame, text="拖拽图片到这里", height=300,
                                   relief="sunken", borderwidth=1)
        drop_frame.pack(fill="both", expand=True, padx=5, pady=5)
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.handle_drop)

        # 图片列表
        self.listbox = tk.Listbox(drop_frame, selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # 按钮区域
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.clear_btn = tk.Button(btn_frame, text="清空列表",
                                   command=self.clear_images)
        self.clear_btn.pack(side="left", padx=5)

        # ======= 右侧面板内容 =======
        # Logo选择区域
        logo_frame = tk.LabelFrame(right_frame, text="Logo选择")
        logo_frame.pack(fill="x", padx=5, pady=5)

        # 白色Logo按钮
        white_btn_frame = tk.Frame(logo_frame)
        white_btn_frame.pack(fill="x", padx=5, pady=5)
        self.white_logo_btn = tk.Button(white_btn_frame, text="选择白色Logo",
                                        command=lambda: self.select_logo("white"))
        self.white_logo_btn.pack(side="left")
        self.white_logo_label = tk.Label(white_btn_frame, text="未选择", fg="gray")
        self.white_logo_label.pack(side="left", padx=10)

        # 黑色Logo按钮
        black_btn_frame = tk.Frame(logo_frame)
        black_btn_frame.pack(fill="x", padx=5, pady=5)
        self.black_logo_btn = tk.Button(black_btn_frame, text="选择黑色Logo",
                                        command=lambda: self.select_logo("black"))
        self.black_logo_btn.pack(side="left")
        self.black_logo_label = tk.Label(black_btn_frame, text="未选择", fg="gray")
        self.black_logo_label.pack(side="left", padx=10)

        # 输出目录选择
        output_frame = tk.LabelFrame(right_frame, text="输出设置")
        output_frame.pack(fill="x", padx=5, pady=5)

        self.output_btn = tk.Button(output_frame, text="设置输出目录",
                                    command=self.select_output_dir)
        self.output_btn.pack(side="left", padx=5, pady=5)
        self.output_label = tk.Label(output_frame, text="未设置", fg="gray")
        self.output_label.pack(side="left", padx=10)

        # 处理按钮
        process_frame = tk.Frame(right_frame)
        process_frame.pack(fill="x", padx=5, pady=10)

        self.process_btn = tk.Button(process_frame, text="开始处理",
                                     command=self.start_processing,
                                     state=tk.DISABLED,
                                     height=2)
        self.process_btn.pack(fill="x", padx=10)

        # 日志区域
        log_frame = tk.LabelFrame(right_frame, text="处理日志")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_scroll = tk.Scrollbar(self.log_text)
        self.log_scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=self.log_scroll.set)
        self.log_scroll.config(command=self.log_text.yview)

        # 状态栏
        status_frame = tk.Frame(self)
        status_frame.pack(fill="x", padx=10, pady=5)
        self.status_label = tk.Label(status_frame, text="就绪", anchor="w")
        self.status_label.pack(fill="x")

    def handle_drop(self, event):
        """处理拖拽文件事件"""
        files = self.parse_dropped_files(event.data)
        valid_images = [f for f in files if f.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

        for img_path in valid_images:
            if img_path not in self.image_paths:
                self.image_paths.append(img_path)
                self.listbox.insert("end", os.path.basename(img_path))
                self.log(f"添加: {os.path.basename(img_path)}")

        if self.image_paths:
            self.process_btn.config(state=tk.NORMAL)

    def parse_dropped_files(self, data):
        """解析拖拽文件路径"""
        # Windows返回带花括号的路径列表，macOS/Linux返回空格分隔的路径
        if data.startswith('{') and data.endswith('}'):
            return data.strip('{}').split('} {')
        return data.split()

    def select_logo(self, logo_type):
        """选择Logo文件"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")]
        )

        if file_path:
            if logo_type == "white":
                self.white_logo_path = file_path
                self.white_logo_label.config(text=os.path.basename(file_path))
                self.log(f"白色Logo设置: {os.path.basename(file_path)}")
            else:
                self.black_logo_path = file_path
                self.black_logo_label.config(text=os.path.basename(file_path))
                self.log(f"黑色Logo设置: {os.path.basename(file_path)}")

            self.validate_settings()

    def select_output_dir(self):
        """选择输出目录"""
        from tkinter import filedialog
        dir_path = filedialog.askdirectory()

        if dir_path:
            self.output_dir = dir_path
            self.output_label.config(text=os.path.basename(dir_path))
            self.log(f"输出目录设置: {dir_path}")
            self.validate_settings()

    def validate_settings(self):
        """检查设置是否完整"""
        if self.image_paths and self.white_logo_path and self.black_logo_path and self.output_dir:
            self.process_btn.config(state=tk.NORMAL)
            self.status_label.config(text="设置完成，可以开始处理")
        else:
            self.process_btn.config(state=tk.DISABLED)
            missing = []
            if not self.image_paths: missing.append("图片")
            if not self.white_logo_path: missing.append("白色Logo")
            if not self.black_logo_path: missing.append("黑色Logo")
            if not self.output_dir: missing.append("输出目录")
            self.status_label.config(text=f"缺少: {', '.join(missing)}")

    def clear_images(self):
        """清空所有图片"""
        self.image_paths = []
        self.photo_refs = []
        self.listbox.delete(0, "end")
        self.log("已清空图片列表")
        self.validate_settings()

    def start_processing(self):
        """启动处理线程"""
        self.process_btn.config(state=tk.DISABLED)
        self.log("开始处理图片...")
        self.status_label.config(text="处理中...")

        # 在新线程中处理避免界面冻结
        threading.Thread(target=self.process_images, daemon=True).start()

    def get_bottom_region_average_brightness(self, img):
        """获取图片底部20%区域的平均亮度"""
        width, height = img.size
        # 计算底部20%区域
        bottom_start = int(height * 0.8)
        bottom_region = img.crop((0, bottom_start, width, height))

        # 转换为灰度图并计算平均亮度
        gray_img = bottom_region.convert("L")
        histogram = gray_img.histogram()
        total_pixels = bottom_region.width * bottom_region.height
        weighted_sum = sum(i * count for i, count in enumerate(histogram))

        return weighted_sum / (total_pixels * 255)  # 归一化到0-1范围

    def overlay_logo(self, background, logo_path, position):
        """将Logo覆盖到背景图片上"""
        try:
            foreground = Image.open(logo_path)
            if foreground.mode != 'RGBA':
                foreground = foreground.convert('RGBA')

            # 创建背景图片的副本
            composite = background.copy()

            # 粘贴Logo到指定位置
            composite.paste(foreground, position, foreground)
            return composite
        except Exception as e:
            self.log(f"Logo覆盖错误: {str(e)}")
            return None

    def process_images(self):
        """处理图片并添加Logo"""
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        success_count = 0
        error_count = 0

        for img_path in self.image_paths:
            try:
                self.log(f"处理: {os.path.basename(img_path)}")
                img = Image.open(img_path).convert("RGBA")
                width, height = img.size

                # 1. 分析底部20%区域的亮度
                brightness = self.get_bottom_region_average_brightness(img)
                brightness_percent = int(brightness * 100)
                self.log(f"  底部区域亮度: {brightness_percent}%")

                # 2. 根据亮度选择合适的Logo
                if brightness < 0.5:  # 深色区域
                    logo_path = self.white_logo_path
                    logo_type = "白色Logo"
                else:  # 浅色区域
                    logo_path = self.black_logo_path
                    logo_type = "黑色Logo"

                self.log(f"  使用: {logo_type} ({os.path.basename(logo_path)})")

                # 3. 计算Logo位置（底部居中）
                logo_img = Image.open(logo_path)
                logo_width, logo_height = logo_img.size

                # 计算位置 - 底部20%区域内居中
                x_position = (width - logo_width) // 2
                y_position = height - int(height * 0.2) + (int(height * 0.2) - logo_height) // 2

                # 4. 添加Logo
                result_img = self.overlay_logo(img, logo_path, (x_position, y_position))

                if result_img:
                    # 5. 保存结果
                    output_path = os.path.join(self.output_dir, f"processed_{os.path.basename(img_path)}")

                    # 根据原始格式保存
                    if img_path.lower().endswith('.jpg') or img_path.lower().endswith('.jpeg'):
                        result_img = result_img.convert('RGB')

                    result_img.save(output_path)
                    self.log(f"  保存成功: {os.path.basename(output_path)}")
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                error_msg = f"处理失败 {os.path.basename(img_path)}: {str(e)}"
                self.log(error_msg)
                error_count += 1

        # 处理完成
        self.log(f"\n处理完成! 成功: {success_count}张, 失败: {error_count}张")
        self.status_label.config(text=f"处理完成: {success_count}成功, {error_count}失败")
        self.process_btn.config(state=tk.NORMAL)

    def log(self, message):
        """添加日志信息"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.status_label.config(text=message)


if __name__ == "__main__":
    app = SmartLogoApp()
    app.mainloop()