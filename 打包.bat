@echo off
chcp 65001 >nul
echo ========================================
echo   股票交易助手 - 自动打包脚本
echo ========================================
echo.

echo [1/3] 检查PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo 安装失败！请检查网络连接。
        pause
        exit /b 1
    )
) else (
    echo PyInstaller已安装 ✓
)

echo.
echo [2/3] 开始打包程序...
echo 这可能需要几分钟时间，请耐心等待...
echo.

REM 使用build.spec文件打包（包含akshare数据文件）
pyinstaller --clean --noconfirm build.spec

if errorlevel 1 (
    echo.
    echo 使用spec文件打包失败，尝试直接打包...
    pyinstaller --name=股票交易助手 --onefile --windowed --clean --noconfirm ^
        --hidden-import=akshare.futures.cons ^
        --hidden-import=akshare.futures.futures_basis ^
        stock_trader.py
)

if errorlevel 1 (
    echo.
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.
echo ========================================
echo 可执行文件位置: dist\股票交易助手.exe
echo ========================================
echo.
echo 您可以将此文件分享给其他用户使用。
echo 双击运行即可，无需安装Python。
echo.
pause

