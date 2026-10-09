# Skill Inventory

轻量内部 Skill 管理平台：管理 SKILL.md 草稿、发布快照，通过 HTTP 读取已发布内容。

前端 React + TypeScript + Ant Design + Vite；后端 FastAPI + SQLAlchemy + Psycopg；PostgreSQL 18；Docker Compose + Nginx。

## 快速了解项目

Skill Inventory 将团队工作方法作为 SKILL.md 文本集中管理，供内部客户端通过 HTTP 获取。它负责内容管理和分发，不负责执行 Skill 或调用 AI 模型。

核心流程：**新建草稿 → 保存或修改 → 发布快照 → 客户端读取 → 修改草稿 → 再次发布**。

| 能力 | 当前实现与边界 |
| --- | --- |
| 内容管理 | 新建、编辑、详情、搜索、状态筛选、分页和删除；标识创建后不可变 |
| 发布 | 每个 Skill 仅保存一份最新发布快照；首次 revision 为 1，每次发布递增，即使内容相同 |
| 客户端读取 | 仅公开已发布的名称、简介、revision、发布时间及原文；不公开草稿 |
| 文本处理 | 原样保存 Markdown；不解析 frontmatter，不执行代码；预览显示转义后的原文，不渲染 Markdown |
| 状态 | “未发布”表示尚无快照；已发布后即使草稿有修改，仍属于“已发布”，详情页另行提示未发布修改 |
| 暂不支持 | 认证、SSO、权限角色、审批、撤回发布、历史版本与回滚、MCP、文件包上传、AI 执行和云部署方案 |

### 代码导航与调用链

```text
frontend/src/
  app/                 页面路由、布局、主题
  pages/               列表、详情、新建/编辑、客户端接入
  components/          Skill 表单、原文预览
  api/                 HTTP 请求封装
  types/               TypeScript 数据类型
backend/src/skill_inventory/
  routes/              管理端和客户端 HTTP 接口
  schemas.py           请求校验与响应结构
  services/skills.py   草稿、发布、删除及事务处理
  repositories/        查询、搜索、分页与行锁
  models.py            数据库表映射
  config.py / db.py    环境配置与数据库连接
  seed.py              演示数据
backend/migrations/     Alembic 数据库迁移
backend/tests/          后端测试
compose.yaml           本地 web / api / db 编排
compose.test.yaml      隔离测试环境
```

浏览器 → Nginx（静态页面及同源 API 代理）→ FastAPI 路由 → 服务层 → 查询层 / SQLAlchemy → PostgreSQL。开发模式由 Vite 代理 API。管理接口使用 UUID 定位记录，客户端使用稳定的 slug 定位发布内容。

## 本地启动

需要 Docker Desktop（Linux 容器）及 Docker Compose v2，确保 Docker Engine 正在运行。只运行容器时无需本机 Node、Python 或 PostgreSQL。

1. 将 `.env.example` 复制为 `.env`，填写非空 `POSTGRES_PASSWORD`。`.env` 已被 Git 和镜像构建排除，不提交凭据。
2. 在项目根目录执行：

```sh
docker compose up --build -d
docker compose ps
```

打开 [管理页面](http://localhost:8080) 或 [API 文档](http://localhost:8080/docs)。仅 web 绑定宿主机 `127.0.0.1:8080`；数据库和 API 无宿主机公开端口。

启动时等待 PostgreSQL 健康，执行 Alembic 迁移，成功后启动 API；迁移失败时不会继续启动。首版运行一个 API 副本。

可选：显式创建示例数据（重复运行不覆盖现有 Skill）：

```sh
docker compose exec api uv run --no-sync python scripts/seed.py
```

## 使用流程

在 Skill 库新建草稿，填写名称、标识、简介和 Markdown 原文。保存后进入详情页发布。标识创建后不可修改，建议使用 `code-review` 等小写形式。

编辑已发布 Skill 只修改草稿，客户端仍读取上次发布快照；再次发布才更新内容并递增 revision。详情页删除需确认，列表页删除直接执行；两处都会同时删除草稿和发布快照。首版不保存历史发布版本。

仅保存文本，不自动解析或重写 frontmatter，不执行内容中的代码；预览为安全转义的原文。名称必填且最多 120 字符；简介最多 1000 字符；内容必填且最多 256 KiB UTF-8；slug 最多 64 字符，仅小写字母、数字和中间连字符。

## 客户端接口

```sh
# 已发布元数据列表，支持 q、limit（默认 20，最大 100）、offset
curl "http://localhost:8080/api/v1/skills?limit=20&offset=0"

# 发布元数据，含 revision
curl "http://localhost:8080/api/v1/skills/code-review"

# SKILL.md 原文，text/plain; charset=utf-8
curl "http://localhost:8080/api/v1/skills/code-review/content"
```

列表返回 `{items, total, limit, offset}`，不包含原文；原文使用 `/content` 获取。未发布、不存在或删除的 Skill 返回 404。

管理接口位于 `/api/admin/skills`：GET/POST 列表和创建，`/{id}` GET/PUT/DELETE，`/{id}/publish` POST 发布。PUT 替换草稿字段，不能修改 slug。冲突返回 409，输入不合法返回 422，数据库不可用返回 503。`/healthz` 检查数据库连接。

发布请求可携带 `{name, description, content}`，后端在同一事务中保存这些字段并发布，确保快照对应本次提交的表单。无请求体时发布当前草稿。新建页首次创建成功后会保留 ID，后续发布失败可直接重试发布或保存草稿。

## 数据结构

数据库用两张表分离草稿和发布内容，关系为 `skills 1 → 0..1 published_skills`。未发布时没有快照行；发布时新增或覆盖该行，并不追加历史版本。

| 表 | 字段 | 含义与约束 |
| --- | --- | --- |
| `skills` | `id` | UUID 主键，管理端引用 |
| `skills` | `slug` | 唯一字符串，最长 64 字符，客户端稳定标识 |
| `skills` | `name`, `description`, `content` | 当前草稿；名称最长 120 字符，简介最长 1000 字符，正文为 Text |
| `skills` | `created_at`, `updated_at` | 带时区时间戳；修改草稿时更新 updated_at |
| `published_skills` | `skill_id` | 主键，同时外键引用 skills.id；删除草稿时级联删除 |
| `published_skills` | `name`, `description`, `content` | 最近一次发布时复制的完整快照 |
| `published_skills` | `revision`, `published_at` | 发布序号和带时区发布时间 |

请求层限制正文为非空文本、最多 262144 个 UTF-8 字节；名称和正文不能全为空白，名称、简介和正文均拒绝 NUL 字符。正文的字节限制由请求校验实施，不是数据库 Text 字段长度。

管理列表返回 `SkillSummary`：草稿元数据、UUID、创建/更新时间，以及可空的 `published_revision`、`published_at`；不包含正文。管理详情 `SkillDetail` 增加草稿 `content` 和可空的 `published`，后者包含发布元数据及快照正文。

发布时锁定对应草稿行，在同一事务中更新快照；携带表单时保存草稿与发布一起提交，失败一起回滚。编辑保存不会改变发布快照。新建页的“创建记录”和“发布”是两次请求，发布失败后已创建的草稿仍保留，页面复用其 ID 进行重试。

## 页面与交互

| 页面路径 | 内容与操作 |
| --- | --- |
| `/` | 自动跳转 `/skills` |
| `/skills` | Skill 库；名称/标识搜索、状态筛选、刷新、分页；点击名称查看详情，点击编辑进入表单 |
| `/skills/new` | 新建；名称、唯一标识、简介和正文；保存草稿或直接发布 |
| `/skills/:id` | 详情；查看草稿和发布内容两个标签页、发布序号、更新时间；复制原文接口地址；编辑、再次发布、确认删除 |
| `/skills/:id/edit` | 编辑；标识禁用；保存草稿进入详情，发布提交当前表单并返回上一页，无应用历史时返回列表 |
| `/guide` | 客户端接入说明、接口示例和复制操作 |

搜索通过回车或搜索按钮提交；切换搜索条件或状态回到第一页。列表每页可选 10/20/50/100 条；列表只为未发布项提供发布按钮，已发布项可在详情或编辑页再次发布。列表发布直接发布已保存草稿。

编辑器可切换原文预览并显示 UTF-8 字节数。保存或发布失败时显示错误，保留表单以便重试。返回与取消回到列表，不自动保存。**列表页删除不弹确认；演示删除时请使用临时记录。** 删除分页最后一项后会退回上一页。

## 接口设计

所有路径均相对同源入口 `http://localhost:8080`；除原文接口与 DELETE 空响应外，请求/响应使用 JSON。无认证，管理与客户端接口的路径区分不构成权限隔离。

### 管理接口

| 方法与路径 | 输入 | 成功响应 |
| --- | --- | --- |
| `GET /api/admin/skills` | `q`、`status`、`limit`、`offset` | 200，`Page<SkillSummary>` |
| `POST /api/admin/skills` | `slug`、`name`、`description`、`content` | 201，`SkillDetail` |
| `GET /api/admin/skills/{id}` | UUID | 200，`SkillDetail` |
| `PUT /api/admin/skills/{id}` | `name`、`description`、`content` | 200，`SkillDetail` |
| `POST /api/admin/skills/{id}/publish` | 可省略请求体；或提交完整草稿字段 | 200，`PublishedMetadata` |
| `DELETE /api/admin/skills/{id}` | UUID | 204，无响应体 |

PUT 为替换草稿字段：name、content 必填，description 省略时变为空字符串；不能携带 slug 或其他未知字段。发布携带请求体时遵循同样的字段校验；`{}` 不是有效的完整草稿，请用无请求体发布当前已保存草稿。

创建请求示例：

```json
{
  "slug": "demo-checklist",
  "name": "演示检查清单",
  "description": "演示草稿与发布隔离",
  "content": "# 检查清单\n\n1. 阅读背景。\n2. 核对输出。\n"
}
```

### 客户端接口与响应

| 方法与路径 | 返回 |
| --- | --- |
| `GET /api/v1/skills` | 已发布元数据分页列表，支持 q、limit、offset |
| `GET /api/v1/skills/{slug}` | 单项发布元数据，不包含正文 |
| `GET /api/v1/skills/{slug}/content` | 最新发布原文，`text/plain; charset=utf-8` |
| `GET /healthz` | 数据库可连接时返回 `{"status":"ok"}`，否则 503 |

列表结构示例（时间为示意值）：

```json
{
  "items": [{
    "slug": "code-review",
    "name": "代码审查",
    "description": "统一团队代码审查步骤",
    "revision": 1,
    "published_at": "2026-10-09T00:00:00Z"
  }],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

`q` 最长 120 字符，按名称或 slug 做不区分大小写的包含搜索，不搜索正文；管理端使用草稿名称，客户端使用发布名称。limit 默认为 20，范围 1–100；offset 默认 0，必须非负。管理端 status 可为 draft 或 published，省略表示全部。列表按创建时间倒序、ID 排序，total 是筛选后的总条数。

错误：404 表示记录不存在，或客户端目标未发布/已删除；409 表示 slug 重复；422 表示字段、UUID 或查询参数校验失败；503 表示数据库操作失败。业务错误返回 `{"detail":"错误描述"}`，422 的 detail 为校验问题数组。完整字段定义见运行中的 [Swagger UI](http://localhost:8080/docs) 与 [OpenAPI JSON](http://localhost:8080/openapi.json)。

## 演示内容与操作步骤

启动后执行上文 seed 命令。全新数据库将获得以下数据；命令按 slug 跳过已有项，不覆盖已有修改，也不会把已有草稿自动发布。

| 标识 | 名称 | 初始状态 | 演示用途 |
| --- | --- | --- | --- |
| `code-review` | 代码审查 | 已发布 r1 | 查看发布元数据、正文和客户端接入 |
| `meeting-notes` | 会议纪要 | 未发布 | 展示草稿对客户端不可见 |

建议用以下流程完成一次演示：

1. 打开 `/skills`，搜索 `code-review`，切换已发布/未发布筛选，查看两个示例的不同状态。
2. 打开代码审查详情，分别查看草稿与客户端发布内容；访问 `/api/v1/skills/code-review/content` 获取原文。
3. 新建临时 Skill，标识使用未占用的 `demo-checklist`，填写上方请求示例中的内容并保存草稿。客户端访问其 `/content` 此时返回 404。
4. 在详情页确认发布，记录 revision 和正文；编辑正文后只保存草稿。详情提示有未发布修改，客户端仍读取旧正文。
5. 在编辑页修改并点击发布，返回后客户端读到新正文，revision 增加；这一步展示当前表单保存与发布的事务一致性。
6. 如需演示删除，进入临时记录详情，先取消删除确认以验证记录仍存在，再确认删除；客户端读取返回 404。

这些步骤描述可复现的演示流程，不表示每次启动自动执行。历史功能验证记录见 [实施记录](docs/IMPLEMENTATION_STATUS.md)；本次 README 更新不重新生成示例数据或修改业务数据。

## 测试和检查

独立 Compose 项目使用临时 PostgreSQL，测试与业务卷隔离：

```sh
docker compose -p skillinventory-test -f compose.test.yaml run --build --rm test
docker compose -p skillinventory-test -f compose.test.yaml down
```

后端本机开发（Python 3.12+ 与 uv）：

```sh
cd backend
uv sync --frozen --no-install-project
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
```

首次同步先安装锁文件中的构建工具，再构建本项目；`build` 依赖组固定 hatchling、editables 和 uv 的版本，项目构建复用这些已安装依赖。

配置 `DATABASE_URL=postgresql+psycopg://...` 连接本地开发库，然后执行 `uv run alembic upgrade head` 和 `uv run uvicorn skill_inventory.main:app --reload`。也可通过 POSTGRES_HOST/PORT/USER/PASSWORD/DB 环境变量配置，密码特殊字符无需手动 URL 转义。

本机集成测试需设置 `TEST_DATABASE_URL`，数据库名必须以 `_test` 结尾；测试会清空该测试库的 Skill 表。未设置时数据库测试跳过，不能将跳过当作集成测试通过。

前端本机开发（Node 24、npm）：

```sh
cd frontend
npm ci
npm run dev
npm run typecheck
npm run build
```

Vite 将 API 代理至本机 `127.0.0.1:8000`，开发页面默认 `localhost:5173`。容器使用锁文件安装依赖。

## 停止、持久化及备份

```sh
docker compose stop
docker compose start
docker compose logs --tail=100 api
```

数据库存于 `postgres_data` 命名卷，普通停止、`down` 和容器重建不会删除数据。**`docker compose down -v` 会删除业务数据卷，勿用于日常停止。** 修改 `.env` 密码不会自动修改已有数据库用户密码。

备份（文件直接生成在数据库容器内，避免 Windows PowerShell 二进制重定向损坏）：

```sh
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/skill-inventory.dump'
docker compose cp db:/tmp/skill-inventory.dump ./skill-inventory.dump
```

恢复到同结构的目标数据库前先备份目标；恢复会覆盖目标表数据：

```sh
docker compose stop api web
docker compose cp ./skill-inventory.dump db:/tmp/skill-inventory.dump
docker compose exec db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/skill-inventory.dump'
docker compose start api web
```

## 范围

当前为本机 MVP，无认证、SSO、权限角色、审批、MCP 或历史版本。Nginx 和 API 仅接受 localhost / 127.0.0.1 主机名；管理写请求携带 Origin 时，仅允许这两个主机的 8080（容器页面）或 5173（开发页面）来源，无 Origin 的本机命令行调用仍可用。页面禁止被其他页面嵌入。以上限制不替代身份认证；向内网多人开放前需补充认证和访问控制。不支持 Skill 文件包上传或云部署。

设计与实施计划在 `docs/superpowers/`。参考了 [skill-registry](https://github.com/tangredtea/skill-registry) 和 [skill-server](https://github.com/netclaw-dev/skill-server) 的流程，没有复制其代码。
