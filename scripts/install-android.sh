#!/usr/bin/env bash
# One-click install script for Investment Assistant on Android (Termux)
set -euo pipefail

echo "====================================="
echo "  市场投资助手 - Termux 安装脚本"
echo "====================================="
echo ""

# Check if running in Termux
if [ -z "${TERMUX_VERSION:-}" ] && [ ! -d "/data/data/com.termux" ]; then
    echo "错误：此脚本需要在 Termux 中运行"
    exit 1
fi

INSTALL_DIR="$HOME/investment-assistant"

# Step 1: Install system dependencies
echo "[1/5] 安装系统依赖..."
pkg update -y
pkg install -y python nodejs-lts git curl build-essential rust

# Step 2: Clone or update repo
echo "[2/5] 获取项目代码..."
if [ -d "$INSTALL_DIR" ]; then
    echo "项目已存在，更新中..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "克隆项目..."
    git clone "${REPO_URL:-.}" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Step 3: Install Python dependencies
echo "[3/5] 安装 Python 依赖..."
pip install --upgrade pip
pip install uv
uv sync

# Step 4: Install frontend dependencies and build
echo "[4/5] 构建前端..."
cd frontend
npm install
npm run build
cd ..

# Step 5: Create start script
echo "[5/5] 创建启动脚本..."
cat > "$INSTALL_DIR/start.sh" << 'STARTEOF'
#!/usr/bin/env bash
echo "启动市场投资助手..."
echo "浏览器打开: http://localhost:8000"
echo "按 Ctrl+C 停止"
echo ""
cd "$(dirname "$0")"

# Start backend
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Open browser
termux-open-url "http://localhost:8000" 2>/dev/null || echo "请手动打开浏览器访问 http://localhost:8000"

# Wait for backend process
wait $BACKEND_PID
STARTEOF

chmod +x "$INSTALL_DIR/start.sh"

echo ""
echo "====================================="
echo "  安装完成！"
echo ""
echo "  启动命令: cd $INSTALL_DIR && ./start.sh"
echo "  浏览器打开: http://localhost:8000"
echo "====================================="
