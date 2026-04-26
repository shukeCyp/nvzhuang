#!/bin/bash
set -e

# 创建虚拟环境（已存在则跳过）
if [ ! -d ".venv" ]; then
  uv venv .venv
fi
source .venv/bin/activate

# 安装 Python 依赖
uv pip install -r requirements.txt

# 安装 playwright 浏览器（已安装则跳过）
python -m playwright install chromium 2>/dev/null || true

# 编译前端
cd frontend
npm install
npm run build
cd ..

# 将编译产物复制到 backend/vue
rm -rf backend/vue
cp -r frontend/dist backend/vue

# 启动应用
python backend/main.py
