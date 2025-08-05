import sys
import os  # 添加os模块用于文件路径检查
import json

from PyQt6.QtCore import Qt, QSize, QFile, QTextStream, QEventLoop, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox  # 添加QMessageBox用于提示
from qfluentwidgets import FluentIcon as FIF, FluentWindow, SplashScreen, setTheme, Theme
from qfluentwidgets.common.config import qconfig  # 导入qconfig用于获取主题设置
from app.view.home_Interface import HomeInterface
from app.view.settings_interface import SettingsInterface, markflowConfig, load_theme_styles  # 导入配置类和load_theme_styles函数
from app.view.watermark_interface import WatermarkInterface  # 导入水印管理界面
# 导入资源文件
import app.components.resources_rc


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口图标，使用资源路径
        self.setWindowIcon(QIcon(':/app/res/favicon.ico'))
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
        self.setMinimumSize(800, 700)

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


def load_global_styles(app):
    """加载全局样式表"""
    try:
        # 获取当前主题
        theme_mode = qconfig.get(markflowConfig.themeMode)
        theme_dir = "light" if theme_mode == Theme.LIGHT else "dark"
        
        # 定义需要加载的样式表资源路径
        qss_files = [
            f":/app/res/qss/{theme_dir}/home.qss",
            f":/app/res/qss/{theme_dir}/settings.qss",
            f":/app/res/qss/{theme_dir}/watermark.qss"
        ]
        
        all_styles = ""
        
        # 读取并合并所有样式表
        for qss_path in qss_files:
            # 使用QFile读取资源文件
            file = QFile(qss_path)
            if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                stream = QTextStream(file)
                style = stream.readAll()
                all_styles += style + "\n"
                file.close()
                print(f"成功加载样式表: {qss_path}")
            else:
                print(f"无法加载样式表: {qss_path}")
        
        # 应用样式表到整个应用程序
        app.setStyleSheet(all_styles)
        
    except Exception as e:
        print(f"加载全局样式表时出错: {e}")


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


if __name__ == '__main__':
    # 启用高分屏缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    
    # 检查并创建必要的数据文件夹
    check_data_folder()
    
    # 设置主题
    setTheme(qconfig.get(markflowConfig.themeMode))
    
    # 加载全局样式表
    load_global_styles(app)
    
    # 创建主窗口
    w = MainWindow()
    w.show()
    
    app.exec()
