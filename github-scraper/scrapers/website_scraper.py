"""
网站爬虫模块 - 负责爬取网站基本信息
"""
import re
import os
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import pandas as pd
from bs4 import BeautifulSoup

# 修改为相对导入
from .base_scraper import BaseScraper
# 修改为绝对导入
from utils import get_logger
from utils.feishu_manager import FeishuManager

# 获取日志记录器
logger = get_logger('website_scraper')


class WebsiteScraper(BaseScraper):
    """网站信息爬虫类"""
    
    def __init__(self, use_proxy: bool = None, max_threads: int = None):
        """
        初始化网站爬虫
        
        Args:
            use_proxy: 是否使用代理，None表示使用配置文件设置
            max_threads: 最大线程数，None表示使用配置文件设置
        """
        super().__init__(use_proxy, max_threads)
        
        # 常见联系方式正则表达式
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'(\+\d{1,3})?[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}'
    
    def scrape_website(self, url: str) -> Dict[str, Any]:
        """
        爬取单个网站信息
        
        Args:
            url: 网站URL
            
        Returns:
            Dict[str, Any]: 网站信息，包含URL、标题、描述、关键词等
        """
        try:
            logger.info(f"开始爬取网站: {url}")
            
            # 标准化URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # 获取网站首页
            response = self.get(url, headers={'User-Agent': 'Website-Scraper'})
            
            # 处理重定向
            if response.url != url:
                logger.info(f"URL重定向: {url} -> {response.url}")
                url = response.url
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 基本信息
            website_info = {
                'website_url': url,
                'title': self._get_title(soup),
                'description': self._get_meta_content(soup, 'description'),
                'keywords': self._get_meta_content(soup, 'keywords'),
                'favicon': self._get_favicon(soup, url),
            }
            
            # 提取主要链接
            links = self._extract_links(soup, url)
            website_info['main_links'] = '\n'.join(links[:20]) if links else ''
            
            # 提取联系方式
            contacts = self._extract_contacts(soup, url)
            website_info['contacts'] = '\n'.join(contacts) if contacts else ''
            
            logger.info(f"网站爬取成功: {url}")
            return website_info
            
        except Exception as e:
            logger.error(f"爬取网站信息失败: {url}, 错误: {e}")
            return {'website_url': url, 'error': str(e)}
    
    def scrape_websites(self, website_urls: List[str], show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        爬取多个网站信息
        
        Args:
            website_urls: 网站URL列表
            show_progress: 是否显示进度条
            
        Returns:
            List[Dict[str, Any]]: 网站信息列表
        """
        return self.scrape_urls(website_urls, self.scrape_website, show_progress, "网站爬取")
    
    def _get_title(self, soup: BeautifulSoup) -> str:
        """
        获取网站标题
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 网站标题
        """
        title_tag = soup.find('title')
        return title_tag.text.strip() if title_tag else ''
    
    def _get_meta_content(self, soup: BeautifulSoup, name: str) -> str:
        """
        获取元标签内容
        
        Args:
            soup: BeautifulSoup对象
            name: 元标签名称
            
        Returns:
            str: 元标签内容
        """
        meta_tag = soup.find('meta', attrs={'name': name})
        if not meta_tag:
            meta_tag = soup.find('meta', attrs={'property': f'og:{name}'})
            
        return meta_tag.get('content', '').strip() if meta_tag else ''
    
    def _get_favicon(self, soup: BeautifulSoup, base_url: str) -> str:
        """
        获取网站图标
        
        Args:
            soup: BeautifulSoup对象
            base_url: 网站基础URL
            
        Returns:
            str: 网站图标URL
        """
        # 尝试不同类型的favicon标签
        favicon_link = soup.find('link', rel=lambda r: r and ('icon' in r.lower() or 'shortcut' in r.lower()))
        
        if favicon_link and favicon_link.get('href'):
            favicon_url = favicon_link['href']
            return urljoin(base_url, favicon_url)
        
        # 尝试默认路径
        parsed_url = urlparse(base_url)
        default_favicon = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
        
        try:
            response = self._session.head(default_favicon, timeout=5)
            if response.status_code == 200:
                return default_favicon
        except Exception:
            pass
            
        return ''
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str, max_links: int = 30) -> List[str]:
        """
        提取网站主要链接
        
        Args:
            soup: BeautifulSoup对象
            base_url: 网站基础URL
            max_links: 最大链接数量
            
        Returns:
            List[str]: 链接列表
        """
        links = set()
        base_domain = urlparse(base_url).netloc
        
        # 获取所有a标签
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
                
            # 将相对URL转为绝对URL
            absolute_url = urljoin(base_url, href)
            
            # 只保留同域名的链接
            parsed = urlparse(absolute_url)
            if parsed.netloc == base_domain:
                # 规范化URL并添加到集合
                normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if len(normalized_url) < 255:  # 避免过长的URL
                    links.add(normalized_url)
                    
            if len(links) >= max_links:
                break
                
        return list(links)
    
    def _extract_contacts(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        提取网站联系方式
        
        Args:
            soup: BeautifulSoup对象
            base_url: 网站基础URL
            
        Returns:
            List[str]: 联系方式列表
        """
        contacts = set()
        
        # 尝试从页面内容提取邮箱
        page_text = soup.get_text()
        emails = re.findall(self.email_pattern, page_text)
        for email in emails:
            contacts.add(f"Email: {email}")
            
        # 尝试从页面内容提取电话号码
        phones = re.findall(self.phone_pattern, page_text)
        for phone in phones:
            contacts.add(f"Phone: {phone}")
            
        # 尝试从联系页面提取更多信息
        contact_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().lower()
            if ('contact' in text or 'about' in text) and href:
                contact_links.append(urljoin(base_url, href))
                
        # 访问联系页面查找更多联系方式
        for link in contact_links[:2]:  # 限制只查看前2个可能的联系页面
            try:
                response = self.get(link, headers={'User-Agent': 'Website-Scraper'}, timeout=10)
                contact_soup = BeautifulSoup(response.text, 'lxml')
                
                # 提取联系页面的邮箱和电话
                page_text = contact_soup.get_text()
                emails = re.findall(self.email_pattern, page_text)
                for email in emails:
                    contacts.add(f"Email: {email}")
                    
                phones = re.findall(self.phone_pattern, page_text)
                for phone in phones:
                    contacts.add(f"Phone: {phone}")
            except Exception as e:
                logger.debug(f"访问联系页面失败: {link}, 错误: {e}")
                
        return list(contacts)
    
    def _process_large_text_fields(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理可能包含大量文本的字段，避免Excel文件和飞书表格超出大小限制
        
        Args:
            data: 网站数据列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的数据列表
        """
        # Excel单元格大小限制约为32,767字符
        # 飞书单元格大小限制为50,000字节
        max_excel_chars = 30000  # 为安全起见，设置为30,000字符
        max_feishu_bytes = 45000  # 为安全起见，设置为45,000字节
        
        processed_data = []
        for website in data:
            processed_site = website.copy()
            
            # 处理大文本字段列表
            large_text_fields = ['text_content', 'meta_description', 'description', 'content', 'seo_text']
            
            for field in large_text_fields:
                if field in processed_site and processed_site[field]:
                    text = processed_site[field]
                    if isinstance(text, str):
                        # 检查字符长度(Excel限制)
                        if len(text) > max_excel_chars:
                            truncated = text[:max_excel_chars]
                            processed_site[field] = truncated + "\n... (由于长度限制，内容已截断)"
                            logger.info(f"{field}已截断为{max_excel_chars}字符，原始长度: {len(text)}字符")
                        
                        # 检查字节大小(飞书限制)
                        byte_size = len(text.encode('utf-8'))
                        if byte_size > max_feishu_bytes:
                            truncated = text
                            while len(truncated.encode('utf-8')) > max_feishu_bytes:
                                truncated = truncated[:int(len(truncated)*0.9)]  # 每次截断10%
                            processed_site[field] = truncated + "\n... (由于大小限制，内容已截断)"
                            logger.info(f"{field}已截断为适合飞书表格大小，原始大小: {byte_size}字节")
            
            processed_data.append(processed_site)
        
        return processed_data
    
    def export_to_excel(self, website_data: List[Dict[str, Any]], output_file: str = 'websites.xlsx') -> str:
        """
        将爬取结果导出到Excel
        
        Args:
            website_data: 网站数据列表
            output_file: 输出文件路径
            
        Returns:
            str: 输出文件路径
        """
        try:
            if not website_data:
                logger.error("没有数据需要导出到Excel")
                return ""
            
            # 处理大文本字段
            processed_website_data = self._process_large_text_fields(website_data)
                
            # 打印数据字段以进行调试
            print("\n爬取的网站数据字段:")
            for i, site in enumerate(processed_website_data):
                print(f"\n网站 {i+1} ({site.get('website_url', 'unknown')}):")
                for key, value in site.items():
                    if key in ['text_content', 'meta_description']:
                        value_str = f"{value[:50]}..." if value else "空"
                    else:
                        value_str = str(value)
                    print(f"  - {key}: {value_str}")
            
            # 创建DataFrame
            new_df = pd.DataFrame(processed_website_data)
            
            # 整理列顺序
            columns = [
                'website_url', 'title', 'description', 'keywords',
                'favicon', 'main_links', 'contacts'
            ]
            
            # 只保留存在的列
            columns = [col for col in columns if col in new_df.columns]
            new_df = new_df[columns]
            
            # 检查文件是否已存在
            if os.path.exists(output_file):
                try:
                    # 尝试读取现有文件
                    existing_df = pd.read_excel(output_file)
                    
                    # 检查是否为相同的网站URL，避免重复
                    for _, row in new_df.iterrows():
                        # 查找是否已存在相同URL的网站
                        if 'website_url' in row and 'website_url' in existing_df.columns:
                            same_url_rows = existing_df[existing_df['website_url'] == row['website_url']]
                            
                            if not same_url_rows.empty:
                                # 如果已存在，则更新该行
                                for idx in same_url_rows.index:
                                    for col in new_df.columns:
                                        if col in existing_df.columns:
                                            existing_df.at[idx, col] = row[col]
                                logger.info(f"更新已存在的网站: {row['website_url']}")
                            else:
                                # 如果不存在，则添加新行
                                existing_df = pd.concat([existing_df, pd.DataFrame([row])], ignore_index=True)
                                logger.info(f"添加新的网站: {row['website_url']}")
                    
                    # 保存合并后的数据
                    existing_df.to_excel(output_file, index=False)
                    logger.info(f"数据已更新到: {output_file}")
                    
                except Exception as e:
                    logger.warning(f"读取现有Excel文件失败: {e}，将创建新文件")
                    new_df.to_excel(output_file, index=False)
                    logger.info(f"数据已保存到新文件: {output_file}")
            else:
                # 文件不存在，直接创建新文件
                new_df.to_excel(output_file, index=False)
                logger.info(f"数据已保存到: {output_file}")
                
            return output_file
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return ""
            
    def export_to_feishu(self, website_data: List[Dict[str, Any]]) -> bool:
        """
        将爬取结果导出到飞书电子表格
        
        Args:
            website_data: 网站数据列表
            
        Returns:
            bool: 是否成功导出
        """
        try:
            # 检查数据
            if not website_data:
                logger.error("没有数据可以导出到飞书")
                return False
            
            # 处理大文本字段
            processed_website_data = self._process_large_text_fields(website_data)
                
            # 创建DataFrame
            df = pd.DataFrame(processed_website_data)
            
            # 整理列顺序
            columns = [
                'website_url', 'title', 'description', 'keywords',
                'favicon', 'main_links', 'contacts'
            ]
            
            # 只保留存在的列
            columns = [col for col in columns if col in df.columns]
            df = df[columns]
            
            # 初始化飞书管理器
            feishu_manager = FeishuManager()
            
            # 尝试读取现有数据
            existing_df = feishu_manager.read_website_data()
            
            if existing_df is not None and not existing_df.empty:
                # 检查是否为相同的网站URL，避免重复
                for _, row in df.iterrows():
                    # 查找是否已存在相同URL的网站
                    if 'website_url' in row and 'website_url' in existing_df.columns:
                        same_url_rows = existing_df[existing_df['website_url'] == row['website_url']]
                        
                        if not same_url_rows.empty:
                            # 如果已存在，则更新该行
                            for idx in same_url_rows.index:
                                for col in df.columns:
                                    if col in existing_df.columns:
                                        existing_df.at[idx, col] = row[col]
                            logger.info(f"更新飞书表格中已存在的网站: {row['website_url']}")
                        else:
                            # 如果不存在，则添加新行
                            existing_df = pd.concat([existing_df, pd.DataFrame([row])], ignore_index=True)
                            logger.info(f"添加新的网站到飞书表格: {row['website_url']}")
                
                # 将更新后的数据写入飞书
                result = feishu_manager.write_website_data(existing_df)
            else:
                # 直接写入新数据
                result = feishu_manager.write_website_data(df)
                
            if result:
                logger.info("网站数据成功导出到飞书")
                return True
            else:
                logger.error("网站数据导出到飞书失败")
                return False
                
        except Exception as e:
            logger.error(f"导出到飞书失败: {e}")
            return False 