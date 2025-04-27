# GitHub和网站信息爬取工具前端界面

## 项目介绍
这是GitHub和网站信息爬取工具的前端界面，使用React框架开发，提供了友好的用户界面来操作爬虫功能，可以爬取GitHub仓库和网站信息，并提供数据可视化和管理功能。

## 功能特点
- 提供简洁美观的用户界面
- 支持GitHub仓库和网站信息的爬取
- 支持URL自动识别
- 实时显示爬取进度和结果
- 数据可视化展示
- 历史数据管理和查询
- 支持数据导出和分享
- 支持数据删除和清理
- 飞书数据同步管理
- 移动设备响应式布局

## 安装和启动

### 前置条件
- Node.js 16.x 或更高版本
- npm 8.x 或更高版本
- 后端API服务已启动并运行

### 安装步骤
1. 安装依赖
```bash
cd frontend
npm install
```

2. 启动开发服务器
```bash
npm start
```

3. 构建生产版本
```bash
npm run build
```

## 开发指南

### 目录结构
```
frontend/
├── public/                # 静态资源
├── src/                   # 源代码
│   ├── components/        # 通用组件
│   ├── pages/             # 页面组件
│   ├── api/               # API请求
│   ├── utils/             # 工具函数
│   ├── contexts/          # React上下文
│   ├── hooks/             # 自定义Hooks
│   ├── assets/            # 图片和样式资源
│   ├── App.js             # 应用入口
│   └── index.js           # 渲染入口
└── package.json           # 项目配置
```

### 技术栈
- React 18
- React Router 6
- Ant Design UI库
- Axios用于API请求
- Context API进行状态管理

## 使用方法

### 爬取GitHub仓库信息
1. 在主页上方输入框中输入GitHub仓库URL
2. 点击"爬取"按钮
3. 实时查看爬取进度和结果
4. 爬取完成后，可在数据表格中查看详细信息

### 爬取网站信息
1. 在主页上方输入框中输入网站URL
2. 系统会自动识别URL类型
3. 点击"爬取"按钮
4. 实时查看爬取进度和结果
5. 爬取完成后，可在数据表格中查看详细信息

### 数据管理
1. 在"数据管理"页面可查看所有历史爬取数据
2. 支持按URL、日期等条件筛选
3. 支持删除单条或批量数据
4. 支持导出数据为Excel格式

### 飞书同步
1. 在"飞书同步"页面可管理飞书电子表格同步
2. 查看同步状态和历史记录
3. 手动触发同步操作
4. 配置自动同步选项

## 与后端交互
前端通过RESTful API与后端服务交互，主要接口包括：
- `/api/scrape/github` - 爬取GitHub仓库信息
- `/api/scrape/website` - 爬取网站信息
- `/api/data/github` - 获取GitHub数据
- `/api/data/website` - 获取网站数据
- `/api/delete` - 删除数据记录
- `/api/clean` - 清理和去重数据
- `/api/feishu` - 飞书表格操作相关API

## 贡献指南
欢迎贡献代码或提出建议，请遵循以下步骤：
1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证
MIT License 