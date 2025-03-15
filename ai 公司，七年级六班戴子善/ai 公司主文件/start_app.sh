#!/bin/bash
# 启动多智能体工作流系统前端应用

echo "正在启动多智能体工作流系统..."
echo "请确保已安装 Python 和 Flask 库"

# 检查 Flask 是否已安装
if ! python3 -c "import flask" &> /dev/null; then
    echo "正在安装 Flask..."
    pip3 install flask
fi

# 检查是否需要使用新版前端
USE_NEW_UI=true

# 设置环境变量以使用新版前端
if [ "$USE_NEW_UI" = true ]; then
    export FLASK_TEMPLATE="new-index.html"
    echo "将使用新版前端界面..."
else
    export FLASK_TEMPLATE="index.html"
    echo "将使用标准前端界面..."
fi

# 启动应用
python3 app.py

echo "应用已启动，请在浏览器中访问 http://127.0.0.1:5000"