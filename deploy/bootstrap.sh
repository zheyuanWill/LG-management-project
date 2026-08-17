#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# LG 船舶管理 ERP · ECS 一键部署脚本（在服务器上运行）
#
# 它会自动完成：
#   1. 安装 Docker + docker compose 插件（用阿里云镜像源，国内快）
#   2. 配置 Docker Hub 国内镜像加速器（否则拉镜像会超时）
#   3. 生成强随机密钥（JWT / 数据库 / MinIO）
#   4. 自动探测 ECS 公网 IP，填好 MinIO 公开地址
#   5. 构建并启动整套生产服务
#   6. 等待站点就绪并打印访问地址
#
# 由 deploy/deploy-to-ecs.sh 自动调起；也可手动在服务器上执行：
#   cd /root/lg-management && bash deploy/bootstrap.sh
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

# 无论在哪执行，都切换到项目根目录（脚本在 deploy/ 下）
cd "$(cd "$(dirname "$0")" && pwd)/.."
echo "==> 工作目录: $(pwd)"

# 非 root 用户用 sudo
if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
DOCKER="docker"
if [ "$(id -u)" -ne 0 ]; then DOCKER="sudo docker"; fi

# ── 1. 安装 Docker ─────────────────────────────────────────────────────────
if command -v docker >/dev/null 2>&1 && $DOCKER compose version >/dev/null 2>&1; then
  echo "==> Docker 已安装，跳过"
else
  echo "==> 安装 Docker（阿里云镜像源）..."
  if [ -f /etc/os-release ]; then . /etc/os-release; fi
  if command -v dnf >/dev/null 2>&1 || command -v yum >/dev/null 2>&1; then
    PM=$(command -v dnf || command -v yum)
    $SUDO $PM install -y dnf-plugins-core 2>/dev/null || true
    $SUDO $PM config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo 2>/dev/null || true
    $SUDO $PM install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  elif command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get update -y
    $SUDO apt-get install -y ca-certificates curl
    $SUDO install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
    $SUDO apt-get update -y
    $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  else
    echo "!! 不支持的发行版，请手动安装 Docker 后重试"; exit 1
  fi
  $SUDO systemctl enable --now docker
fi

# ── 2. 配置 Docker Hub 国内镜像加速器 ──────────────────────────────────────
if [ ! -f /etc/docker/daemon.json ] || ! grep -q registry-mirrors /etc/docker/daemon.json; then
  echo "==> 配置 Docker 镜像加速器"
  $SUDO mkdir -p /etc/docker
  $SUDO tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://hub-mirror.c.163.com",
    "https://registry.cn-hangzhou.aliyuncs.com"
  ]
}
EOF
  $SUDO systemctl restart docker
  sleep 3
fi

# ── 3. 准备 .env（首次从模板复制） ─────────────────────────────────────────
if [ ! -f .env ]; then
  echo "==> 从模板生成 .env"
  cp deploy/.env.prod.example .env
fi

gen() { openssl rand -hex 16; }

# 仅替换仍为占位符的值，已手动设置的不动
JWT=$(gen); PG=$(gen); MIN=$(gen)
sed -i "s#^JWT_SECRET_KEY=__GENERATE__#JWT_SECRET_KEY=$JWT#" .env
sed -i "s#^PG_PASSWORD=__GENERATE__#PG_PASSWORD=$PG#" .env
sed -i "s#^MINIO_PASSWORD=__GENERATE__#MINIO_PASSWORD=$MIN#" .env

# ── 4. 探测公网 IP，填 MinIO 公开地址 ─────────────────────────────────────
PUBLIC_IP=$(curl -s -m 3 http://100.100.100.200/latest/meta-data/public-ipv4 2>/dev/null \
            || curl -s -m 3 ifconfig.me 2>/dev/null || echo "")
if [ -n "$PUBLIC_IP" ]; then
  sed -i "s#^MINIO_PUBLIC_ENDPOINT=__AUTO__#MINIO_PUBLIC_ENDPOINT=http://$PUBLIC_IP:9000#" .env
  echo "==> 检测到公网 IP: $PUBLIC_IP"
else
  echo "==> 未探测到公网 IP，MinIO 公开地址保持 localhost（文件下载可能不可用，请手动设 MINIO_PUBLIC_ENDPOINT）"
fi

# ── 5. 构建并启动生产服务 ─────────────────────────────────────────────────
echo "==> 构建并启动生产服务（首次构建较慢，约几分钟）..."
$DOCKER compose -f docker-compose.prod.yml up -d --build

# ── 6. 等待站点就绪 ───────────────────────────────────────────────────────
echo "==> 等待站点就绪..."
for i in $(seq 1 60); do
  if curl -fsS -m 5 http://localhost/ >/dev/null 2>&1; then
    echo "==> 站点已就绪!"
    break
  fi
  sleep 5
done

echo ""
echo "════════════════════════════════════════════════════════════════════════"
if [ -n "$PUBLIC_IP" ]; then
  echo " 访问地址:  http://$PUBLIC_IP/"
else
  echo " 访问地址:  http://<你的ECS公网IP>/"
fi
echo " 默认管理员: 请在后端日志 / 数据库中确认（开发环境为 admin / admin123）"
echo ""
echo " 常用命令:"
echo "   查看状态:  docker compose -f docker-compose.prod.yml ps"
echo "   查看日志:  docker compose -f docker-compose.prod.yml logs -f <服务名>"
echo "   重启:      docker compose -f docker-compose.prod.yml restart"
echo "   更新代码:  重新传代码后执行 docker compose -f docker-compose.prod.yml up -d --build"
echo "════════════════════════════════════════════════════════════════════════"
