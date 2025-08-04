# -*- coding: utf-8 -*-
# @Time    : 2025/7/23 00:25
# @Author  : Quenan

import os
import json
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QFileDialog, QApplication
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (SettingCardGroup, PushSettingCard, OptionsSettingCard, HyperlinkCard,
                            PrimaryPushSettingCard, Theme, setTheme)
from qfluentwidgets.common.config import ConfigItem, OptionsConfigItem, OptionsValidator, qconfig, QConfig


class MarkFlowConfig(QConfig):
    """ MarkFlow configuration """
    # 获取系统下载目录并创建MarkFlow子目录
    default_download_path = os.path.join(Path.home(), 'Downloads', 'MarkFlow')
    # 确保目录存在
    os.makedirs(default_download_path, exist_ok=True)
    
    # 工作目录配置项，使用默认下载路径作为默认值
    workFolder = ConfigItem("Folders", "WorkFolder", default_download_path)
    themeMode = OptionsConfigItem(
        "Theme", "themeMode", Theme.DARK, OptionsValidator(Theme), restart=False
    )


# 创建全局配置实例
markflowConfig = MarkFlowConfig()


def load_config_from_file():
    """从data/config.json文件加载配置到QConfig中"""
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_file_path = os.path.join(current_dir, 'data', 'config.json')
    
    # 检查配置文件是否存在
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 从配置文件读取工作目录并设置到QConfig中
            if "Out_path" in config_data:
                qconfig.set(markflowConfig.workFolder, config_data["Out_path"])
                
            # 从配置文件读取主题模式并设置到QConfig中
            if "Theme_mode" in config_data:
                theme_map = {
                    "Light": Theme.LIGHT,
                    "Dark": Theme.DARK,
                    "Auto": Theme.AUTO
                }
                theme = theme_map.get(config_data["Theme_mode"], Theme.AUTO)
                qconfig.set(markflowConfig.themeMode, theme)
                
        except Exception as e:
            print(f"读取配置文件时出错: {e}")


def save_config_to_file():
    """将QConfig中的配置保存到data/config.json文件中"""
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_file_path = os.path.join(current_dir, 'data', 'config.json')
    
    try:
        # 读取现有配置文件内容（如果存在）
        config_data = {}
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        # 更新配置数据
        config_data["Out_path"] = qconfig.get(markflowConfig.workFolder)
        
        theme_value = qconfig.get(markflowConfig.themeMode)
        theme_map_reverse = {
            Theme.LIGHT: "Light",
            Theme.DARK: "Dark",
            Theme.AUTO: "Auto"
        }
        config_data["Theme_mode"] = theme_map_reverse.get(theme_value, "Auto")
        
        # 写入配置文件
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"保存配置文件时出错: {e}")


# 在模块加载时读取配置文件
load_config_from_file()


def load_theme_styles(app, theme_mode):
    """根据主题模式加载相应的样式表"""
    try:
        # 确定主题目录
        theme_dir = "light" if theme_mode == Theme.LIGHT else "dark"
        
        # 定义要加载的样式表文件列表
        qss_files = [
            f"app/res/qss/{theme_dir}/home.qss",
            f"app/res/qss/{theme_dir}/settings.qss",
            f"app/res/qss/{theme_dir}/watermark.qss"  # 添加水印界面样式表
        ]
        
        # 存储所有样式表内容
        all_styles = ""
        
        # 遍历并加载所有样式表
        for qss_path in qss_files:
            # 检查文件是否存在
            if os.path.exists(qss_path):
                # 读取样式表
                with open(qss_path, "r", encoding="utf-8") as f:
                    style = f.read()
                    all_styles += style + "\n"

                print(f"{os.path.basename(qss_path)}样式表导入成功")
        
        # 应用所有样式表
        app.setStyleSheet(all_styles)
        
    except Exception as e:
        # 其他异常处理
        print(None, "导入失败", f"导入样式表时出错:\n{str(e)}")


class CustomFolderSettingCard(PushSettingCard):
    """ 自定义文件夹设置卡片，支持覆盖模式 """
    
    folderChanged = pyqtSignal(str)
    
    def __init__(self, configItem, title, content=None, directory="./", parent=None):
        super().__init__("选择文件夹", FIF.FOLDER, title, content, parent)
        self.configItem = configItem
        # 使用配置中保存的路径或默认路径
        saved_folder = qconfig.get(configItem)
        self._dialogDirectory = saved_folder if saved_folder and saved_folder != "./" else markflowConfig.default_download_path
        
        self.clicked.connect(self.__onButtonClicked)
        
    def __onButtonClicked(self):
        """ 选择文件夹 """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("选择工作目录"), self._dialogDirectory)
        
        if not folder:
            return
            
        # 保存选择的文件夹到配置中
        qconfig.set(self.configItem, folder)
        self.folderChanged.emit(folder)
        
        # 保存配置到文件
        save_config_to_file()
        
        # 更新显示内容
        self.setContent(folder)


class SettingsInterface(QWidget):
    """设置界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('SettingsInterface')

        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.settingLabel = QLabel('设置', self)
        self.settingLabel.setObjectName('settingLabel')
        main_layout.addWidget(self.settingLabel)
        
        # 创建设置卡片组
        self.create_setting_cards()
        main_layout.addWidget(self.setting_group)
        main_layout.addWidget(self.about_group)
        
        # 添加拉伸因子确保矩形顶部对齐
        main_layout.addStretch(1)
        
    def create_setting_cards(self):
        """创建设置卡片"""
        # 设置组
        self.setting_group = SettingCardGroup("", self)
        
        # 获取配置中保存的工作目录
        work_folder = qconfig.get(markflowConfig.workFolder)
        content = work_folder if work_folder else markflowConfig.default_download_path
        
        # 文件夹选择卡片（自定义，支持覆盖模式）
        self.folder_card = CustomFolderSettingCard(
            markflowConfig.workFolder,  # configItem
            "工作目录",  # title
            content,  # content (显示当前选择的目录)
            work_folder if work_folder else markflowConfig.default_download_path,  # directory
            self.setting_group  # parent
        )
        
        # 主题设置卡片
        self.theme_card = OptionsSettingCard(
            markflowConfig.themeMode,  # configItem
            FIF.BRUSH,
            "应用主题",
            "更改应用程序的外观",
            texts=["浅色", "深色", "跟随系统"],
            parent=self.setting_group
        )
        
        # 连接主题设置变化信号
        self.theme_card.configItem.valueChanged.connect(self.on_theme_changed)
        
        # 添加卡片到组
        self.setting_group.addSettingCard(self.folder_card)
        self.setting_group.addSettingCard(self.theme_card)
        
        # 关于组
        self.about_group = SettingCardGroup("关于", self)
        
        # 外链卡片
        self.link_card = HyperlinkCard(
            'https://github.com/quenandev/markflow',
            '打开官方文档',
            FIF.LINK,
            '官方文档',
            '查看最新官方文档和使用说明',
            self.about_group
        )
        
        # 关于卡片
        self.about_card = PrimaryPushSettingCard(
            '检查更新',
            FIF.INFO,
            '关于 MarkFlow',
            '© 2025 Quenan. 版本 1.0.0',
            self.about_group
        )
        
        # 添加关于卡片到组
        self.about_group.addSettingCard(self.link_card)
        self.about_group.addSettingCard(self.about_card)
        
    def on_theme_changed(self, value):
        """主题更改时保存配置到文件并设置应用程序主题"""
        # 保存配置到文件
        save_config_to_file()
        
        # 设置应用程序主题
        setTheme(value)
        
        # 重新加载样式表
        app = QApplication.instance()
        load_theme_styles(app, value)