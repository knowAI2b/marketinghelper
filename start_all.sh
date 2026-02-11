#!/usr/bin/env bash
# 一键启动前后端：先启动后端 API，再启动前端 WebUI；Ctrl+C 会同时停止两者。

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 可选：激活 conda 环境（若存在）
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  # shellcheck source=/dev/null
  . "$HOME/miniconda3/etc/profile.d/conda.sh"
  conda activate py310 2>/dev/null || true
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  # shellcheck source=/dev/null
  . "$HOME/anaconda3/etc/profile.d/conda.sh"
  conda activate py310 2>/dev/null || true
fi

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "[start_all] 正在停止前后端..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "[start_all] 启动后端 API (port 5173)..."
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 5173 &
BACKEND_PID=$!
sleep 2

echo "[start_all] 启动前端 WebUI (port 8000)..."
(cd webui && npm run dev) &
FRONTEND_PID=$!
sleep 2

echo ""
echo "  Backend:  http://localhost:5173  (API / docs)"
echo "  Frontend: http://localhost:8000 (Web 界面)"
echo ""
echo "  按 Ctrl+C 停止前后端"
echo ""

wait
