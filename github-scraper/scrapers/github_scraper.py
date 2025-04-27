"""
GitHub爬虫模块 - 负责爬取GitHub仓库信息
"""
import re
import time
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from bs4 import BeautifulSoup
import pandas as pd
import github
from github import Github

# 修改为相对导入
from .base_scraper import BaseScraper
# 修改为绝对导入
from utils import get_logger, get_config
from utils.feishu_manager import FeishuManager

# 获取日志记录器
logger = get_logger('github_scraper')


class GitHubScraper(BaseScraper):
    """GitHub仓库信息爬虫类"""
    
    def __init__(self, use_proxy: bool = None, max_threads: int = None):
        """
        初始化GitHub爬虫
        
        Args:
            use_proxy: 是否使用代理，None表示使用配置文件设置
            max_threads: 最大线程数，None表示使用配置文件设置
        """
        super().__init__(use_proxy, max_threads)
        self.github_client = None
        self._init_github_client()
    
    def _init_github_client(self) -> None:
        """初始化GitHub API客户端"""
        token = self.config.github_token
        if token:
            try:
                self.github_client = Github(token)
                logger.info("GitHub API客户端初始化成功")
            except Exception as e:
                logger.error(f"GitHub API客户端初始化失败: {e}")
                self.github_client = None
        else:
            logger.warning("未提供GitHub Token，API访问可能受限")
            self.github_client = Github()
    
    def scrape_repo(self, repo_url: str) -> Dict[str, Any]:
        """
        爬取单个GitHub仓库信息
        
        Args:
            repo_url: GitHub仓库URL
            
        Returns:
            Dict[str, Any]: 仓库信息，包含URL、名称、README、Star数等
        """
        try:
            logger.info(f"开始爬取仓库: {repo_url}")
            
            # 解析URL，提取用户名和仓库名
            owner, repo_name = self._parse_github_url(repo_url)
            if not owner or not repo_name:
                logger.error(f"无效的GitHub仓库URL: {repo_url}")
                return {}
                
            repo_info = {
                'repository_url': repo_url,
                'repository_name': f"{owner}/{repo_name}",
            }
            
            # 通过API获取信息（如果有GitHub Token）
            if self.github_client:
                api_info = self._get_repo_info_from_api(owner, repo_name)
                repo_info.update(api_info)
            else:
                # 无API访问权限，使用网页爬虫
                html_info = self._get_repo_info_from_html(repo_url)
                repo_info.update(html_info)
                
            logger.info(f"仓库爬取成功: {repo_url}")
            return repo_info
            
        except Exception as e:
            logger.error(f"爬取仓库信息失败: {repo_url}, 错误: {e}")
            return {'repository_url': repo_url, 'error': str(e)}
    
    def scrape_repos(self, repo_urls: List[str], show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        爬取多个GitHub仓库信息
        
        Args:
            repo_urls: GitHub仓库URL列表
            show_progress: 是否显示进度条
            
        Returns:
            List[Dict[str, Any]]: 仓库信息列表
        """
        return self.scrape_urls(repo_urls, self.scrape_repo, show_progress, "GitHub仓库爬取")
    
    def _parse_github_url(self, url: str) -> Tuple[str, str]:
        """
        解析GitHub URL，提取用户名和仓库名
        
        Args:
            url: GitHub仓库URL
            
        Returns:
            Tuple[str, str]: (用户名, 仓库名)，如果解析失败则返回空字符串
        """
        # 匹配形如 https://github.com/user/repo 的URL
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, url)
        
        if match:
            owner = match.group(1)
            repo_name = match.group(2)
            # 移除可能的.git后缀
            repo_name = repo_name.replace('.git', '')
            return owner, repo_name
        
        return '', ''
    
    def _get_repo_info_from_api(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """
        通过GitHub API获取仓库信息
        
        Args:
            owner: 仓库所有者
            repo_name: 仓库名称
            
        Returns:
            Dict[str, Any]: 仓库信息
        """
        try:
            # 获取仓库信息
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            
            # 提取所需信息
            info = {
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'last_updated': repo.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'language': repo.language or '',
                'license': repo.license.name if repo.license else '',
                'issues': repo.open_issues_count,
                'description': repo.description or '',  # 添加仓库描述
            }
            
            # 尝试获取README内容
            try:
                readme = repo.get_readme()
                info['readme'] = readme.decoded_content.decode('utf-8')
            except github.GithubException:
                logger.warning(f"无法获取 {owner}/{repo_name} 的README")
                info['readme'] = ''
            
            # 获取贡献者数量
            try:
                contributors = list(repo.get_contributors())
                info['contributors'] = len(contributors)
            except github.GithubException:
                logger.warning(f"无法获取 {owner}/{repo_name} 的贡献者信息")
                info['contributors'] = 0
                
            return info
            
        except github.GithubException as e:
            logger.error(f"GitHub API错误: {e}")
            # 出现API错误，尝试使用网页爬虫作为备选方案
            return self._get_repo_info_from_html(f"https://github.com/{owner}/{repo_name}")
        except Exception as e:
            logger.error(f"获取仓库API信息出错: {e}")
            return {}
    
    def _get_repo_info_from_html(self, repo_url: str) -> Dict[str, Any]:
        """
        通过网页爬虫获取仓库信息
        
        Args:
            repo_url: 仓库URL
            
        Returns:
            Dict[str, Any]: 仓库信息
        """
        try:
            response = self.get(repo_url, headers={'User-Agent': 'GitHub-Scraper'})
            soup = BeautifulSoup(response.text, 'lxml')
            
            info = {}
            
            # 获取仓库描述
            desc_elem = soup.select_one('p[class*="f4"]')  # GitHub的仓库描述通常在带f4类的p标签中
            if desc_elem:
                info['description'] = desc_elem.text.strip()
            
            # 获取Star数量
            star_elem = soup.select_one('a[href$="/stargazers"]')
            if star_elem:
                star_text = star_elem.text.strip()
                info['stars'] = self._parse_count(star_text)
            
            # 获取Fork数量
            fork_elem = soup.select_one('a[href$="/network/members"]')
            if fork_elem:
                fork_text = fork_elem.text.strip()
                info['forks'] = self._parse_count(fork_text)
            
            # 获取Issue数量
            issues_elem = soup.select_one('a[href$="/issues"]')
            if issues_elem:
                issues_text = issues_elem.text.strip()
                info['issues'] = self._parse_count(issues_text)
            
            # 获取最近更新时间
            time_elem = soup.select_one('relative-time')
            if time_elem:
                info['last_updated'] = time_elem.get('datetime', '')
            
            # 获取主要语言
            lang_elem = soup.select_one('span[itemprop="programmingLanguage"]')
            if lang_elem:
                info['language'] = lang_elem.text.strip()
            
            # 获取许可证
            license_elem = soup.select_one('a[href$="/blob/master/LICENSE"]')
            if license_elem:
                info['license'] = license_elem.text.strip()
            
            # 获取贡献者数量
            contributors_link = soup.select_one('a[href$="/graphs/contributors"]')
            if contributors_link:
                info['contributors'] = self._get_contributors_count(repo_url)
            
            # 获取README内容
            readme_elem = soup.select_one('#readme')
            if readme_elem:
                readme_content = readme_elem.select_one('article')
                if readme_content:
                    info['readme'] = readme_content.get_text(separator='\n')
            
            return info
            
        except Exception as e:
            logger.error(f"从HTML获取仓库信息失败: {e}")
            return {}
    
    def _get_contributors_count(self, repo_url: str) -> int:
        """
        获取仓库贡献者数量
        
        Args:
            repo_url: 仓库URL
            
        Returns:
            int: 贡献者数量
        """
        try:
            contributors_url = f"{repo_url}/graphs/contributors"
            response = self.get(contributors_url, headers={'User-Agent': 'GitHub-Scraper'})
            
            soup = BeautifulSoup(response.text, 'lxml')
            contributors = soup.select('.authors-list .contributions h3')
            
            return len(contributors)
        except Exception as e:
            logger.error(f"获取贡献者数量失败: {e}")
            return 0
    
    def _parse_count(self, count_text: str) -> int:
        """
        解析计数文本，如"1.2k"转为1200
        
        Args:
            count_text: 计数文本
            
        Returns:
            int: 解析后的整数
        """
        try:
            count_text = count_text.strip()
            if 'k' in count_text.lower():
                return int(float(count_text.lower().replace('k', '')) * 1000)
            elif 'm' in count_text.lower():
                return int(float(count_text.lower().replace('m', '')) * 1000000)
            else:
                return int(float(count_text))
        except (ValueError, TypeError):
            return 0
    
    def _process_large_text_fields(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理可能包含大量文本的字段，避免Excel文件和飞书表格超出大小限制
        
        Args:
            data: 仓库数据列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的数据列表
        """
        # Excel单元格大小限制约为32,767字符
        # 飞书单元格大小限制为50,000字节
        max_excel_chars = 30000  # 为安全起见，设置为30,000字符
        max_feishu_bytes = 45000  # 为安全起见，设置为45,000字节
        
        processed_data = []
        for repo in data:
            processed_repo = repo.copy()
            
            # 处理readme字段
            if 'readme' in processed_repo and processed_repo['readme']:
                readme = processed_repo['readme']
                if isinstance(readme, str):
                    # 检查字符长度(Excel限制)
                    if len(readme) > max_excel_chars:
                        truncated = readme[:max_excel_chars]
                        processed_repo['readme'] = truncated + "\n... (由于长度限制，内容已截断)"
                        logger.info(f"README已截断为{max_excel_chars}字符，原始长度: {len(readme)}字符")
                    
                    # 检查字节大小(飞书限制)
                    byte_size = len(readme.encode('utf-8'))
                    if byte_size > max_feishu_bytes:
                        truncated = readme
                        while len(truncated.encode('utf-8')) > max_feishu_bytes:
                            truncated = truncated[:int(len(truncated)*0.9)]  # 每次截断10%
                        processed_repo['readme'] = truncated + "\n... (由于大小限制，内容已截断)"
                        logger.info(f"README已截断为适合飞书表格大小，原始大小: {byte_size}字节")
            
            # 处理description字段
            if 'description' in processed_repo and processed_repo['description']:
                desc = processed_repo['description']
                if isinstance(desc, str):
                    # 检查字符长度(Excel限制)
                    if len(desc) > max_excel_chars:
                        truncated = desc[:max_excel_chars]
                        processed_repo['description'] = truncated + "... (由于长度限制，内容已截断)"
                        logger.info(f"描述已截断为{max_excel_chars}字符，原始长度: {len(desc)}字符")
                    
                    # 检查字节大小(飞书限制)
                    byte_size = len(desc.encode('utf-8'))
                    if byte_size > max_feishu_bytes:
                        truncated = desc
                        while len(truncated.encode('utf-8')) > max_feishu_bytes:
                            truncated = truncated[:int(len(truncated)*0.9)]  # 每次截断10%
                        processed_repo['description'] = truncated + "... (由于大小限制，内容已截断)"
                        logger.info(f"描述已截断为适合飞书表格大小，原始大小: {byte_size}字节")
            
            processed_data.append(processed_repo)
        
        return processed_data
    
    def export_to_excel(self, repo_data: List[Dict[str, Any]], output_file: str = 'github_repos.xlsx') -> str:
        """
        将爬取结果导出到Excel
        
        Args:
            repo_data: 仓库数据列表
            output_file: 输出文件路径
            
        Returns:
            str: 输出文件路径
        """
        try:
            if not repo_data:
                logger.error("没有数据需要导出到Excel")
                return ""
            
            # 处理大文本字段
            processed_repo_data = self._process_large_text_fields(repo_data)
                
            # 打印数据字段以进行调试
            print("\n爬取的GitHub数据字段:")
            for i, repo in enumerate(processed_repo_data):
                print(f"\n仓库 {i+1} ({repo.get('repository_name', 'unknown')}):")
                for key, value in repo.items():
                    if key == 'readme':
                        value_str = f"{value[:50]}..." if value else "空"
                    else:
                        value_str = str(value)
                    print(f"  - {key}: {value_str}")
            
            # 创建DataFrame
            new_df = pd.DataFrame(processed_repo_data)
            
            # 打印DataFrame信息用于调试
            logger.info(f"待导出数据的DataFrame行数: {len(new_df)}, 列: {list(new_df.columns)}")
            
            # 整理列顺序
            columns = [
                'repository_url', 'repository_name', 'description', 'stars', 'forks', 
                'last_updated', 'language', 'license', 'contributors', 'issues', 'readme'
            ]
            
            # 只保留存在的列
            columns = [col for col in columns if col in new_df.columns]
            new_df = new_df[columns]
            
            # 确保repository_url列存在，这是去重的关键
            if 'repository_url' not in new_df.columns:
                logger.error("待导出数据中没有repository_url列，无法进行去重")
                return ""
                
            # 检查文件是否已存在
            if os.path.exists(output_file):
                try:
                    # 读取现有文件
                    existing_df = pd.read_excel(output_file)
                    logger.info(f"成功读取现有Excel文件, 行数: {len(existing_df)}")
                    
                    # 确保现有数据中有repository_url列
                    if 'repository_url' not in existing_df.columns:
                        logger.warning("现有Excel文件中没有repository_url列，无法进行去重，将使用新数据创建文件")
                        new_df.to_excel(output_file, index=False)
                        logger.info(f"数据已保存到: {output_file}")
                        return output_file
                    
                    # 记录更新前的行数
                    original_count = len(existing_df)
                    
                    # 记录每个URL是否已处理
                    processed_urls = set()
                    updated_count = 0
                    new_count = 0
                    
                    # 一次处理一行数据，确保不重复添加
                    for _, row in new_df.iterrows():
                        url = row['repository_url']
                        
                        # 跳过已处理的URL
                        if url in processed_urls:
                            logger.warning(f"跳过重复URL: {url}")
                            continue
                            
                        # 标记为已处理
                        processed_urls.add(url)
                        
                        # 查找是否已存在相同URL的仓库
                        same_url_rows = existing_df[existing_df['repository_url'] == url]
                        
                        if not same_url_rows.empty:
                            # 如果已存在，则更新该行
                            for idx in same_url_rows.index:
                                for col in new_df.columns:
                                    if col in existing_df.columns:
                                        existing_df.at[idx, col] = row[col]
                            logger.info(f"更新已存在的仓库: {url}")
                            updated_count += 1
                        else:
                            # 如果不存在，则添加新行
                            existing_df = pd.concat([existing_df, pd.DataFrame([row])], ignore_index=True)
                            logger.info(f"添加新的仓库: {url}")
                            new_count += 1
                    
                    # 记录操作统计
                    logger.info(f"Excel操作统计: 原有数据 {original_count} 行, 更新 {updated_count} 行, 新增 {new_count} 行")
                    
                    # 保存合并后的数据
                    existing_df.to_excel(output_file, index=False)
                    logger.info(f"数据已更新到: {output_file}, 当前共 {len(existing_df)} 行")
                    
                    # 验证写入
                    try:
                        verify_df = pd.read_excel(output_file)
                        logger.info(f"验证文件: 成功读取 {len(verify_df)} 行数据")
                        if len(verify_df) == 0:
                            logger.error("文件写入失败: 文件存在但不包含数据")
                            # 尝试直接强制写入
                            new_df.to_excel(output_file, index=False)
                            logger.info("尝试强制写入新数据")
                            
                            # 再次验证
                            verify_df = pd.read_excel(output_file)
                            logger.info(f"再次验证: 读取到 {len(verify_df)} 行数据")
                    except Exception as e:
                        logger.error(f"验证文件时出错: {e}")
                        
                except Exception as e:
                    logger.warning(f"读取现有Excel文件失败: {e}，将创建新文件")
                    new_df.to_excel(output_file, index=False)
                    logger.info(f"数据已保存到新文件: {output_file}")
            else:
                # 文件不存在，直接创建新文件
                new_df.to_excel(output_file, index=False)
                logger.info(f"数据已保存到新文件: {output_file} (共 {len(new_df)} 行)")
                
            # 返回输出文件路径
            return output_file
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # 尝试备选方案保存
            try:
                temp_file = f"{output_file}.backup"
                new_df.to_excel(temp_file, index=False)
                logger.info(f"已保存到备份文件: {temp_file}")
                return temp_file
            except:
                return ""
            
    def export_to_feishu(self, repo_data: List[Dict[str, Any]]) -> bool:
        """
        将爬取结果导出到飞书电子表格
        
        Args:
            repo_data: 仓库数据列表
            
        Returns:
            bool: 是否成功导出
        """
        try:
            # 检查数据
            if not repo_data:
                logger.error("没有数据可以导出到飞书")
                return False
            
            # 处理大文本字段
            processed_repo_data = self._process_large_text_fields(repo_data)
                
            # 创建DataFrame
            df = pd.DataFrame(processed_repo_data)
            
            # 整理列顺序
            columns = [
                'repository_url', 'repository_name', 'description', 'stars', 'forks', 
                'last_updated', 'language', 'license', 'contributors', 'issues', 'readme'
            ]
            
            # 只保留存在的列
            columns = [col for col in columns if col in df.columns]
            df = df[columns]
            
            # 初始化飞书管理器
            feishu_manager = FeishuManager()
            
            # 尝试读取现有数据
            existing_df = feishu_manager.read_github_data()
            
            if existing_df is not None and not existing_df.empty:
                # 检查是否为相同的仓库URL，避免重复
                for _, row in df.iterrows():
                    # 查找是否已存在相同URL的仓库
                    if 'repository_url' in row and 'repository_url' in existing_df.columns:
                        same_url_rows = existing_df[existing_df['repository_url'] == row['repository_url']]
                        
                        if not same_url_rows.empty:
                            # 如果已存在，则更新该行
                            for idx in same_url_rows.index:
                                for col in df.columns:
                                    if col in existing_df.columns:
                                        existing_df.at[idx, col] = row[col]
                            logger.info(f"更新飞书表格中已存在的仓库: {row['repository_url']}")
                        else:
                            # 如果不存在，则添加新行
                            existing_df = pd.concat([existing_df, pd.DataFrame([row])], ignore_index=True)
                            logger.info(f"添加新的仓库到飞书表格: {row['repository_url']}")
                
                # 将更新后的数据写入飞书
                result = feishu_manager.write_github_data(existing_df)
            else:
                # 直接写入新数据
                result = feishu_manager.write_github_data(df)
                
            if result:
                logger.info("GitHub仓库数据成功导出到飞书")
                return True
            else:
                logger.error("GitHub仓库数据导出到飞书失败")
                return False
                
        except Exception as e:
            logger.error(f"导出到飞书失败: {e}")
            return False 