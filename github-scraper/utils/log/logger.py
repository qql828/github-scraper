"""
日志模块 - 负责配置和管理日志记录
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# 默认日志格式
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# 默认日期格式
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
# 默认日志目录
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')


def setup_logger(
    name: str = 'github_scraper',
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console: bool = True,
    format_str: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT
) -> logging.Logger:
    """
    设置并返回一个日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径，如果为None则自动生成
        max_size: 每个日志文件的最大大小
        backup_count: 保留的日志文件数量
        console: 是否在控制台输出日志
        format_str: 日志格式
        date_format: 日期格式
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    formatter = logging.Formatter(format_str, date_format)
    
    # 如果没有指定日志文件，则使用默认路径
    if log_file is None:
        # 确保日志目录存在
        os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)
        log_file = os.path.join(DEFAULT_LOG_DIR, f'{name}.log')
    
    # 添加文件处理器
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"无法创建日志文件处理器: {e}\n")
    
    # 添加控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = 'github_scraper') -> logging.Logger:
    """
    获取一个已配置的日志记录器，如果不存在则创建一个默认的
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    logger = logging.getLogger(name)
    
    # 如果还没有配置处理器，则设置一个默认的
    if not logger.handlers:
        return setup_logger(name)
        
    return logger 