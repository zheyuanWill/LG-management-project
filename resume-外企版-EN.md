# [Your Name]

**Frontend Engineer — AI Integration Specialist**

[Phone] · [Email] · [GitHub/Portfolio] · [Location]

---

## Summary

Frontend engineer with 1 year of professional experience building production React applications with deep AI/LLM integration. Shipped 4 products across 2 companies, including a B2B logistics SaaS and an enterprise maritime document system. Strong expertise in SSE streaming, LLM tool calling, cross-platform React/React Native development, and data visualization. Comfortable working across the stack — from React frontends to Python/FastAPI AI services.

---

## Technical Skills

**Frontend**: React 18/19, TypeScript, React Native (Expo), Next.js fundamentals
**State & Data**: Zustand, Redux Toolkit, TanStack Query v5, TanStack Router
**UI & Visualization**: Ant Design, MUI v6, ECharts (custom series), ReactFlow, TipTap, Konva
**AI/LLM Integration**: SSE streaming, tool call orchestration, structured output parsing, multi-modal input, RAG pipelines
**AI Backend**: Python, FastAPI, LangChain, OpenAI/Anthropic/Gemini APIs, ChromaDB, DashScope
**Build & DevOps**: Vite, pnpm monorepo, Docker, GCP Cloud Run, GitHub Actions CI/CD
**Testing**: Jest, React Testing Library, Cypress E2E, Storybook
**Other**: Stripe (Elements + Connect), Firebase Auth, i18n, WatermelonDB (offline-first)

---

## Professional Experience

### Company A — Frontend Engineer | [Start Date] – Present

**Product: Flexhaul.ai** — B2B logistics SaaS for US domestic parcel & LTL shipping
*React 18, TypeScript, Vite, Redux Toolkit, TanStack Query, MUI v6, Stripe*

- **Built a global AI chatbox** with SSE streaming, real-time tool call visualization, and Markdown rendering. Lazy-loaded the component to isolate `react-markdown` from the main bundle, keeping FCP under 2s
- **Implemented AI-powered form filling** — "paste text → structured shipment data" using AI Parse APIs. Covered single quotes, batch parsing (CSV/text → multiple orders), and insurance claim parsing. Reduced manual data entry time by ~70%
- **Designed a text-to-filter system** — users type natural language ("show FedEx shipments from last week") and Redux `aiFilterSlice` automatically applies structured filters, bridging AI output with existing filter UI
- **Led the FH Design System** — 30+ reusable components (FHTable, FHModal, FHTextField) with ESLint rules enforcing MUI decoupling in feature code
- **Architected multi-role routing** for Shipper/Carrier/Admin (80+ routes) with `React.lazy` code splitting and Vite `manualChunks` (6 vendor chunks)
- **Integrated Stripe payments** — Elements, Connect, Google Pay, PayPal for shipper billing and carrier payouts

**Product: Flexhaul AI Agent** — Conversational AI backend for logistics operations
*Python 3.11, FastAPI, LangChain, OpenAI/Anthropic/Gemini*

- **Designed a multi-provider LLM layer** supporting GPT-4o-mini, Claude 3.5 Sonnet, and Gemini 2.0 Flash with environment-variable hot-switching — zero code changes to swap providers
- **Implemented 6 domain-specific tools** (live rate queries, shipment tracking, knowledge search) using LangChain's tool calling agent. Tools return `__action__` payloads that drive frontend navigation and filter application
- **Built SSE streaming pipeline** with `astream_events` for token-level output, tool lifecycle events, and action dispatching
- **Deployed on GCP Cloud Run** — Docker containers, 1–10 auto-scaling instances, <3s rate query latency, <5s cold start

---

### Company B — Frontend Engineer | [Start Date] – [End Date]

**Product: LG-Management** — Ship repair project management & supply chain system
*React 19, Vite 6, TanStack Router, Zustand, ECharts, ReactFlow, React Native (Expo), pnpm monorepo*

- **Architected a pnpm monorepo** with 3 shared packages: `@lg/core` (domain models + RBAC), `@lg/api-client` (pluggable HTTP transport), `@lg/react-hooks` (React Query wrappers + auth store). Web and mobile share 80%+ business logic
- **Built a pluggable HTTP transport layer** — single `HttpTransport` interface adapting `fetch` (web), `uni.request` (WeChat Mini Program), and Expo storage across 3 platforms
- **Created a visual workflow editor** using ReactFlow with 10 node types (approval, condition, parallel gateway, timer, subprocess), 50-step undo/redo, drag-and-drop creation, and backend validation
- **Developed custom ECharts visualizations** — Gantt chart with `renderItem` custom series, Sankey supply chain flow, performance gauges, and a 7/14/30-day trend dashboard
- **Built Kingdee ERP integration monitoring** — connection status, sync log table with filters/retry/AI diagnosis, real-time trend charts, and auto-refresh

**Product: LG-Doc** — Offshore maritime document management system
*React 19, Ant Design 6, TipTap, Konva, React Native (Expo 54), WatermelonDB*

- **Integrated 4 AI capabilities**: smart form filling (DeepSeek structured output), document quality review (AI scoring), photo defect detection (Qwen-VL vision model), and conversational assistant (SSE streaming with self-implemented tool calling — no LangChain)
- **Designed an offline-first mobile architecture** using WatermelonDB + LokiJS for local persistence, with pull/push incremental sync for maritime crews working in low-connectivity environments
- **Built a document editor** combining TipTap rich text (6 extensions) with Konva canvas photo annotation (pen, arrow, rect, text tools) supporting 3 group types (table, data grid, photo)
- **Implemented optimistic locking** with `version_int` conflict detection, a conflict resolution modal ("keep local" / "use server"), and 800ms debounced saves to minimize collisions
- **Contributed to RAG pipeline** — Chroma + DashScope embeddings for semantic document search, used by AI assist and chat features to provide context from historical documents

---

## Key Achievements

| Achievement | Impact |
|-------------|--------|
| SSE streaming AI chat shipped in 2 products | Real-time AI interaction across web + mobile |
| Multi-LLM provider abstraction | Zero-downtime model switching (GPT-4o ↔ Claude ↔ Gemini) |
| Cross-platform monorepo with transport abstraction | 80%+ code reuse across Web, Mobile, Mini Program |
| Offline-first document system | Maritime crews can work without connectivity |
| AI-powered form filling (3 domains) | ~70% reduction in manual data entry |
| Design system with ESLint enforcement | Consistent UI across 80+ pages |

---

## Education

**[University Name]** — [Degree] in [Major] | [Graduation Year]
