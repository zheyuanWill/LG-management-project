# LG 船舶管理 ERP · 生产部署包

零运维部署到阿里云 ECS 的一整套脚本与配置。**你只需要在控制台点几下建服务器，再在本机粘贴一条命令。**

## 三步上线

1. **建服务器**：按 [阿里云部署指南](./阿里云部署指南.md) 在控制台创建 ECS（Alibaba Cloud Linux 3，放行 22/80/443/9000，记下公网 IP）。
2. **一键部署**（在本机 Git Bash 执行）：
   ```bash
   LG_SSH_KEY=~/.ssh/aliyun.pem bash deploy/deploy-to-ecs.sh <公网IP>
   ```
3. **访问**：浏览器打开 `http://<公网IP>/`。

## 文件说明

| 文件 | 作用 |
|---|---|
| `docker-compose.prod.yml` | 生产编排（代码烤进镜像、仅 caddy/minio 暴露、单 Caddy 入口） |
| `deploy/Caddyfile` | 生产反向代理（`/api/*`→后端，其余→前端；支持域名自动 HTTPS） |
| `deploy/.env.prod.example` | 生产环境变量模板（密钥/MinIO 公开地址由脚本自动生成） |
| `deploy/bootstrap.sh` | **在 ECS 上跑**：装 Docker、配镜像源、生成密钥、构建启动服务 |
| `deploy/deploy-to-ecs.sh` | **在本机跑**：打包代码上传 ECS 并触发 bootstrap |
| `deploy/阿里云部署指南.md` | 控制台建机步骤 + HTTPS 升级 + MinIO 混合内容处理 |

## 关键点（已帮你处理好的坑）

- **Docker Hub 国内拉镜像慢/超时** → bootstrap 已配置阿里云/daocloud/163 镜像加速器。
- **前端用同源 `/api/v1`** → 无需构建时配 API 地址，Caddy 反代即可。
- **MinIO 预签名 URL 浏览器可达** → 脚本自动填 `MINIO_PUBLIC_ENDPOINT=http://<公网IP>:9000`（暴露 9000 端口）。
- **数据库表自动建** → 后端启动 `init_db()` 建表，`init.sql` 启用 pgvector，无需手动迁移。
- **生产安全** → 移除 `--reload` 与源码挂载，JWT/数据库/MinIO 密码均为随机强口令。

## 进阶

- 域名备案后切 HTTPS：见指南「三、备案后升级到 HTTPS」。
- 日常运维命令：见指南「四、日常运维」。
