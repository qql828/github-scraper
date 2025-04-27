# 环境变量配置指南

为了使飞书导出功能正常工作，您需要在项目根目录下创建一个`.env`文件，并配置以下环境变量：

```
# GitHub API配置
GITHUB_TOKEN=your_github_token_here

# 代理配置
USE_PROXY=False
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080

# 请求配置
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=5

# 爬虫配置
MAX_THREADS=5
REQUEST_DELAY=1.0

# 飞书应用配置
FEISHU_APP_ID=your_feishu_app_id_here
FEISHU_APP_SECRET=your_feishu_app_secret_here

# 飞书电子表格配置 - GitHub数据
FEISHU_GITHUB_SPREADSHEET_TOKEN=your_github_spreadsheet_token_here
FEISHU_GITHUB_SHEET_ID=your_github_sheet_id_here

# 飞书电子表格配置 - 网站数据
FEISHU_WEBSITE_SPREADSHEET_TOKEN=your_website_spreadsheet_token_here
FEISHU_WEBSITE_SHEET_ID=your_website_sheet_id_here
```

## 配置说明

### 飞书应用配置

1. **FEISHU_APP_ID**：飞书应用的App ID
2. **FEISHU_APP_SECRET**：飞书应用的App Secret

### 飞书电子表格配置

1. **FEISHU_GITHUB_SPREADSHEET_TOKEN**：GitHub数据电子表格的Token，可以从表格URL中获取
2. **FEISHU_GITHUB_SHEET_ID**：GitHub数据表格的Sheet ID（工作表ID）
3. **FEISHU_WEBSITE_SPREADSHEET_TOKEN**：网站数据电子表格的Token
4. **FEISHU_WEBSITE_SHEET_ID**：网站数据表格的Sheet ID

## 创建飞书应用步骤

1. 登录[飞书开发者平台](https://open.feishu.cn/)
2. 创建一个自建应用
3. 在应用详情页找到App ID和App Secret
4. 在应用的"权限管理"中，添加以下权限：
   - `sheets:spreadsheet:*` (电子表格的读写权限)
   - `sheets:sheet:*` (工作表的读写权限)
5. 发布应用（可以是内部测试版或正式版）
6. 将应用添加到你的团队/企业中

## 创建和配置电子表格

1. 在飞书中创建两个电子表格，分别用于存储GitHub数据和网站数据
2. 对于每个电子表格：
   - 从URL中提取表格Token (spreadsheet_token)
     - 例如: `https://example.feishu.cn/sheets/xxxxxx`，其中`xxxxxx`是token
   - 获取Sheet ID (sheet_id)
     - 可以在表格设置中找到，或者从URL中的片段获取
3. 将这些值填入`.env`文件中对应的配置项中

## 使用示例

配置完成后，您可以使用以下命令将数据保存到飞书：

```bash
# 将GitHub仓库数据保存到飞书
python run.py github --url https://github.com/username/repo --save-to-feishu

# 将网站数据保存到飞书
python run.py website --url https://example.com --save-to-feishu

# 同时爬取并保存到飞书
python run.py all --github_url https://github.com/username/repo --website_url https://example.com --save-to-feishu
```

您也可以运行示例脚本：

```bash
python examples/feishu_export_example.py
``` 