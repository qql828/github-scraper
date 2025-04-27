"""
配置管理模块 - 负责读取和管理配置文件
"""
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """配置管理类，用于加载和管理环境变量和配置信息"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化配置，加载环境变量"""
        if self._initialized:
            return
            
        # 加载.env文件
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(env_path)
        
        # GitHub 配置
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        
        # 代理配置
        self.use_proxy = self._parse_bool(os.getenv('USE_PROXY', 'False'))
        self.http_proxy = os.getenv('HTTP_PROXY', '')
        self.https_proxy = os.getenv('HTTPS_PROXY', '')
        
        # 请求配置
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        
        # 爬虫配置
        self.max_threads = int(os.getenv('MAX_THREADS', '5'))
        self.request_delay = float(os.getenv('REQUEST_DELAY', '1.0'))
        
        # 飞书应用配置
        self.feishu_app_id = os.getenv('FEISHU_APP_ID', '')
        self.feishu_app_secret = os.getenv('FEISHU_APP_SECRET', '')
        
        # 飞书电子表格配置
        self.feishu_github_spreadsheet_token = os.getenv('FEISHU_GITHUB_SPREADSHEET_TOKEN', '')
        self.feishu_github_sheet_id = os.getenv('FEISHU_GITHUB_SHEET_ID', '')
        self.feishu_website_spreadsheet_token = os.getenv('FEISHU_WEBSITE_SPREADSHEET_TOKEN', '')
        self.feishu_website_sheet_id = os.getenv('FEISHU_WEBSITE_SHEET_ID', '')
        
        # 其他设置
        self.auto_save_to_feishu = self._parse_bool(os.getenv('AUTO_SAVE_TO_FEISHU', 'False'))
        
        self._initialized = True
        logger.info("配置已加载")
    
    def _parse_bool(self, value: str) -> bool:
        """解析字符串布尔值"""
        return value.lower() in ('true', 'yes', '1', 't', 'y')
    
    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """获取代理配置字典，用于requests库"""
        if not self.use_proxy:
            return None
            
        proxies = {}
        if self.http_proxy:
            proxies['http'] = self.http_proxy
        if self.https_proxy:
            proxies['https'] = self.https_proxy
        
        return proxies if proxies else None
    
    def get_github_headers(self) -> Dict[str, str]:
        """获取GitHub API请求头"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Scraper'
        }
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
            
        return headers
    
    def get_feishu_config(self) -> Dict[str, str]:
        """获取飞书API配置"""
        return {
            'app_id': self.feishu_app_id,
            'app_secret': self.feishu_app_secret
        }
    
    def get_feishu_github_sheet_config(self) -> Dict[str, str]:
        """获取飞书GitHub数据表格配置"""
        return {
            'spreadsheet_token': self.feishu_github_spreadsheet_token,
            'sheet_id': self.feishu_github_sheet_id
        }
    
    def get_feishu_website_sheet_config(self) -> Dict[str, str]:
        """获取飞书网站数据表格配置"""
        return {
            'spreadsheet_token': self.feishu_website_spreadsheet_token,
            'sheet_id': self.feishu_website_sheet_id
        }
    
    def update_config(self, **kwargs) -> bool:
        """更新配置值"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"配置项 {key} 已更新为 {value}")
            else:
                logger.warning(f"未知配置项: {key}")
        return True
    
    def validate(self) -> bool:
        """验证配置有效性"""
        # 检查GitHub token是否设置（针对GitHub爬虫）
        if not self.github_token:
            logger.warning("GitHub Token未设置，API请求可能受限")
        
        # 检查代理配置是否一致
        if self.use_proxy and not (self.http_proxy or self.https_proxy):
            logger.warning("启用了代理但未提供代理服务器地址")
        
        # 检查飞书配置是否设置
        if not (self.feishu_app_id and self.feishu_app_secret):
            logger.warning("飞书应用凭证未设置，飞书API功能将无法使用")
            
        return True


# 创建全局配置实例
config = Config()


def get_config() -> Config:
    """获取配置单例实例"""
    return config


def update_config(data: Dict[str, Any]) -> bool:
    """
    更新系统配置并保存到.env文件
    
    :param data: 包含配置项的字典
    :return: 是否成功更新
    """
    try:
        # 获取配置实例
        config_instance = get_config()
        
        # 需要更新到.env文件的配置项映射
        env_mappings = {
            'github_token': 'GITHUB_TOKEN',
            'use_proxy': 'USE_PROXY',
            'http_proxy': 'HTTP_PROXY',
            'https_proxy': 'HTTPS_PROXY',
            'request_timeout': 'REQUEST_TIMEOUT',
            'max_retries': 'MAX_RETRIES',
            'retry_delay': 'RETRY_DELAY',
            'max_threads': 'MAX_THREADS',
            'request_delay': 'REQUEST_DELAY',
            'feishu_app_id': 'FEISHU_APP_ID',
            'feishu_app_secret': 'FEISHU_APP_SECRET',
            'feishu_github_spreadsheet_token': 'FEISHU_GITHUB_SPREADSHEET_TOKEN',
            'feishu_github_sheet_id': 'FEISHU_GITHUB_SHEET_ID',
            'feishu_website_spreadsheet_token': 'FEISHU_WEBSITE_SPREADSHEET_TOKEN',
            'feishu_website_sheet_id': 'FEISHU_WEBSITE_SHEET_ID',
            'auto_save_to_feishu': 'AUTO_SAVE_TO_FEISHU'
        }
        
        # 更新内存中的配置
        update_dict = {}
        for key, value in data.items():
            if hasattr(config_instance, key):
                update_dict[key] = value
        
        # 如果没有任何有效配置，直接返回
        if not update_dict:
            logger.warning("没有有效的配置项需要更新")
            return False
        
        # 更新内存中的配置实例
        config_instance.update_config(**update_dict)
        
        # 更新.env文件
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        
        # 读取现有的.env文件内容
        env_content = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # 更新配置值
        for key, value in update_dict.items():
            if key in env_mappings:
                env_key = env_mappings[key]
                # 将布尔值转换为字符串
                if isinstance(value, bool):
                    env_content[env_key] = str(value)
                else:
                    env_content[env_key] = str(value)
        
        # 写回.env文件
        with open(env_path, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        logger.info("系统配置已更新并保存到.env文件")
        return True
        
    except Exception as e:
        logger.error(f"更新系统配置失败: {e}")
        return False


def update_feishu_config(
    app_id: str = None,
    app_secret: str = None,
    github_spreadsheet_token: str = None,
    github_sheet_id: str = None,
    website_spreadsheet_token: str = None,
    website_sheet_id: str = None
) -> bool:
    """
    更新飞书配置并保存到.env文件
    
    :param app_id: 飞书应用ID
    :param app_secret: 飞书应用密钥
    :param github_spreadsheet_token: GitHub数据电子表格Token
    :param github_sheet_id: GitHub数据工作表ID
    :param website_spreadsheet_token: 网站数据电子表格Token
    :param website_sheet_id: 网站数据工作表ID
    :return: 是否成功更新
    """
    try:
        # 获取配置实例
        config_instance = get_config()
        
        # 更新内存中的配置
        update_dict = {}
        if app_id is not None and app_id.strip():
            update_dict['feishu_app_id'] = app_id.strip()
        
        if app_secret is not None and app_secret.strip():
            update_dict['feishu_app_secret'] = app_secret.strip()
            
        if github_spreadsheet_token is not None and github_spreadsheet_token.strip():
            update_dict['feishu_github_spreadsheet_token'] = github_spreadsheet_token.strip()
            
        if github_sheet_id is not None and github_sheet_id.strip():
            update_dict['feishu_github_sheet_id'] = github_sheet_id.strip()
            
        if website_spreadsheet_token is not None and website_spreadsheet_token.strip():
            update_dict['feishu_website_spreadsheet_token'] = website_spreadsheet_token.strip()
            
        if website_sheet_id is not None and website_sheet_id.strip():
            update_dict['feishu_website_sheet_id'] = website_sheet_id.strip()
        
        # 更新内存中的配置实例
        config_instance.update_config(**update_dict)
        
        # 更新.env文件
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        
        # 读取现有的.env文件内容
        env_content = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # 更新配置值
        if 'feishu_app_id' in update_dict:
            env_content['FEISHU_APP_ID'] = update_dict['feishu_app_id']
            
        if 'feishu_app_secret' in update_dict:
            env_content['FEISHU_APP_SECRET'] = update_dict['feishu_app_secret']
            
        if 'feishu_github_spreadsheet_token' in update_dict:
            env_content['FEISHU_GITHUB_SPREADSHEET_TOKEN'] = update_dict['feishu_github_spreadsheet_token']
            
        if 'feishu_github_sheet_id' in update_dict:
            env_content['FEISHU_GITHUB_SHEET_ID'] = update_dict['feishu_github_sheet_id']
            
        if 'feishu_website_spreadsheet_token' in update_dict:
            env_content['FEISHU_WEBSITE_SPREADSHEET_TOKEN'] = update_dict['feishu_website_spreadsheet_token']
            
        if 'feishu_website_sheet_id' in update_dict:
            env_content['FEISHU_WEBSITE_SHEET_ID'] = update_dict['feishu_website_sheet_id']
        
        # 写回.env文件
        with open(env_path, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        logger.info("飞书配置已更新并保存到.env文件")
        return True
        
    except Exception as e:
        logger.error(f"更新飞书配置失败: {e}")
        return False 