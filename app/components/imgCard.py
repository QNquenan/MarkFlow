# -*- coding: utf-8 -*-
# @Time    : 2025/7/22 23:17
# @Author  : Quenan

from PyQt6.QtWidgets import QVBoxLayout
from qfluentwidgets import ElevatedCardWidget, BodyLabel, CaptionLabel


class ImgCard(ElevatedCardWidget):
    """图片卡片组件"""
    
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 180)  # 设置卡片固定尺寸
        
        # 卡片内容布局
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)
        
        # 卡片标题
        self.title_label = BodyLabel(title, self)
        self.title_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        
        # 卡片内容
        self.content_label = CaptionLabel(content, self)
        self.content_label.setStyleSheet('color: #888;')
        
        # 添加到布局
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.content_label)
        card_layout.addStretch(1)
        
    def set_title(self, text: str):
        """设置标题文本"""
        self.title_label.setText(text)
        
    def set_content(self, text: str):
        """设置内容文本"""
        self.content_label.setText(text)