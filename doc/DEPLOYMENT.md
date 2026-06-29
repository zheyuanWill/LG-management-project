# LG Management 部署指南（小白详细版）

本文档面向**完全没有云服务经验的用户**，将一步步教你如何部署系统。

---

## 目录

1. [基础概念扫盲](#1-基础概念扫盲)
2. [阿里云账号注册与准备](#2-阿里云账号注册与准备)
3. [购买云服务器 ECS](#3-购买云服务器-ecs)
4. [购买云数据库 RDS PostgreSQL](#4-购买云数据库-rds-postgresql)
5. [购买云数据库 Redis](#5-购买云数据库-redis)
6. [购买对象存储 OSS](#6-购买对象存储-oss)
7. [域名购买与备案](#7-域名购买与备案)
8. [SSL 证书申请](#8-ssl-证书申请)
9. [部署后端 API](#9-部署后端-api)
10. [部署 Web Admin](#10-部署-web-admin)
11. [Mobile App 发布 - Android](#11-mobile-app-发布---android)
12. [Mobile App 发布 - iOS](#12-mobile-app-发布---ios)
13. [Mobile App 发布 - HarmonyOS](#13-mobile-app-发布---harmonyos)
14. [完整配置示例](#14-完整配置示例)
15. [常见问题](#15-常见问题)

---

## 1. 基础概念扫盲

在开始之前，先了解一些基本概念：

### 什么是阿里云？

阿里云是阿里巴巴的云计算平台，类似于国外的 AWS（亚马逊云）。你可以在上面"租用"服务器、数据库等资源，按使用时间付费，不需要自己买实体服务器。

### 各种服务是什么？

| 服务名称 | 通俗解释 | 类比 |
|----------|----------|------|
| **ECS（云服务器）** | 一台远程的电脑，你的程序运行在上面 | 就像租了一台 24 小时开机的电脑 |
| **RDS（云数据库）** | 专门存储数据的服务，比如用户信息、订单数据 | 就像一个超大的 Excel 表格 |
| **Redis（缓存数据库）** | 临时存储常用数据，加快访问速度 | 就像把常用资料放在桌面上 |
| **OSS（对象存储）** | 存储文件的地方，比如图片、文档 | 就像一个无限大的网盘 |
| **CDN（内容分发）** | 让用户就近访问资源，加快速度 | 就像在各地设置快递站 |
| **域名** | 网站地址，如 www.example.com | 就像门牌号 |
| **SSL 证书** | 让网站变成 https，更安全 | 就像给网站加了一把锁 |

### 为什么需要这么多服务？

```
用户访问流程：

船员手机 App ──→ 阿里云 CDN ──→ ECS 服务器 ──→ RDS 数据库
     │                              │              │
     │                              ▼              │
     │                           Redis 缓存 ←──────┘
     │
     └──→ 上传照片 ──→ OSS 存储
```

---

## 2. 阿里云账号注册与准备

### 2.1 注册阿里云账号

1. 打开浏览器，访问：https://www.aliyun.com

2. 点击右上角【免费注册】

3. 选择注册方式（推荐用手机号）：
   - 输入手机号
   - 获取验证码
   - 设置密码
   - 点击【同意协议并注册】

4. **实名认证**（必须完成，否则无法购买服务）：
   - 登录后点击右上角头像 → 【账号管理】
   - 左侧菜单点击【实名认证】
   - 选择【个人实名认证】或【企业实名认证】
   - 按提示上传身份证照片
   - 等待审核（一般几分钟到几小时）

### 2.2 充值

1. 点击右上角【费用】→【充值】
2. 建议先充值 500-1000 元（后续按实际使用扣费）
3. 支持支付宝、微信、银行卡

### 2.3 预估费用

| 服务 | 配置 | 月费用（约） |
|------|------|-------------|
| ECS 服务器 | 2核4G | ￥150-300 |
| RDS PostgreSQL | 1核1G | ￥50-100 |
| Redis | 256MB | ￥30-50 |
| OSS | 按量付费 | ￥10-50 |
| 域名 | .com | ￥55/年 |
| **合计** | | **￥250-500/月** |

> 💡 新用户可以领取优惠券，首购 ECS 可能只要几十块钱

---

## 3. 购买云服务器 ECS

ECS 是运行你的后端程序的地方。

### 3.1 进入购买页面

1. 登录阿里云控制台：https://home.console.aliyun.com
2. 在搜索框输入【ECS】，点击【云服务器 ECS】
3. 点击【创建实例】

### 3.2 选择配置（图文步骤）

**第一步：基础配置**

```
付费模式：选择【包年包月】（更便宜）或【按量付费】（灵活）
         ↓ 新手建议选包年包月，1个月起
         
地域：选择【华东1（杭州）】或【华东2（上海）】
     ↓ 选离你用户近的地方
     
实例规格：
  - 点击【共享型】或【计算型】
  - 选择 2核4G（ecs.c6.large 或 ecs.s6-c1m2.large）
  ↓ 这个配置足够运行你的系统
  
镜像：
  - 选择【公共镜像】
  - 操作系统选【Ubuntu】
  - 版本选【20.04 64位】
```

**第二步：网络和安全组**

```
网络：保持默认（会自动创建 VPC）

公网 IP：
  - 勾选【分配公网 IPv4 地址】
  - 带宽计费模式：【按固定带宽】
  - 带宽值：5 Mbps（够用了）

安全组：
  - 选择【新建安全组】
  - 开放端口：勾选 22、80、443、8000
```

**第三步：系统配置**

```
登录凭证：选择【自定义密码】
  - 登录名：root（默认）
  - 密码：设置一个复杂密码（记下来！）
    例如：Lg@Management2024!
    
实例名称：lg-management-server
```

**第四步：确认订单**

```
购买时长：建议先买 1 个月试试
点击【确认下单】→ 【支付】
```

### 3.3 获取服务器信息

购买完成后：

1. 回到 ECS 控制台：https://ecs.console.aliyun.com
2. 点击【实例】，找到刚创建的服务器
3. **记录以下信息**：

```
公网 IP：xxx.xxx.xxx.xxx  ← 这就是你的服务器地址
内网 IP：172.x.x.x        ← 内部通信用
实例 ID：i-xxxxxxxxxx
```

### 3.4 连接服务器

**方法一：使用阿里云网页终端（最简单）**

1. 在 ECS 实例列表，点击【远程连接】
2. 选择【Workbench 远程连接】
3. 输入密码，点击确定

**方法二：使用 SSH 工具（推荐）**

Windows 用户：
1. 下载 Xshell：https://www.xshell.com/zh/free-for-home-school/
2. 新建会话：
   - 主机：填写公网 IP
   - 端口：22
   - 用户名：root
   - 密码：你设置的密码

Mac 用户：
1. 打开【终端】应用
2. 输入命令：
```bash
ssh root@你的公网IP
# 例如：ssh root@47.96.123.45
```
3. 输入密码（输入时不会显示，直接输完按回车）

---

## 4. 购买云数据库 RDS PostgreSQL

RDS 是存储你的业务数据的地方。

### 4.1 进入购买页面

1. 在阿里云控制台搜索【RDS】
2. 点击【云数据库 RDS】
3. 点击【创建实例】

### 4.2 选择配置

```
数据库引擎：选择【PostgreSQL】

版本：选择【15】（最新稳定版）

系列：选择【基础版】（便宜，够用）

规格：
  - 通用型 1核1G（pg.n2.small.1）
  - 存储空间：20GB（后续可扩容）

地域：选择和 ECS 相同的地域！（重要）
      例如都选【华东1（杭州）】

网络类型：选择【专有网络】
  - VPC：选择和 ECS 同一个 VPC
```

### 4.3 购买并获取信息

购买完成后：

1. 进入 RDS 控制台：https://rdsnext.console.aliyun.com
2. 找到你的实例，点击进入详情

**获取连接地址：**
1. 左侧菜单点击【数据库连接】
2. 记录【内网地址】，格式类似：
```
rm-bp1xxxxxxxx.pg.rds.aliyuncs.com
端口：5432
```

**创建数据库账号：**
1. 左侧菜单点击【账号管理】
2. 点击【创建账号】
3. 填写信息：
```
数据库账号：lg_admin        ← 记下来
账号类型：高权限账号
密码：Lg@Database2024!     ← 记下来（设置复杂点）
```

**创建数据库：**
1. 左侧菜单点击【数据库管理】
2. 点击【创建数据库】
3. 填写信息：
```
数据库名：lg_management    ← 记下来
字符集：UTF-8
```

**配置白名单：**
1. 左侧菜单点击【数据安全性】→【白名单配置】
2. 点击【修改】default 分组
3. 添加你的 ECS 内网 IP（172.x.x.x）
4. 或者添加 ECS 所在 VPC 的网段（如 172.16.0.0/16）

### 4.4 你获得的信息

```
数据库地址：rm-bp1xxxxxxxx.pg.rds.aliyuncs.com
端口：5432
数据库名：lg_management
用户名：lg_admin
密码：Lg@Database2024!

# 完整连接字符串（后面要用）：
DATABASE_URL=postgresql+asyncpg://lg_admin:Lg@Database2024!@rm-bp1xxxxxxxx.pg.rds.aliyuncs.com:5432/lg_management
```

---

## 5. 购买云数据库 Redis

Redis 用于缓存和会话管理。

### 5.1 购买步骤

1. 搜索【Redis】，进入【云数据库 Redis】
2. 点击【创建实例】
3. 选择配置：

```
版本：Redis 7.0

系列：【标准版-单副本】（最便宜）

规格：256MB（够用了）

地域：和 ECS、RDS 选同一个！

网络：选择同一个 VPC
```

### 5.2 获取连接信息

购买完成后：

1. 进入 Redis 控制台
2. 点击实例，进入详情

**获取连接地址：**
1. 查看【连接信息】
2. 记录【内网地址】：
```
r-bp1xxxxxxxx.redis.rds.aliyuncs.com
端口：6379
```

**设置密码：**
1. 点击【账号管理】
2. 点击【创建账号】或【修改密码】
3. 设置密码：`Lg@Redis2024!`

**配置白名单：**
1. 点击【白名单设置】
2. 添加 ECS 的内网 IP

### 5.3 你获得的信息

```
Redis 地址：r-bp1xxxxxxxx.redis.rds.aliyuncs.com
端口：6379
密码：Lg@Redis2024!

# 完整连接字符串（后面要用）：
REDIS_URL=redis://:Lg@Redis2024!@r-bp1xxxxxxxx.redis.rds.aliyuncs.com:6379/0
```

> 注意：密码前面有个冒号 `:`，不要漏掉！格式是 `redis://:密码@地址:端口/数据库号`

---

## 6. 购买对象存储 OSS

OSS 用于存储上传的文件（照片、文档等）。

### 6.1 创建 Bucket

1. 搜索【OSS】，进入【对象存储 OSS】
2. 点击【创建 Bucket】
3. 填写信息：

```
Bucket 名称：lg-management-files
              （只能小写字母、数字、短横线）
              
地域：和 ECS 选同一个

存储类型：标准存储

读写权限：私有（安全）
```

### 6.2 获取访问密钥

1. 点击右上角头像 → 【AccessKey 管理】
2. 点击【创建 AccessKey】
3. 按提示验证身份
4. **立即保存这两个值**（只显示一次！）：

```
AccessKey ID：LTAI5txxxxxxxxx
AccessKey Secret：xxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ 重要：AccessKey Secret 只显示一次，务必保存！丢失了只能重新创建。

### 6.3 配置跨域（CORS）

1. 进入 Bucket 详情
2. 左侧菜单【数据安全】→【跨域设置】
3. 点击【创建规则】：

```
来源：*
允许 Methods：全部勾选
允许 Headers：*
```

### 6.4 你获得的信息

```
Bucket 名称：lg-management-files
Bucket 地域：oss-cn-hangzhou（看你选的地域）
Endpoint（外网）：oss-cn-hangzhou.aliyuncs.com
AccessKey ID：LTAI5txxxxxxxxx
AccessKey Secret：xxxxxxxxxxxxxxxxxxxxxxxx

# 环境变量配置（后面要用）：
MINIO_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
MINIO_ACCESS_KEY=LTAI5txxxxxxxxx
MINIO_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
MINIO_BUCKET=lg-management-files
MINIO_USE_SSL=true
```

---

## 7. 域名购买与备案

### 7.1 购买域名

1. 搜索【域名】，进入【域名注册】
2. 搜索你想要的域名，例如：`lgmanagement.com`
3. 选择可用的后缀（.com、.cn 等）
4. 加入购物车，购买（约 55元/年）

### 7.2 域名备案（必须！）

在中国大陆使用域名，必须完成 ICP 备案。

1. 搜索【备案】，进入【ICP 备案】
2. 点击【开始备案】
3. 按步骤填写：
   - 主办单位信息（个人/企业）
   - 网站信息
   - 上传身份证、营业执照（企业）
   - 人脸核验
4. 提交后等待审核（约 3-20 个工作日）

> 💡 备案期间可以先用 IP 地址访问测试

### 7.3 域名解析

备案完成后，添加域名解析：

1. 进入【云解析 DNS】
2. 找到你的域名，点击【解析设置】
3. 添加记录：

```
主机记录：api
记录类型：A
记录值：你的 ECS 公网 IP
        例如：47.96.123.45

主机记录：admin
记录类型：CNAME
记录值：你的 CDN 域名（后面配置 CDN 时获得）
```

---

## 8. SSL 证书申请

### 8.1 申请免费证书

1. 搜索【SSL 证书】
2. 点击【SSL 证书管理】→【免费证书】
3. 点击【创建证书】
4. 填写域名：`api.yourdomain.com`
5. 点击【提交审核】
6. 按提示完成域名验证（添加 DNS 记录）
7. 等待签发（几分钟到几小时）

### 8.2 下载证书

1. 证书签发后，点击【下载】
2. 选择【Nginx】格式
3. 下载得到两个文件：
   - `xxx.pem`（证书文件）
   - `xxx.key`（私钥文件）

---

## 9. 部署后端 API

现在开始实际部署！

### 9.1 连接服务器并安装基础软件

SSH 连接到你的 ECS 服务器后，执行以下命令：

```bash
# 更新系统
apt update && apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 启动 Docker
systemctl enable docker
systemctl start docker

# 验证 Docker 安装成功
docker --version
# 应该显示类似：Docker version 24.0.x

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 验证
docker-compose --version

# 安装 Nginx
apt install nginx -y

# 安装 Git
apt install git -y
```

### 9.2 创建项目目录和配置文件

```bash
# 创建目录
mkdir -p /opt/lg-management
cd /opt/lg-management

# 创建环境变量文件（用实际的值替换！）
cat > .env << 'EOF'
# ===========================================
# 数据库配置 - 把下面的值替换成你的
# ===========================================
# 在 RDS 控制台获取
POSTGRES_HOST=rm-bp1xxxxxxxx.pg.rds.aliyuncs.com
POSTGRES_PORT=5432
POSTGRES_USER=lg_admin
POSTGRES_PASSWORD=Lg@Database2024!
POSTGRES_DB=lg_management

# 完整连接字符串（自动组合上面的值）
DATABASE_URL=postgresql+asyncpg://lg_admin:Lg@Database2024!@rm-bp1xxxxxxxx.pg.rds.aliyuncs.com:5432/lg_management

# ===========================================
# Redis 配置 - 把下面的值替换成你的
# ===========================================
# 在 Redis 控制台获取
REDIS_URL=redis://:Lg@Redis2024!@r-bp1xxxxxxxx.redis.rds.aliyuncs.com:6379/0

# ===========================================
# OSS 配置 - 把下面的值替换成你的
# ===========================================
# 在 OSS 控制台和 AccessKey 管理获取
MINIO_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
MINIO_ACCESS_KEY=LTAI5txxxxxxxxx
MINIO_SECRET_KEY=你的AccessKeySecret
MINIO_BUCKET=lg-management-files
MINIO_USE_SSL=true

# ===========================================
# 安全配置
# ===========================================
# 随便生成一个长字符串，用于加密
# 可以运行这个命令生成：openssl rand -hex 32
JWT_SECRET_KEY=这里填一个随机的32位以上的字符串

# 环境
DEBUG=false
EOF
```

### 9.3 创建 Docker Compose 配置

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    image: python:3.11-slim
    container_name: lgm-api
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./api:/app
    working_dir: /app
    env_file:
      - .env
    command: >
      bash -c "
        pip install -r requirements.txt &&
        alembic upgrade head &&
        python -m app.db.seed &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000
      "
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF
```

### 9.4 上传代码到服务器

**方法一：使用 Git（推荐）**

在服务器上：
```bash
cd /opt/lg-management
git clone https://github.com/your-username/LG-management.git temp
cp -r temp/services/api ./api
rm -rf temp
```

**方法二：使用 SFTP 上传**

使用 FileZilla 或其他 SFTP 工具：
1. 连接服务器（IP、端口22、用户名root、密码）
2. 将本地的 `services/api` 文件夹上传到 `/opt/lg-management/api`

### 9.5 启动服务

```bash
cd /opt/lg-management

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 等待看到类似这样的输出说明成功：
# INFO:     Uvicorn running on http://0.0.0.0:8000
# 按 Ctrl+C 退出日志查看
```

### 9.6 配置 Nginx

```bash
# 上传 SSL 证书到服务器
mkdir -p /etc/nginx/ssl
# 使用 SFTP 上传证书文件到 /etc/nginx/ssl/

# 创建 Nginx 配置
cat > /etc/nginx/sites-available/lg-api << 'EOF'
server {
    listen 80;
    server_name api.yourdomain.com;  # 改成你的域名
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;  # 改成你的域名

    ssl_certificate /etc/nginx/ssl/api.yourdomain.com.pem;
    ssl_certificate_key /etc/nginx/ssl/api.yourdomain.com.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/lg-api /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

### 9.7 验证部署

在浏览器访问：
- http://你的ECS公网IP:8000/health
- https://api.yourdomain.com/health（配置域名后）

应该看到：`{"status":"ok"}`

---

## 10. 部署 Web Admin

### 10.1 在本地构建

在你的开发电脑上：

```bash
# 进入项目目录
cd /path/to/LG-management

# 安装依赖
pnpm install

# 修改 API 地址
# 编辑 apps/web-admin/.env.production（如果没有就创建）
echo "VITE_API_BASE_URL=https://api.yourdomain.com" > apps/web-admin/.env.production

# 构建
pnpm build:packages
cd apps/web-admin
pnpm build

# 构建完成后，dist 文件夹就是要部署的内容
```

### 10.2 上传到 OSS

**方法一：使用阿里云控制台（最简单）**

1. 进入 OSS 控制台
2. 创建新 Bucket：`lg-web-admin`（公共读）
3. 进入 Bucket → 【文件管理】
4. 点击【上传文件】
5. 把 `dist` 文件夹里的**所有内容**上传上去

**方法二：使用命令行工具**

```bash
# 安装 ossutil
# macOS
brew install aliyun-cli

# Windows：下载 https://help.aliyun.com/document_detail/120075.html

# 配置
aliyun configure
# 输入 AccessKey ID、AccessKey Secret、Region（cn-hangzhou）

# 上传
cd apps/web-admin
aliyun oss cp -r dist/ oss://lg-web-admin/ --update
```

### 10.3 配置静态网站托管

1. 进入 `lg-web-admin` Bucket
2. 点击【数据管理】→【静态页面】
3. 开启静态页面托管
4. 默认首页：`index.html`
5. 默认404页：`index.html`

### 10.4 配置 CDN 加速

1. 进入【CDN】控制台
2. 点击【域名管理】→【添加域名】
3. 配置：
   - 加速域名：`admin.yourdomain.com`
   - 业务类型：网站加速
   - 源站信息：
     - 类型：OSS域名
     - 域名：`lg-web-admin.oss-cn-hangzhou.aliyuncs.com`
4. 点击【确定】，获得 CNAME 地址
5. 去域名解析添加 CNAME 记录

### 10.5 访问测试

- OSS 直接访问：`http://lg-web-admin.oss-cn-hangzhou.aliyuncs.com`
- CDN 访问：`https://admin.yourdomain.com`

---

## 11. Mobile App 发布 - Android

### 11.1 准备工作

1. **安装 HBuilderX**
   - 下载：https://www.dcloud.io/hbuilderx.html
   - 选择【App开发版】

2. **注册 DCloud 账号**
   - https://dev.dcloud.net.cn/
   - 用于云打包

3. **生成签名证书**
   
   在命令行执行：
   ```bash
   keytool -genkey -v -keystore lg-management.keystore \
     -alias lg-management \
     -keyalg RSA \
     -keysize 2048 \
     -validity 10000
   ```
   
   按提示输入信息：
   ```
   密钥库口令：LgApp2024!（记住！）
   您的名字与姓氏：LG Management
   组织单位名称：YourCompany
   组织名称：YourCompany
   城市或区域名称：Shanghai
   省/市/自治区名称：Shanghai
   国家/地区代码：CN
   ```

### 11.2 修改配置

1. 用 HBuilderX 打开 `apps/mobile-app` 文件夹

2. 修改 `src/manifest.json`：
   ```json
   {
     "name": "LG船舶管理",
     "appid": "__UNI__XXXXXXX",
     "versionName": "1.0.0",
     "versionCode": "100"
   }
   ```

3. 修改 `src/utils/api.ts`：
   ```typescript
   const apiBaseUrl = 'https://api.yourdomain.com/api'
   ```

### 11.3 云打包 APK

1. 菜单：【发行】→【原生App-云打包】
2. 选择【Android】
3. 配置：
   - 使用自有证书
   - 证书文件：选择 `lg-management.keystore`
   - 证书密码：`LgApp2024!`
   - 证书别名：`lg-management`
4. 点击【打包】
5. 等待打包完成（5-15分钟）
6. 下载 APK 文件

### 11.4 上架应用商店

以华为应用市场为例：

1. 注册：https://developer.huawei.com
2. 完成实名认证
3. 进入【管理中心】→【我的应用】→【新建应用】
4. 填写应用信息：
   - 应用名称：LG船舶管理
   - 应用分类：商务办公
   - 上传图标（512x512 PNG）
   - 上传截图（至少3张手机截图）
5. 上传 APK 文件
6. 填写隐私政策 URL
7. 提交审核

---

## 12. Mobile App 发布 - iOS

### 12.1 准备工作

1. **需要一台 Mac 电脑**

2. **注册 Apple Developer Program**
   - https://developer.apple.com/programs/
   - 费用：$99/年（约 ￥688）
   - 需要 7-14 天审核

3. **安装 Xcode**
   - 从 Mac App Store 下载

### 12.2 创建证书和描述文件

1. 登录 https://developer.apple.com
2. 进入【Certificates, Identifiers & Profiles】

**创建 App ID：**
```
Identifiers → 点击 + → App IDs
Platform: iOS
Bundle ID: com.yourcompany.lgmanagement
```

**创建证书：**
```
Certificates → 点击 + → iOS Distribution (App Store)
按提示在 Mac 上生成证书请求文件
上传后下载证书
```

**创建 Provisioning Profile：**
```
Profiles → 点击 + → App Store
选择你的 App ID
选择证书
下载 .mobileprovision 文件
```

### 12.3 云打包 IPA

1. 在 HBuilderX 中打开项目
2. 【发行】→【原生App-云打包】→【iOS】
3. 配置：
   - appid：`com.yourcompany.lgmanagement`
   - 证书私钥密码：你的密码
   - 上传 .p12 证书和 .mobileprovision 文件
4. 点击【打包】
5. 下载 IPA 文件

### 12.4 上架 App Store

1. 登录 https://appstoreconnect.apple.com
2. 【我的App】→【添加App】
3. 填写信息：
   - 名称：LG船舶管理
   - 语言：简体中文
   - Bundle ID：选择已创建的
4. 准备素材：
   - 1024x1024 图标
   - iPhone 截图（1290x2796）
   - 隐私政策 URL
5. 使用 Transporter 上传 IPA
6. 选择版本 → 提交审核

---

## 13. Mobile App 发布 - HarmonyOS

### 13.1 准备工作

1. **注册华为开发者账号**
   - https://developer.huawei.com
   - 完成实名认证

2. **下载 DevEco Studio**
   - https://developer.harmonyos.com/cn/develop/deveco-studio

### 13.2 编译 HarmonyOS 版本

```bash
# 在 apps/mobile-app 目录
# 添加 package.json 脚本
"build:harmony": "uni build -p mp-harmony"

# 编译
pnpm build:harmony
```

### 13.3 使用 DevEco Studio 打包

1. 打开 DevEco Studio
2. 导入编译产物
3. 配置签名
4. Build → Build Hap(s)/App(s)

### 13.4 上架 AppGallery

1. 登录 AppGallery Connect
2. 创建应用
3. 上传 HAP/APP 包
4. 填写商品信息
5. 提交审核

---

## 14. 完整配置示例

### 14.1 服务器 .env 文件完整示例

```bash
# /opt/lg-management/.env

# ============ 数据库 ============
# 从 RDS 控制台 → 数据库连接 获取
POSTGRES_HOST=rm-bp1234567890.pg.rds.aliyuncs.com
POSTGRES_PORT=5432
# 从 RDS 控制台 → 账号管理 获取/设置
POSTGRES_USER=lg_admin
POSTGRES_PASSWORD=Lg@Database2024!
# 从 RDS 控制台 → 数据库管理 获取
POSTGRES_DB=lg_management

DATABASE_URL=postgresql+asyncpg://lg_admin:Lg@Database2024!@rm-bp1234567890.pg.rds.aliyuncs.com:5432/lg_management

# ============ Redis ============
# 从 Redis 控制台 → 连接信息 获取地址
# 从 Redis 控制台 → 账号管理 设置密码
REDIS_URL=redis://:Lg@Redis2024!@r-bp0987654321.redis.rds.aliyuncs.com:6379/0

# ============ OSS ============
# 从 OSS 控制台获取 Endpoint
MINIO_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
# 从 AccessKey 管理获取
MINIO_ACCESS_KEY=LTAI5tAbCdEfGhIjKlMnOp
MINIO_SECRET_KEY=AbCdEfGhIjKlMnOpQrStUvWxYz123456
# 你创建的 Bucket 名称
MINIO_BUCKET=lg-management-files
MINIO_USE_SSL=true

# ============ 安全 ============
# 运行 openssl rand -hex 32 生成
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4

# ============ 环境 ============
DEBUG=false
```

### 14.2 Mobile App API 地址配置

```typescript
// apps/mobile-app/src/utils/api.ts

// 开发环境
// const apiBaseUrl = 'http://localhost:8000/api'

// 生产环境
const apiBaseUrl = 'https://api.yourdomain.com/api'
```

---

## 15. 常见问题

### Q1: 数据库连接失败？

检查：
1. RDS 白名单是否添加了 ECS 的内网 IP
2. 数据库账号密码是否正确
3. 数据库名是否创建

### Q2: Redis 连接失败？

检查：
1. Redis 白名单设置
2. 密码格式：`redis://:密码@地址:6379/0`（密码前有冒号）

### Q3: App 无法连接服务器？

检查：
1. API 地址是否正确（https://）
2. 服务器安全组是否开放 443 端口
3. SSL 证书是否配置正确

### Q4: 上传文件失败？

检查：
1. OSS AccessKey 是否正确
2. Bucket 是否存在
3. CORS 是否配置

### Q5: 域名无法访问？

检查：
1. 域名是否备案通过
2. DNS 解析是否生效（可用 `ping yourdomain.com` 测试）
3. SSL 证书是否正确安装

---

## 获取帮助

如果遇到问题：

1. **阿里云工单**：控制台右上角【工单】
2. **官方文档**：https://help.aliyun.com
3. **社区论坛**：https://developer.aliyun.com/ask/

---

*文档版本：2.0.0（小白详细版）*
*最后更新：2026-01-09*
