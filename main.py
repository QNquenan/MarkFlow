# -*- coding: utf-8 -*-
# @Time    : 2025/6/21 下午6:12
# @Author  : Quenan

import threading
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES


class ImageProcessorApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("图片处理工具 - 拖拽上传")
        self.geometry("800x600")
        self.image_paths = []
        self.photo_refs = []  # 防止图像被垃圾回收

        # 创建界面组件
        self.create_widgets()

    def create_widgets(self):
        # 拖拽区域
        self.drop_frame = tk.LabelFrame(self, text="拖拽图片到这里", height=400,
                                        relief="sunken", borderwidth=2)
        self.drop_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)

        # 缩略图展示区
        self.canvas = tk.Canvas(self.drop_frame, bg="#f0f0f0")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # 控制按钮区域
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        self.process_btn = tk.Button(btn_frame, text="开始处理",
                                     command=self.start_processing,
                                     state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=20)

        self.clear_btn = tk.Button(btn_frame, text="清空图片",
                                   command=self.clear_images)
        self.clear_btn.pack(side=tk.LEFT, padx=20)

        # 结果展示区
        self.result_frame = tk.LabelFrame(self, text="处理结果")
        self.result_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.horizontal_label = tk.Label(self.result_frame,
                                         text="横图: 0", anchor="w")
        self.horizontal_label.pack(fill="x", padx=10)

        self.vertical_label = tk.Label(self.result_frame,
                                       text="竖图: 0", anchor="w")
        self.vertical_label.pack(fill="x", padx=10)

        self.result_text = tk.Text(self.result_frame, height=6)
        self.result_text.pack(fill="both", expand=True, padx=10, pady=5)

    def handle_drop(self, event):
        """处理拖拽文件事件"""
        files = self.parse_dropped_files(event.data)
        valid_images = [f for f in files if f.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

        for img_path in valid_images:
            if img_path not in self.image_paths:
                self.image_paths.append(img_path)
                self.display_thumbnail(img_path)

        if self.image_paths:
            self.process_btn.config(state=tk.NORMAL)

    def parse_dropped_files(self, data):
        """解析拖拽文件路径"""
        # Windows返回带花括号的路径列表，macOS/Linux返回空格分隔的路径
        if data.startswith('{') and data.endswith('}'):
            return data.strip('{}').split('} {')
        return data.split()

    def display_thumbnail(self, img_path):
        """显示图片缩略图"""
        try:
            img = Image.open(img_path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            self.photo_refs.append(photo)  # 保留引用

            # 在画布上创建缩略图
            num = len(self.photo_refs)
            row = (num - 1) // 6
            col = (num - 1) % 6
            x = col * 110 + 20
            y = row * 110 + 20

            self.canvas.create_image(x, y, image=photo, anchor="nw")
            self.canvas.create_text(x + 50, y + 105, text=Path(img_path).name,
                                    anchor="n", width=100)

            # 自动扩展画布
            canvas_height = max(500, (row + 1) * 110 + 20)
            self.canvas.config(scrollregion=(0, 0, 700, canvas_height))

        except Exception as e:
            self.result_text.insert(tk.END, f"错误: {img_path} - {str(e)}\n")

    def clear_images(self):
        """清空所有图片"""
        self.image_paths = []
        self.photo_refs = []
        self.canvas.delete("all")
        self.result_text.delete(1.0, tk.END)
        self.process_btn.config(state=tk.DISABLED)
        self.horizontal_label.config(text="横图: 0")
        self.vertical_label.config(text="竖图: 0")

    def start_processing(self):
        """启动处理线程"""
        self.process_btn.config(state=tk.DISABLED)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "开始处理图片...\n")

        # 在新线程中处理避免界面冻结
        threading.Thread(target=self.process_images, daemon=True).start()

    def process_images(self):
        """处理图片并分类"""
        horizontal_count = 0
        vertical_count = 0

        for img_path in self.image_paths:
            try:
                with Image.open(img_path) as img:
                    width, height = img.size

                    if width >= height:
                        horizontal_count += 1
                        orientation = "横图"
                    else:
                        vertical_count += 1
                        orientation = "竖图"

                    result_line = f"{Path(img_path).name}: {width}x{height} ({orientation})\n"
                    self.result_text.insert(tk.END, result_line)
                    self.result_text.see(tk.END)

            except Exception as e:
                error_msg = f"{Path(img_path).name}: 处理失败 - {str(e)}\n"
                self.result_text.insert(tk.END, error_msg)
                self.result_text.see(tk.END)

        # 更新UI统计结果
        self.horizontal_label.config(text=f"横图: {horizontal_count}")
        self.vertical_label.config(text=f"竖图: {vertical_count}")
        self.result_text.insert(tk.END, f"\n处理完成! 横图: {horizontal_count}张, 竖图: {vertical_count}张\n")
        self.process_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    app = ImageProcessorApp()
    app.mainloop()