#!/usr/bin/env bash
# 启动小红书助手开发服务的便捷脚本
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
    echo "[start_dev] 跳过 conda 环境激活 (SKIP_CONDA=1)"
    return 0
  fi

  # 优先使用 conda 命令（已在 PATH 中）
  if command -v conda &>/dev/null; then
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME" 2>/dev/null || {
      echo "[start_dev] 错误: conda 环境 '$CONDA_ENV_NAME' 不存在"
      echo "[start_dev] 可用环境: $(conda env list | grep -v '^#' | awk '{print $1}' | tr '\n' ' ')"
      exit 1
    }
    echo "[start_dev] 已激活 conda 环境: $CONDA_ENV_NAME"
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
      echo "[start_dev] 错误: conda 环境 '$CONDA_ENV_NAME' 不存在"
      echo "[start_dev] 可用环境: $(conda env list | grep -v '^#' | awk '{print $1}' | tr '\n' ' ')"
      exit 1
    }
    echo "[start_dev] 已激活 conda 环境: $CONDA_ENV_NAME"
    return 0
  fi

  echo "[start_dev] 未检测到 conda，使用当前 Python 环境"
  echo "[start_dev] 提示: 设置 SKIP_CONDA=1 可跳过此警告"
}

echo "[start_dev] 项目根目录: $PROJECT_ROOT"

# 激活 conda 环境
activate_conda

echo "[start_dev] Python: $(python -V)"
echo "[start_dev] Python 路径: $(which python)"

# 安装依赖
if [ -z "$SKIP_INSTALL" ]; then
  echo "[start_dev] 安装依赖..."
  pip install -e ".[dev]"
else
  echo "[start_dev] 跳过依赖安装 (SKIP_INSTALL=1)"
fi

# 启动 FastAPI 开发服务
echo "[start_dev] 启动 FastAPI 开发服务 (port 5173)..."
exec uvicorn api.main:app --reload --host 0.0.0.0 --port 5173