# 使用示例

本目录包含两个示例文件：
- `github_repos.txt`: GitHub仓库URL列表
- `websites.txt`: 网站URL列表

## 爬取GitHub仓库示例

```bash
# 从文件批量爬取
python ../main.py github --file github_repos.txt --output github_results.xlsx

# 爬取单个仓库
python ../main.py github --url https://github.com/microsoft/vscode --output vscode_repo.xlsx
```

## 爬取网站示例

```bash
# 从文件批量爬取
python ../main.py website --file websites.txt --output website_results.xlsx

# 爬取单个网站
python ../main.py website --url https://www.python.org --output python_site.xlsx
```

## 同时爬取GitHub和网站

```bash
# 同时爬取单个GitHub仓库和网站
python ../main.py all --github_url https://github.com/microsoft/vscode --website_url https://www.python.org

# 同时爬取多个GitHub仓库和网站
python ../main.py all --github_file github_repos.txt --website_file websites.txt
```

## 使用代理示例

```bash
# 使用单个代理爬取
python ../main.py github --file github_repos.txt --proxy http://proxy_host:proxy_port

# 使用代理文件爬取
python ../main.py website --file websites.txt --proxy_file proxies.txt
```

## 其他参数示例

```bash
# 设置线程数和超时时间
python ../main.py github --file github_repos.txt --threads 10 --timeout 30

# 开启详细日志
python ../main.py website --url https://www.python.org --verbose
``` 