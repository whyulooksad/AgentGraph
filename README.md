# Story2Proposal Agent

## 一、项目简介
**Story2Proposal Agent** 是我围绕科研写作这件事做的一个多 Agent 应用。

它想解决的问题很直接：把一份已经有一定结构的研究内容，逐步整理成论文草稿。这里的输入不是随便一段描述，而是一份结构化的 `ResearchStory`，里面通常已经有研究问题、方法、实验、结论、局限性这些材料，只是还没有真正组织成一篇论文。

这个项目关注的不是“一次性把论文吐出来”，而是把论文生成过程拆开来做。不同 Agent 分别负责结构规划、章节写作、评审、收敛和最终渲染，让整个过程更稳定，也更容易修改。

另外，这个应用建立在我之前写的多 Agent 编排框架 **AgentGraph** 之上。底层 runtime 在仓库的 `src/` 目录下，如果想看这部分设计，请直接看 [src/README.md](src/README.md)。

## 二、系统架构
```text
输入：ResearchStory
    |
    v
节点1：orchestrator
    |
    |-- 接收整份研究 story
    |-- 初始化本次写作运行状态
    |-- 启动整条论文生成流程
    v
节点2：architect
    |
    |-- 读取研究问题、方法、实验、结论等材料
    |-- 规划整篇论文的标题、章节结构和写作顺序
    |-- 生成 blueprint
    |-- 初始化 contract
    v
节点3：章节写作循环
    |
    |-- section_writer
    |   |-- 读取当前 section contract
    |   |-- 生成当前章节 draft
    |
    |-- 并行进入三个 evaluator
    |   |
    |   |-- reasoning_evaluator
    |   |   |-- 检查论证和 claim / evidence 对齐
    |   |
    |   |-- data_fidelity_evaluator
    |   |   |-- 检查 claim、evidence 和 experiment 是否真的对齐
    |   |
    |   |-- visual_evaluator
    |   |   |-- 检查图表和 visual 使用情况
    |   |
    |   v
    |  review_controller
    |   |-- 聚合三路 review
    |   |-- 应用 contract patch
    |   |-- 判断下一步流向
    |
    |-- 分支1：当前 section 需要重写
    |   |
    |   └-- 回到 section_writer
    |
    |-- 分支2：当前 section 通过，且还有下一节
    |   |
    |   └-- 进入下一轮 section_writer
    |
    |-- 分支3：所有 section 都完成
    |   |
    |   └-- 进入 refiner
    v
节点4：refiner
    |
    |-- 做全局收敛和整体润色
    |-- 补充摘要、章节备注等全局内容
    v
节点5：renderer
    |
    |-- 基于 blueprint / contract / drafts / reviews
    |-- 渲染最终 manuscript
    |-- 输出 markdown / LaTeX
    v
最终输出：论文草稿及其中间产物
```

## 三、代码结构
```text
Story2Proposal/
├── backend/                  # 后端主目录
│   ├── api/                  # FastAPI 接口层
│   ├── domain/               # 核心业务逻辑
│   ├── graph/                # Agent 图定义与装配
│   ├── schemas/              # 结构化对象定义
│   ├── servers/              # workflow / MCP 相关服务
│   ├── scripts/              # 后端脚本入口
│   ├── src/                  # AgentGraph runtime
│   ├── prompts/              # Agent prompts
│   ├── data/                 # stories / outputs
│   ├── config.py             # 后端路径与配置
│   ├── llm_io.py             # LLM 结构化读写
│   └── runner.py             # 后端运行入口
├── frontend/                 # 前端运行工作台
├── README.md                 # 本文档
├── AGENTS.md                 # Story2Proposal Agent 的共享约束说明
├── .env                      # 环境变量配置
├── pyproject.toml            # 项目依赖与包配置
└── backend/                  # 唯一后端源码位置
    ├── mcp_manager.py
    ├── mcp_server.py
    ├── memory.py
    ├── skill.py
    ├── types.py
    ├── utils.py
    ├── _settings.py
    ├── README.md
    └── src_test/
```

## 四、

## 五、环境依赖
### 5.1 Python 依赖

- Python `>= 3.12`
- 建议使用 `uv` 管理后端依赖

安装方式：

```powershell
uv sync
```

当前项目在 `pyproject.toml` 里声明的核心依赖包括：
- `openai`
- `mcp`
- `pydantic`
- `pydantic-settings`
- `httpx`
- `Jinja2`
- `jsonschema`
- `common-expression-language`
- `Pygments`
- `fastapi`
- `uvicorn`
- `python-dotenv`

### 5.2 前端依赖

前端位于 `frontend/`，使用 `React + Vite + TypeScript`。

安装方式：

```powershell
cd frontend
npm install
```

### 5.3 环境变量（.env）

| 变量名 | 说明 |
| --- | --- |
| `OPENAI_API_KEY` | 模型服务的 API Key |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 |
| `STORY2PROPOSAL_MODEL` | Story2Proposal 默认使用的后端模型 |

示例：

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
STORY2PROPOSAL_MODEL=qwen-plus
```

## 六、使用指南

先开后端：

```powershell
cd E:\Work\Story2Proposal
uv run python -m backend.api.server
```

再开前端：

```powershell
cd E:\Work\Story2Proposal\frontend
npm run dev -- --host 0.0.0.0
```

然后在浏览器里走这条链路：

1. 打开 `Story` 页
2. 新建或编辑一个 `ResearchStory`
3. 点 `保存 Story`
4. 点 `创建 Run`
5. 跳到对应的 `Run Detail` 页
6. 观察这些状态是否正常更新

- 顶部状态会不会从 `running` 往后更新
- `currentNode / currentSectionId / nextNode` 会不会变化
- `section` 状态会不会变化
- artifact tabs 里哪些项会出现 `已更新`
- 点开某个已更新的 artifact 后，标记会不会消失
- run 完成后，轮询状态会不会变成“已停止轮询”

## 七、License

本项目基于 [MIT License](https://github.com/whyulooksad/ReportAgent/blob/main/LICENSE) 开源。
