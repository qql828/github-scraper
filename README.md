# GitHub 项目信息爬取工具

一个简单实用的工具，用于爬取 GitHub 仓库的基本信息并保存到 Excel 文件中。

## 功能特点

- 一键爬取 GitHub 仓库信息（包括项目名称、描述、Star数、Fork数等）
- 自动保存到 Excel 文件，便于管理和查阅
- 支持批量刷新已爬取的仓库信息，获取最新数据
- 查看已爬取的仓库列表及项目总数
- 删除指定仓库的信息
- 智能识别已存在的仓库，避免重复添加
- 交互式循环模式，支持连续操作
- 强健的错误处理机制，包括文件权限和网络问题处理

## 技术栈

- Python 3.6+
- pandas：数据处理和 Excel 文件操作
- requests：发送 HTTP 请求获取 GitHub 数据
- BeautifulSoup4：解析 HTML 内容
- argparse：处理命令行参数

## 安装步骤

1. 克隆或下载本仓库到本地
2. 确保您已安装 Python 3.6 或更高版本
3. 安装所需依赖：

```bash
pip install -r requirements.txt
```

## 基本用法

### 爬取单个仓库信息

```bash
python main.py --url https://github.com/用户名/仓库名
```

例如：
```bash
python main.py --url https://github.com/microsoft/vscode
```

### 刷新所有已爬取的仓库信息

```bash
python main.py --refresh
```

### 查看已爬取的仓库列表

```bash
python main.py --list
```

### 使用交互式模式

直接运行程序，不带任何参数：

```bash
python main.py
```

在交互式模式下，您可以：
- 输入 GitHub 仓库 URL 来爬取项目信息
- 输入 `refresh` 刷新所有已爬取的仓库信息
- 输入 `list` 查看已爬取的仓库列表
- 输入 `delete 仓库名称` 删除指定仓库的信息
- 输入 `exit` 退出程序

## 高级用法

### 指定输出文件

```bash
python main.py --url https://github.com/用户名/仓库名 --output 自定义文件名.xlsx
```

## 项目结构

```
.
├── main.py              # 主程序入口
├── scraper.py           # GitHub 爬虫模块
├── excel_handler.py     # Excel 文件处理模块
├── requirements.txt     # 项目依赖
├── readme.md            # 项目说明
└── 使用说明.md           # 详细使用说明（中文）
```

## 错误处理

本工具实现了强健的错误处理机制，可以应对常见的问题情况：

1. **文件权限问题**：
   - 检测 Excel 文件是否被其他程序（如 Microsoft Excel）打开
   - 检查文件和目录的写入权限
   - 提供详细的错误信息和解决建议

2. **网络连接问题**：
   - 处理网络超时和连接错误
   - 提供网络故障排查建议

3. **GitHub API 限制**：
   - 处理 GitHub 访问频率限制问题
   - 提供适当的重试策略

详细的错误信息和解决方案请参阅 `使用说明.md` 文件。

## 注意事项

- 请确保您的网络可以正常访问 GitHub
- 不要频繁大量爬取，以免触发 GitHub 的访问限制
- 使用工具时，请确保 Excel 文件未被其他程序打开
- 删除操作不可恢复，请谨慎操作

## 贡献指南

欢迎贡献代码或提出建议！您可以：
1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请查看 LICENSE 文件

## 联系方式

如有任何问题或建议，欢迎提交 Issue 或联系项目维护者。