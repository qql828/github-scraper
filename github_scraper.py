#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GitHub 数据爬取模块

此模块负责从 GitHub 仓库 URL 中提取各种信息，如仓库名称、描述、Star 数等。
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_scraper')

class GitHubScraper:
    """GitHub 数据爬取类，用于从 GitHub 仓库 URL 中提取信息"""
    
    def __init__(self):
        """初始化爬虫，设置 headers 等"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    def validate_url(self, url: str) -> bool:
        """
        验证输入的 URL 是否为有效的 GitHub 仓库链接
        
        参数:
            url: 需要验证的 GitHub 仓库 URL
            
        返回:
            bool: URL 是否有效
        """
        pattern = r'^https?://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9._-]+/?$'
        return bool(re.match(pattern, url))
    
    def extract_repo_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从 GitHub 仓库 URL 中提取仓库信息
        
        参数:
            url: GitHub 仓库 URL
            
        返回:
            Dict 或 None: 包含仓库信息的字典，如果提取失败则返回 None
        """
        # 验证 URL
        if not self.validate_url(url):
            logger.error(f"无效的 GitHub 仓库 URL: {url}")
            return None
        
        try:
            # 发送请求获取页面内容
            logger.info(f"开始爬取 GitHub 仓库: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取仓库名称
            repo_name = url.strip('/').split('/')[-1]
            
            # 提取仓库描述
            description_tag = soup.select_one('p[itemprop="description"]')
            if not description_tag:
                # 尝试其他可能的选择器
                description_tag = soup.select_one('.f4.my-3')
                if not description_tag:
                    description_tag = soup.select_one('p.col-9.color-fg-muted.my-1.pr-4')
            
            description = description_tag.text.strip() if description_tag else "无描述"
            
            # 提取 Star 数量
            star_tag = soup.select_one('a[href*="stargazers"]')
            star_count = star_tag.text.strip() if star_tag else "0"
            
            # 提取 Fork 数量
            fork_tag = soup.select_one('a[href*="forks"]')
            fork_count = fork_tag.text.strip() if fork_tag else "0"
            
            # 提取 Issue 数量
            issue_tag = soup.select_one('a[href*="issues"]')
            issue_count = issue_tag.text.strip() if issue_tag else "0"
            
            # 提取 README 内容 - 使用多种选择器尝试获取
            readme_content = "无 README 内容"
            
            # 尝试方法1 - 主要选择器
            readme_tag = soup.select_one('#readme article')
            if readme_tag:
                readme_content = readme_tag.text.strip()
            
            # 尝试方法2 - 备选选择器
            if readme_content == "无 README 内容":
                readme_tag = soup.select_one('.markdown-body')
                if readme_tag:
                    readme_content = readme_tag.text.strip()
            
            # 尝试方法3 - 获取 README 文件内容
            if readme_content == "无 README 内容":
                readme_url = f"{url}/raw/master/README.md"
                try:
                    readme_response = requests.get(readme_url, headers=self.headers, timeout=10)
                    if readme_response.status_code == 200:
                        readme_content = readme_response.text
                except:
                    # 如果直接访问 README 失败，尝试访问主分支 main
                    try:
                        readme_url = f"{url}/raw/main/README.md"
                        readme_response = requests.get(readme_url, headers=self.headers, timeout=10)
                        if readme_response.status_code == 200:
                            readme_content = readme_response.text
                    except:
                        logger.warning(f"无法获取 README 文件内容: {url}")
            
            # 限制 README 内容长度，避免过长
            if len(readme_content) > 5000:
                readme_content = readme_content[:5000] + "...(内容已截断)"
            
            # 清理数字
            star_count = self._clean_count(star_count)
            fork_count = self._clean_count(fork_count)
            issue_count = self._clean_count(issue_count)
            
            # 构建结果字典
            repo_info = {
                'repo_url': url,
                'repo_name': repo_name,
                'description': description,
                'star_count': star_count,
                'fork_count': fork_count,
                'issue_count': issue_count,
                'readme_content': readme_content
            }
            
            logger.info(f"成功爬取仓库信息: {repo_name}")
            return repo_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None
        except Exception as e:
            logger.error(f"提取仓库信息时发生错误: {e}")
            return None
    
    def _clean_count(self, count_str: str) -> int:
        """
        清理数字字符串，转换为整数
        
        参数:
            count_str: 包含数字的字符串，可能有 "k", "m" 等单位
            
        返回:
            int: 转换后的整数
        """
        try:
            # 移除所有非数字、点和单位的字符
            cleaned = re.sub(r'[^\d.km]', '', count_str.lower())
            
            # 转换 k 和 m 单位
            if 'k' in cleaned:
                return int(float(cleaned.replace('k', '')) * 1000)
            elif 'm' in cleaned:
                return int(float(cleaned.replace('m', '')) * 1000000)
            else:
                return int(float(cleaned)) if cleaned else 0
        except:
            return 0