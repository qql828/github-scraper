"""
Excel文件管理模块 - 提供Excel文件操作功能
"""
import os
import logging
import re
import pandas as pd
from typing import Optional, List, Tuple, Union

from utils import get_logger
from utils.feishu_manager import FeishuManager

# 获取日志记录器
logger = get_logger('excel_manager')

def delete_url_from_excel(url: str, excel_file: str) -> Tuple[bool, str]:
    """
    从Excel文件中删除指定URL对应的记录
    
    Args:
        url: 要删除的URL
        excel_file: Excel文件路径
    
    Returns:
        Tuple[bool, str]: (是否成功, 提示信息)
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(excel_file):
            return False, f"文件 {excel_file} 不存在"
        
        # 读取Excel文件
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return False, f"读取Excel文件失败: {e}"
        
        # 检查是否为空DataFrame
        if df.empty:
            return False, f"Excel文件 {excel_file} 没有任何数据"
        
        # 判断URL列名
        url_column = None
        if 'repository_url' in df.columns:
            url_column = 'repository_url'
        elif 'website_url' in df.columns:
            url_column = 'website_url'
        else:
            return False, "无法识别URL列，Excel文件格式不正确"
        
        # 检查URL是否存在
        if url not in df[url_column].values:
            # 输出URL和可用的URL列表，用于调试
            logger.debug(f"要删除的URL: {url}")
            logger.debug(f"文件中的URL列表: {df[url_column].values.tolist()}")
            return False, f"URL '{url}' 不存在于文件中"
        
        # 删除匹配的行
        original_count = len(df)
        df = df[df[url_column] != url]
        deleted_count = original_count - len(df)
        
        # 保存回Excel文件
        df.to_excel(excel_file, index=False)
        
        logger.info(f"已从 {excel_file} 中删除URL: {url}")
        return True, f"成功删除 {deleted_count} 条记录"
        
    except Exception as e:
        logger.error(f"删除URL时出错: {e}")
        return False, f"删除URL时出错: {e}"

def is_github_repo_url(url: str) -> bool:
    """
    判断是否为GitHub仓库URL
    
    Args:
        url: 要判断的URL
        
    Returns:
        bool: 是否为GitHub仓库URL
    """
    # 去除前缀，简化比较
    url = url.lower().strip()
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    if url.startswith('www.'):
        url = url[4:]
        
    # 检查是否为github.com域名，并且有用户名/仓库名格式
    return url.startswith('github.com/') and '/' in url.split('github.com/')[1]

def delete_url(url: str) -> Tuple[bool, str]:
    """
    根据URL类型自动选择删除GitHub仓库还是网站URL，同时删除本地Excel和飞书表格中的数据
    
    Args:
        url: 要删除的URL
    
    Returns:
        Tuple[bool, str]: (是否成功, 提示信息)
    """
    # 设置数据文件夹路径
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    # 检查data目录是否存在
    if not os.path.exists(data_dir):
        return False, "数据目录不存在，请先运行爬取命令"
    
    # 初始化飞书管理器
    feishu_manager = FeishuManager()
    
    # 判断URL类型
    is_github = is_github_repo_url(url)
    logger.info(f"URL类型判断: {url} -> {'GitHub仓库' if is_github else '一般网站'}")
    
    if is_github:
        # GitHub仓库URL
        excel_file = os.path.join(data_dir, 'github.xlsx')
        file_type = "GitHub仓库"
        # 从飞书删除 - 使用新的删除方法
        logger.info(f"开始从飞书表格中删除GitHub仓库: {url}")
        feishu_success = feishu_manager.delete_github_record(url)
    else:
        # 一般网站URL
        excel_file = os.path.join(data_dir, 'website.xlsx')
        file_type = "网站"
        # 从飞书删除 - 使用新的删除方法
        logger.info(f"开始从飞书表格中删除网站: {url}")
        feishu_success = feishu_manager.delete_website_record(url)
    
    # 检查对应的Excel文件是否存在
    if not os.path.exists(excel_file):
        logger.warning(f"{file_type}数据文件不存在: {excel_file}")
        # 即使本地文件不存在，可能飞书表格中有数据被删除
        if feishu_success:
            return True, f"已从飞书表格中删除{file_type}数据，本地{file_type}数据文件不存在"
        return False, f"{file_type}数据文件不存在，请先爬取{file_type}数据"
    
    # 执行从Excel删除操作
    logger.info(f"开始从Excel文件中删除{file_type}: {url}, 文件路径: {excel_file}")
    excel_success, excel_message = delete_url_from_excel(url, excel_file)
    
    # 根据操作结果返回信息
    if excel_success and feishu_success:
        return True, f"成功从Excel和飞书表格中删除{file_type}数据"
    elif excel_success:
        return True, f"成功从Excel删除{file_type}数据，但从飞书表格删除失败"
    elif feishu_success:
        return True, f"成功从飞书表格删除{file_type}数据，但从Excel删除失败: {excel_message}"
    else:
        return False, f"删除{file_type}数据失败: {excel_message}" 