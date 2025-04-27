"""
代理管理模块 - 负责管理和验证HTTP代理
"""
import time
import random
import logging
import threading
import requests
from typing import Dict, List, Optional, Tuple, Union

# 修改为绝对导入
from utils.log.logger import get_logger

# 获取日志记录器
logger = get_logger('proxy_manager')


class ProxyManager:
    """代理管理器，管理一组HTTP代理并提供代理轮换"""
    
    def __init__(self, test_url: str = 'https://httpbin.org/ip'):
        """
        初始化代理管理器
        
        Args:
            test_url: 用于测试代理有效性的URL
        """
        self.test_url = test_url
        self.proxies: List[Dict[str, str]] = []
        self.working_proxies: List[Dict[str, str]] = []
        self.lock = threading.Lock()
        self.current_proxy_index = 0
        self.last_proxy_check = 0
        
    def add_proxy(self, proxy: Union[Dict[str, str], str]) -> bool:
        """
        添加代理到管理器并验证其可用性
        
        Args:
            proxy: 代理配置，可以是字典形式 {'http': 'http://host:port', 'https': 'https://host:port'}
                  或字符串形式 'http://host:port'
                  
        Returns:
            bool: 代理是否添加成功
        """
        # 如果是字符串形式，转换为字典
        if isinstance(proxy, str):
            proxy_dict = {'http': proxy, 'https': proxy}
        else:
            proxy_dict = proxy
            
        # 验证代理是否有效
        if self._test_proxy(proxy_dict):
            with self.lock:
                # 避免重复添加
                if proxy_dict not in self.proxies:
                    self.proxies.append(proxy_dict)
                    self.working_proxies.append(proxy_dict)
                    logger.info(f"成功添加代理: {proxy_dict}")
                    return True
        else:
            logger.warning(f"代理无效，未添加: {proxy_dict}")
            
        return False
        
    def add_proxies(self, proxies: List[Union[Dict[str, str], str]]) -> int:
        """
        批量添加代理
        
        Args:
            proxies: 代理列表
            
        Returns:
            int: 成功添加的代理数量
        """
        success_count = 0
        for proxy in proxies:
            if self.add_proxy(proxy):
                success_count += 1
                
        logger.info(f"批量添加代理完成，成功: {success_count}/{len(proxies)}")
        return success_count
        
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """
        获取一个可用的代理
        
        Returns:
            Optional[Dict[str, str]]: 代理配置或None（如果没有可用代理）
        """
        self._refresh_proxies_if_needed()
        
        with self.lock:
            if not self.working_proxies:
                return None
                
            # 循环使用代理
            proxy = self.working_proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.working_proxies)
            return proxy
            
    def remove_proxy(self, proxy: Dict[str, str]) -> None:
        """
        从管理器中移除代理
        
        Args:
            proxy: 要移除的代理
        """
        with self.lock:
            if proxy in self.proxies:
                self.proxies.remove(proxy)
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
                # 重置索引以避免越界
                if self.working_proxies:
                    self.current_proxy_index = self.current_proxy_index % len(self.working_proxies)
                else:
                    self.current_proxy_index = 0
                    
            logger.info(f"已移除代理: {proxy}")
            
    def _test_proxy(self, proxy: Dict[str, str]) -> bool:
        """
        测试代理是否有效
        
        Args:
            proxy: 要测试的代理
            
        Returns:
            bool: 代理是否有效
        """
        try:
            response = requests.get(
                self.test_url,
                proxies=proxy,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"代理测试失败: {proxy}, 错误: {e}")
            return False
            
    def _refresh_proxies_if_needed(self, force: bool = False) -> None:
        """
        定期刷新代理列表，检查代理可用性
        
        Args:
            force: 是否强制刷新
        """
        current_time = time.time()
        # 每30分钟或强制刷新时检查一次
        if force or (current_time - self.last_proxy_check > 1800):  
            logger.debug("刷新代理列表...")
            with self.lock:
                self.working_proxies = []
                for proxy in self.proxies:
                    if self._test_proxy(proxy):
                        self.working_proxies.append(proxy)
                    else:
                        logger.warning(f"代理已失效: {proxy}")
                
                # 重置索引
                if self.working_proxies:
                    self.current_proxy_index = 0
                    
                self.last_proxy_check = current_time
                logger.info(f"代理刷新完成，当前可用代理: {len(self.working_proxies)}/{len(self.proxies)}")
                
    def load_proxies_from_file(self, file_path: str) -> int:
        """
        从文件加载代理列表
        
        Args:
            file_path: 代理列表文件路径，每行一个代理地址
            
        Returns:
            int: 成功加载的代理数量
        """
        proxies = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and not proxy.startswith('#'):
                        proxies.append(proxy)
                        
            return self.add_proxies(proxies)
        except Exception as e:
            logger.error(f"从文件加载代理失败: {e}")
            return 0
            
    def get_stats(self) -> Tuple[int, int]:
        """
        获取代理统计信息
        
        Returns:
            Tuple[int, int]: (总代理数, 可用代理数)
        """
        return len(self.proxies), len(self.working_proxies)


# 创建全局代理管理器实例
proxy_manager = ProxyManager()


def get_proxy_manager() -> ProxyManager:
    """获取代理管理器单例实例"""
    return proxy_manager 