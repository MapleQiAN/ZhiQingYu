# 栀情屿 (ZhiQingYu) v0.1

一个极简的AI情绪陪伴Web应用，帮助用户倾诉情绪、梳理心情，并自动生成情绪日记和统计。

## ⚠️ 重要声明

**本应用不是专业的心理治疗工具，不能替代专业的心理健康服务。** 如果你正在经历严重的心理困扰或危机，请立即联系：
- 当地的心理健康热线
- 专业的心理咨询师或心理医生
- 紧急情况下拨打急救电话

## 功能特性

- 💬 **情绪陪伴聊天**：与AI倾诉你的情绪和想法
- 📊 **自动情绪分析**：每条消息自动分析情绪类别、强度和主题
- 📅 **情绪日记**：自动生成每日情绪摘要
- 📈 **情绪统计**：查看情绪趋势、分布和热门主题
- 🛡️ **高危情绪识别**：自动识别高危情绪并提供安全引导

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy 2
- SQLite
- Pydantic v2

### 前端
- Vite
- Vue 3 (Composition API)
- TypeScript
- NaiveUI
- Vue Router
- Vue I18n (多语言支持：中英文)
- Recharts
- pnpm (包管理器)

### LLM支持
- OpenAI API
- Ollama (本地模型)
- Mock Provider (开发测试)

## 项目结构

```
ZhiQingYu/
├── backend/              # 后端代码
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心逻辑（LLM Provider、风险检测）
│   │   ├── models/      # SQLAlchemy模型
│   │   ├── schemas/     # Pydantic模型
│   │   ├── services/    # 业务逻辑服务
│   │   ├── db.py        # 数据库配置
│   │   └── main.py      # FastAPI应用入口
│   └── requirements.txt
├── web/                  # 前端代码
│   ├── src/
│   │   ├── views/       # Vue页面组件
│   │   ├── components/  # Vue组件
│   │   ├── router/      # Vue Router配置
│   │   ├── i18n/        # 多语言配置
│   │   └── lib/         # 工具函数和API封装
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
└── README.md
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- pnpm (推荐) 或 npm/yarn
- (可选) Docker 和 Docker Compose

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量（可选）：
创建 `.env` 文件：
```env
# LLM Provider选择: "openai", "ollama", "mock" (默认)
LLM_PROVIDER=mock

# OpenAI配置（如果使用OpenAI）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Ollama配置（如果使用Ollama）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# 数据库配置（可选，默认使用SQLite）
DATABASE_URL=sqlite:///./zhiqingyu.db
```

5. 启动后端服务：
```bash
python -m app.main
# 或使用uvicorn
uvicorn app.main:app --reload --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

### 前端设置

1. 安装 pnpm（如果尚未安装）：
```bash
npm install -g pnpm
```

2. 进入前端目录：
```bash
cd web
```

3. 安装依赖：
```bash
pnpm install
```

4. 启动开发服务器：
```bash
pnpm run dev
```

前端应用将在 `http://localhost:3000` 启动。

**注意**：前端支持多语言切换（中文/English），可在页面右上角切换语言。

## API文档

启动后端服务后，访问 `http://localhost:8000/docs` 查看自动生成的API文档。

### 主要API端点

- `POST /api/chat` - 发送聊天消息
- `GET /api/daily?from=YYYY-MM-DD&to=YYYY-MM-DD` - 获取日期范围内的日记列表
- `GET /api/daily/{date}` - 获取单日详情
- `GET /api/stats/overview?days=7` - 获取情绪统计概览

## 部署

### Docker部署（推荐）

1. 构建并启动服务：
```bash
docker-compose up -d
```

2. 访问应用：
- 前端: `http://localhost:3000`
- 后端API: `http://localhost:8000`

### 源代码部署

#### 后端

1. 按照"快速开始"中的步骤设置后端
2. 使用生产级ASGI服务器运行：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 前端

1. 构建生产版本：
```bash
cd web
pnpm run build
```

2. 预览生产版本（可选）：
```bash
pnpm run preview
```

生产构建产物在 `web/dist` 目录，可使用 Nginx 等 Web 服务器部署。

## 开发说明

### 添加新的LLM Provider

1. 在 `backend/app/core/providers/` 下创建新的provider文件
2. 实现 `LLMProvider` 接口
3. 在 `backend/app/core/provider_factory.py` 中注册新的provider

### 数据库迁移

当前使用SQLite，数据库文件会自动创建在项目根目录。如需迁移到其他数据库，修改 `backend/app/db.py` 中的 `DATABASE_URL`。

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**再次提醒**：本应用仅供情绪陪伴和记录使用，不能替代专业的心理健康服务。如有严重心理困扰，请寻求专业帮助。

