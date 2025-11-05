@echo off
chcp 65001 >nul
echo ========================================
echo   股票交易助手 - 重新打包脚本
echo ========================================
echo.

echo [1/3] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo 清理完成 ✓

echo.
echo [2/3] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller
)

echo.
echo [3/3] 开始重新打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --clean --noconfirm build.spec

if errorlevel 1 (
    echo.
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 新的exe文件位置: dist\股票交易助手.exe
echo.
echo 注意：请先测试新版本，确保功能正常后再分发给用户。
echo.
pause

