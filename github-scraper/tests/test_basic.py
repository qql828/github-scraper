"""
基本功能测试模块
"""
import unittest
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import get_config
from utils.log import get_logger
from scrapers import GitHubScraper, WebsiteScraper


class TestBasicFunctionality(unittest.TestCase):
    """基本功能测试类"""
    
    def test_config_loading(self):
        """测试配置加载"""
        config = get_config()
        self.assertIsNotNone(config)
        self.assertTrue(hasattr(config, 'github_token'))
        self.assertTrue(hasattr(config, 'max_threads'))
        
    def test_logger_creation(self):
        """测试日志记录器创建"""
        logger = get_logger('test')
        self.assertIsNotNone(logger)
        
    def test_github_scraper_init(self):
        """测试GitHub爬虫初始化"""
        scraper = GitHubScraper(use_proxy=False)
        self.assertIsNotNone(scraper)
        
    def test_website_scraper_init(self):
        """测试网站爬虫初始化"""
        scraper = WebsiteScraper(use_proxy=False)
        self.assertIsNotNone(scraper)
        
    def test_github_url_parsing(self):
        """测试GitHub URL解析"""
        scraper = GitHubScraper(use_proxy=False)
        test_url = "https://github.com/microsoft/vscode"
        owner, repo = scraper._parse_github_url(test_url)
        self.assertEqual(owner, "microsoft")
        self.assertEqual(repo, "vscode")


if __name__ == '__main__':
    unittest.main()


 