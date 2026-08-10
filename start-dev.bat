@echo off
chcp 65001 >nul
title LG 船舶管理 ERP

echo ╔══════════════════════════════════════════════════╗
echo ║     LG 船舶管理 ERP · 开发环境启动脚本          ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM ── 检查 Docker ──
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Docker，请先安装 Docker Desktop
    pause
    exit /b 1
)

REM ── 检查 .env 文件 ──
if not exist ".env" (
    echo [提示] 未找到 .env 文件，正在从 .env.example 复制...
    copy .env.example .env >nul
    echo [完成] 已创建 .env，请修改其中的密码等配置
)

REM ── 构建并启动所有服务 ──
echo.
echo [1/4] 构建后端镜像...
docker compose build backend ai-service celery-worker celery-beat

echo.
echo [2/4] 构建前端镜像...
docker compose build frontend

echo.
echo [3/4] 启动基础服务 (PostgreSQL + Redis + MinIO)...
docker compose up -d postgres redis minio

echo.
echo [等待数据库就绪...]
timeout /t 10 /nobreak >nul

echo.
echo [4/4] 启动所有服务...
docker compose up -d

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  所有服务已启动！                              ║
echo ║                                                ║
echo ║  前端:  http://localhost:3000                  ║
echo ║  后端:  http://localhost:8000/api/v1           ║
echo ║  MinIO: http://localhost:9001                 ║
echo ║  AI:    http://localhost:8001                 ║
echo ║                                                ║
echo ║  默认账号: admin / admin123                    ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo 按任意键查看服务状态...
pause >nul
docker compose ps
pause