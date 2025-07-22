from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt6.QtGui import QPainter
import os  # 添加os模块用于路径操作
from app.components.imgCard import ImgCard
from app.components.addImgBox import AddImgBox  # 导入新的AddImgBox类


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
        
        # 添加拉伸因子确保矩形顶部对齐
        main_layout.addStretch(1)

