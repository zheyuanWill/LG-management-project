#!/usr/bin/env bash
# init.sh — LG 船舶管理 ERP 启动与验证脚本（harness 标准入口）
# 适配 harness engineering：一条命令完成依赖就绪 → 启动 → 验证 → 打印入口。
# Windows 用户请用仓库根的 start-dev.bat（功能等价）。

set -euo pipefail

# ── 可配置变量 ──────────────────────────────
# 依赖安装/构建命令（镜像）
INSTALL_CMD="docker compose build backend ai-service celery-worker celery-beat frontend"
# 基础验证命令（后端健康检查）
VERIFY_CMD="curl -fsS http://localhost:8000/docs >/dev/null 2>&1 && echo '  backend : OK (http://localhost:8000/docs)' || echo '  backend : UNREACHABLE'"
# 启动命令
START_CMD="docker compose up -d"
# 设为 1 则在脚本末尾直接拉起服务（默认仅打印）
RUN_START_COMMAND="${RUN_START_COMMAND:-0}"

echo "==> 仓库根目录: $(pwd)"

# 1) 构建依赖镜像
echo "==> [1/3] 构建依赖镜像..."
eval "$INSTALL_CMD"

# 2) 启动全部服务
echo "==> [2/3] 启动服务 ($START_CMD)..."
eval "$START_CMD"
echo "     (等待 10s 让容器就绪)"
sleep 10

# 3) 验证基础状态
echo "==> [3/3] 验证基础状态..."
echo "--- 容器状态 ---"
docker compose ps
echo "--- 后端健康检查 ---"
eval "$VERIFY_CMD"

echo ""
echo "==> 访问入口："
echo "     前端  : http://localhost:3000"
echo "     后端  : http://localhost:8000/docs"
echo "     MinIO : http://localhost:9001"
echo "     AI    : http://localhost:8001"
echo "     默认账号: admin / admin123"
echo "==> 手动启动命令: $START_CMD"

if [ "$RUN_START_COMMAND" = "1" ]; then
  eval "$START_CMD"
fi
