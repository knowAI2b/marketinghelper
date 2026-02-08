#!/usr/bin/env bash
set -euo pipefail

# 启动小红书助手开发服务的便捷脚本
# 要求：本机已安装 conda 且存在名为 py310 的环境。

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. 初始化 conda（根据常见安装路径，必要时请手动修改）
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  # miniconda 常见路径
  # shellcheck source=/dev/null
  . "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  # anaconda 常见路径
  # shellcheck source=/dev/null
  . "$HOME/anaconda3/etc/profile.d/conda.sh"
else
  echo "[start_dev.sh] 未找到 conda.sh，请根据本机实际安装路径修改脚本中 conda.sh 的路径。" >&2
  exit 1
fi

# 2. 激活指定 conda 环境
conda activate py310

cd "$PROJECT_ROOT"

echo "[start_dev.sh] 使用环境：$(python -V)"
echo "[start_dev.sh] 项目根目录：$PROJECT_ROOT"

# 3. 安装依赖（可根据需要改成只在首次执行时安装）
pip install -e ".[dev]"

# 4. 启动 FastAPI 开发服务
exec uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

