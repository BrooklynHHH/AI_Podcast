#!/bin/bash

echo "🚀 启动AI播客生成器..."

# 检查Python依赖
echo "📦 检查Python依赖..."
cd agent-server
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 文件不存在"
    exit 1
fi

# 安装Python依赖
echo "📥 安装Python依赖..."
pip install -r requirements.txt

# 启动后端服务
echo "🔧 启动后端服务..."
python server.py &
BACKEND_PID=$!

# 等待后端服务启动
sleep 3

# 检查后端服务是否启动成功
if curl -s http://localhost:5001 > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 回到项目根目录
cd ..

# 安装前端依赖
echo "📦 安装前端依赖..."
npm install

# 启动前端服务
echo "🌐 启动前端服务..."
npm run serve

# 清理函数
cleanup() {
    echo "🛑 正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 等待用户中断
wait 