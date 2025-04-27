#!/usr/bin/env python3
"""
GitHub和网站信息爬取工具 - 主程序入口
"""
import os
import sys
import argparse
import logging
from typing import List, Union, Optional

# 修改为明确的导入路径
from scrapers.github_scraper import GitHubScraper
from scrapers.website_scraper import WebsiteScraper
from utils import get_config, get_logger
from utils.proxy import get_proxy_manager

# 设置日志
logger = get_logger('main')


def read_urls_from_file(file_path: str) -> List[str]:
    """
    从文件中读取URL列表
    
    Args:
        file_path: URL文件路径
        
    Returns:
        List[str]: URL列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        logger.info(f"从文件 {file_path} 中读取了 {len(urls)} 个URL")
        return urls
    except Exception as e:
        logger.error(f"读取URL文件失败: {e}")
        return []


def parse_args():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析结果
    """
    parser = argparse.ArgumentParser(description='GitHub和网站信息爬取工具')
    subparsers = parser.add_subparsers(dest='command', help='爬取命令')
    
    # GitHub爬虫参数
    github_parser = subparsers.add_parser('github', help='爬取GitHub仓库信息')
    github_url_group = github_parser.add_mutually_exclusive_group(required=True)
    github_url_group.add_argument('--url', type=str, help='GitHub仓库URL')
    github_url_group.add_argument('--file', type=str, help='包含GitHub仓库URL的文件路径')
    github_parser.add_argument('--output', type=str, default='github_repos.xlsx', help='输出Excel文件路径')
    github_parser.add_argument('--save-to-feishu', action='store_true', help='将数据保存到飞书电子表格')
    
    # 网站爬虫参数
    website_parser = subparsers.add_parser('website', help='爬取网站信息')
    website_url_group = website_parser.add_mutually_exclusive_group(required=True)
    website_url_group.add_argument('--url', type=str, help='网站URL')
    website_url_group.add_argument('--file', type=str, help='包含网站URL的文件路径')
    website_parser.add_argument('--output', type=str, default='websites.xlsx', help='输出Excel文件路径')
    website_parser.add_argument('--save-to-feishu', action='store_true', help='将数据保存到飞书电子表格')
    
    # 同时爬取GitHub和网站的参数
    all_parser = subparsers.add_parser('all', help='同时爬取GitHub仓库和网站信息')
    all_parser.add_argument('--github_url', type=str, help='GitHub仓库URL')
    all_parser.add_argument('--github_file', type=str, help='包含GitHub仓库URL的文件路径')
    all_parser.add_argument('--website_url', type=str, help='网站URL')
    all_parser.add_argument('--website_file', type=str, help='包含网站URL的文件路径')
    all_parser.add_argument('--github_output', type=str, default='github_repos.xlsx', help='GitHub输出Excel文件路径')
    all_parser.add_argument('--website_output', type=str, default='websites.xlsx', help='网站输出Excel文件路径')
    all_parser.add_argument('--save-to-feishu', action='store_true', help='将数据保存到飞书电子表格')
    
    # 通用参数
    for p in [github_parser, website_parser, all_parser]:
        p.add_argument('--threads', type=int, help='并发线程数')
        p.add_argument('--timeout', type=int, help='请求超时时间（秒）')
        p.add_argument('--retries', type=int, help='失败重试次数')
        p.add_argument('--proxy', type=str, help='使用代理（http://host:port）')
        p.add_argument('--proxy_file', type=str, help='代理列表文件路径')
        p.add_argument('--verbose', action='store_true', help='显示详细日志')
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # 验证all命令至少需要一个GitHub或网站URL源
    if args.command == 'all' and not any([args.github_url, args.github_file, args.website_url, args.website_file]):
        all_parser.error("'all'命令至少需要一个GitHub或网站URL源")
    
    return args


def update_config_from_args(args):
    """
    根据命令行参数更新配置
    
    Args:
        args: 命令行参数
    """
    config = get_config()
    
    # 更新配置
    if hasattr(args, 'threads') and args.threads:
        config.update_config(max_threads=args.threads)
    
    if hasattr(args, 'timeout') and args.timeout:
        config.update_config(request_timeout=args.timeout)
    
    if hasattr(args, 'retries') and args.retries:
        config.update_config(max_retries=args.retries)
    
    if hasattr(args, 'verbose') and args.verbose:
        # 设置更详细的日志级别
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # 处理代理配置
    if hasattr(args, 'proxy') and args.proxy:
        config.update_config(use_proxy=True)
        proxy_manager = get_proxy_manager()
        proxy_manager.add_proxy(args.proxy)
    
    if hasattr(args, 'proxy_file') and args.proxy_file:
        config.update_config(use_proxy=True)
        proxy_manager = get_proxy_manager()
        proxy_manager.load_proxies_from_file(args.proxy_file)


def crawl_github(url: Optional[str] = None, file_path: Optional[str] = None, 
                output: str = 'github_repos.xlsx', save_to_feishu: bool = False):
    """
    爬取GitHub仓库信息
    
    Args:
        url: GitHub仓库URL
        file_path: 包含GitHub仓库URL的文件路径
        output: 输出文件路径
        save_to_feishu: 是否保存到飞书
        
    Returns:
        tuple: (excel输出路径, 飞书导出成功标志)
    """
    scraper = GitHubScraper()
    urls = []
    
    if url:
        urls = [url]
    elif file_path:
        urls = read_urls_from_file(file_path)
    
    if not urls:
        logger.error("没有有效的GitHub仓库URL")
        return None, False
    
    logger.info(f"开始爬取 {len(urls)} 个GitHub仓库")
    results = scraper.scrape_repos(urls)
    
    if not results:
        logger.error("GitHub仓库爬取失败，没有获取到任何数据")
        return None, False
    
    # 保存到Excel
    output_path = scraper.export_to_excel(results, output)
    
    # 如果需要，保存到飞书
    feishu_success = False
    if save_to_feishu:
        feishu_success = scraper.export_to_feishu(results)
        
    return output_path, feishu_success


def crawl_website(url: Optional[str] = None, file_path: Optional[str] = None, 
                 output: str = 'websites.xlsx', save_to_feishu: bool = False):
    """
    爬取网站信息
    
    Args:
        url: 网站URL
        file_path: 包含网站URL的文件路径
        output: 输出文件路径
        save_to_feishu: 是否保存到飞书
        
    Returns:
        tuple: (excel输出路径, 飞书导出成功标志)
    """
    scraper = WebsiteScraper()
    urls = []
    
    if url:
        urls = [url]
    elif file_path:
        urls = read_urls_from_file(file_path)
    
    if not urls:
        logger.error("没有有效的网站URL")
        return None, False
    
    logger.info(f"开始爬取 {len(urls)} 个网站")
    results = scraper.scrape_websites(urls)
    
    if not results:
        logger.error("网站爬取失败，没有获取到任何数据")
        return None, False
    
    # 保存到Excel
    output_path = scraper.export_to_excel(results, output)
    
    # 如果需要，保存到飞书
    feishu_success = False
    if save_to_feishu:
        feishu_success = scraper.export_to_feishu(results)
        
    return output_path, feishu_success


def main():
    """主程序入口"""
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 更新配置
        update_config_from_args(args)
        
        # 根据命令执行对应操作
        if args.command == 'github':
            output_path, feishu_success = crawl_github(
                args.url, 
                args.file, 
                args.output,
                args.save_to_feishu
            )
            
            if output_path:
                print(f"GitHub仓库数据已保存到：{output_path}")
                
            if args.save_to_feishu:
                if feishu_success:
                    print("GitHub仓库数据已成功保存到飞书电子表格")
                else:
                    print("GitHub仓库数据保存到飞书电子表格失败")
                
        elif args.command == 'website':
            output_path, feishu_success = crawl_website(
                args.url, 
                args.file, 
                args.output,
                args.save_to_feishu
            )
            
            if output_path:
                print(f"网站数据已保存到：{output_path}")
                
            if args.save_to_feishu:
                if feishu_success:
                    print("网站数据已成功保存到飞书电子表格")
                else:
                    print("网站数据保存到飞书电子表格失败")
                
        elif args.command == 'all':
            github_output = None
            website_output = None
            github_feishu_success = False
            website_feishu_success = False
            
            # 爬取GitHub仓库
            if args.github_url or args.github_file:
                github_output, github_feishu_success = crawl_github(
                    args.github_url, 
                    args.github_file, 
                    args.github_output,
                    args.save_to_feishu
                )
                
                if github_output:
                    print(f"GitHub仓库数据已保存到：{github_output}")
                    
                if args.save_to_feishu:
                    if github_feishu_success:
                        print("GitHub仓库数据已成功保存到飞书电子表格")
                    else:
                        print("GitHub仓库数据保存到飞书电子表格失败")
            
            # 爬取网站
            if args.website_url or args.website_file:
                website_output, website_feishu_success = crawl_website(
                    args.website_url, 
                    args.website_file, 
                    args.website_output,
                    args.save_to_feishu
                )
                
                if website_output:
                    print(f"网站数据已保存到：{website_output}")
                    
                if args.save_to_feishu:
                    if website_feishu_success:
                        print("网站数据已成功保存到飞书电子表格")
                    else:
                        print("网站数据保存到飞书电子表格失败")
                    
            if not github_output and not website_output:
                logger.error("爬取失败，没有成功保存任何数据")
                
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)


if __name__ == "__main__":
    main() 