#!/usr/bin/env bash
# 一键启动前后端：先启动后端 API，再启动前端 WebUI；Ctrl+C 会同时停止两者。
#
# 可通过环境变量自定义：
#   CONDA_ENV_NAME=py310   - conda 环境名称（默认 py310）
#   SKIP_CONDA=1           - 跳过 conda 环境激活
#   SKIP_INSTALL=1         - 跳过依赖安装

set -euo pipefail

# 配置项（可通过环境变量覆盖）
CONDA_ENV_NAME="${CONDA_ENV_NAME:-py310}"
SKIP_CONDA="${SKIP_CONDA:-}"
SKIP_INSTALL="${SKIP_INSTALL:-}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 尝试激活 conda 环境
activate_conda() {
  if [ -n "$SKIP_CONDA" ]; then
    echo "[start_all] 跳过 conda 环境激活 (SKIP_CONDA=1)"
    return 0
  fi

  # 优先使用 conda 命令（已在 PATH 中）
  if command -v conda &>/dev/null; then
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME" 2>/dev/null || {
      echo "[start_all] 警告: conda 环境 '$CONDA_ENV_NAME' 不存在，使用当前 Python"
      return 1
    }
    echo "[start_all] 已激活 conda 环境: $CONDA_ENV_NAME"
    return 0
  fi

  # 回退：尝试常见 conda 安装路径
  local conda_sh=""
  for path in \
    "$HOME/miniconda3/etc/profile.d/conda.sh" \
    "$HOME/anaconda3/etc/profile.d/conda.sh" \
    "/opt/conda/etc/profile.d/conda.sh" \
    "/usr/local/conda/etc/profile.d/conda.sh"
  do
    if [ -f "$path" ]; then
      conda_sh="$path"
      break
    fi
  done

  if [ -n "$conda_sh" ]; then
    # shellcheck source=/dev/null
    . "$conda_sh"
    conda activate "$CONDA_ENV_NAME" 2>/dev/null || {
      echo "[start_all] 警告: conda 环境 '$CONDA_ENV_NAME' 不存在，使用当前 Python"
      return 1
    }
    echo "[start_all] 已激活 conda 环境: $CONDA_ENV_NAME"
  else
    echo "[start_all] 未检测到 conda，使用当前 Python 环境"
  fi
}

# 检查并安装 Python 依赖
install_python_deps() {
  if [ -n "$SKIP_INSTALL" ]; then
    echo "[start_all] 跳过 Python 依赖安装 (SKIP_INSTALL=1)"
    return 0
  fi

  # 检查 xhs_assistant 模块是否已安装
  if python -c "import xhs_assistant" 2>/dev/null; then
    echo "[start_all] Python 依赖已安装"
  else
    echo "[start_all] 安装 Python 依赖..."
    pip install -e ".[dev]" -q
    echo "[start_all] Python 依赖安装完成"
  fi
}

# 检查并安装前端依赖
install_frontend_deps() {
  if [ -n "$SKIP_INSTALL" ]; then
    echo "[start_all] 跳过前端依赖安装 (SKIP_INSTALL=1)"
    return 0
  fi

  # 检查 node_modules 是否存在
  if [ -d "webui/node_modules" ]; then
    echo "[start_all] 前端依赖已安装"
  else
    echo "[start_all] 安装前端依赖..."
    (cd webui && npm install --silent)
    echo "[start_all] 前端依赖安装完成"
  fi
}

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

# 激活 conda 环境
activate_conda

echo "[start_all] Python: $(which python 2>/dev/null || echo '未找到')"
echo "[start_all] 项目根目录: $PROJECT_ROOT"

# 安装依赖
install_python_deps
install_frontend_deps

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