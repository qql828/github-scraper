#!/usr/bin/env python3
"""
GitHub和网站信息爬取工具启动脚本
"""
import sys
import os
import re

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入主模块
from main import main
from utils.excel_manager import delete_url

def is_github_url(url):
    """
    判断是否为GitHub仓库URL
    """
    # 去除前缀，简化比较
    url = url.lower().strip()
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    if url.startswith('www.'):
        url = url[4:]
        
    # 检查是否为github.com域名
    return url.startswith('github.com/') and '/' in url.split('github.com/')[1]

def is_website_url(url):
    """
    判断是否为一般网站URL
    """
    pattern = r'^https?://(?:www\.)?(?!github\.com)[^/]+\.[^/]+/?.*$'
    return bool(re.match(pattern, url))

def auto_detect_url(url, extra_args=None):
    """
    自动检测URL类型，执行对应的爬取命令
    
    Args:
        url: 要检测的URL
        extra_args: 额外的命令行参数列表
    
    Returns:
        bool: 是否成功识别并设置参数
    """
    # 设置数据文件夹路径
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # 确保文件夹存在
    os.makedirs(data_dir, exist_ok=True)
    
    if is_github_url(url):
        # GitHub仓库URL
        github_output = os.path.join(data_dir, 'github.xlsx')
        print(f"检测到GitHub仓库URL: {url}")
        print(f"将爬取GitHub仓库信息并保存到 {github_output}")
        new_argv = ['run.py', 'github', '--url', url, '--output', github_output]
        
        # 添加额外参数
        if extra_args:
            new_argv.extend(extra_args)
            
        sys.argv = new_argv
    
    elif is_website_url(url):
        # 一般网站URL
        website_output = os.path.join(data_dir, 'website.xlsx')
        print(f"检测到网站URL: {url}")
        print(f"将爬取网站信息并保存到 {website_output}")
        new_argv = ['run.py', 'website', '--url', url, '--output', website_output]
        
        # 添加额外参数
        if extra_args:
            new_argv.extend(extra_args)
            
        sys.argv = new_argv
    
    else:
        print(f"无法识别的URL格式: {url}")
        print("URL格式应为: https://github.com/用户名/仓库名 或 https://example.com")
        return False
    
    return True

def handle_delete_command(url):
    """
    处理删除URL命令
    
    Args:
        url: 要删除的URL
        
    Returns:
        bool: 是否执行成功
    """
    if not url:
        print("错误: 未提供URL")
        print("用法: python run.py delete url <URL>")
        return False
    
    # 执行删除操作
    success, message = delete_url(url)
    
    if success:
        print(f"删除成功: {message}")
    else:
        print(f"删除失败: {message}")
    
    return success

def show_help():
    """
    显示帮助信息
    """
    print("GitHub和网站信息爬取工具")
    print("=" * 30)
    print("\n使用方法:")
    print("  1. 智能URL识别模式:")
    print("     python run.py <URL>")
    print("     例如: python run.py https://github.com/microsoft/vscode")
    print("     例如: python run.py https://python.org")
    print("\n     * GitHub仓库信息会自动保存到 data/github.xlsx")
    print("     * 网站信息会自动保存到 data/website.xlsx")
    print("     * 支持增量更新，同一URL信息会更新而不是重复添加")
    print("\n  2. 命令行模式:")
    print("     python run.py github --url <URL> [--output <FILE>]")
    print("     python run.py website --url <URL> [--output <FILE>]")
    print("     python run.py github --file <FILE_WITH_URLS> [--output <FILE>]")
    print("\n  3. 删除URL记录:")
    print("     python run.py delete url <URL>")
    print("     例如: python run.py delete url https://github.com/microsoft/vscode")
    print("     例如: python run.py delete url https://python.org")
    print("\n更多详细信息:")
    print("  python run.py github --help")
    print("  python run.py website --help")
    print("  python run.py all --help")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 显示帮助信息
        show_help()
        sys.exit(0)
        
    elif len(sys.argv) >= 3 and sys.argv[1] == "delete" and sys.argv[2] == "url":
        # 处理删除URL命令
        if len(sys.argv) < 4:
            print("错误: 未提供URL")
            print("用法: python run.py delete url <URL>")
            sys.exit(1)
        
        # 获取URL并执行删除
        url_to_delete = sys.argv[3]
        success = handle_delete_command(url_to_delete)
        sys.exit(0 if success else 1)
        
    elif len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
        # 如果第一个参数不是命令选项，则视为URL
        url = sys.argv[1]
        
        # 收集额外的参数
        extra_args = []
        if len(sys.argv) > 2:
            extra_args = sys.argv[2:]
        
        # 尝试自动识别URL类型并执行相应的爬取命令
        if not auto_detect_url(url, extra_args):
            sys.exit(1)
    
    # 继续执行原始的main函数
    main() 