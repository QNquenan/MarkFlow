# -*- coding: utf-8 -*-
# @Time    : 2025/7/23 00:25
# @Author  : Quenan

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget


class SettingsInterface(QWidget):
    """主页界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('SettingsInterface')

        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 添加拉伸因子确保矩形顶部对齐
        main_layout.addStretch(1)

