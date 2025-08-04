import sys
import os  # 添加os模块用于文件路径检查
import json

from PyQt6.QtCore import QSize, QFile, QTextStream, QEventLoop, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox  # 添加QMessageBox用于提示
from qfluentwidgets import FluentIcon as FIF, FluentWindow, SplashScreen, setTheme, Theme
from qfluentwidgets.common.config import qconfig  # 导入qconfig用于获取主题设置
from app.view.home_Interface import HomeInterface
from app.view.settings_interface import SettingsInterface, markflowConfig, load_theme_styles  # 导入配置类和load_theme_styles函数
from app.view.watermark_interface import WatermarkInterface  # 导入水印管理界面

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口图标
        self.setWindowIcon(QIcon('app/res/img/logo.png'))
        self.setWindowTitle('MarkFlow')

        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        # 导入界面
        self.home_interface = HomeInterface()
        self.settings_interface = SettingsInterface()
        self.watermark_interface = WatermarkInterface()  # 创建水印管理界面实例

        # 初始化
        self.initNav()
        self.initWindows()
        
        # 在创建其他子页面前先显示主界面
        self.show()
        
        # 创建子界面
        self.createSubInterface()
        
        # 隐藏启动页面
        self.splashScreen.finish()

    def initNav(self):
        """初始化导航栏"""
        self.addSubInterface(self.home_interface, FIF.HOME, '主页')
        self.addSubInterface(self.watermark_interface, FIF.PHOTO, '水印管理')
        self.addSubInterface(self.settings_interface, FIF.SETTING, '设置', position='NavigationItemPosition.BOTTOM')

    def initWindows(self):
        """初始化窗口"""
        self.resize(960, 780)
        self.setMinimumWidth(760)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        QApplication.processEvents()
        
    def createSubInterface(self):
        """创建子界面"""
        # 使用事件循环模拟加载过程
        loop = QEventLoop(self)
        QTimer.singleShot(1500, loop.quit)
        loop.exec()


def check_data_folder():
    """检查data文件夹和config.json文件是否存在"""
    # 获取程序所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    
    # 检查data文件夹是否存在
    data_folder_path = os.path.join(current_dir, 'data')
    if not os.path.exists(data_folder_path):
        # 创建data文件夹
        os.makedirs(data_folder_path)
        print("已创建data文件夹")
    
    # 检查文件是否存在
    data_json_path = os.path.join(data_folder_path, 'config.json')
    if not os.path.exists(data_json_path):
        default_config_path = os.path.join(current_dir, 'config', 'default_config.json')
        if os.path.exists(default_config_path):
            # 从默认配置文件读取内容
            with open(default_config_path, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
            
            # 写入
            with open(data_json_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            print("已从默认配置文件创建config.json文件")
        else:
            with open(data_json_path, 'w', encoding='utf-8') as f:
                f.write('{}')
            print("已创建空的config.json文件")


if __name__ == "__main__":
    # 检查data文件夹和data.json文件
    check_data_folder()
    
    app = QApplication(sys.argv)
    
    # 设置应用程序主题
    theme_mode = qconfig.get(markflowConfig.themeMode)
    setTheme(theme_mode)
    
    # 根据主题加载样式表
    load_theme_styles(app, theme_mode)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())