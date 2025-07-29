import sys
import os  # 添加os模块用于文件路径检查

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox  # 添加QMessageBox用于提示
from qfluentwidgets import FluentIcon as FIF, FluentWindow, SplashScreen, setTheme, Theme
from app.view.home_Interface import HomeInterface
from app.view.settings_interface import SettingsInterface

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # 导入界面
        self.home_interface = HomeInterface()
        self.settings_interface = SettingsInterface()

        # 初始化
        self.initNav()
        self.initWindows()

    def initNav(self):
        """初始化导航栏"""

        self.addSubInterface(self.home_interface, FIF.HOME, '主页')
        self.addSubInterface(self.settings_interface, FIF.SETTING, '设置', position='NavigationItemPosition.BOTTOM')

    def initWindows(self):
        """初始化窗口"""

        # 设置窗口大小和最小宽度
        self.resize(960, 780)
        self.setMinimumWidth(760)

        # 设置窗口图标和标题
        self.setWindowIcon(QIcon(':/gallery/images/logo.png'))
        self.setWindowTitle('MarkFlow')

        # 设置毛玻璃效果（Mica）
        # self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 居中显示窗口
        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

if __name__ == "__main__":
    setTheme(Theme.AUTO)
    app = QApplication(sys.argv)
    
    # 尝试加载home.qss样式表
    try:
        # 获取当前脚本所在目录
        qss_path = os.path.join(r"app/res/qss/dark/home.qss")
        
        # 检查文件是否存在
        if os.path.exists(qss_path):
            # 读取并应用样式表
            with open(qss_path, "r", encoding="utf-8") as f:
                style = f.read()
                app.setStyleSheet(style)
            
            # 显示导入成功提示
            print(None, "导入成功", "home.qss样式表导入成功！")
        else:
            # 文件不存在提示
            print(None, "导入失败", "home.qss文件未找到！")
    except Exception as e:
        # 其他异常处理
        print(None, "导入失败", f"导入样式表时出错:\n{str(e)}")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())