import json
import os

from PIL import Image
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QHBoxLayout, QSizePolicy
from qfluentwidgets import LineEdit, ComboBox, PushButton, PrimaryPushButton, MessageBox, InfoBar

from app.components.addImgBox import AddImgBox


class WatermarkProcessor(QObject):
    """水印处理器，用于在单独线程中处理图片添加水印"""
    # 定义信号，用于在线程处理完成后通知主线程
    progress = pyqtSignal(int, int)  # 当前进度，总数量
    finished = pyqtSignal()  # 处理完成信号
    error = pyqtSignal(str)  # 错误信息

    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.config = {}
        self._is_running = False

    def set_data(self, image_paths, config):
        """设置处理数据"""
        self.image_paths = image_paths
        self.config = config

    def process_images(self):
        """处理图片添加水印"""
        if self._is_running:
            return
            
        self._is_running = True
        try:
            total_count = len(self.image_paths)
            use_logo = self.config.get('Use_logo', '')
            out_path = self.config.get('Out_path', '')
            logo_size = self.config.get('Logo_size', {})
            logo_bottom = self.config.get('Logo_bottom', 0)  # 获取底部距离配置
            logo_xy = self.config.get('Logo_xy', {})
            
            # 检查必要配置
            if not use_logo:
                self.error.emit("未选择水印图片")
                self._is_running = False
                return
                
            if not out_path:
                self.error.emit("未设置输出路径")
                self._is_running = False
                return
                
            # 确保输出目录存在
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            
            # 加载水印图片
            # 修复路径处理问题
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logo_path = os.path.join(base_dir, 'data', 'watermarks', use_logo)
            
            if not os.path.exists(logo_path):
                self.error.emit(f"水印图片不存在: {logo_path}")
                self._is_running = False
                return
                
            logo_image = Image.open(logo_path)
            
            # 获取水印尺寸
            width = logo_size.get('width', 100)
            height = logo_size.get('height', 100)
            logo_image = logo_image.resize((width, height), Image.LANCZOS)
            
            # 获取水印位置
            x_pos = logo_xy.get('x', 0)  # 0:居中, 1:靠左, 2:靠右
            y_pos = logo_xy.get('y', 0)  # 0:居中, 1:靠上, 2:靠下
            
            # 处理每张图片
            for i, image_path in enumerate(self.image_paths):
                # 发送进度信号
                self.progress.emit(i + 1, total_count)
                
                try:
                    # 打开原始图片
                    original_image = Image.open(image_path)
                    
                    # 获取EXIF信息
                    exif_data = original_image.info.get('exif')
                    
                    # 计算水印位置
                    logo_x, logo_y = self._calculate_logo_position_pil(original_image, logo_image, x_pos, y_pos, logo_bottom)
                    
                    # 粘贴水印到原始图片
                    # 如果logo_image有alpha通道，则使用alpha通道作为mask
                    if logo_image.mode == 'RGBA':
                        original_image.paste(logo_image, (logo_x, logo_y), logo_image)
                    else:
                        original_image.paste(logo_image, (logo_x, logo_y))
                    
                    # 保存图片
                    filename = os.path.basename(image_path)
                    name, ext = os.path.splitext(filename)
                    output_path = os.path.join(out_path, f"{name}_watermarked{ext}")
                    
                    # 保存最终图片，保留EXIF信息，使用最高质量导出
                    save_kwargs = {}
                    if exif_data:
                        save_kwargs['exif'] = exif_data
                    
                    # 根据不同格式使用最高质量保存方式
                    if ext.lower() in ['.jpg', '.jpeg']:
                        # JPEG格式使用最高质量保存
                        save_kwargs['quality'] = 100
                        original_image.save(output_path, "JPEG", **save_kwargs)
                    elif ext.lower() == '.png':
                        # PNG格式使用无压缩保存
                        save_kwargs['optimize'] = False
                        original_image.save(output_path, "PNG", **save_kwargs)
                    else:
                        # 其他格式使用默认设置保存
                        original_image.save(output_path, **save_kwargs)
                    
                    # 显式关闭图片以释放内存
                    original_image.close()
                        
                except Exception as e:
                    self.error.emit(f"处理图片 {image_path} 时出错: {str(e)}")
                    continue
                finally:
                    # 确保在任何情况下都尝试释放资源
                    if 'original_image' in locals():
                        try:
                            original_image.close()
                        except:
                            pass
            
            # 显式关闭水印图片以释放内存
            logo_image.close()
            
            # 发送完成信号
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"处理图片时出错: {str(e)}")
        finally:
            self._is_running = False
    
    def _calculate_logo_position_pil(self, image, logo, x_pos, y_pos, bottom_margin=0):
        """计算水印位置 (PIL版本)"""
        image_width, image_height = image.size
        logo_width, logo_height = logo.size
        
        # 计算x坐标
        if x_pos == 0:  # 居中
            logo_x = (image_width - logo_width) // 2
        elif x_pos == 1:  # 靠左
            logo_x = 0
        elif x_pos == 2:  # 靠右
            logo_x = image_width - logo_width
        else:
            logo_x = 0
            
        # 计算y坐标
        if y_pos == 0:  # 居中
            logo_y = (image_height - logo_height) // 2
        elif y_pos == 1:  # 靠上
            logo_y = 0
        elif y_pos == 2:  # 靠下
            logo_y = image_height - logo_height - bottom_margin  # 考到底部边距
        else:
            logo_y = 0
            
        return logo_x, logo_y


class HomeInterface(QWidget):
    """主页界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('HomeInterface')

        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 使用新的AddImgBox组件
        self.add_img_box = AddImgBox(self)
        main_layout.addWidget(self.add_img_box)

        # 添加配置控件
        self.add_config_controls(main_layout)

        # 读取配置文件并设置默认值
        self.load_config()

        # 连接按钮信号
        self.save_config_button.clicked.connect(self.save_config)
        self.reset_button.clicked.connect(self.reset_config)
        self.start_task_button.clicked.connect(self.start_task)
        self.clear_button.clicked.connect(self.clear_image_list)

        # 水印处理线程和处理器
        self.watermark_thread = None
        self.watermark_processor = None
        self.state_tooltip = None


    def add_config_controls(self, parent_layout):
        """添加配置控件"""
        # 创建主水平布局
        main_config_layout = QHBoxLayout()
        main_config_layout.setObjectName('mainConfigLayout')
        main_config_layout.setContentsMargins(0, 20, 0, 0)

        # 创建输入框区域（垂直布局）
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(0, 0, 0, 0)

        # 宽度输入框
        self.width_input = LineEdit()
        self.width_input.setPlaceholderText("输入宽度")
        width_layout = QHBoxLayout()
        width_label = QLabel("宽度（px）:")
        width_label.setObjectName("widthLabel")
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_input)
        input_layout.addLayout(width_layout)

        # 高度输入框
        self.height_input = LineEdit()
        self.height_input.setPlaceholderText("输入高度")
        height_layout = QHBoxLayout()
        height_label = QLabel("高度（px）:")
        height_label.setObjectName("heightLabel")
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_input)
        input_layout.addLayout(height_layout)

        # 距离底部距离输入框
        self.bottom_margin_input = LineEdit()
        self.bottom_margin_input.setPlaceholderText("输入距离底部距离")
        bottom_margin_layout = QHBoxLayout()
        bottom_margin_label = QLabel("底部距离（px）:")
        bottom_margin_label.setObjectName("bottomMarginLabel")
        bottom_margin_layout.addWidget(bottom_margin_label)
        bottom_margin_layout.addWidget(self.bottom_margin_input)
        input_layout.addLayout(bottom_margin_layout)

        self.tip = QLabel("Tips: 不要忘记点击保存配置口牙")
        self.tip.setObjectName("tip")
        input_layout.addWidget(self.tip)
        
        input_layout.addStretch()

        # 创建下拉框区域（垂直布局）
        combo_widget = QWidget()
        combo_layout = QVBoxLayout(combo_widget)
        combo_layout.setSpacing(10)
        combo_layout.setContentsMargins(20, 0, 20, 0)  # 添加左右边距

        # 关于y的下拉框（垂直对齐方式）
        self.vertical_align_combo = ComboBox()
        self.vertical_align_combo.addItems(['居中', '靠上', '靠下'])
        self.vertical_align_combo.setCurrentText('居中')
        vertical_layout = QHBoxLayout()
        vertical_layout.addStretch()  # 添加左侧弹性空间
        vertical_align_label = QLabel("垂直对齐:")
        vertical_align_label.setObjectName("verticalAlignLabel")
        vertical_layout.addWidget(vertical_align_label)
        vertical_layout.addWidget(self.vertical_align_combo)
        vertical_layout.addStretch()  # 添加右侧弹性空间
        combo_layout.addLayout(vertical_layout)

        # 关于x的下拉框（水平对齐方式）
        self.horizontal_align_combo = ComboBox()
        self.horizontal_align_combo.addItems(['居中', '靠左', '靠右'])
        self.horizontal_align_combo.setCurrentText('居中')
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addStretch()  # 添加左侧弹性空间
        horizontal_align_label = QLabel("水平对齐:")
        horizontal_align_label.setObjectName("horizontalAlignLabel")
        horizontal_layout.addWidget(horizontal_align_label)
        horizontal_layout.addWidget(self.horizontal_align_combo)
        horizontal_layout.addStretch()  # 添加右侧弹性空间
        combo_layout.addLayout(horizontal_layout)
        combo_layout.addStretch()

        # 创建按钮区域（垂直布局）
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.reset_button = PushButton("重置")
        self.clear_button = PushButton("清空图片列表")
        self.save_config_button = PushButton("保存配置")
        self.start_task_button = PrimaryPushButton("开始任务")

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_config_button)
        button_layout.addWidget(self.start_task_button)
        button_layout.addStretch()

        # 将三个区域添加到主配置布局中，并平均分配宽度
        main_config_layout.addWidget(input_widget, 1)
        main_config_layout.addWidget(combo_widget, 1)
        main_config_layout.addWidget(button_widget, 1)

        # 将配置布局添加到父布局
        parent_layout.addLayout(main_config_layout)

    def load_config(self):
        """加载配置文件并设置默认值"""
        try:
            # 获取配置文件路径
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'config.json')

            # 读取配置文件
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # 读取Logo_size并设置到输入框
                logo_size = config.get('Logo_size', {})
                width = logo_size.get('width', '')
                height = logo_size.get('height', '')

                # 设置输入框的值
                self.width_input.setText(str(width))
                self.height_input.setText(str(height))

                # 读取Logo_bottom并设置到底部距离输入框
                bottom_margin = config.get('Logo_bottom', '')
                self.bottom_margin_input.setText(str(bottom_margin))

                # 读取Logo_xy并设置下拉框选项
                logo_xy = config.get('Logo_xy', {})
                x = logo_xy.get('x', 0)
                y = logo_xy.get('y', 0)

                # 设置下拉框选项 (0是居中，1是靠上/靠左，2是靠下/靠右)
                # 垂直对齐方式: 0-居中, 1-靠上, 2-靠下
                if y == 0:
                    self.vertical_align_combo.setCurrentText('居中')
                elif y == 1:
                    self.vertical_align_combo.setCurrentText('靠上')
                elif y == 2:
                    self.vertical_align_combo.setCurrentText('靠下')

                # 水平对齐方式: 0-居中, 1-靠左, 2-靠右
                if x == 0:
                    self.horizontal_align_combo.setCurrentText('居中')
                elif x == 1:
                    self.horizontal_align_combo.setCurrentText('靠左')
                elif x == 2:
                    self.horizontal_align_combo.setCurrentText('靠右')
            else:
                # 配置文件不存在时设置默认值
                self.bottom_margin_input.setText("0")
        except Exception as e:
            # 如果读取配置文件出错，设置默认值
            print(f"读取配置文件时出错: {e}")
            self.bottom_margin_input.setText("0")

    def save_config(self):
        """保存配置到文件"""
        try:
            # 获取配置文件路径
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'config.json')

            # 读取现有配置或创建新配置
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}

            # 获取输入框的值
            try:
                width = int(self.width_input.text()) if self.width_input.text() else 0
                height = int(self.height_input.text()) if self.height_input.text() else 0
                bottom_margin = int(self.bottom_margin_input.text()) if self.bottom_margin_input.text() else 0
            except ValueError:
                width = 0
                height = 0
                bottom_margin = 0

            # 获取下拉框的值并转换为数字
            # 垂直对齐方式: 居中-0, 靠上-1, 靠下-2
            vertical_text = self.vertical_align_combo.currentText()
            if vertical_text == '居中':
                y = 0
            elif vertical_text == '靠上':
                y = 1
            elif vertical_text == '靠下':
                y = 2
            else:
                y = 0

            # 水平对齐方式: 居中-0, 靠左-1, 靠右-2
            horizontal_text = self.horizontal_align_combo.currentText()
            if horizontal_text == '居中':
                x = 0
            elif horizontal_text == '靠左':
                x = 1
            elif horizontal_text == '靠右':
                x = 2
            else:
                x = 0

            # 更新配置
            config['Logo_size'] = {
                'width': width,
                'height': height
            }
            config['Logo_bottom'] = bottom_margin  # 保存到底部距离独立字段
            config['Logo_xy'] = {
                'x': x,
                'y': y
            }

            # 保存配置到文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            # 显示保存成功的提示
            InfoBar.success(
                title="保存成功",
                content="配置已成功保存",
                parent=self,
                duration=3000
            )

        except Exception as e:
            print(f"保存配置文件时出错: {e}")
            InfoBar.error(
                title="保存失败",
                content="配置保存失败，请检查权限或磁盘空间",
                parent=self,
                duration=3000
            )

    def reset_config(self):
        """重置配置到默认值"""
        # 弹出确认对话框
        box = MessageBox(
            "确认重置",
            "确定要将配置重置为默认值吗？",
            self
        )
        box.yesButton.setText("好的")
        box.cancelButton.setText("取消")
        if box.exec():
            # 重置输入框和下拉框的值
            self.width_input.setText("1000")
            self.height_input.setText("250")
            self.bottom_margin_input.setText("0")  # 重置底部距离输入框为默认值0
            self.vertical_align_combo.setCurrentText("居中")
            self.horizontal_align_combo.setCurrentText("居中")
            
            # 显示重置成功的提示
            InfoBar.success(
                title="重置成功",
                content="配置已重置为默认值",
                parent=self,
                duration=3000
            )

    def start_task(self):
        """开始任务"""
        try:
            # 获取配置文件路径
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'config.json')
            
            # 读取配置文件
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 检查是否有Use_logo的值
                use_logo = config.get('Use_logo')
                if not use_logo:
                    # 弹出警告提示
                    InfoBar.warning(
                        title="警告",
                        content="请先选择水印图片",
                        parent=self,
                        duration=3000
                    )
                    return
            else:
                # 配置文件不存在，弹出警告提示
                InfoBar.warning(
                    title="警告",
                    content="请先选择水印图片",
                    parent=self,
                    duration=3000
                )
                return
                
        except Exception as e:
            print(f"读取配置文件时出错: {e}")
            InfoBar.warning(
                title="错误",
                content="配置文件读取失败",
                parent=self,
                duration=3000
            )
            return
        
        # 检查是否有图片需要处理
        if not self.add_img_box.added_images:
            InfoBar.warning(
                title="警告",
                content="请先添加需要处理的图片",
                parent=self,
                duration=3000
            )
            return
        
        # 检查是否正在处理中
        if hasattr(self, '_is_processing') and self._is_processing:
            InfoBar.warning(
                title="警告",
                content="正在处理中，请稍后再试",
                parent=self,
                duration=3000
            )
            return
        
        # 显示开始处理提示
        InfoBar.info(
            title="开始处理",
            content="正在处理图片，请稍候...",
            parent=self,
            duration=3000
        )
        
        # 清理旧的线程（如果存在）
        if hasattr(self, 'watermark_thread') and self.watermark_thread:
            if self.watermark_thread.isRunning():
                self.watermark_thread.quit()
                self.watermark_thread.wait()
            self.watermark_thread.deleteLater()
            
        if hasattr(self, 'watermark_processor') and self.watermark_processor:
            self.watermark_processor.deleteLater()
        
        # 创建水印处理线程和处理器
        self.watermark_thread = QThread()
        self.watermark_processor = WatermarkProcessor()
        self.watermark_processor.moveToThread(self.watermark_thread)
        
        # 连接信号
        self.watermark_thread.started.connect(self.watermark_processor.process_images)
        self.watermark_processor.finished.connect(self.processing_finished)
        self.watermark_processor.error.connect(self.processing_error)
        self.watermark_processor.finished.connect(self.watermark_thread.quit)
        self.watermark_processor.error.connect(self.watermark_thread.quit)
        # 确保线程正确清理
        self.watermark_thread.finished.connect(self.on_thread_finished)
        
        # 设置处理数据
        self.watermark_processor.set_data(list(self.add_img_box.added_images), config)
        
        # 设置处理状态
        self._is_processing = True
        
        # 启动线程
        self.watermark_thread.start()
    
    def on_thread_finished(self):
        """线程结束后的清理工作"""
        if hasattr(self, 'watermark_thread') and self.watermark_thread:
            self.watermark_thread.deleteLater()
            self.watermark_thread = None
        if hasattr(self, 'watermark_processor') and self.watermark_processor:
            self.watermark_processor.deleteLater()
            self.watermark_processor = None
        self.is_processing = False
    
    def processing_error(self, error_msg):
        """处理出错"""
        # 重置处理状态
        self._is_processing = False
        
        InfoBar.error(
            title="错误",
            content=error_msg,
            parent=self,
            duration=5000
        )
    
    def processing_finished(self):
        """处理完成"""
        # 重置处理状态
        self._is_processing = False
        
        InfoBar.success(
            title="处理完成",
            content="所有图片已处理完成并保存到输出目录",
            parent=self,
            duration=5000
        )
    
    
    def cleanup_threads(self):
        """清理所有正在运行的线程"""
        if hasattr(self, 'watermark_thread') and self.watermark_thread and self.watermark_thread.isRunning():
            self.watermark_thread.quit()
            self.watermark_thread.wait()
    
    @property
    def is_processing(self):
        """检查是否有正在运行的处理任务"""
        return hasattr(self, '_is_processing') and self._is_processing
    
    @is_processing.setter
    def is_processing(self, value):
        """设置处理状态"""
        self._is_processing = value
    
    def clear_image_list(self):
        """清空图片列表"""
        # 清空AddImgBox中的所有图片
        # 遍历布局中的所有widget
        for i in reversed(range(self.add_img_box.main_layout.count())):
            widget = self.add_img_box.main_layout.itemAt(i).widget()
            if widget and widget != self.add_img_box.default_container:
                # 从布局中移除并删除widget
                self.add_img_box.main_layout.removeWidget(widget)
                widget.deleteLater()

        # 清空已添加图片的集合
        self.add_img_box.added_images.clear()

        # 如果默认容器不存在，则创建它
        if not self.add_img_box.default_container:
            self.add_img_box.default_container = QWidget(self.add_img_box.scroll_widget)
            self.add_img_box.default_container.setObjectName('defaultContainer')
            container_layout = QVBoxLayout(self.add_img_box.default_container)
            container_layout.setContentsMargins(0, 0, 0, 0)

            self.add_img_box.default_label = QLabel('拖拽图片到这里')
            self.add_img_box.default_label.setObjectName('defaultLabel')
            self.add_img_box.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.add_img_box.default_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            container_layout.addWidget(self.add_img_box.default_label)
            self.add_img_box.default_container.setLayout(container_layout)
            self.add_img_box.main_layout.addWidget(self.add_img_box.default_container)

            # 设置容器大小为视口大小
            if self.add_img_box.viewport():
                self.add_img_box.default_container.resize(self.add_img_box.viewport().size())
                self.add_img_box.default_container.setMinimumSize(self.add_img_box.viewport().size())

        # 禁用滚动条，恢复初始状态
        self.add_img_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.add_img_box.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 显示清空成功的提示
        InfoBar.success(
            title="清空成功",
            content="图片列表已清空",
            parent=self,
            duration=3000
        )

