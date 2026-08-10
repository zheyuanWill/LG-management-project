# ── 前端 (React + Vite) ──────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN if [ -f pnpm-lock.yaml ]; then \
        npm install -g pnpm && \
        pnpm install --frozen-lockfile; \
    else \
        npm install; \
    fi

COPY . .
RUN npm run build

# ── 运行阶段: Caddy 服务 ──────────────────────────────
FROM caddy:2-alpine

COPY --from=build /app/dist /usr/share/caddy
COPY Caddyfile /etc/caddy/Caddyfile

EXPOSE 80