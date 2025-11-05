#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动修复build.spec文件，添加akshare所需的数据文件
"""

import os
import akshare

def find_akshare_data_files():
    """查找akshare的所有数据文件"""
    akshare_path = os.path.dirname(akshare.__file__)
    data_files = []
    
    # 查找file_fold文件夹
    file_fold = os.path.join(akshare_path, 'file_fold')
    if os.path.exists(file_fold):
        data_files.append((file_fold, 'akshare/file_fold'))
        print(f"找到akshare数据文件夹: {file_fold}")
    
    # 查找其他可能的数据文件夹
    for item in os.listdir(akshare_path):
        item_path = os.path.join(akshare_path, item)
        if os.path.isdir(item_path) and ('data' in item.lower() or 'file' in item.lower()):
            if item != '__pycache__':
                data_files.append((item_path, f'akshare/{item}'))
                print(f"找到akshare数据文件夹: {item_path}")
    
    return data_files

def update_build_spec():
    """更新build.spec文件"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-
import os
import akshare

block_cipher = None

# 获取akshare的安装路径
akshare_path = os.path.dirname(akshare.__file__)

datas = []
if os.path.exists('watchlist.json'):
    datas.append(('watchlist.json', '.'))

# 添加akshare的数据文件文件夹
akshare_data_folder = os.path.join(akshare_path, 'file_fold')
if os.path.exists(akshare_data_folder):
    datas.append((akshare_data_folder, 'akshare/file_fold'))

a = Analysis(
    ['stock_trader.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pandas',
        'numpy',
        'akshare',
        'akshare.futures',
        'akshare.futures.cons',
        'akshare.futures.futures_basis',
        'akshare.stock',
        'akshare.tool',
        'tkinter',
        'json',
        'threading',
        'datetime',
        'requests',
        'lxml',
        'beautifulsoup4',
        'html5lib',
        'openpyxl',
        'xlrd',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='股票交易助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)
"""
    
    with open('build.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("build.spec文件已更新！")

if __name__ == '__main__':
    print("检查akshare数据文件...")
    data_files = find_akshare_data_files()
    print(f"\n找到 {len(data_files)} 个数据文件夹")
    print("\n更新build.spec文件...")
    update_build_spec()
    print("\n完成！现在可以运行打包命令了。")

