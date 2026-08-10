-- ═══════════════════════════════════════════════════
-- 初始化脚本: 启用 pgvector 扩展并创建初始角色
-- 仅在数据库首次创建时执行
-- ═══════════════════════════════════════════════════

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建应用角色 (用于后端连接，权限受限)
CREATE ROLE lg_app WITH LOGIN PASSWORD 'lgdev2026';
GRANT CONNECT ON DATABASE lg_erp TO lg_app;
GRANT USAGE ON SCHEMA public TO lg_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lg_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lg_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lg_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO lg_app;