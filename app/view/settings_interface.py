# -*- coding: utf-8 -*-
# @Time    : 2025/7/23 00:25
# @Author  : Quenan

import os
import json
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QFile, QTextStream
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QFileDialog, QApplication
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (SettingCardGroup, PushSettingCard, OptionsSettingCard, HyperlinkCard,
                            PrimaryPushSettingCard, Theme, setTheme)
from qfluentwidgets import (ScrollArea, qconfig, InfoBar, InfoBarPosition)  # 添加ScrollArea
from qfluentwidgets.common.config import ConfigItem, OptionsConfigItem, OptionsValidator, QConfig

class MarkFlowConfig(QConfig):
    """ MarkFlow configuration """
    default_download_path = os.path.join(Path.home(), 'Downloads', 'MarkFlow')
    os.makedirs(default_download_path, exist_ok=True)
    
    workFolder = ConfigItem("Folders", "WorkFolder", default_download_path)
    themeMode = OptionsConfigItem(
        "Theme", "themeMode", Theme.DARK, OptionsValidator(Theme), restart=False
    )

markflowConfig = MarkFlowConfig()

def get_application_path():
    """获取应用程序所在目录的正确路径"""
    if getattr(sys, 'frozen', False):
        # 如果程序是打包后的exe文件
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是直接运行的Python脚本
        application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return application_path

def load_config_from_file():
    """从data/config.json文件加载配置到QConfig中"""
    current_dir = get_application_path()
    config_file_path = os.path.join(current_dir, 'data', 'config.json')
    
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if "Out_path" in config_data:
                qconfig.set(markflowConfig.workFolder, config_data["Out_path"])
                
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
    current_dir = get_application_path()
    config_file_path = os.path.join(current_dir, 'data', 'config.json')
    
    try:
        config_data = {}
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        config_data["Out_path"] = qconfig.get(markflowConfig.workFolder)
        
        theme_value = qconfig.get(markflowConfig.themeMode)
        theme_map_reverse = {
            Theme.LIGHT: "Light",
            Theme.DARK: "Dark",
            Theme.AUTO: "Auto"
        }
        config_data["Theme_mode"] = theme_map_reverse.get(theme_value, "Auto")
        
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"保存配置文件时出错: {e}")

load_config_from_file()

def load_theme_styles(app, theme_mode):
    """根据主题模式加载相应的样式表"""
    try:
        theme_dir = "light" if theme_mode == Theme.LIGHT else "dark"
        
        # 使用资源路径
        qss_files = [
            f":/app/res/qss/{theme_dir}/home.qss",
            f":/app/res/qss/{theme_dir}/settings.qss",
            f":/app/res/qss/{theme_dir}/watermark.qss"
        ]
        
        all_styles = ""
        
        for qss_path in qss_files:
            # 使用QFile读取资源文件
            file = QFile(qss_path)
            if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                stream = QTextStream(file)
                style = stream.readAll()
                all_styles += style + "\n"
                file.close()
                print(f"{os.path.basename(qss_path)}样式表导入成功")
            else:
                print(f"无法加载样式表: {qss_path}")
        
        app.setStyleSheet(all_styles)
        
    except Exception as e:
        print(None, "导入失败", f"导入样式表时出错:\n{str(e)}")

class CustomFolderSettingCard(PushSettingCard):
    """ 自定义文件夹设置卡片，支持覆盖模式 """
    
    folderChanged = pyqtSignal(str)
    
    def __init__(self, configItem, title, content=None, directory="./", parent=None):
        super().__init__("选择文件夹", FIF.FOLDER, title, content, parent)
        self.configItem = configItem
        saved_folder = qconfig.get(configItem)
        self._dialogDirectory = saved_folder if saved_folder and saved_folder != "./" else markflowConfig.default_download_path
        
        self.clicked.connect(self.__onButtonClicked)
        
    def __onButtonClicked(self):
        """ 选择文件夹 """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("选择输出目录"), self._dialogDirectory)
        
        if not folder:
            return
            
        qconfig.set(self.configItem, folder)
        self.folderChanged.emit(folder)
        
        save_config_to_file()
        
        self.setContent(folder)

class SettingsInterface(QWidget):
    """设置界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('SettingsInterface')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.settingLabel = QLabel('设置', self)
        self.settingLabel.setObjectName('settingLabel')
        main_layout.addWidget(self.settingLabel)
        
        self.create_setting_cards()
        main_layout.addWidget(self.setting_group)
        main_layout.addWidget(self.about_group)
        
        main_layout.addStretch(1)
        
    def create_setting_cards(self):
        """创建设置卡片"""
        self.setting_group = SettingCardGroup("", self)
        
        work_folder = qconfig.get(markflowConfig.workFolder)
        content = work_folder if work_folder else markflowConfig.default_download_path
        
        self.folder_card = CustomFolderSettingCard(
            markflowConfig.workFolder,
            "工作目录",
            content,
            work_folder if work_folder else markflowConfig.default_download_path,
            self.setting_group
        )
        
        self.theme_card = OptionsSettingCard(
            markflowConfig.themeMode,
            FIF.BRUSH,
            "应用主题",
            "更改应用程序的外观",
            texts=["浅色", "深色", "跟随系统"],
            parent=self.setting_group
        )
        
        self.theme_card.configItem.valueChanged.connect(self.on_theme_changed)
        
        self.setting_group.addSettingCard(self.folder_card)
        self.setting_group.addSettingCard(self.theme_card)
        
        self.about_group = SettingCardGroup("关于", self)
        
        self.link_card = HyperlinkCard(
            'https://github.com/QNquenan/MarkFlow',
            '打开Github',
            FIF.GITHUB,
            'Github仓库',
            '查看最新的版本！',
            self.about_group
        )
        
        self.about_card = PrimaryPushSettingCard(
            '检查更新',
            FIF.INFO,
            '关于 MarkFlow',
            '© 2025 Quenan. 版本 1.0.0',
            self.about_group
        )
        
        # 连接检查更新按钮的点击信号
        self.about_card.clicked.connect(self.check_updates)
        
        self.about_group.addSettingCard(self.link_card)
        self.about_group.addSettingCard(self.about_card)
        
    def check_updates(self):
        """检查更新按钮的点击事件处理"""
        InfoBar.info(
            title="提示",
            content="自己去Github瞅一眼就好啦🫡",
            parent=self,
            duration=3000
        )
        
    def on_theme_changed(self, value):
        """主题更改时保存配置到文件并设置应用程序主题"""
        save_config_to_file()
        setTheme(value)
        app = QApplication.instance()
        load_theme_styles(app, value)