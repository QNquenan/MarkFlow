import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import os
import threading
from tkinter import filedialog, messagebox
import piexif  # 用于处理EXIF数据
import webbrowser  # 用于打开浏览器

# 增加 Pillow 的像素限制以防止解压缩炸弹错误
Image.MAX_IMAGE_PIXELS = None  # 禁用限制


class EnhancedWatermarkApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("MarkFlow")
        self.geometry("1100x800")
        self.image_paths = []
        self.thumbnail_refs = []
        self.white_logo_path = None
        self.black_logo_path = None
        self.output_dir = ""
        self.create_widgets()

    def create_widgets(self):
        # 主布局分上下两部分
        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== 上半部分：缩略图列表 =====
        list_frame = tk.LabelFrame(main_frame, text="图片列表", padx=10, pady=5)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 带滚动条的Canvas容器
        canvas_container = tk.Frame(list_frame)
        canvas_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # 保存框架ID以便后续调整宽度
        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self.on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ===== 下半部分：控制区域 =====
        control_frame = tk.Frame(main_frame, bg="#f0f0f0")
        control_frame.pack(fill="x", padx=5, pady=5)

        # 左侧 - Logo设置
        logo_frame = tk.LabelFrame(control_frame, text="Logo设置", padx=10, pady=10)
        logo_frame.pack(side="left", fill="both", padx=5, pady=5, ipadx=10, ipady=5)

        tk.Button(logo_frame, text="选择白色Logo",
                  command=lambda: self.select_logo("white")).pack(fill="x", pady=5)
        self.white_logo_label = tk.Label(logo_frame, text="未选择", fg="gray")
        self.white_logo_label.pack()

        tk.Button(logo_frame, text="选择黑色Logo",
                  command=lambda: self.select_logo("black")).pack(fill="x", pady=5)
        self.black_logo_label = tk.Label(logo_frame, text="未选择", fg="gray")
        self.black_logo_label.pack()

        # 中间 - 水印设置
        settings_frame = tk.LabelFrame(control_frame, text="水印设置", padx=10, pady=10)
        settings_frame.pack(side="left", fill="both", padx=5, pady=5, ipadx=10, ipady=5)

        # 水印尺寸控制
        size_frame = tk.Frame(settings_frame)
        size_frame.pack(fill="x", pady=5)

        tk.Label(size_frame, text="宽度(像素):", width=15, anchor="w").pack(side="left")
        self.width_var = tk.IntVar(value=1000)
        tk.Entry(size_frame, textvariable=self.width_var, width=10).pack(side="left", padx=5)

        size_frame2 = tk.Frame(settings_frame)
        size_frame2.pack(fill="x", pady=5)

        tk.Label(size_frame2, text="高度(像素):", width=15, anchor="w").pack(side="left")
        self.height_var = tk.IntVar(value=250)
        tk.Entry(size_frame2, textvariable=self.height_var, width=10).pack(side="left", padx=5)

        # 水印位置控制
        pos_frame = tk.Frame(settings_frame)
        pos_frame.pack(fill="x", pady=5)

        tk.Label(pos_frame, text="距底部位置(%):", width=15, anchor="w").pack(side="left")
        self.bottom_var = tk.IntVar(value=10)
        tk.Entry(pos_frame, textvariable=self.bottom_var, width=10).pack(side="left", padx=5)

        # 输出目录设置
        output_frame = tk.Frame(settings_frame)
        output_frame.pack(fill="x", pady=10)
        tk.Button(output_frame, text="设置输出目录",
                  command=self.select_output_dir).pack(fill="x")
        self.output_label = tk.Label(output_frame, text="未设置", fg="gray")
        self.output_label.pack()

        # 右侧 - 操作按钮
        action_frame = tk.LabelFrame(control_frame, text="操作", padx=10, pady=10)
        action_frame.pack(side="right", fill="both", padx=5, pady=5, ipadx=10, ipady=5)

        self.process_btn = tk.Button(action_frame, text="开始处理",
                                     command=self.start_processing,
                                     height=2, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.process_btn.pack(fill="x", padx=5, pady=10)

        clear_btn = tk.Button(action_frame, text="清空图片列表",
                              command=self.clear_images, height=2)
        clear_btn.pack(fill="x", padx=5, pady=5)

        # 添加"关于"按钮
        about_btn = tk.Button(action_frame, text="关于",
                              command=self.show_about, height=2, bg="#2196F3", fg="white")
        about_btn.pack(fill="x", padx=5, pady=5)

        # ===== 日志区域 =====
        log_frame = tk.LabelFrame(control_frame, text="处理日志", padx=10, pady=10)
        log_frame.pack(side="left", fill="both", padx=5, pady=5, expand=True)

        self.log_text = tk.Text(log_frame, height=8)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_scroll = tk.Scrollbar(self.log_text)
        self.log_scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=self.log_scroll.set)
        self.log_scroll.config(command=self.log_text.yview)

        # 状态栏
        status_frame = tk.Frame(self, height=30, bg="#e0e0e0")
        status_frame.pack(fill="x", side="bottom")
        self.status_label = tk.Label(status_frame, text="就绪", anchor="w", bg="#e0e0e0")
        self.status_label.pack(fill="x", padx=10)

        # 注册拖放事件
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

        # 添加5%外边距
        self.scrollable_frame.config(padx=15, pady=15)

    def show_about(self):
        """显示关于弹窗（位于屏幕中间）"""
        about_window = tk.Toplevel(self)
        about_window.title("关于 MarkFlow")
        about_window.resizable(False, False)
        about_window.grab_set()  # 使窗口模态化

        # 设置窗口位置在屏幕中间
        self.update_idletasks()  # 确保窗口位置计算准确
        app_width = self.winfo_width()
        app_height = self.winfo_height()
        app_x = self.winfo_rootx()
        app_y = self.winfo_rooty()

        about_width = 400
        about_height = 250

        # 计算位置使弹窗在应用中间
        pos_x = app_x + (app_width - about_width) // 2
        pos_y = app_y + (app_height - about_height) // 2

        about_window.geometry(f"{about_width}x{about_height}+{pos_x}+{pos_y}")

        # 应用样式
        bg_color = "#f5f5f5"
        button_bg = "#e0e0e0"
        hover_bg = "#d0d0d0"

        about_window.configure(bg=bg_color)

        # 添加标题
        title_label = tk.Label(about_window, text="MarkFlow", font=("Arial", 18, "bold"), bg=bg_color)
        title_label.pack(pady=(20, 10))

        # 添加作者信息
        author_label = tk.Label(about_window, text="作者：鹊楠", font=("Arial", 12), bg=bg_color)
        author_label.pack(pady=5)

        # 添加版本信息
        version_label = tk.Label(about_window, text="版本：1.0.1", font=("Arial", 12), bg=bg_color)
        version_label.pack(pady=5)

        # 添加分隔线
        separator = tk.Frame(about_window, height=2, bg="#cccccc")
        separator.pack(fill="x", padx=20, pady=15)

        # 添加按钮框架
        button_frame = tk.Frame(about_window, bg=bg_color)
        button_frame.pack(pady=10)

        # 添加GitHub按钮
        def open_github():
            webbrowser.open("https://github.com/QNquenan/MarkFlow")

        github_btn = tk.Button(button_frame, text="GitHub",
                               command=open_github, width=10, height=2,
                               bg=button_bg, relief="flat")
        github_btn.pack(side="left", padx=10)
        github_btn.bind("<Enter>", lambda e: github_btn.config(bg=hover_bg))
        github_btn.bind("<Leave>", lambda e: github_btn.config(bg=button_bg))

        # 添加哔哩哔哩按钮
        def open_bilibili():
            webbrowser.open("https://space.bilibili.com/495882959")

        bilibili_btn = tk.Button(button_frame, text="哔哩哔哩",
                                 command=open_bilibili, width=10, height=2,
                                 bg=button_bg, relief="flat")
        bilibili_btn.pack(side="left", padx=10)
        bilibili_btn.bind("<Enter>", lambda e: bilibili_btn.config(bg=hover_bg))
        bilibili_btn.bind("<Leave>", lambda e: bilibili_btn.config(bg=button_bg))

        # 添加博客按钮
        def open_blog():
            webbrowser.open("https://blog.quenan.cn/")

        blog_btn = tk.Button(button_frame, text="博客",
                             command=open_blog, width=10, height=2,
                             bg=button_bg, relief="flat")
        blog_btn.pack(side="left", padx=10)
        blog_btn.bind("<Enter>", lambda e: blog_btn.config(bg=hover_bg))
        blog_btn.bind("<Leave>", lambda e: blog_btn.config(bg=button_bg))

        # 添加关闭按钮
        close_btn = tk.Button(about_window, text="关闭",
                              command=about_window.destroy, width=15, height=1,
                              bg="#f44336", fg="white")
        close_btn.pack(pady=15)

        # 添加回车键关闭功能
        about_window.bind("<Return>", lambda e: about_window.destroy())

    def on_canvas_configure(self, event):
        """调整滚动区域宽度以适应画布"""
        self.canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def on_mousewheel(self, event):
        """处理鼠标滚轮事件以实现滚动"""
        # 在Windows上，event.delta是120的倍数
        # 在Mac上，event.delta可能较小，需要除以120
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def handle_drop(self, event):
        """处理拖拽文件事件"""
        files = self.parse_dropped_files(event.data)
        valid_images = [f for f in files if f.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'))]

        for img_path in valid_images:
            if img_path not in self.image_paths:
                self.image_paths.append(img_path)
                self.add_thumbnail(img_path)
                self.log(f"添加: {os.path.basename(img_path)}")

        self.validate_settings()

    def parse_dropped_files(self, data):
        """解析拖拽文件路径"""
        if data.startswith('{') and data.endswith('}'):
            return data.strip('{}').split('} {')
        return data.split()

    def add_thumbnail(self, img_path):
        """添加图片缩略图到列表"""
        try:
            # 创建缩略图
            img = Image.open(img_path)

            # 计算缩略图尺寸，保持宽高比
            max_size = (200, 200)
            img.thumbnail(max_size, Image.LANCZOS)

            # 转换为Tkinter兼容格式
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_refs.append(photo)

            # 创建缩略图容器 - 使用fill="x"和expand=True
            thumb_frame = tk.Frame(self.scrollable_frame, bd=1, relief="solid",
                                   padx=10, pady=10, bg="white")
            thumb_frame.pack(fill="x", pady=8, expand=True)

            # 为每个缩略图项绑定鼠标滚轮事件
            thumb_frame.bind("<MouseWheel>", self.on_mousewheel)

            # 内部框架用于组织内容
            inner_frame = tk.Frame(thumb_frame, bg="white")
            inner_frame.pack(fill="x", expand=True)

            # 为内部框架绑定鼠标滚轮事件
            inner_frame.bind("<MouseWheel>", self.on_mousewheel)

            # 图片标签
            label_img = tk.Label(inner_frame, image=photo, bg="white")
            label_img.image = photo
            label_img.pack(side="left", padx=5)

            # 为图片标签绑定鼠标滚轮事件
            label_img.bind("<MouseWheel>", self.on_mousewheel)

            # 文件名标签
            filename = os.path.basename(img_path)
            if len(filename) > 30:
                filename = filename[:27] + "..."

            file_frame = tk.Frame(inner_frame, bg="white")
            file_frame.pack(side="left", padx=10, fill="x", expand=True)

            # 为文件框架绑定鼠标滚轮事件
            file_frame.bind("<MouseWheel>", self.on_mousewheel)

            file_label = tk.Label(file_frame, text=filename, anchor="w", justify="left",
                                  bg="white", wraplength=300)
            file_label.pack(fill="x", expand=True)

            # 为文件标签绑定鼠标滚轮事件
            file_label.bind("<MouseWheel>", self.on_mousewheel)

            # 删除按钮
            delete_btn = tk.Button(inner_frame, text="×", fg="red", font=("Arial", 14, "bold"),
                                   command=lambda path=img_path: self.remove_image(path, thumb_frame),
                                   width=2, height=1, bg="white", bd=0)
            delete_btn.pack(side="right", padx=5)

            # 为删除按钮绑定鼠标滚轮事件
            delete_btn.bind("<MouseWheel>", self.on_mousewheel)

        except Exception as e:
            self.log(f"缩略图创建失败: {img_path} - {str(e)}")

    def remove_image(self, img_path, frame):
        """从列表中移除图片"""
        if img_path in self.image_paths:
            self.image_paths.remove(img_path)
            frame.destroy()
            self.log(f"移除: {os.path.basename(img_path)}")
            self.validate_settings()

    def clear_images(self):
        """清空所有图片"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.image_paths = []
        self.thumbnail_refs = []
        self.log("已清空图片列表")
        self.validate_settings()

    def select_logo(self, logo_type):
        """选择Logo文件"""
        file_path = filedialog.askopenfilename(
            title=f"选择{logo_type}Logo",
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
        dir_path = filedialog.askdirectory(title="选择输出目录")

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

    def start_processing(self):
        """启动处理线程"""
        self.process_btn.config(state=tk.DISABLED)
        self.log("开始处理图片...")
        self.status_label.config(text="处理中...")

        threading.Thread(target=self.process_images, daemon=True).start()

    def process_images(self):
        """处理图片并添加Logo"""
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        success_count = 0
        error_count = 0

        bottom_percent = self.bottom_var.get() / 100.0
        logo_width = self.width_var.get()
        logo_height = self.height_var.get()

        # 验证设置
        if bottom_percent <= 0 or bottom_percent >= 1:
            messagebox.showerror("错误", "底部位置百分比必须在1-99之间")
            self.log("错误: 底部位置百分比必须在1-99之间")
            self.process_btn.config(state=tk.NORMAL)
            return

        if logo_width <= 0 or logo_height <= 0:
            messagebox.showerror("错误", "水印尺寸必须大于0")
            self.log("错误: 水印尺寸必须大于0")
            self.process_btn.config(state=tk.NORMAL)
            return

        for img_path in self.image_paths:
            try:
                self.log(f"处理: {os.path.basename(img_path)}")

                # 读取原始EXIF信息
                exif_dict = {}
                try:
                    if 'exif' in Image.open(img_path).info:
                        exif_dict = piexif.load(Image.open(img_path).info['exif'])
                        self.log("  检测到EXIF信息，将完整保留")
                except Exception as e:
                    self.log(f"  读取EXIF时出错: {str(e)}")

                # 打开原始图片（不修改尺寸）
                img = Image.open(img_path).convert("RGBA")
                width, height = img.size

                # 分析底部区域的亮度
                brightness = self.get_bottom_region_brightness(img, bottom_percent)
                brightness_percent = int(brightness * 100)
                self.log(f"  底部区域亮度: {brightness_percent}%")

                # 根据亮度选择合适的Logo
                if brightness < 0.5:
                    logo_path = self.white_logo_path
                    logo_type = "白色Logo"
                else:
                    logo_path = self.black_logo_path
                    logo_type = "黑色Logo"

                self.log(f"  使用: {logo_type} ({os.path.basename(logo_path)})")

                # 调整Logo尺寸
                logo_img = Image.open(logo_path).convert("RGBA")
                logo_img = logo_img.resize((logo_width, logo_height), Image.LANCZOS)

                # 计算位置（底部区域居中）
                bottom_area_start = int(height * (1 - bottom_percent))
                x_position = (width - logo_width) // 2
                y_position = bottom_area_start + (int(height * bottom_percent) - logo_height) // 2

                # 添加水印
                composite = img.copy()
                composite.paste(logo_img, (x_position, y_position), logo_img)

                # 保存结果（保留原始EXIF）
                filename, ext = os.path.splitext(os.path.basename(img_path))
                output_path = os.path.join(self.output_dir, f"{filename}_watermarked{ext}")

                # 设置保存参数（禁用压缩）
                save_params = {}
                if exif_dict:
                    exif_bytes = piexif.dump(exif_dict)
                    save_params['exif'] = exif_bytes

                # 根据格式设置最佳质量参数
                if ext.lower() in ['.jpg', '.jpeg']:
                    save_params['quality'] = 100  # 最高质量
                    save_params['subsampling'] = 0  # 关闭子采样
                elif ext.lower() == '.png':
                    save_params['compress_level'] = 0  # 无损压缩

                # 如果是JPG格式需要转为RGB
                if ext.lower() in ['.jpg', '.jpeg']:
                    composite = composite.convert('RGB')

                # 保存图片（保留原始EXIF和尺寸）
                composite.save(output_path, **save_params)
                self.log(f"  保存成功: {os.path.basename(output_path)} (保留原始尺寸和EXIF)")
                success_count += 1

            except Exception as e:
                error_msg = f"  处理失败: {str(e)}"
                self.log(error_msg)
                error_count += 1

        # 处理完成
        self.log(f"\n处理完成! 成功: {success_count}张, 失败: {error_count}张")
        self.status_label.config(text=f"处理完成: {success_count}成功, {error_count}失败")
        self.process_btn.config(state=tk.NORMAL)

    def get_bottom_region_brightness(self, img, bottom_percent):
        """获取图片底部区域的平均亮度"""
        width, height = img.size
        bottom_start = int(height * (1 - bottom_percent))
        bottom_region = img.crop((0, bottom_start, width, height))

        gray_img = bottom_region.convert("L")
        pixels = list(gray_img.getdata())
        total_brightness = sum(pixels)
        average_brightness = total_brightness / (len(pixels) * 255)

        return average_brightness

    def log(self, message):
        """添加日志信息"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.update_idletasks()


if __name__ == "__main__":
    app = EnhancedWatermarkApp()
    app.mainloop()