
# 多智能体工作流系统

## 项目简介

多智能体工作流系统是一个基于Flask的Web应用，通过多个AI智能体协同工作，为用户提供全面的智能服务。系统由分析官、首席执行官、小说家、程序员、审核员等多个角色组成，每个智能体负责不同的任务，共同完成用户的需求。

## 功能特点

- **多智能体协作**：多个AI角色协同工作，各司其职
- **流式响应**：实时展示AI生成内容，提供更好的用户体验
- **任务管理**：自动创建和跟踪任务列表
- **文件管理**：支持文件的自动保存和组织
- **响应式界面**：适配不同设备的友好用户界面

## 系统架构

### 前端

- 基于HTML5、CSS3和JavaScript构建
- 使用Font Awesome提供图标支持
- 集成代码高亮功能

### 后端

- 基于Flask的Web服务
- 多线程处理用户请求
- 流式响应技术
- 智能体管理系统

## 智能体角色

- **分析官**：负责分析用户需求
- **首席执行官**：负责决策和任务分配
- **小说家**：负责创意写作和内容生成
- **程序员**：负责代码生成和技术实现
- **审核员**：负责内容审核和质量控制
- **网络搜索员**：负责搜索互联网信息
- **文件整理员**：负责管理和组织用户文件

## 快速开始

### 环境要求

- Python 3.6+
- Flask
- 其他依赖库（详见requirements.txt）

### 安装步骤

1. 克隆仓库到本地
```bash
git clone https://github.com/yourusername/ai-workflow-system.git
cd ai-workflow-system
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动应用
```bash
./start_app.sh
```
或者直接运行
```bash
python app.py
```

4. 在浏览器中访问 http://localhost:5001

## 使用说明

1. 在首页输入您的需求
2. 系统会自动分配合适的智能体处理您的请求
3. 实时查看生成结果
4. 可以切换不同的智能体获取不同视角的回应

## 项目结构

```
ai-workflow-system/
├── app.py                 # 主应用文件
├── ai_workflow_system.py  # 工作流系统核心
├── agents/                # 智能体模块
│   ├── base_agent.py      # 基础智能体类
│   ├── analyst.py         # 分析官
│   ├── ceo.py             # 首席执行官
│   └── ...                # 其他智能体
├── static/                # 静态资源
│   ├── css/               # 样式文件
│   └── js/                # JavaScript文件
├── templates/             # HTML模板
│   └── index.html         # 主页模板
└── start_app.sh           # 启动脚本
```

## 贡献指南

欢迎贡献代码或提出建议！请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参见 [LICENSE](LICENSE) 文件

