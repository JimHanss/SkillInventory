# Skill Inventory MVP 技术与设计方案

状态：用户已于 2026-10-09 确认本方案，进入实施计划阶段。尚未初始化应用或安装依赖。

## 目标与已确认范围

公司员工通过页面创建、查看、更新、发布、删除内部 Skill；客户端通过 HTTP 获取已发布 Skill 的元数据和 SKILL.md 原文。本地运行，仅支持文本，不支持文件包。用户已明确选定 React + TypeScript + Ant Design、PostgreSQL 和 Docker 容器；此前单服务与 SQLite 方案已被替换。

## 技术选型

前端使用 React + TypeScript + Ant Design，Vite 构建，npm 管理依赖与锁文件。以 Ant Design 的 Layout、Table、Form、Input.TextArea、Modal 和消息提示实现管理流程；接口访问集中在类型化 fetch 客户端中。

后端保留 Python + FastAPI + Uvicorn，使用 SQLAlchemy 2、Psycopg 3 连接 PostgreSQL，Alembic 管理数据库迁移。使用同步 Session 与同步路由，按请求创建和关闭 Session，repository 负责持久化、service 负责发布事务。uv 管理 Python 依赖与锁文件；pytest/httpx 用于接口测试，Ruff 用于静态检查。

Docker Compose 管理 web、api、db 三个服务。web 使用 Node 多阶段构建 React 静态产物，再由 Nginx 提供页面并代理 /api、/healthz、/docs、/openapi.json 到 api；浏览器只访问同一入口。db 使用 PostgreSQL 18 和命名卷，数据卷挂载 /var/lib/postgresql，避免旧版镜像数据路径假设。容器仅 COPY 各自所需源码；.dockerignore 排除私有上下文、秘密、依赖目录和测试缓存。

开发模式可本地运行 Vite 并代理接口，默认交付仍为 Compose 一键构建和启动。首版不引入 Redis、消息队列或独立搜索服务。

本机已验证 Python 3.14.6、uv、Node 24.19.0 以及 Docker CLI 存在；Docker daemon 和 Compose 可用性尚未验证。宿主机 npm/npx 不可用，前端依赖安装、构建及 Context7 查询可在后续获批后通过 Node 容器完成。当前 Context7 CLI 因缺少 npx 未能执行，使用官方文档作为替代。实际依赖版本及镜像补丁版本在初始化时验证、锁定，不使用浮动 latest。

## 数据与发布语义

skills 表保存 id、唯一且创建后不可修改的 slug、草稿 name/description/content、created_at、updated_at。name 和 content 必填；slug 仅允许小写字母、数字及中间连字符，长度不超过 64。name 最大 120 字符，description 最大 1000 字符，content 最大 256 KiB（UTF-8）。内容作为原文存储，不自动改写 YAML frontmatter；元数据以表单字段为准。

published_skills 表以 skill_id 为唯一外键，保存最近一次发布时 name/description/content 的完整快照、递增 revision、published_at。首次发布 revision 为 1；再次发布原子替换快照并递增 revision。不提供历史版本读取。

使用 PostgreSQL TEXT 保存内容，TIMESTAMPTZ 保存 UTC 时间。数据库约束保证 slug 唯一和外键完整性。发布事务首先锁定对应 skills 行，再读取草稿并更新快照，保证并发发布 revision 正确递增；编辑、删除同样通过事务处理。

保存草稿不会改变已发布快照；客户端始终读取快照。尚未发布的条目对客户端返回 404。管理界面显示未发布或已发布，并提示保存后需再次发布。删除需页面二次确认，事务删除草稿和快照；已知 slug 随后返回 404。

## 页面与接口

页面：Skill 列表（按名称/slug 搜索、按发布状态筛选）、新建/编辑页、详情页（草稿和发布内容）、客户端接入说明。使用 React Router 管理页面路由，Nginx 对前端路由提供 index.html 回退，API 请求不能回退为 HTML。编辑器使用 Ant Design Input.TextArea；首版显示 React 转义的原文预览，不使用 dangerouslySetInnerHTML。

管理 API 使用 /api/admin/skills：GET 列表、POST 新建；/{id} 支持 GET、PUT、DELETE；/{id}/publish 支持 POST。列表采用 limit/offset，limit 默认 20、最大 100。PUT 替换草稿字段，slug 不可修改。

客户端 API：GET /api/v1/skills 返回已发布元数据及 revision；GET /api/v1/skills/{slug} 返回已发布元数据；GET /api/v1/skills/{slug}/content 返回 text/plain; charset=utf-8 的 SKILL.md 原文。提供 GET /healthz 检查数据库可访问性，GET /docs 查看 OpenAPI。

业务错误包括不存在 404、slug 冲突 409、输入不合法 422；内部错误不向客户端暴露 SQL 或本地路径。管理列表不返回完整 content，详情才返回。

## 本地运行与边界

默认对宿主机仅发布 web 的 127.0.0.1:8080，api 和 db 只在 Compose 内部网络访问。通过 .env 配置数据库用户、密码、库名；连接地址由配置读取，不在代码中写入凭据。.env 不提交，.env.example 仅含变量说明。

db 使用 pg_isready 健康检查；api 等待 db 健康后执行 alembic upgrade head，成功后启动 Uvicorn，迁移失败则退出。首版仅运行一个 api 副本。web 等待 api 健康后启动。数据库命名卷在普通停止、重启和重建时保留，README 明确 down -v 会删除数据。示例数据通过显式命令创建，不在每次启动时插入。

首版面向本机演示，不提供用户账户、SSO、RBAC、MCP、审批、云部署或远程 Skill 执行。若需要开放给公司内网多人使用，必须另行补充认证与访问控制；当前不将匿名管理接口直接开放到公网。

## 计划初始化的文件

- compose.yaml、.env.example、.gitignore、.dockerignore、README.md。
- frontend/package.json、package-lock.json、tsconfig.json、vite.config.ts、Dockerfile。
- frontend/src/app/、pages/、components/、api/、types/。
- frontend/nginx.conf、index.html。
- backend/pyproject.toml、uv.lock、Dockerfile、alembic.ini、migrations/。
- backend/src/skill_inventory/main.py、config.py、db.py、models.py、schemas.py。
- backend/src/skill_inventory/repositories/skills.py、services/skills.py、routes/admin.py、public.py。
- backend/tests/、backend/scripts/seed.py。

应用入口、健康检查、初始 schema 和首页构成第一步可运行骨架；CRUD、发布快照和客户端读取按后续实现计划完成，不把骨架标记为完整 MVP。

## 验收与验证

通过 Docker Compose 构建并启动全部服务；浏览器访问 http://localhost:8080 能打开页面和调用 API。验证创建、编辑、发布、删除及重建容器后的持久化；重点测试未发布不可读取、草稿修改不影响发布内容、并发发布正确递增 revision、slug 冲突和删除后 404。后端集成测试使用独立 PostgreSQL 测试库，不以 SQLite 代替，避免污染本地业务数据。

执行 Compose 配置检查、镜像构建、迁移、Ruff、pytest、TypeScript 类型检查、前端构建和浏览器交互检查，检查前端路由刷新与接口错误提示。当前只有方案文档，没有应用，尚未执行上述检查。

## 参考

- https://github.com/tangredtea/skill-registry ：管理与分发流程参考，未复制代码。
- https://github.com/netclaw-dev/skill-server ：远端文本读取参考，未复制代码。
- https://ant.design/docs/react/use-with-vite/ ：Ant Design 与 Vite 集成。
- https://fastapi.tiangolo.com/deployment/docker/ ：FastAPI 容器部署。
- https://docs.docker.com/compose/how-tos/startup-order/ ：Compose 健康依赖与启动顺序。
- https://www.postgresql.org/docs/current/tutorial-transactions.html ：数据库事务。

## 审阅后的下一步

用户确认本书面方案后，按 writing-plans 技能编写实施计划并确认执行方式，再初始化应用骨架。目录当前不是 Git 仓库，因此方案尚未提交；后续若初始化 Git，正常提交必须保留项目上下文与安全检查，不绕过 gate。
