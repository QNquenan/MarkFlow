from PyQt6.QtCore import Qt, QMimeData, QUrl, QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QScrollArea, QWidget, QLabel, QVBoxLayout, QApplication, QSizePolicy
from qfluentwidgets import FlowLayout, RoundMenu, Action, FluentIcon
import os

class ProcessedImageData:
    """处理后的图片数据"""
    def __init__(self, image_path, filename, pixmap=None, error=None):
        self.image_path = image_path
        self.filename = filename
        self.pixmap = pixmap
        self.error = error

class ImageProcessor(QObject):
    """图片处理器，用于在单独线程中处理图片"""
    finished = pyqtSignal(ProcessedImageData)
    error = pyqtSignal(str)
    processing_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.file_queue = []

    def process_images(self, file_paths):
        """处理图片文件列表"""
        self.file_queue.extend(file_paths)
        self._process_next()

    def _process_next(self):
        """处理队列中的下一个文件"""
        if self.file_queue:
            file_path = self.file_queue.pop(0)
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                
                try:
                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            200, 100, 
                            Qt.AspectRatioMode.KeepAspectRatio, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                        processed_data = ProcessedImageData(file_path, filename, scaled_pixmap)
                    else:
                        processed_data = ProcessedImageData(file_path, filename, error="图片加载失败")
                except Exception as e:
                    processed_data = ProcessedImageData(file_path, filename, error=f"处理图片时出错: {str(e)}")
                
                self.finished.emit(processed_data)
            else:
                self.error.emit(f"文件不存在: {file_path}")
            
            QTimer.singleShot(10, self._process_next)
        else:
            self.processing_done.emit()

class AddImgBox(QScrollArea):
    """可滚动图片容器组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AddImgBox')
        self.setMinimumHeight(300)
        
        self.added_images = set()
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName('scrollWidget')
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.main_layout = FlowLayout(self.scroll_widget)
        self.main_layout.setObjectName('mainLayout')
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.default_container = QWidget(self.scroll_widget)
        self.default_container.setObjectName('defaultContainer')
        container_layout = QVBoxLayout(self.default_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.default_label = QLabel('拖拽图片到这里')
        self.default_label.setObjectName('defaultLabel')
        self.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        container_layout.addWidget(self.default_label)
        self.default_container.setLayout(container_layout)
        self.main_layout.addWidget(self.default_container)

        self.setAcceptDrops(True)
        
        self.thread = QThread()
        self.image_processor = ImageProcessor()
        self.image_processor.moveToThread(self.thread)
        self.image_processor.finished.connect(self.addImageCard)
        self.image_processor.error.connect(self.handleImageError)
        
        self.thread.start()

    def dragEnterEvent(self, event):
        """处理拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """处理拖放事件"""
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            if self.default_container and self.default_container.parent():
                self.main_layout.removeWidget(self.default_container)
                self.default_container.deleteLater()
                self.default_container = None
                self.default_label = None
                
                self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            file_paths = []
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path not in self.added_images:
                    self.added_images.add(file_path)
                    file_paths.append(file_path)
            
            if file_paths:
                self.image_processor.process_images(file_paths)
            
            event.acceptProposedAction()
        else:
            event.ignore()

    def handleImageError(self, error_msg):
        """处理图片处理错误"""
        print(f"图片处理错误: {error_msg}")

    def resizeEvent(self, event):
        """处理窗口大小调整事件"""
        super().resizeEvent(event)
        if hasattr(self, 'default_container') and self.default_container:
            self.default_container.resize(self.viewport().size())
            self.default_container.setMinimumSize(self.viewport().size())
            
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        if self.parent():
            parent_height = self.parent().height()
            self.setFixedHeight(int(parent_height * 0.5))

    def addImageCard(self, processed_data):
        """添加图片卡片"""
        card = QWidget()
        card.setObjectName('imageCard')
        card.setMinimumSize(206, 120)
        card.setMaximumWidth(206)
        
        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos: self.showCardContextMenu(card, pos))
        card.image_path = processed_data.image_path

        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        img_label = QLabel()
        img_label.setObjectName('imageLabel')
        
        if processed_data.error:
            img_label.setText(processed_data.error)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setStyleSheet("color: red; border: 1px solid gray;border-radius: 10px;")
        else:
            img_label.setPixmap(processed_data.pixmap)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        name_label = QLabel(processed_data.filename)
        name_label.setObjectName('nameLabel')
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(img_label)
        layout.addWidget(name_label)
        
        self.main_layout.addWidget(card)
        QApplication.processEvents()
    
    def showCardContextMenu(self, card, pos):
        """显示卡片上下文菜单"""
        menu = RoundMenu(parent=self)
        
        delete_action = Action(FluentIcon.DELETE, '删除')
        delete_action.triggered.connect(lambda: self.removeCard(card))
        menu.addAction(delete_action)
        
        menu.exec(card.mapToGlobal(pos))
    
    def removeCard(self, card):
        """移除卡片"""
        self.main_layout.removeWidget(card)
        if hasattr(card, 'image_path'):
            self.added_images.discard(card.image_path)
        card.deleteLater()
        
        self.main_layout.update()
        self.scroll_widget.update()
        QApplication.processEvents()
        
        if self.main_layout.count() == 0:
            if not self.default_container:
                self.default_container = QWidget(self.scroll_widget)
                self.default_container.setObjectName('defaultContainer')
                container_layout = QVBoxLayout(self.default_container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                
                self.default_label = QLabel('拖拽图片到这里')
                self.default_label.setObjectName('defaultLabel')
                self.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.default_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                
                container_layout.addWidget(self.default_label)
                self.default_container.setLayout(container_layout)
                self.main_layout.addWidget(self.default_container)
                
                if self.viewport():
                    self.default_container.resize(self.viewport().size())
                    self.default_container.setMinimumSize(self.viewport().size())
            
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def closeEvent(self, event):
        """窗口关闭事件，用于正确关闭线程"""
        self.thread.quit()
        self.thread.wait()
        event.accept()