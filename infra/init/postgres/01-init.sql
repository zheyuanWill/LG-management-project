-- 初始化数据库扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建用于全文搜索的配置（中文支持需要额外配置）
-- CREATE TEXT SEARCH CONFIGURATION zhparser (COPY = simple);

-- 数据库注释
COMMENT ON DATABASE lg_management IS '修船项目以销定采的一体化项目管理 & 供应链系统';

