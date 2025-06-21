# build.py
import PyInstaller.__main__
import os
import shutil

# 清理之前的构建
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('MarkFlow.spec'):
    os.remove('MarkFlow.spec')

# 打包参数
params = [
    'main.py',  # 主程序文件名
    '--name=MarkFlow',
    '--onefile',  # 打包为单个文件
    '--windowed',  # 不显示控制台窗口
    # '--icon=icon.ico',  # 应用图标
    # '--add-data=templates;templates',  # 包含模板文件夹
    # '--add-data=tkinterdnd2;tkinterdnd2',  # 包含拖拽库
    '--hidden-import=PIL._tkinter_finder',  # 隐藏导入
    '--clean',  # 清理临时文件
    '--noconfirm'  # 不确认覆盖
]

# 执行打包
PyInstaller.__main__.run(params)

print("\n打包完成！可执行文件位于 dist/MarkFlow.exe")