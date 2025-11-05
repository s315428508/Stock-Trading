# 股票交易助手 - 打包版使用说明

## 📦 如何打包程序

### 方法一：使用批处理文件（最简单）

1. 双击运行 `打包.bat`
2. 等待打包完成（可能需要几分钟）
3. 在 `dist` 文件夹中找到 `股票交易助手.exe`

### 方法二：使用Python脚本

1. 确保已安装PyInstaller：`pip install pyinstaller`
2. 运行：`python build_exe.py`
3. 在 `dist` 文件夹中找到 `股票交易助手.exe`

### 方法三：手动命令

```bash
pip install pyinstaller
pyinstaller --name=股票交易助手 --onefile --windowed --clean stock_trader.py
```

## 📤 分享给朋友

1. 打包完成后，将 `dist/股票交易助手.exe` 复制出来
2. 可以直接通过QQ、微信、邮件等方式发送给朋友
3. 朋友收到后双击运行即可，无需安装Python或任何其他软件

## 💡 使用提示

- **文件大小**：exe文件大约100-200MB（因为包含了Python解释器和所有库）
- **首次运行**：可能需要等待几秒钟（程序自解压）
- **杀毒软件**：可能会误报，添加信任即可
- **网络要求**：需要网络连接以获取股票数据

## 🔧 故障排除

### 问题1：打包失败
- 确保已安装所有依赖：`pip install -r requirements.txt`
- 确保PyInstaller版本正确：`pip install --upgrade pyinstaller`

### 问题2：exe文件无法运行
- 确保是Windows 10/11系统
- 检查杀毒软件是否拦截
- 尝试以管理员身份运行

### 问题3：无法获取股票数据
- 检查网络连接
- 某些企业网络可能需要配置代理

## 📝 文件说明

- `stock_trader.py` - 主程序源码
- `build_exe.py` - Python打包脚本
- `打包.bat` - Windows批处理打包脚本
- `build.spec` - PyInstaller配置文件
- `使用说明.txt` - 给最终用户的使用说明
- `打包说明.md` - 详细的打包说明

