# GitHub爬虫工具

一个强大的GitHub仓库和网站信息爬取工具，可以收集GitHub仓库的详细信息以及相关网站内容，并支持将数据导出到Excel和飞书。

## 功能特点

- **GitHub仓库爬取**：自动收集仓库信息，包括stars、forks、README内容、语言、许可证等
- **网站信息爬取**：抓取网站的标题、描述、关键词、技术栈等信息
- **数据导出**：支持将数据导出到Excel表格
- **飞书集成**：一键同步数据到飞书电子表格
- **代理支持**：内置代理管理，轻松应对IP限制
- **批量处理**：支持从文件批量导入URL进行处理
- **Web界面**：用户友好的React前端界面
- **命令行支持**：支持通过命令行使用所有功能

## 系统架构

该项目分为前端和后端两部分：

### 后端（Python）

- 基于Flask的RESTful API服务
- 多线程爬虫引擎
- Excel数据处理
- 飞书API集成
- 日志和错误处理

### 前端（React）

- 基于React的单页应用
- Ant Design UI组件
- Axios用于API通信
- 响应式设计，适配桌面和移动设备

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+ (仅前端开发需要)
- Git

### 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/qql828/github-scraper.git
   cd github-scraper
   ```

2. 安装后端依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量（可选）
   创建`.env`文件，添加以下配置：
   ```
   GITHUB_TOKEN=your_github_token
   FEISHU_APP_ID=your_feishu_app_id
   FEISHU_APP_SECRET=your_feishu_app_secret
   ```

4. 运行后端服务
   ```bash
   # 在Windows上
   start.bat
   
   # 在Linux/Mac上
   chmod +x start.sh
   ./start.sh
   ```

5. 前端开发（可选）
   ```bash
   cd frontend
   npm install
   npm start
   ```

## 使用指南

### Web界面使用

1. 启动服务后，访问 http://localhost:5000
2. 在GitHub页面输入GitHub仓库URL，点击"爬取"按钮
3. 在网站页面输入网站URL，点击"爬取"按钮
4. 在数据管理页面查看和管理已爬取的数据
5. 在飞书同步页面将数据同步到飞书

### 命令行使用

爬取单个GitHub仓库：
```bash
python main.py github --url https://github.com/username/repo
```

爬取多个GitHub仓库：
```bash
python main.py github --file repos.txt
```

爬取网站：
```bash
python main.py website --url https://example.com
```

使用代理：
```bash
python main.py github --url https://github.com/username/repo --proxy http://127.0.0.1:7890
```

同步到飞书：
```bash
python main.py github --url https://github.com/username/repo --save-to-feishu
```

## 项目结构

```
github-scraper/
├── api_server.py        # Flask API服务器
├── main.py              # 命令行入口
├── run.py               # 启动脚本
├── requirements.txt     # Python依赖
├── scrapers/            # 爬虫模块
│   ├── github_scraper.py  # GitHub爬虫
│   ├── website_scraper.py # 网站爬虫
│   └── base_scraper.py    # 基础爬虫类
├── utils/               # 工具函数
│   ├── config.py          # 配置管理
│   ├── excel_manager.py   # Excel处理
│   ├── feishu_manager.py  # 飞书API集成
│   └── proxy/             # 代理管理
├── data/                # 数据存储
├── logs/                # 日志目录
├── frontend/            # React前端
│   ├── public/
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── api/           # API客户端
│   │   └── utils/         # 工具函数
│   ├── package.json
│   └── README.md
└── README.md            # 项目文档
```

## 配置说明

可通过`utils/config.py`修改配置，或者使用环境变量：

- `GITHUB_TOKEN`: GitHub API令牌（可选，但可增加API限制）
- `FEISHU_APP_ID`: 飞书应用ID
- `FEISHU_APP_SECRET`: 飞书应用密钥
- `MAX_THREADS`: 最大线程数
- `REQUEST_TIMEOUT`: 请求超时时间
- `MAX_RETRIES`: 最大重试次数
- `USE_PROXY`: 是否使用代理

## 贡献指南

欢迎提交Pull Request或Issue!

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

## 许可证

该项目采用MIT许可证 - 详情请参阅LICENSE文件

## 联系方式

如有问题或建议，请提交Issue或直接联系仓库所有者。

---

**注意**: 请确保在使用此工具时遵循GitHub和被爬取网站的使用条款。设置适当的爬取间隔，避免对目标站点造成过大负担。