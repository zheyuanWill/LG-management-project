#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# LG 船舶管理 ERP · 本地一键上传并部署到阿里云 ECS
#
# 在你的电脑上运行（需 Git Bash / WSL / macOS 终端，且已配置好 SSH 密钥能登 ECS）：
#   bash deploy/deploy-to-ecs.sh <ECS公网IP> [ssh用户，默认 root]
#
# 例：
#   bash deploy/deploy-to-ecs.sh 47.98.12.34
#   bash deploy/deploy-to-ecs.sh 47.98.12.34 root
#   LG_SSH_KEY=~/.ssh/aliyun.pem bash deploy/deploy-to-ecs.sh 47.98.12.34
#
# 做了什么：把项目打包（排除 node_modules/.git/__pycache__ 等）scp 到 ECS，
#           然后 ssh 进去执行 deploy/bootstrap.sh 完成部署。
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

ECS_IP="${1:?用法: deploy/deploy-to-ecs.sh <ECS公网IP> [ssh用户]}"
ECS_USER="${2:-root}"

SSH_KEY="${LG_SSH_KEY:-}"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
if [ -n "$SSH_KEY" ]; then SSH_OPTS="$SSH_OPTS -i $SSH_KEY"; fi

# 切到项目根目录
cd "$(cd "$(dirname "$0")" && pwd)/.."
ROOT="$(pwd)"
echo "==> 项目目录: $ROOT"

TARBALL="/tmp/lg-deploy-$$.tar.gz"
echo "==> 打包项目（排除 node_modules / .git / __pycache__ / .env 等）..."
tar czf "$TARBALL" \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='dist' \
  --exclude='.venv' \
  --exclude='.env' \
  --exclude='.idea' \
  --exclude='*.log' \
  -C "$ROOT" .

echo "==> 上传到 $ECS_USER@$ECS_IP ..."
scp $SSH_OPTS "$TARBALL" "$ECS_USER@$ECS_IP:/root/lg-deploy.tar.gz"

echo "==> 登录 ECS 并部署..."
ssh $SSH_OPTS "$ECS_USER@$ECS_IP" bash -s <<'REMOTE'
set -e
mkdir -p /root/lg-management
tar xzf /root/lg-deploy.tar.gz -C /root/lg-management
rm -f /root/lg-deploy.tar.gz
cd /root/lg-management
bash deploy/bootstrap.sh
REMOTE

rm -f "$TARBALL"
echo "==> 完成。"
