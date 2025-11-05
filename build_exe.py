#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 将股票交易助手打包成Windows可执行文件
"""

import os
import sys

# 尝试导入PyInstaller
try:
    import PyInstaller.__main__
except ImportError:
    print("错误：PyInstaller未安装！")
    print("请运行以下命令安装：")
    print("pip install pyinstaller")
    sys.exit(1)

try:
    import akshare
except ImportError:
    print("错误：akshare未安装！")
    print("请运行以下命令安装：")
    print("pip install akshare")
    sys.exit(1)

# 打包配置
APP_NAME = "股票交易助手"
MAIN_SCRIPT = "stock_trader.py"
ICON_FILE = None  # 如果有图标文件，可以设置路径

# 获取akshare的安装路径
akshare_path = os.path.dirname(akshare.__file__)
akshare_data_folder = os.path.join(akshare_path, 'file_fold')

# PyInstaller参数
args = [
    MAIN_SCRIPT,
    '--name={}'.format(APP_NAME),
    '--onefile',  # 打包成单个exe文件
    '--windowed',  # 不显示控制台窗口（GUI应用）
    '--clean',  # 清理临时文件
    '--noconfirm',  # 覆盖输出目录
]

# 如果有数据文件，添加进去
if os.path.exists('watchlist.json'):
    args.append('--add-data=watchlist.json;.')

# 添加akshare的数据文件
if os.path.exists(akshare_data_folder):
    args.append('--add-data={};akshare/file_fold'.format(akshare_data_folder))

# 添加hiddenimports
args.extend([
    '--hidden-import=pandas',
    '--hidden-import=numpy',
    '--hidden-import=akshare',
    '--hidden-import=akshare.futures',
    '--hidden-import=akshare.futures.cons',
    '--hidden-import=akshare.futures.futures_basis',
    '--hidden-import=akshare.stock',
    '--hidden-import=requests',
    '--hidden-import=lxml',
    '--hidden-import=beautifulsoup4',
])

# 如果有图标文件
if ICON_FILE and os.path.exists(ICON_FILE):
    args.append('--icon={}'.format(ICON_FILE))

print("开始打包程序...")
print("打包参数:", ' '.join(args))

try:
    PyInstaller.__main__.run(args)
    print("\n打包完成！")
    print("可执行文件位置: dist/{}.exe".format(APP_NAME))
    print("\n您可以将 dist 文件夹中的 {} 文件分享给其他用户。".format(APP_NAME))
except Exception as e:
    print("打包失败:", str(e))
    sys.exit(1)

