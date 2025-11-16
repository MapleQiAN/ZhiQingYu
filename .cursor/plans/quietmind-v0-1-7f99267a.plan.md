<!-- 7f99267a-9577-4db9-ad7f-6e06e35d0863 5bc2cade-4b49-4120-9bb1-b64a43e8075c -->
# QuietMind v0.1 实现计划

## 技术栈调整

**后端**（保持不变）：

- Python 3.11+ / FastAPI / SQLAlchemy 2 / SQLite
- LLM Provider 抽象层，支持多厂商：OpenAI、Anthropic Claude、通义千问、文心一言、ollama等

**前端**（重大调整）：

- Vue 3 + TypeScript + Vite
- NaiveUI 组件库
- Vue Router（路由）
- Pinia（状态管理，可选）
- ECharts 或 NaiveUI内置图表（替代Recharts）

## 项目结构

```
quietmind/
├── backend/
│   └── app/
│       ├── api/          # API路由
│       ├── core/         # LLM Provider、风险检测等核心逻辑
│       ├── models/       # SQLAlchemy模型
│       ├── schemas/      # Pydantic模型
│       ├── services/     # 业务逻辑服务
│       ├── db.py
│       └── main.py
├── web/
│   ├── src/
│   │   ├── views/        # 页面组件（Chat、Journal、Overview）
│   │   ├── components/   # 可复用组件
│   │   ├── router/       # Vue Router配置
│   │   ├── stores/       # Pinia stores（可选）
│   │   ├── api/          # API调用封装
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 实现步骤

### 阶段1：后端基础架构

1. **初始化FastAPI项目**

   - 创建 `backend/app/main.py`，配置CORS
   - 创建 `backend/app/db.py`，配置SQLAlchemy + SQLite
   - 实现 `/health` 健康检查接口
   - 创建统一响应格式中间件/工具函数

2. **数据模型定义**

   - `backend/app/models/message.py` - Message模型
   - `backend/app/models/daily_summary.py` - DailySummary模型
   - `backend/app/models/session.py` - Session模型
   - `backend/app/schemas/` - 对应的Pydantic schemas
   - 创建数据库初始化脚本

### 阶段2：LLM Provider多厂商支持

3. **LLM Provider抽象层**

   - `backend/app/core/llm_provider.py` - 定义抽象接口 `LLMProvider`
   - `backend/app/core/providers/` - 各厂商实现：
     - `openai_provider.py` - OpenAI API
     - `anthropic_provider.py` - Claude API
     - `qwen_provider.py` - 通义千问API
     - `ernie_provider.py` - 文心一言API
     - `ollama_provider.py` - Ollama本地模型
     - `mock_provider.py` - 假实现（用于测试）
   - 通过环境变量 `LLM_PROVIDER` 选择使用的provider
   - 统一的prompt构建逻辑，确保JSON输出格式一致

4. **风险检测模块**

   - `backend/app/core/risk_detection.py` - 高危关键词检测
   - 维护中英文高危短语列表
   - 实现风险级别升级逻辑

### 阶段3：后端API实现

5. **聊天API (`/api/chat`)**

   - 创建/更新Session
   - 保存用户消息到数据库
   - 调用LLMProvider生成回复和情绪分析
   - 应用风险检测规则
   - 保存助手回复
   - 更新/创建当日DailySummary
   - 返回统一格式响应

6. **日记API**

   - `GET /api/daily` - 获取日期范围内的摘要列表
   - `GET /api/daily/{date}` - 获取单日详情（含代表性消息）

7. **统计API**

   - `GET /api/stats/overview` - 计算情绪趋势、分布、热门主题

### 阶段4：前端Vue3项目

8. **初始化Vue3项目**

   - 使用Vite创建Vue3 + TypeScript项目
   - 安装NaiveUI、Vue Router、axios
   - 配置Vite代理（开发环境连接后端）
   - 创建基础Layout组件（顶部导航：Chat/Journal/Overview）

9. **API封装**

   - `web/src/api/chat.ts` - 聊天API
   - `web/src/api/daily.ts` - 日记API
   - `web/src/api/stats.ts` - 统计API
   - 统一错误处理和响应格式处理

10. **聊天页面 (`/`)**

    - 使用NaiveUI的 `n-card`、`n-input`、`n-button` 等组件
    - 消息气泡布局（用户右对齐，助手左对齐）
    - 情绪标签hover显示
    - 顶部显示今日主情绪
    - 实现发送逻辑（回车发送，Shift+Enter换行）
    - Loading状态和错误提示

11. **日记页面 (`/journal`)**

    - 左侧：时间轴或日历组件（使用NaiveUI组件）
    - 右侧：选中日期的详情展示
    - 调用 `/api/daily` 和 `/api/daily/{date}`

12. **概览页面 (`/overview`)**

    - 使用ECharts或NaiveUI图表组件
    - 情绪趋势折线图
    - 情绪分布条形图
    - 热门主题标签列表
    - 调用 `/api/stats/overview`

### 阶段5：完善与优化

13. **错误处理与用户体验**

    - 后端统一异常捕获和错误响应
    - 前端全局错误提示（使用NaiveUI的message组件）
    - Loading状态管理
    - 空状态展示

14. **Docker部署支持**

    - 创建 `backend/Dockerfile` - 后端容器化配置（Python 3.11，安装依赖，运行FastAPI）
    - 创建 `web/Dockerfile` - 前端容器化配置（多阶段构建：构建静态文件 + Nginx服务）
    - 创建 `docker-compose.yml` - 一键部署配置（后端+前端+数据库卷挂载）
    - 创建 `.env.example` - 环境变量模板（包含所有LLM Provider的配置示例）
    - 创建 `nginx.conf` - Nginx配置（用于前端静态文件服务，可选）

15. **源代码部署支持**

    - 创建 `backend/requirements.txt` - Python依赖清单
    - 创建 `web/package.json` - 前端依赖（已包含在Vue3初始化中）
    - 创建部署脚本：
      - `scripts/setup-backend.sh` - 后端环境初始化（创建虚拟环境、安装依赖、初始化数据库）
      - `scripts/setup-frontend.sh` - 前端构建脚本（安装依赖、构建生产版本）
      - `scripts/setup-backend.bat` - Windows后端部署脚本
      - `scripts/setup-frontend.bat` - Windows前端部署脚本
    - 创建 `scripts/start-backend.sh` / `scripts/start-backend.bat` - 后端启动脚本
    - 创建 `scripts/start-frontend.sh` / `scripts/start-frontend.bat` - 前端启动脚本

16. **文档与配置**

    - 更新README.md，包含：
      - 项目介绍和免责声明
      - 环境变量配置说明（各LLM Provider的配置方式）
      - **Docker一键部署步骤**（docker-compose up）
      - **源代码部署步骤**（Linux/Mac/Windows详细说明）
      - 开发环境运行步骤
      - 技术栈说明
      - 常见问题排查

## 关键技术点

### LLM Provider配置示例

通过环境变量选择provider：

- `LLM_PROVIDER=openai` → 使用OpenAI
- `LLM_PROVIDER=ollama` → 使用Ollama
- 各provider需要不同的环境变量（API Key、Base URL等）

### 前端路由结构

- `/` - 聊天页
- `/journal` - 日记页
- `/overview` - 概览页

### 数据流

1. 用户发送消息 → 前端调用 `/api/chat`
2. 后端调用LLM Provider → 获取回复和情绪分析
3. 后端保存数据并更新DailySummary
4. 前端接收响应并更新UI

## 注意事项

- 所有LLM Provider必须输出统一JSON格式
- 高危情绪检测需要双重保障（LLM判断 + 规则过滤）
- 前端使用NaiveUI保持简洁风格
- 保持代码结构清晰，便于后续扩展新的LLM Provider

### To-dos

- [ ] 初始化FastAPI项目：创建main.py、db.py，配置SQLAlchemy和SQLite，实现/health接口
- [ ] 创建数据模型：Message、DailySummary、Session的SQLAlchemy模型和Pydantic schemas
- [ ] 实现LLM Provider抽象接口，定义统一的LLMResult数据结构
- [ ] 实现多个LLM Provider：OpenAI、Claude、通义千问、文心一言、Ollama、Mock
- [ ] 实现风险检测模块：高危关键词列表和风险级别判断逻辑
- [ ] 实现/api/chat接口：会话管理、消息保存、LLM调用、DailySummary更新
- [ ] 实现/api/daily和/api/daily/{date}接口：日记列表和详情查询
- [ ] 实现/api/stats/overview接口：情绪趋势、分布、热门主题统计
- [ ] 初始化Vue3项目：Vite + TypeScript + NaiveUI + Vue Router配置
- [ ] 封装前端API调用：chat.ts、daily.ts、stats.ts，统一错误处理
- [ ] 实现聊天页面：消息气泡、输入框、发送逻辑、情绪标签显示
- [ ] 实现日记页面：时间轴/日历、日期详情展示
- [ ] 实现概览页面：情绪趋势图、分布图、热门主题列表
- [ ] 完善错误处理和用户体验：后端统一异常捕获、前端错误提示、Loading状态
- [ ] 编写README.md：项目介绍、环境配置说明、运行步骤、技术栈说明