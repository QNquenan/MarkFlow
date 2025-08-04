from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer, QEasingCurve
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QWidget, 
                             QFileDialog, QApplication, QMenu)
from qfluentwidgets import (SmoothScrollArea, PushButton, FlowLayout, 
                            FluentIcon as FIF, RoundMenu, Action, MessageBoxBase, 
                            SubtitleLabel, LineEdit)
import os
import json

class RenameDialog(MessageBoxBase):
    """重命名对话框"""
    
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.current_name = current_name
        self.setup_ui()
    
    def setup_ui(self):
        self.titleLabel = SubtitleLabel('重命名', self)
        
        self.nameLineEdit = LineEdit(self)
        self.nameLineEdit.setText(self.current_name)
        self.nameLineEdit.setPlaceholderText('请输入新的文件名')
        self.nameLineEdit.setClearButtonEnabled(True)
        
        self.nameLineEdit.setFocus()
        self.nameLineEdit.selectAll()
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameLineEdit)
        
        self.yesButton.setText('确定')
        self.cancelButton.setText('取消')
        
        self.widget.setMinimumWidth(350)
    
    def getName(self):
        """获取输入的文件名"""
        return self.nameLineEdit.text()
    
    def validate(self):
        """验证输入"""
        name = self.getName().strip()
        if not name:
            return False
        
        if name == self.current_name:
            return False
            
        return True

class WatermarkCard(QWidget):
    """水印卡片组件"""
    watermarkSelected = pyqtSignal(str)
    
    def __init__(self, image_path, filename, parent=None):
        super().__init__(parent)
        self.setObjectName("watermarkCard")
        self.image_path = image_path
        self.filename = filename
        self.is_selected = False
        self.setup_ui()
        self.load_image()
    
    def setup_ui(self):
        """设置界面"""
        self.setFixedSize(160, 160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        self.content_widget.setFixedSize(144, 144)
        
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setFixedSize(120, 120)
        
        self.name_label = QLabel(self.filename)
        self.name_label.setObjectName("nameLabel")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        content_layout.addWidget(self.img_label)
        content_layout.addWidget(self.name_label)
        
        layout.addWidget(self.content_widget)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def load_image(self):
        """加载并显示图片"""
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    120, 120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.img_label.setPixmap(scaled_pixmap)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_selected:
                self.set_selected(True)
                self.watermarkSelected.emit(self.filename)
        super().mousePressEvent(event)
    
    def set_selected(self, selected):
        """设置选中状态"""
        self.is_selected = selected
        self.update_selection_style()
    
    def update_selection_style(self):
        """更新选中样式"""
        if self.is_selected:
            self.content_widget.setProperty("selected", True)
        else:
            self.content_widget.setProperty("selected", False)
        
        self.content_widget.style().unpolish(self.content_widget)
        self.content_widget.style().polish(self.content_widget)
        self.content_widget.update()
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = RoundMenu(parent=self)
        
        rename_action = Action(FIF.EDIT, '重命名')
        rename_action.triggered.connect(self.request_rename)
        menu.addAction(rename_action)
        
        delete_action = Action(FIF.DELETE, '删除')
        delete_action.triggered.connect(self.request_delete)
        menu.addAction(delete_action)
        
        menu.exec(self.mapToGlobal(pos))
    
    def request_rename(self):
        """请求重命名卡片"""
        dialog = RenameDialog(self.filename, self.window())
        if dialog.exec():
            new_name = dialog.getName()
            if new_name and new_name != self.filename:
                self.rename_watermark(new_name)
    
    def rename_watermark(self, new_name):
        """重命名水印文件"""
        try:
            if not os.path.splitext(new_name)[1]:
                ext = os.path.splitext(self.filename)[1]
                new_name = new_name + ext
            
            new_path = os.path.join(os.path.dirname(self.image_path), new_name)
            
            if os.path.exists(new_path):
                from qfluentwidgets import MessageBox
                box = MessageBox("错误", f"文件名 '{new_name}' 已存在!", self.window())
                box.exec()
                return False
            
            os.rename(self.image_path, new_path)
            
            self.image_path = new_path
            self.filename = new_name
            
            self.name_label.setText(new_name)
            
            return True
        except Exception as e:
            print(f"重命名水印时出错: {e}")
            from qfluentwidgets import MessageBox
            box = MessageBox("错误", f"重命名失败: {str(e)}", self.window())
            box.exec()
            return False
    
    def request_delete(self):
        """请求删除卡片"""
        parent_interface = self.parent()
        while parent_interface and not isinstance(parent_interface, WatermarkInterface):
            parent_interface = parent_interface.parent()
        
        if parent_interface and hasattr(parent_interface, 'selected_card'):
            if parent_interface.selected_card == self:
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title="删除失败",
                    content="无法删除当前选中的水印，请先选择其他水印再进行删除操作。",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=parent_interface.window()
                )
                return
        
        self.hide_card()
    
    def hide_card(self):
        """隐藏卡片"""
        try:
            if os.path.exists(self.image_path):
                os.remove(self.image_path)
            
            self.hide()
        except Exception as e:
            print(f"隐藏水印时出错: {e}")
    
    def get_image_path(self):
        """获取图片路径"""
        return self.image_path

class WatermarkInterface(SmoothScrollArea):
    """水印管理界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScrollAnimation(Qt.Orientation.Vertical, 800, QEasingCurve.Type.InOutQuad)
        self.setScrollAnimation(Qt.Orientation.Horizontal, 800, QEasingCurve.Type.InOutQuad)
        self.watermark_dir = self.get_watermark_directory()
        self.selected_card = None
        self.setup_ui()
        self.load_watermarks()
        self.load_selected_watermark()
        
    def _safe_delete_file(self, file_path):
        """安全删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"删除水印文件时出错: {e}")
    
    def get_watermark_directory(self):
        """获取水印目录路径"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        watermark_dir = os.path.join(project_root, 'data', 'watermarks')
        
        os.makedirs(watermark_dir, exist_ok=True)
        return watermark_dir
    
    def setup_ui(self):
        """设置界面"""
        self.setObjectName('WatermarkInterface')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFrameShape(SmoothScrollArea.Shape.NoFrame)
        
        self.setScrollAnimation(Qt.Orientation.Vertical, 500, QEasingCurve.Type.OutQuint)
        self.setScrollAnimation(Qt.Orientation.Horizontal, 500, QEasingCurve.Type.OutQuint)
        
        self.viewport().setObjectName("scrollViewport")
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("scrollWidget")
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        main_layout = QVBoxLayout(self.scroll_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.title_label = QLabel('水印管理', self)
        self.title_label.setObjectName("titleLabel")
        main_layout.addWidget(self.title_label)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.import_button = PushButton(FIF.ADD, '导入水印', self)
        self.import_button.clicked.connect(self.import_watermark)
        button_layout.addWidget(self.import_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        
        self.watermark_area = QWidget(self.scroll_widget)
        self.watermark_area.setObjectName("watermarkArea")
        self.watermark_layout = FlowLayout(self.watermark_area)
        self.watermark_layout.setContentsMargins(0, 0, 0, 0)
        self.watermark_layout.setHorizontalSpacing(12)
        self.watermark_layout.setVerticalSpacing(12)
        self.watermark_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        main_layout.addWidget(self.watermark_area)
        main_layout.addStretch(1)
    
    def handle_watermark_selected(self, filename):
        """处理水印选中事件"""
        if self.selected_card:
            self.selected_card.set_selected(False)
        
        for i in range(self.watermark_layout.count()):
            widget = self.watermark_layout.itemAt(i).widget()
            if widget and isinstance(widget, WatermarkCard) and widget.filename == filename:
                self.selected_card = widget
                break
        
        self.save_selected_watermark(filename)
    
    def save_selected_watermark(self, filename):
        """保存选中的水印到配置文件"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_file_path = os.path.join(project_root, 'data', 'config.json')
            
            config_data = {}
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            
            config_data['Use_logo'] = filename
            
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"保存选中水印到配置文件时出错: {e}")
    
    def load_selected_watermark(self):
        """加载并选中配置文件中指定的水印"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_file_path = os.path.join(project_root, 'data', 'config.json')
            
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                selected_watermark = config_data.get('Use_logo') or config_data.get('use_logo')
                if selected_watermark:
                    for i in range(self.watermark_layout.count()):
                        widget = self.watermark_layout.itemAt(i).widget()
                        if widget and isinstance(widget, WatermarkCard) and widget.filename == selected_watermark:
                            widget.set_selected(True)
                            self.selected_card = widget
                            break
        except Exception as e:
            print(f"加载选中水印时出错: {e}")
    
    def remove_watermark_card(self, card):
        """隐藏水印卡片（避免删除导致的崩溃）"""
        card.hide_card()
    
    def import_watermark(self):
        """导入水印图片(支持批量导入)"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择水印图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_paths:
            success_count = 0
            failed_files = []
            
            for file_path in file_paths:
                try:
                    filename = os.path.basename(file_path)
                    target_path = os.path.join(self.watermark_dir, filename)
                    
                    counter = 1
                    name, ext = os.path.splitext(filename)
                    while os.path.exists(target_path):
                        new_name = f"{name}_{counter}{ext}"
                        target_path = os.path.join(self.watermark_dir, new_name)
                        counter += 1
                    
                    from shutil import copy2
                    copy2(file_path, target_path)
                    
                    card = WatermarkCard(target_path, os.path.basename(target_path), self)
                    card.watermarkSelected.connect(self.handle_watermark_selected)
                    self.watermark_layout.addWidget(card)
                    
                    success_count += 1
                except Exception as e:
                    failed_files.append((os.path.basename(file_path), str(e)))
                    print(f"导入水印 {file_path} 失败: {e}")
            
            QApplication.processEvents()
            
            if failed_files:
                from qfluentwidgets import MessageBox
                msg = f"成功导入 {success_count} 个水印"
                if failed_files:
                    msg += f"\n失败 {len(failed_files)} 个:\n"
                    for file_name, error in failed_files[:3]:
                        msg += f"- {file_name}: {error}\n"
                    if len(failed_files) > 3:
                        msg += f"... 还有 {len(failed_files) - 3} 个文件导入失败"
                
                box = MessageBox("导入完成", msg, self.window())
                box.exec()
            elif success_count > 0:
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.success(
                    title="导入成功",
                    content=f"成功导入 {success_count} 个水印",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
    
    def load_watermarks(self):
        """加载已有的水印"""
        if not os.path.exists(self.watermark_dir):
            return
        
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        
        for filename in os.listdir(self.watermark_dir):
            if filename.lower().endswith(image_extensions):
                image_path = os.path.join(self.watermark_dir, filename)
                card = WatermarkCard(image_path, filename, self)
                card.watermarkSelected.connect(self.handle_watermark_selected)
                self.watermark_layout.addWidget(card)