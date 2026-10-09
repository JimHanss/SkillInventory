# Skill Inventory MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可通过 Docker Compose 本地启动的 Skill 文本管理平台，实现草稿管理、发布和客户端读取。

**Architecture:** React 管理页面通过 Nginx 同源访问 FastAPI，PostgreSQL 保存草稿和发布快照。后端分离路由、业务服务与持久化，发布事务锁定草稿行后更新快照。第一项交付可启动骨架，其余任务补齐完整 MVP。

**Tech Stack:** React、TypeScript、Ant Design、Vite、React Router、npm；Python、FastAPI、SQLAlchemy 2、Psycopg 3、Alembic、uv；PostgreSQL 18、Nginx、Docker Compose；pytest/httpx、Ruff。

**Spec:** `docs/superpowers/specs/2026-10-09-skill-inventory-design.md`（用户已确认）。

## Global Constraints

- 仅支持 SKILL.md 文本，不支持文件包；不执行 Skill 内容。
- slug 仅允许小写字母、数字及中间连字符，长度不超过 64，创建后不可修改。
- name 最大 120 字符，description 最大 1000 字符，content 最大 256 KiB（UTF-8）；name 和 content 必填。
- 内容作为原文存储，不自动改写 YAML frontmatter；元数据以表单字段为准。
- GET 列表使用 limit/offset；limit 默认 20、最大 100。
- 首次发布 revision 为 1；再次发布递增；草稿编辑不改变已发布快照。
- 默认宿主机入口 127.0.0.1:8080；api 和 db 只在 Compose 内部网络访问。
- PostgreSQL 18 数据卷挂载 /var/lib/postgresql，时间使用 TIMESTAMPTZ/UTC。
- 镜像不使用浮动 latest，依赖生成真实锁文件；不手写伪造锁文件。
- .env 不提交；不提供账户、SSO、RBAC、MCP、审批或云部署。
- 当前目录没有 Git 仓库；提交前先初始化 Git、按 project-context helper 初始化并准备上下文，然后正常 git commit。安全 gate 失败不得绕过；无法提交时保留文件并报告。
- Context7 查询须先 library 再 docs、每个问题最多三条命令、在默认沙箱外执行；宿主机缺少 npx，执行阶段优先使用经验证的 Node 容器入口。网络或配额失败应明确报告，不能以训练记忆充当当前文档。

## Review Focus

1. 中文与 emoji 的 UTF-8 字节长度边界：按字节限制且保持原文不变（任务 2）。
2. 名称含 %、_ 或引号：搜索按字面匹配，不能扩大匹配或注入 SQL（任务 2）。
3. 同时首次发布同一个 Skill：无唯一键异常，revision 最终为 2（任务 3）。
4. 页面直接刷新与不存在 API：前端路由可打开，API 404 必须保持 JSON（任务 4、5）。
5. 保存或发布网络失败：保留编辑内容，显示错误且不误报成功（任务 4）。

## 文件与接口约定

- `compose.yaml`、`.env.example`、`.gitignore`、`.dockerignore`、`README.md`：运行入口与配置。
- `frontend/Dockerfile`、`.dockerignore`、`nginx.conf`、`package.json`、`package-lock.json`、`tsconfig.json`、`vite.config.ts`、`index.html`：构建和代理。
- `frontend/src/main.tsx`、`app/App.tsx`、`app/styles.css`：应用布局和路由。
- `frontend/src/pages/SkillListPage.tsx`、`SkillEditPage.tsx`、`SkillDetailPage.tsx`、`ApiGuidePage.tsx`：页面职责分别为查询、编辑、查看、接入说明。
- `frontend/src/components/SkillForm.tsx`、`ContentPreview.tsx`：共享表单和安全原文显示。
- `frontend/src/types/skills.ts`、`api/client.ts`、`api/skills.ts`：类型和 HTTP 边界。
- `backend/pyproject.toml`、`uv.lock`、`Dockerfile`、`.dockerignore`、`alembic.ini`、`migrations/env.py`、`migrations/versions/0001_skills.py`：依赖与数据库迁移。
- `backend/src/skill_inventory/__init__.py`、`main.py`、`config.py`、`db.py`、`models.py`、`schemas.py`：入口、配置、连接、表与 DTO。
- `backend/src/skill_inventory/repositories/skills.py`、`services/skills.py`、`routes/admin.py`、`routes/public.py`：持久化、事务和两类接口。
- `backend/tests/conftest.py`、`test_health.py`、`test_admin.py`、`test_publish.py`、`test_public.py`：独立 PostgreSQL 测试库；`backend/scripts/seed.py`：显式示例数据。
- `compose.test.yaml`：独立 test-db 和 test 服务，不挂载业务数据卷；测试结束只清理该项目。

DTO：`SkillCreate(slug, name, description, content)`；`SkillUpdate(name, description, content)`；`SkillSummary(id, slug, name, description, created_at, updated_at, published_revision, published_at)`；`SkillDetail` 追加草稿 content 和可空 published 快照；`PublishedSkill(slug, name, description, revision, published_at)`；`Page[T](items, total, limit, offset)`。id 使用 UUID 字符串，时间使用 ISO 8601 UTC。

## Task 1: 初始化可运行的容器骨架

**Files:** 根运行配置、前后端构建配置、main/config/db/models、初始迁移、React 入口与首页、test_health、compose.test.yaml、README。

**Interfaces:** `create_app() -> FastAPI`；`get_session() -> Iterator[Session]`；`GET /healthz` 成功返回 `{"status":"ok"}`，数据库不可访问返回 503 且不暴露连接字符串。App 暂时显示 Skill Inventory 标题、初始化状态和接口入口，不声称 CRUD 已完成。

- [ ] 验证 Docker daemon/Compose 可用；获取候选库当前文档并锁定兼容版本。若 Docker 未启动，报告具体错误，继续不依赖 daemon 的文件工作。
- [ ] 创建健康检查测试：正常数据库 `status_code == 200` 且 `json() == {"status":"ok"}`；模拟数据库不可用 `status_code == 503` 且响应不包含数据库密码。运行 `docker compose -p skillinventory-test -f compose.test.yaml run --rm test pytest tests/test_health.py -q`，实现前预期导入或入口缺失失败；环境失败不能算红灯测试证据。
- [ ] 创建依赖配置、应用工厂、数据库连接与两表迁移；建立 web/api/db 容器和健康依赖。Nginx API 代理保留原 URI；前端构建使用 npm ci，后端依赖使用 uv 锁定同步。数据库连接由独立环境字段构造 URL，正确处理密码特殊字符。
- [ ] 创建前端入口、布局和 Vite 开发代理；显式 COPY 所需文件，排除 `.project-context/`、`.env`、缓存和本地依赖。建立独立测试库与 session fixture，每次测试回滚或清理自身数据。
- [ ] 生成真实 uv.lock/package-lock.json，运行 `docker compose config --quiet`、`docker compose up --build -d`，重复健康测试；访问入口返回 HTML，/healthz 返回上述 JSON。README 写清配置步骤与启动命令。
- [ ] 初始化 Git 和 project-context（若仍缺失），核对上下文未被打包或跟踪；更新模块记录并 prepare，正常提交 `chore: bootstrap containerized skill inventory`。

## Task 2: 草稿管理与校验

**Files:** schemas、repository、service、routes/admin、test_admin。

**Interfaces:** service 的 `create_skill(session, data: SkillCreate) -> SkillDetail`、`get_skill(session, skill_id: UUID) -> SkillDetail`、`list_skills(session, q: str | None, status: str | None, limit: int, offset: int) -> Page[SkillSummary]`、`update_skill(session, skill_id: UUID, data: SkillUpdate) -> SkillDetail`、`delete_skill(session, skill_id: UUID) -> None`。路由负责业务异常到 HTTP 的映射。

- [ ] 编写 test_admin：POST 返回 201，GET/PUT 返回 200，DELETE 返回 204 后 GET 为 404；重复 slug 为 409；修改 slug 为 422；超长/非法 slug、空白 name/content、负 offset、limit=101 为 422；列表不含 content，返回 total 和分页字段。
- [ ] 增加 UTF-8 原文测试：合法的多字节文本往返完全相等，恰好 262144 字节接受、262145 字节拒绝；HTML 字符和 frontmatter 不改写。搜索 `%`、`_`、引号只匹配包含对应字面字符的记录。status 接受 draft/published，非法值为 422。
- [ ] 运行独立测试服务的 `pytest tests/test_admin.py -q`，确认因缺失功能失败；实现上述 DTO、参数化查询、校验和 API，service 显式控制写事务，数据库唯一约束异常映射 409。默认 q 对 name/slug 不区分大小写搜索。
- [ ] 重跑 test_admin 和 test_health 全部通过；运行 `ruff check .`。按实际改动更新 project-context、prepare，正常提交 `feat: add skill draft management`。

## Task 3: 发布快照与客户端接口

**Files:** service、repository、routes/admin、routes/public、test_publish、test_public。

**Interfaces:** `publish_skill(session, skill_id: UUID) -> PublishedSkill`；`list_published(session, q: str | None, limit: int, offset: int) -> Page[PublishedSkill]`；`get_published(session, slug: str) -> PublishedSkill`；`get_published_content(session, slug: str) -> str`。POST /api/admin/skills/{id}/publish 返回 200 与发布元数据；客户端路由遵循 spec。

- [ ] 编写 test_publish/test_public：未发布详情与原文 404且列表不可见；首次发布 revision=1；编辑草稿后原文仍等于旧内容；再次发布 revision=2并返回新内容；删除后所有读取 404；原文 Content-Type 为 text/plain 且 UTF-8 内容精确相等。
- [ ] 增加两个独立连接同时首次发布测试：两个请求都成功，revision 集合为 `{1, 2}`，最终 revision 为 2；事务失败不残留半成品。列表分页返回 total 且不含 content；不存在 id 发布返回 404。
- [ ] 运行 `pytest tests/test_publish.py tests/test_public.py -q` 确认红灯；实现先锁定 skills 行、读取草稿、更新/插入快照、提交的事务；注册公开路由，只读取发布快照。
- [ ] 重跑后端全部测试及 Ruff；更新上下文、prepare，正常提交 `feat: publish skills and serve client content`。

## Task 4: 实现 Ant Design 管理页面

**Files:** 前端 pages/components/types/api 与 App 路由。

**Interfaces:** `request<T>(path: string, init?: RequestInit): Promise<T>` 处理 JSON 错误与 204；skills API 导出 `listSkills`、`createSkill`、`getSkill`、`updateSkill`、`deleteSkill`、`publishSkill`，参数/结果对应已定义 DTO。路由 `/skills`、`/skills/new`、`/skills/:id`、`/skills/:id/edit`、`/guide`，首页跳转 `/skills`。

- [ ] 在运行中的浏览器建立可复现验收步骤：搜索与状态筛选、翻页、新建、编辑、详情、发布、删除确认、接口说明；记录当前页面缺少流程的事实，不为静态布局编写镜像测试。
- [ ] 实现 API 客户端与类型，再实现列表、共享表单、详情和接入说明。表单验证对应后端限制，slug 创建后禁改；发布按钮先保存成功再发布或要求用户先保存，不发布未保存的本地内容。详情分别显示草稿和发布快照。
- [ ] 添加请求中禁用操作、错误提示、空列表和不存在条目状态。模拟保存/发布请求失败：编辑文本仍保留，无成功提示，可重试；删除取消不发请求。原文通过 React 文本节点显示，HTML/script 文本不执行。
- [ ] 运行 `npm run typecheck`（tsc --noEmit）和 `npm run build`；在容器或可用 Node 环境中执行。浏览器验证宽屏与窄屏可编辑、长文本可滚动；刷新详情和编辑 URL 仍可打开，不存在 API 返回 JSON 404。
- [ ] 更新上下文、prepare，正常提交 `feat: build skill inventory management ui`。

## Task 5: 完成启动文档与端到端验收

**Files:** README、backend/scripts/seed.py、compose 与代理配置（仅修正验收发现的问题）。

**Interfaces:** `uv run python scripts/seed.py` 显式插入一个示例草稿和一个已发布 Skill，重复运行不重复插入或覆盖用户编辑；README 给出经验证的 Compose 执行方式与 curl 原文读取示例。

- [ ] 为 seed 幂等性增加后端测试，运行确认红灯后实现；示例文本不包含秘密，默认启动不调用 seed。
- [ ] 从空测试库执行迁移和全量后端测试，执行前端类型检查/构建与镜像构建。校验 /docs 能加载 /openapi.json，/api/不存在 返回 JSON 404，Nginx 原文响应不改写内容。
- [ ] 浏览器完成创建→发布→读取→编辑→验证旧发布→再次发布→删除闭环。重建 web/api/db 容器但保留卷，验证数据存在；测试库清理仅针对 skillinventory-test，不执行业务卷删除。
- [ ] README 记录首次启动、环境变量、迁移、显式 seed、测试、停止、备份及恢复流程；明确 `docker compose down -v` 会删除数据，当前无认证仅供本机演示。
- [ ] 执行最终 diff 检查，核对 `.project-context/` 和 `.env` 没有进入 Git 或镜像上下文；更新上下文、prepare，正常提交 `docs: document and verify local mvp workflow`。报告实际检查结果，缺失的工具/网络/安全 gate 覆盖不能标为通过。

## 自审与交接

已对照 spec 覆盖技术栈、草稿发布隔离、列表/读取接口、迁移与持久化、容器健康启动、页面与安全原文显示、输入限制和错误处理。五个 Review Focus 均分配了验证任务；本计划未执行，尚无应用测试结果。项目无 Git 仓库，方案与计划均未提交。

推荐 Native 执行：任务共享 DTO、事务与容器配置，当前项目小，按顺序在本会话实施更适合快速 MVP。须先由用户审阅本计划并选择 Native 或 Subagent-driven，再加载相应执行技能。若选择 Native，使用 executing-plans；若选择 Subagent-driven，使用 subagent-driven-development。最终按所选技能执行独立审查，不能自行假定用户已批准执行方式。
