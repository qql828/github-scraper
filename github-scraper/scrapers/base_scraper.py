"""
爬虫基类 - 为不同类型的爬虫提供通用功能
"""
import time
import random
import threading
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# 修改为绝对导入
from utils import get_config, get_logger
from utils.proxy import get_proxy_manager

# 获取日志记录器
logger = get_logger('base_scraper')


class BaseScraper:
    """爬虫基类，提供基础爬取功能和错误处理"""
    
    def __init__(self, use_proxy: bool = None, max_threads: int = None):
        """
        初始化爬虫
        
        Args:
            use_proxy: 是否使用代理，None表示使用配置文件设置
            max_threads: 最大线程数，None表示使用配置文件设置
        """
        self.config = get_config()
        self.proxy_manager = get_proxy_manager()
        
        # 如果显式指定了参数，则覆盖配置文件的设置
        self.use_proxy = use_proxy if use_proxy is not None else self.config.use_proxy
        self.max_threads = max_threads if max_threads is not None else self.config.max_threads
        
        # 请求会话，可以复用连接
        self._session = requests.Session()
        
        # 用于控制并发请求的信号量
        self._request_semaphore = threading.Semaphore(self.max_threads)
        
        logger.info(f"初始化爬虫，线程数: {self.max_threads}, 使用代理: {self.use_proxy}")
        
    def get(self, url: str, headers: Optional[Dict[str, str]] = None, 
            params: Optional[Dict[str, Any]] = None, 
            timeout: Optional[int] = None) -> requests.Response:
        """
        发送GET请求并自动处理重试、代理等逻辑
        
        Args:
            url: 请求URL
            headers: 请求头
            params: URL参数
            timeout: 超时时间（秒）
            
        Returns:
            Response: 请求响应对象
            
        Raises:
            requests.RequestException: 请求失败且重试耗尽时抛出
        """
        return self._request('GET', url, headers, params=params, timeout=timeout)
    
    def post(self, url: str, headers: Optional[Dict[str, str]] = None,
             data: Optional[Dict[str, Any]] = None, 
             json: Optional[Dict[str, Any]] = None,
             timeout: Optional[int] = None) -> requests.Response:
        """
        发送POST请求并自动处理重试、代理等逻辑
        
        Args:
            url: 请求URL
            headers: 请求头
            data: 表单数据
            json: JSON数据
            timeout: 超时时间（秒）
            
        Returns:
            Response: 请求响应对象
            
        Raises:
            requests.RequestException: 请求失败且重试耗尽时抛出
        """
        return self._request('POST', url, headers, data=data, json=json, timeout=timeout)
    
    def _request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                 params: Optional[Dict[str, Any]] = None, 
                 data: Optional[Dict[str, Any]] = None,
                 json: Optional[Dict[str, Any]] = None,
                 timeout: Optional[int] = None) -> requests.Response:
        """
        发送HTTP请求并处理重试、代理等逻辑
        
        Args:
            method: 请求方法（GET、POST等）
            url: 请求URL
            headers: 请求头
            params: URL参数
            data: 表单数据
            json: JSON数据
            timeout: 超时时间（秒）
            
        Returns:
            Response: 请求响应对象
            
        Raises:
            requests.RequestException: 请求失败且重试耗尽时抛出
        """
        timeout = timeout or self.config.request_timeout
        max_retries = self.config.max_retries
        retry_delay = self.config.retry_delay
        
        proxies = None
        if self.use_proxy:
            proxies = self.proxy_manager.get_proxy()
            if proxies:
                logger.debug(f"使用代理: {proxies}")
        
        # 限制并发请求数
        with self._request_semaphore:
            for retry in range(max_retries + 1):
                try:
                    # 添加随机延迟，避免请求过于集中
                    if retry > 0 or self.config.request_delay > 0:
                        delay = self.config.request_delay
                        if retry > 0:
                            # 指数退避策略，随着重试次数增加延迟时间
                            delay = retry_delay * (2 ** (retry - 1))
                        # 添加少量随机性，避免请求完全同步
                        time.sleep(delay + random.uniform(0, 0.5))
                    
                    response = self._session.request(
                        method,
                        url,
                        headers=headers,
                        params=params,
                        data=data,
                        json=json,
                        proxies=proxies,
                        timeout=timeout
                    )
                    
                    # 检查响应状态码，处理常见错误
                    if response.status_code == 429:  # Too Many Requests
                        logger.warning(f"请求频率限制: {url}, 将在{retry_delay}秒后重试")
                        time.sleep(retry_delay)
                        continue
                    
                    response.raise_for_status()
                    return response
                    
                except requests.RequestException as e:
                    # 最后一次重试失败，抛出异常
                    if retry >= max_retries:
                        logger.error(f"请求失败: {url}, 错误: {e}, 重试耗尽")
                        raise
                    
                    # 如果使用代理且失败，尝试更换代理
                    if self.use_proxy and proxies:
                        logger.warning(f"代理请求失败，尝试更换代理: {proxies}")
                        proxies = self.proxy_manager.get_proxy()
                    
                    logger.warning(f"请求失败: {url}, 错误: {e}, 将在{retry_delay}秒后重试 ({retry+1}/{max_retries})")
                    time.sleep(retry_delay)
    
    def scrape_urls(self, urls: List[str], 
                   scrape_func: callable, 
                   show_progress: bool = True, 
                   desc: str = "爬取进度") -> List[Dict[str, Any]]:
        """
        并发爬取多个URL
        
        Args:
            urls: 要爬取的URL列表
            scrape_func: 爬取函数，接收URL参数并返回爬取结果
            show_progress: 是否显示进度条
            desc: 进度条描述
            
        Returns:
            List[Dict[str, Any]]: 爬取结果列表
        """
        results = []
        errors = []
        
        # 创建进度条
        pbar = tqdm(total=len(urls), desc=desc) if show_progress else None
        
        # 使用线程池并发爬取
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_url = {executor.submit(scrape_func, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"爬取 {url} 时出错: {e}")
                    errors.append((url, str(e)))
                finally:
                    if pbar:
                        pbar.update(1)
        
        if pbar:
            pbar.close()
            
        # 日志记录爬取结果统计
        logger.info(f"爬取完成: {len(results)} 成功, {len(errors)} 失败")
        if errors:
            logger.info(f"失败的URLs: {errors}")
            
        return results
    
    def is_valid_url(self, url: str) -> bool:
        """
        检查URL是否有效
        
        Args:
            url: 要检查的URL
            
        Returns:
            bool: URL是否有效
        """
        try:
            result = requests.head(url, allow_redirects=True, timeout=10)
            return result.status_code < 400
        except Exception as e:
            logger.debug(f"URL有效性检查失败: {url}, 错误: {e}")
            return False 