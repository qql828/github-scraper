#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GitHub 项目信息爬取工具主程序

此程序用于爬取 GitHub 项目信息并保存到 Excel 文件中。
用户只需输入 GitHub 仓库的 URL，工具会自动抓取相关信息并保存。
"""

import argparse
import sys
import logging
import time
import os
from github_scraper import GitHubScraper
from excel_handler import ExcelHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

def parse_arguments():
    """
    解析命令行参数
    
    返回:
        argparse.Namespace: 包含解析后参数的对象
    """
    parser = argparse.ArgumentParser(
        description="GitHub 项目信息爬取工具",
        epilog="示例: python main.py --url https://github.com/username/repo"
    )
    
    parser.add_argument(
        "--url", 
        type=str, 
        help="GitHub 仓库 URL"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="github项目.xlsx", 
        help="输出 Excel 文件路径 (默认: github项目.xlsx)"
    )
    
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="列出已爬取的所有仓库信息"
    )
    
    parser.add_argument(
        "--refresh", 
        action="store_true", 
        help="刷新已爬取的所有仓库信息"
    )
    
    return parser.parse_args()

def refresh_all_repos(excel_handler, delay=1):
    """
    刷新所有已爬取的仓库信息
    
    参数:
        excel_handler: Excel 处理器实例
        delay: 请求间隔延迟(秒)，避免触发 GitHub 限制
    
    返回:
        bool: 操作是否成功
    """
    # 获取所有仓库
    repos = excel_handler.get_all_repos()
    if not repos:
        print("暂无爬取记录，Excel 文件为空或不存在。")
        return False
    
    # 检查文件是否可写（提前检查避免浪费时间）
    try:
        with open(excel_handler.excel_path, 'a+b') as f:
            f.seek(0, os.SEEK_END)  # 移动到文件末尾
    except (IOError, PermissionError):
        print(f"错误: 无法写入 Excel 文件，可能原因如下:")
        print(f"  1. Excel 文件 '{excel_handler.excel_path}' 正在被其他程序（如 Microsoft Excel）打开")
        print(f"  2. 您没有文件的写入权限")
        print(f"\n解决方法:")
        print(f"  1. 关闭所有可能正在使用该 Excel 文件的程序")
        print(f"  2. 检查文件是否设置为只读，或尝试以管理员身份运行程序")
        return False
    
    print(f"\n开始刷新所有仓库信息 (共 {len(repos)} 个)...")
    
    # 初始化爬虫
    scraper = GitHubScraper()
    
    # 记录成功和失败的数量
    success_count = 0
    fail_count = 0
    
    # 遍历所有仓库并刷新
    for i, repo in enumerate(repos, 1):
        repo_url = repo['repo_url']
        print(f"[{i}/{len(repos)}] 正在刷新: {repo['repo_name']} ({repo_url})")
        
        # 爬取最新信息
        new_info = scraper.extract_repo_info(repo_url)
        
        if new_info:
            # README 内容已在爬取时截断，无需再次处理
            
            # 更新仓库信息
            if excel_handler.update_repo_info(repo_url, new_info):
                success_count += 1
                print(f"  ✓ 成功更新: ⭐ {new_info['star_count']} | 🍴 {new_info['fork_count']} | ⚠️ {new_info['issue_count']}")
            else:
                fail_count += 1
                print(f"  ✗ 更新失败: 无法写入 Excel 文件，可能被其他程序占用")
        else:
            fail_count += 1
            print(f"  ✗ 更新失败: 无法获取仓库最新信息，请检查网络连接")
        
        # 添加延迟，避免触发 GitHub 限制
        if i < len(repos):
            time.sleep(delay)
    
    if fail_count > 0:
        print(f"\n刷新完成，但有部分失败! 成功: {success_count}, 失败: {fail_count}")
        if fail_count == len(repos):
            print("所有仓库都刷新失败，请检查网络连接或 Excel 文件是否可写。")
    else:
        print(f"\n刷新完成! 所有 {success_count} 个仓库都成功更新。")
    
    return success_count > 0

def list_repos(excel_handler):
    """
    列出已爬取的所有仓库信息
    
    参数:
        excel_handler: Excel 处理器实例
    """
    repos = excel_handler.get_all_repos()
    if not repos:
        print("暂无爬取记录，Excel 文件为空或不存在。")
        return
    
    print(f"\n已爬取的 GitHub 仓库列表 (共 {len(repos)} 个):")
    print("-" * 60)
    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo['repo_name']} - {repo['repo_url']}")
        print(f"   描述: {repo['description'][:50]}{'...' if len(repo['description']) > 50 else ''}")
        print(f"   统计: ⭐ {repo['star_count']} | 🍴 {repo['fork_count']} | ⚠️ {repo['issue_count']}")
        print("-" * 60)

def main():
    """主程序入口"""
    args = parse_arguments()
    
    # 初始化 Excel 处理器
    excel_handler = ExcelHandler(args.output)
    
    # 如果用户请求刷新所有仓库
    if args.refresh:
        refresh_all_repos(excel_handler)
        return
    
    # 如果用户请求列出已爬取的仓库
    if args.list:
        list_repos(excel_handler)
        return
    
    # 如果未提供 URL 参数，则进入交互式循环
    if not args.url:
        print("欢迎使用 GitHub 项目信息爬取工具！")
        print("- 输入 GitHub 仓库 URL 来爬取项目信息")
        print("- 输入 'refresh' 刷新所有已爬取的仓库信息")
        print("- 输入 'list' 查看已爬取的仓库列表")
        print("- 输入 'delete 仓库名称' 删除指定仓库的信息")
        print("- 输入 'exit' 退出程序")
        print("=" * 60)
        
        while True:
            user_input = input("\n请输入命令: ").strip()
            
            if not user_input:
                continue
                
            # 检查是否是退出命令
            if user_input.lower() == 'exit':
                print("感谢使用，再见！")
                return
            
            # 检查是否是刷新命令
            if user_input.lower() == 'refresh':
                refresh_all_repos(excel_handler)
                continue
            
            # 检查是否是列表命令
            if user_input.lower() == 'list':
                list_repos(excel_handler)
                continue
                
            # 检查是否是删除命令
            if user_input.lower().startswith('delete '):
                # 提取仓库名称
                repo_name = user_input[7:].strip()
                if not repo_name:
                    print("错误: 请提供要删除的仓库名称")
                    continue
                
                # 确认删除操作
                confirm = input(f"确定要删除仓库 '{repo_name}' 的信息吗？(y/n): ").strip().lower()
                if confirm != 'y' and confirm != 'yes':
                    print("已取消删除操作")
                    continue
                
                # 删除仓库信息
                if excel_handler.delete_repo(repo_name):
                    print(f"成功删除仓库 '{repo_name}' 的信息")
                else:
                    # 检查错误类型并提供详细的错误信息
                    print(f"删除失败: 可能原因如下:")
                    print(f"  1. 未找到名为 '{repo_name}' 的仓库")
                    print(f"  2. Excel 文件 '{args.output}' 正在被其他程序（如 Microsoft Excel）打开")
                    print(f"  3. 您没有文件的写入权限")
                    print(f"\n解决方法:")
                    print(f"  1. 检查仓库名称是否正确，可使用 'list' 命令查看所有仓库")
                    print(f"  2. 关闭所有可能正在使用该 Excel 文件的程序")
                    print(f"  3. 检查文件是否设置为只读，或尝试以管理员身份运行程序")
                continue
            
            # 否则视为仓库 URL
            repo_url = user_input
            
            # 验证 URL 不为空
            if not repo_url:
                continue
            
            # 初始化爬虫并提取信息
            scraper = GitHubScraper()
            print(f"开始爬取仓库: {repo_url}")
            repo_info = scraper.extract_repo_info(repo_url)
            
            if repo_info:
                # 保存到 Excel
                if excel_handler.save_repo_info(repo_info):
                    print(f"成功爬取并保存仓库信息: {repo_info['repo_name']}")
                    print(f"数据已保存到: {args.output}")
                else:
                    print("保存数据失败，请检查日志获取详细信息。")
            else:
                print("爬取仓库信息失败，请检查 URL 是否正确或网络连接是否正常。")
    else:
        # 命令行模式，处理单个 URL
        repo_url = args.url
        
        # 初始化爬虫并提取信息
        scraper = GitHubScraper()
        print(f"开始爬取仓库: {repo_url}")
        repo_info = scraper.extract_repo_info(repo_url)
        
        if repo_info:
            # 保存到 Excel
            if excel_handler.save_repo_info(repo_info):
                print(f"成功爬取并保存仓库信息: {repo_info['repo_name']}")
                print(f"数据已保存到: {args.output}")
            else:
                print("保存数据失败，请检查日志获取详细信息。")
        else:
            print("爬取仓库信息失败，请检查 URL 是否正确或网络连接是否正常。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.exception("程序运行时发生未处理的异常")
        print(f"错误: {e}")
        sys.exit(1)