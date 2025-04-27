# GitHub 和网站信息爬取工具

这是一个功能强大的爬取工具，用于收集 GitHub 仓库和普通网站的信息，并将数据存储到本地 Excel 文件和飞书表格中。

## 功能特点

- **多源数据爬取**：支持爬取 GitHub 仓库和普通网站信息
- **智能 URL 检测**：自动识别 URL 类型并执行相应的爬取操作
- **增量更新**：避免重复添加已爬取的数据，支持信息更新
- **数据存储与同步**：支持本地 Excel 存储和飞书表格同步
- **可视化管理界面**：提供 Web 界面进行配置和管理
- **灵活的命令行接口**：支持多种命令行使用方式
- **数据去重与清洗**：自动清理和去除重复数据
- **记录删除功能**：支持通过 URL 删除已保存的记录
- **批量处理**：支持从文件批量读取多个 URL 进行爬取

## 已实现功能详情

### 1. 数据爬取功能

#### GitHub 仓库信息爬取
- 支持通过仓库 URL 爬取单个仓库信息
- 支持从文件批量读取多个仓库 URL 进行爬取
- 收集的信息包括：仓库名称、描述、星标数、Fork 数、贡献者数量、语言分布等

#### 网站信息爬取
- 支持通过 URL 爬取单个网站信息
- 收集的信息包括：网站标题、描述、关键词、技术栈信息、服务器类型等

### 2. 数据管理功能

#### 本地数据管理
- 自动将爬取的数据保存至本地 Excel 文件
- 支持增量更新，避免重复添加相同 URL 的数据
- 提供数据去重和清洗功能

#### 飞书表格同步
- 自动将爬取的数据同步至飞书表格
- 支持配置飞书 API Token 和表格 ID
- 提供同步状态监控和历史记录

#### 数据删除
- 支持通过 URL 删除已保存的记录
- 同时从本地 Excel 和飞书表格中删除数据
- 使用优化的 API 调用，提高删除操作的效率

### 3. 用户界面

#### Web 管理界面
- 提供直观的 Web 界面进行系统配置和数据管理
- 显示飞书连接状态和同步统计信息
- 支持通过界面触发同步和清理操作

### 4. 命令行接口

#### 智能 URL 识别模式
- 自动识别输入的 URL 类型并执行相应的爬取操作
- 示例：`python run.py https://github.com/microsoft/vscode`

#### 指定模式爬取
- GitHub 模式：`python run.py github --url <URL> [--output <FILE>]`
- 网站模式：`python run.py website --url <URL> [--output <FILE>]`
- 批量模式：`python run.py github --file <FILE_WITH_URLS> [--output <FILE>]`

#### 数据删除命令
- 删除指定 URL 的记录：`python run.py delete url <URL>`
- 示例：`python run.py delete url https://github.com/microsoft/vscode`

## 安装说明

1. 克隆仓库到本地：
   ```bash
   git clone <仓库URL>
   cd github-scraper
   ```

2. 安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境：
   - 创建 `.env` 文件，配置飞书 API Token 和其他必要参数
   - 参考 `.env.example` 文件了解所需配置项

## 使用方法

### 命令行使用

1. 智能 URL 识别模式：
   ```bash
   python run.py <URL>
   ```

2. 爬取 GitHub 仓库信息：
   ```bash
   python run.py github --url <仓库URL> [--output <输出文件>]
   ```
   
3. 从文件批量爬取 GitHub 仓库：
   ```bash
   python run.py github --file <包含URL的文件> [--output <输出文件>]
   ```

4. 爬取网站信息：
   ```bash
   python run.py website --url <网站URL> [--output <输出文件>]
   ```

5. 删除数据：
   ```bash
   python run.py delete url <URL>
   ```

### Web 界面使用

1. 启动 Web 服务：
   ```bash
   python api_server.py
   ```

2. 打开浏览器访问：`http://localhost:5000`

3. 在界面上配置飞书连接参数，进行数据同步和管理操作

## 数据字段说明

### GitHub 仓库数据字段

| 字段名 | 描述 |
|--------|------|
| repository_url | 仓库 URL |
| name | 仓库名称 |
| full_name | 完整仓库名（用户名/仓库名） |
| owner | 仓库所有者用户名 |
| description | 仓库描述 |
| created_at | 创建时间 |
| updated_at | 最后更新时间 |
| pushed_at | 最后推送时间 |
| stars | 星标数量 |
| forks | Fork 数量 |
| watchers | 观察者数量 |
| open_issues | 开放问题数量 |
| language | 主要编程语言 |
| languages | 所有使用的编程语言（百分比） |
| topics | 主题标签 |
| license | 许可证类型 |
| is_fork | 是否为 Fork 的仓库 |
| contributors_count | 贡献者数量 |
| homepage | 主页 URL |
| size | 仓库大小（KB） |
| default_branch | 默认分支名称 |

### 网站数据字段

| 字段名 | 描述 |
|--------|------|
| website_url | 网站 URL |
| title | 网站标题 |
| description | 网站描述 |
| keywords | 关键词 |
| favicon | 网站图标 URL |
| server | 服务器类型 |
| technologies | 使用的技术栈 |
| analytics | 使用的分析工具 |
| response_time | 响应时间（毫秒） |
| status_code | HTTP 状态码 |
| content_type | 内容类型 |
| external_links | 外部链接数量 |
| internal_links | 内部链接数量 |
| framework | 检测到的框架 |
| meta_tags | Meta 标签信息 |
| headers | HTTP 响应头 |
| text_content | 页面文本内容摘要 |

## 飞书集成

本工具支持将数据同步到飞书表格，实现团队协作和数据共享。

### 配置步骤

1. 在飞书开放平台创建应用并获取 API Token
2. 创建电子表格并获取表格 ID
3. 在 `.env` 文件中配置相关参数：
   ```
   FEISHU_APP_ID=your_app_id
   FEISHU_APP_SECRET=your_app_secret
   FEISHU_SPREADSHEET_TOKEN=your_spreadsheet_token
   GITHUB_SHEET_ID=github_sheet_id
   WEBSITE_SHEET_ID=website_sheet_id
   ```

### 飞书功能

- **数据同步**：将本地数据自动同步到飞书表格
- **数据清理**：支持一键清理飞书表格中的重复数据
- **增量更新**：只更新或添加新数据，避免重复
- **行级操作**：支持精确删除单行数据而不影响整表

## 贡献指南

欢迎贡献代码或提出建议！请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件 