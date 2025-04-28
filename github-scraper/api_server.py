#!/usr/bin/env python3
"""
GitHub 爬虫 API 服务器
为前端应用提供 REST API 接口
"""
import os
import sys
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入主模块
from main import main
from utils.excel_manager import delete_url
from scrapers.github_scraper import GitHubScraper
from scrapers.website_scraper import WebsiteScraper
from utils.feishu_manager import FeishuManager
from utils import get_logger

# 配置日志记录器
logger = get_logger('api_server')

# 创建 Flask 应用
app = Flask(__name__, static_folder='frontend/build')

# 配置CORS，允许来自所有前端的请求
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 数据文件夹路径
DATA_DIR = os.path.join(current_dir, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# GitHub 数据文件路径
GITHUB_DATA_FILE = os.path.join(DATA_DIR, 'github.xlsx')
# 网站数据文件路径
WEBSITE_DATA_FILE = os.path.join(DATA_DIR, 'website.xlsx')

# 创建 FeishuManager 实例
try:
    feishu_manager = FeishuManager()
except Exception as e:
    logger.error(f"初始化飞书管理器失败: {e}")
    feishu_manager = None


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    提供前端静态文件服务
    """
    # 如果请求的是具体的静态文件并且存在，直接提供该文件
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    # 如果请求的是API路由，让后续的路由处理
    elif path.startswith('api/'):
        return {"message": "API路径", "path": path}, 404
    # 否则返回index.html以支持前端路由(SPA)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/scrape/github', methods=['POST'])
def scrape_github():
    """
    爬取 GitHub 仓库信息
    """
    try:
        data = request.json
        url = data.get('url')
        
        # 获取配置中的自动保存到飞书设置
        from utils.config import get_config
        config = get_config()
        default_save_to_feishu = config.auto_save_to_feishu
        
        # 如果请求中明确指定了save_to_feishu，则使用请求的值，否则使用系统默认设置
        save_to_feishu = data.get('save_to_feishu', default_save_to_feishu)
        
        if not url:
            return jsonify({'success': False, 'message': '未提供URL'}), 400
        
        # 检查URL是否已经存在于本地Excel表格中
        url_exists_in_excel = False
        try:
            import pandas as pd
            import os
            if os.path.exists(GITHUB_DATA_FILE):
                github_df = pd.read_excel(GITHUB_DATA_FILE)
                if not github_df.empty and 'repository_url' in github_df.columns:
                    url_exists_in_excel = url in github_df['repository_url'].values
                    if url_exists_in_excel:
                        logger.info(f"GitHub仓库URL已存在于本地Excel表格: {url}")
        except Exception as e:
            logger.error(f"检查URL是否存在于本地Excel时出错: {e}")
            
        # 检查URL是否已存在于飞书表格中    
        url_already_exists_in_feishu = False
        if save_to_feishu and feishu_manager:
            try:
                # 检查URL是否存在于飞书表格
                url_already_exists_in_feishu = feishu_manager._url_exists_in_sheet(
                    feishu_manager.github_spreadsheet_token,
                    feishu_manager.github_sheet_id,
                    'repository_url',
                    url
                )
                if url_already_exists_in_feishu:
                    logger.info(f"GitHub仓库URL已存在于飞书表格: {url}")
            except Exception as e:
                logger.error(f"检查GitHub仓库URL是否存在时出错: {e}")
        
        # 如果URL已存在，直接返回提示
        if url_exists_in_excel or url_already_exists_in_feishu:
            return jsonify({
                'success': True,
                'message': '该URL已存在，请勿重复爬取',
                'data': {'repository_url': url},
                'url_exists': True,
                'feishu_skipped': url_already_exists_in_feishu,
                'excel_skipped': url_exists_in_excel
            })
        
        # 创建 GitHub 爬虫实例
        github_scraper = GitHubScraper()
        
        # 爬取仓库信息
        repo_info = github_scraper.scrape_repo(url)
        
        if not repo_info:
            return jsonify({'success': False, 'message': '爬取失败，请检查URL是否正确'}), 400
        
        # 将爬取结果添加到本地 Excel 文件
        output_file = github_scraper.export_to_excel([repo_info], GITHUB_DATA_FILE)
        
        # 检查输出文件是否为临时文件
        file_locked_warning = ""
        if output_file and output_file.endswith('.temp'):
            file_locked_warning = "Excel文件被其他程序占用，数据已保存到临时文件。请关闭打开的Excel后，将临时文件重命名为正式文件。"
            logger.warning(f"Excel文件被锁定，数据保存到临时文件: {output_file}")
        elif not output_file:
            file_locked_warning = "无法保存到Excel文件，可能被其他程序占用或没有写入权限。"
            logger.error("保存到Excel文件失败")
        
        # 如果需要保存到飞书
        feishu_message = ""
        if save_to_feishu and feishu_manager:
            # 检查飞书管理器是否初始化成功
            if not feishu_manager:
                logger.warning("飞书管理器未初始化，无法保存到飞书")
                feishu_message = "飞书同步未启用或未配置"
            else:
                try:
                    # 在开始保存之前再次检查URL是否已存在
                    if feishu_manager._url_exists_in_sheet(
                        feishu_manager.github_spreadsheet_token,
                        feishu_manager.github_sheet_id,
                        'repository_url',
                        url
                    ):
                        # URL已存在，不需要保存
                        logger.info(f"URL已存在于飞书表格中，跳过保存: {url}")
                        feishu_message = "该URL已存在于飞书表格中，无需重复添加"
                    else:
                        # 使用飞书管理器保存数据
                        success = feishu_manager.append_github_data([repo_info])
                        if success:
                            # 再次检查URL是否真的添加到了飞书表格中
                            if feishu_manager._url_exists_in_sheet(
                                feishu_manager.github_spreadsheet_token,
                                feishu_manager.github_sheet_id,
                                'repository_url',
                                url
                            ):
                                # URL成功添加到飞书
                                logger.info(f"成功保存数据到飞书: {url}")
                                feishu_message = "已同步到飞书"
                            else:
                                # 虽然返回成功，但URL不存在，可能因为URL已存在被跳过了
                                logger.warning(f"飞书同步返回成功，但URL不存在于表格中: {url}")
                                feishu_message = "飞书同步状态未知"
                        else:
                            logger.error(f"保存数据到飞书失败: {url}")
                            feishu_message = "同步到飞书失败"
                except Exception as e:
                    logger.error(f"保存数据到飞书时出错: {e}")
                    feishu_message = f"同步到飞书时出错: {str(e)}"
        
        # 构建响应信息
        message = f"GitHub仓库爬取成功"
        if file_locked_warning:
            message += f"，但{file_locked_warning}"
        if feishu_message:
            message += f"。{feishu_message}"
            
        return jsonify({
            'success': True, 
            'message': message,
            'data': {
                'repository_url': repo_info.get('repository_url'),
                'excel_file': output_file,
                'excel_locked': bool(file_locked_warning),
                'feishu_synced': save_to_feishu and feishu_manager and "已同步到飞书" in feishu_message,
                'feishu_skipped': url_already_exists_in_feishu
            }
        })
    
    except Exception as e:
        logger.error(f"爬取GitHub仓库失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'爬取失败: {str(e)}'}), 500


@app.route('/api/scrape/website', methods=['POST'])
def scrape_website():
    """
    爬取网站信息
    """
    try:
        data = request.json
        url = data.get('url')
        
        # 获取配置中的自动保存到飞书设置
        from utils.config import get_config
        config = get_config()
        default_save_to_feishu = config.auto_save_to_feishu
        
        # 如果请求中明确指定了save_to_feishu，则使用请求的值，否则使用系统默认设置
        save_to_feishu = data.get('save_to_feishu', default_save_to_feishu)
        
        if not url:
            return jsonify({'success': False, 'message': '未提供URL'}), 400
        
        # 检查URL是否已经存在于本地Excel表格中
        url_exists_in_excel = False
        try:
            import pandas as pd
            import os
            if os.path.exists(WEBSITE_DATA_FILE):
                website_df = pd.read_excel(WEBSITE_DATA_FILE)
                if not website_df.empty and 'website_url' in website_df.columns:
                    url_exists_in_excel = url in website_df['website_url'].values
                    if url_exists_in_excel:
                        logger.info(f"网站URL已存在于本地Excel表格: {url}")
        except Exception as e:
            logger.error(f"检查URL是否存在于本地Excel时出错: {e}")
        
        # 检查URL是否已存在于飞书表格中
        url_already_exists_in_feishu = False
        if save_to_feishu and feishu_manager:
            try:
                # 检查URL是否存在于飞书表格
                url_already_exists_in_feishu = feishu_manager._url_exists_in_sheet(
                    feishu_manager.website_spreadsheet_token,
                    feishu_manager.website_sheet_id,
                    'website_url',
                    url
                )
                if url_already_exists_in_feishu:
                    logger.info(f"网站URL已存在于飞书表格: {url}")
            except Exception as e:
                logger.error(f"检查网站URL是否存在时出错: {e}")
        
        # 如果URL已存在，直接返回提示
        if url_exists_in_excel or url_already_exists_in_feishu:
            return jsonify({
                'success': True,
                'message': '该URL已存在，请勿重复爬取',
                'data': {'website_url': url},
                'url_exists': True,
                'feishu_skipped': url_already_exists_in_feishu,
                'excel_skipped': url_exists_in_excel
            })
        
        # 创建网站爬虫实例
        website_scraper = WebsiteScraper()
        
        # 爬取网站信息
        website_info = website_scraper.scrape_website(url)
        
        if not website_info:
            return jsonify({'success': False, 'message': '爬取失败，请检查URL是否正确'}), 400
        
        # 将爬取结果添加到本地 Excel 文件
        output_file = website_scraper.export_to_excel([website_info], WEBSITE_DATA_FILE)
        
        # 检查输出文件是否为临时文件
        file_locked_warning = ""
        if output_file and output_file.endswith('.temp'):
            file_locked_warning = "Excel文件被其他程序占用，数据已保存到临时文件。请关闭打开的Excel后，将临时文件重命名为正式文件。"
            logger.warning(f"Excel文件被锁定，数据保存到临时文件: {output_file}")
        elif not output_file:
            file_locked_warning = "无法保存到Excel文件，可能被其他程序占用或没有写入权限。"
            logger.error("保存到Excel文件失败")
        
        # 如果需要保存到飞书
        feishu_message = ""
        if save_to_feishu and feishu_manager:
            # 检查飞书管理器是否初始化成功
            if not feishu_manager:
                logger.warning("飞书管理器未初始化，无法保存到飞书")
                feishu_message = "飞书同步未启用或未配置"
            else:
                try:
                    # 在开始保存之前再次检查URL是否已存在
                    if feishu_manager._url_exists_in_sheet(
                        feishu_manager.website_spreadsheet_token,
                        feishu_manager.website_sheet_id,
                        'website_url',
                        url
                    ):
                        # URL已存在，不需要保存
                        logger.info(f"URL已存在于飞书表格中，跳过保存: {url}")
                        feishu_message = "该URL已存在于飞书表格中，无需重复添加"
                    else:
                        # 使用飞书管理器保存数据
                        success = feishu_manager.append_website_data([website_info])
                        if success:
                            # 再次检查URL是否真的添加到了飞书表格中
                            if feishu_manager._url_exists_in_sheet(
                                feishu_manager.website_spreadsheet_token,
                                feishu_manager.website_sheet_id,
                                'website_url',
                                url
                            ):
                                # URL成功添加到飞书
                                logger.info(f"成功保存网站数据到飞书: {url}")
                                feishu_message = "已同步到飞书"
                            else:
                                # 虽然返回成功，但URL不存在，可能因为URL已存在被跳过了
                                logger.warning(f"飞书同步返回成功，但URL不存在于表格中: {url}")
                                feishu_message = "飞书同步状态未知"
                        else:
                            logger.error(f"保存网站数据到飞书失败: {url}")
                            feishu_message = "同步到飞书失败"
                except Exception as e:
                    logger.error(f"保存网站数据到飞书时出错: {e}")
                    feishu_message = f"同步到飞书时出错: {str(e)}"
        
        # 构建响应消息
        message = "成功爬取网站信息"
        if file_locked_warning:
            message += f"，但{file_locked_warning}"
        if feishu_message:
            message += f"。{feishu_message}"
            
        return jsonify({
            'success': True, 
            'data': website_info,
            'message': message,
            'excel_file': output_file,
            'excel_locked': bool(file_locked_warning),
            'feishu_synced': save_to_feishu and feishu_manager and "已同步到飞书" in feishu_message,
            'feishu_skipped': url_already_exists_in_feishu
        })
    
    except Exception as e:
        logger.error(f"爬取网站失败: {e}")
        return jsonify({'success': False, 'message': f'爬取失败: {str(e)}'}), 500


@app.route('/api/scrape/auto', methods=['POST'])
def scrape_auto():
    """
    自动识别 URL 类型并爬取
    """
    try:
        data = request.json
        url = data.get('url')
        
        # 获取配置中的自动保存到飞书设置
        from utils.config import get_config
        config = get_config()
        default_save_to_feishu = config.auto_save_to_feishu
        
        # 如果请求中明确指定了save_to_feishu，则使用请求的值，否则使用系统默认设置
        save_to_feishu = data.get('save_to_feishu', default_save_to_feishu)
        
        if not url:
            return jsonify({'success': False, 'message': '未提供URL'}), 400
        
        # 判断 URL 类型
        is_github_repo = 'github.com/' in url and '/' in url.split('github.com/')[1]
        
        if is_github_repo:
            # GitHub 仓库 URL
            # 检查URL是否已经存在于本地Excel表格中
            url_exists_in_excel = False
            try:
                import pandas as pd
                import os
                if os.path.exists(GITHUB_DATA_FILE):
                    github_df = pd.read_excel(GITHUB_DATA_FILE)
                    if not github_df.empty and 'repository_url' in github_df.columns:
                        url_exists_in_excel = url in github_df['repository_url'].values
                        if url_exists_in_excel:
                            logger.info(f"GitHub仓库URL已存在于本地Excel表格: {url}")
            except Exception as e:
                logger.error(f"检查URL是否存在于本地Excel时出错: {e}")
            
            # 如果需要保存到飞书，先检查URL是否已存在
            url_already_exists_in_feishu = False
            if save_to_feishu and feishu_manager:
                try:
                    # 检查URL是否存在于飞书表格
                    url_already_exists_in_feishu = feishu_manager._url_exists_in_sheet(
                        feishu_manager.github_spreadsheet_token,
                        feishu_manager.github_sheet_id,
                        'repository_url',
                        url
                    )
                    if url_already_exists_in_feishu:
                        logger.info(f"GitHub仓库URL已存在于飞书表格: {url}")
                except Exception as e:
                    logger.error(f"检查GitHub仓库URL是否存在时出错: {e}")
            
            # 如果URL已存在，直接返回提示
            if url_exists_in_excel or url_already_exists_in_feishu:
                return jsonify({
                    'success': True,
                    'message': '该URL已存在，请勿重复爬取',
                    'data': {'repository_url': url},
                    'type': 'github',
                    'url_exists': True,
                    'feishu_skipped': url_already_exists_in_feishu,
                    'excel_skipped': url_exists_in_excel
                })
            
            # 创建 GitHub 爬虫实例
            github_scraper = GitHubScraper()
            
            # 爬取仓库信息
            repo_info = github_scraper.scrape_repo(url)
            
            if not repo_info:
                return jsonify({'success': False, 'message': '爬取GitHub仓库失败，请检查URL是否正确'}), 400
            
            # 将爬取结果添加到本地 Excel 文件
            output_file = github_scraper.export_to_excel([repo_info], GITHUB_DATA_FILE)
            
            # 检查输出文件是否为临时文件
            file_locked_warning = ""
            if output_file and output_file.endswith('.temp'):
                file_locked_warning = "Excel文件被其他程序占用，数据已保存到临时文件。请关闭打开的Excel后，将临时文件重命名为正式文件。"
                logger.warning(f"Excel文件被锁定，数据保存到临时文件: {output_file}")
            elif not output_file:
                file_locked_warning = "无法保存到Excel文件，可能被其他程序占用或没有写入权限。"
                logger.error("保存到Excel文件失败")
            
            # 如果需要保存到飞书
            feishu_message = ""
            if save_to_feishu and feishu_manager:
                # 检查飞书管理器是否初始化成功
                if not feishu_manager:
                    logger.warning("飞书管理器未初始化，无法保存到飞书")
                    feishu_message = "飞书同步未启用或未配置"
                elif url_already_exists_in_feishu:
                    # URL已存在，不需要保存
                    feishu_message = "该URL已存在于飞书表格中，无需重复添加"
                    logger.info(f"URL已存在于飞书表格，跳过保存: {url}")
                else:
                    try:
                        # 在开始保存之前再次检查URL是否已存在
                        if feishu_manager._url_exists_in_sheet(
                            feishu_manager.github_spreadsheet_token,
                            feishu_manager.github_sheet_id,
                            'repository_url',
                            url
                        ):
                            # URL已存在，不需要保存
                            logger.info(f"URL已存在于飞书表格中，跳过保存: {url}")
                            feishu_message = "该URL已存在于飞书表格中，无需重复添加"
                        else:
                            # 使用飞书管理器保存数据
                            success = feishu_manager.append_github_data([repo_info])
                            if success:
                                # 再次检查URL是否真的添加到了飞书表格中
                                if feishu_manager._url_exists_in_sheet(
                                    feishu_manager.github_spreadsheet_token,
                                    feishu_manager.github_sheet_id,
                                    'repository_url',
                                    url
                                ):
                                    # URL成功添加到飞书
                                    logger.info(f"成功保存数据到飞书: {url}")
                                    feishu_message = "已同步到飞书"
                                else:
                                    # 虽然返回成功，但URL不存在，可能因为URL已存在被跳过了
                                    logger.warning(f"飞书同步返回成功，但URL不存在于表格中: {url}")
                                    feishu_message = "飞书同步状态未知"
                            else:
                                logger.error(f"保存数据到飞书失败: {url}")
                                feishu_message = "同步到飞书失败"
                    except Exception as e:
                        logger.error(f"保存数据到飞书时出错: {e}")
                        feishu_message = f"同步到飞书时出错: {str(e)}"
            
            # 构建响应消息
            message = "成功爬取GitHub仓库信息"
            if file_locked_warning:
                message += f"，但{file_locked_warning}"
            if feishu_message:
                message += f"。{feishu_message}"
            
            return jsonify({
                'success': True, 
                'data': repo_info,
                'type': 'github',
                'message': message,
                'excel_file': output_file,
                'excel_locked': bool(file_locked_warning),
                'feishu_synced': save_to_feishu and feishu_manager and "已同步到飞书" in feishu_message,
                'feishu_skipped': url_already_exists_in_feishu
            })
        else:
            # 一般网站 URL
            # 检查URL是否已经存在于本地Excel表格中
            url_exists_in_excel = False
            try:
                import pandas as pd
                import os
                if os.path.exists(WEBSITE_DATA_FILE):
                    website_df = pd.read_excel(WEBSITE_DATA_FILE)
                    if not website_df.empty and 'website_url' in website_df.columns:
                        url_exists_in_excel = url in website_df['website_url'].values
                        if url_exists_in_excel:
                            logger.info(f"网站URL已存在于本地Excel表格: {url}")
            except Exception as e:
                logger.error(f"检查URL是否存在于本地Excel时出错: {e}")
            
            # 如果需要保存到飞书，先检查URL是否已存在
            url_already_exists_in_feishu = False
            if save_to_feishu and feishu_manager:
                try:
                    # 检查URL是否存在于飞书表格
                    url_already_exists_in_feishu = feishu_manager._url_exists_in_sheet(
                        feishu_manager.website_spreadsheet_token,
                        feishu_manager.website_sheet_id,
                        'website_url',
                        url
                    )
                    if url_already_exists_in_feishu:
                        logger.info(f"网站URL已存在于飞书表格: {url}")
                except Exception as e:
                    logger.error(f"检查网站URL是否存在时出错: {e}")
            
            # 如果URL已存在，直接返回提示
            if url_exists_in_excel or url_already_exists_in_feishu:
                return jsonify({
                    'success': True,
                    'message': '该URL已存在，请勿重复爬取',
                    'data': {'website_url': url},
                    'type': 'website',
                    'url_exists': True,
                    'feishu_skipped': url_already_exists_in_feishu,
                    'excel_skipped': url_exists_in_excel
                })
            
            # 创建网站爬虫实例
            website_scraper = WebsiteScraper()
            
            # 爬取网站信息
            website_info = website_scraper.scrape_website(url)
            
            if not website_info:
                return jsonify({'success': False, 'message': '爬取网站失败，请检查URL是否正确'}), 400
            
            # 将爬取结果添加到本地 Excel 文件
            output_file = website_scraper.export_to_excel([website_info], WEBSITE_DATA_FILE)
            
            # 检查输出文件是否为临时文件
            file_locked_warning = ""
            if output_file and output_file.endswith('.temp'):
                file_locked_warning = "Excel文件被其他程序占用，数据已保存到临时文件。请关闭打开的Excel后，将临时文件重命名为正式文件。"
                logger.warning(f"Excel文件被锁定，数据保存到临时文件: {output_file}")
            elif not output_file:
                file_locked_warning = "无法保存到Excel文件，可能被其他程序占用或没有写入权限。"
                logger.error("保存到Excel文件失败")
            
            # 如果需要保存到飞书
            feishu_message = ""
            if save_to_feishu and feishu_manager:
                # 检查飞书管理器是否初始化成功
                if not feishu_manager:
                    logger.warning("飞书管理器未初始化，无法保存到飞书")
                    feishu_message = "飞书同步未启用或未配置"
                elif url_already_exists_in_feishu:
                    # URL已存在，不需要保存
                    feishu_message = "该URL已存在于飞书表格中，无需重复添加"
                    logger.info(f"URL已存在于飞书表格，跳过保存: {url}")
                else:
                    try:
                        # 在开始保存之前再次检查URL是否已存在
                        if feishu_manager._url_exists_in_sheet(
                            feishu_manager.website_spreadsheet_token,
                            feishu_manager.website_sheet_id,
                            'website_url',
                            url
                        ):
                            # URL已存在，不需要保存
                            logger.info(f"URL已存在于飞书表格中，跳过保存: {url}")
                            feishu_message = "该URL已存在于飞书表格中，无需重复添加"
                        else:
                            # 使用飞书管理器保存数据
                            success = feishu_manager.append_website_data([website_info])
                            if success:
                                # 再次检查URL是否真的添加到了飞书表格中
                                if feishu_manager._url_exists_in_sheet(
                                    feishu_manager.website_spreadsheet_token,
                                    feishu_manager.website_sheet_id,
                                    'website_url',
                                    url
                                ):
                                    # URL成功添加到飞书
                                    logger.info(f"成功保存网站数据到飞书: {url}")
                                    feishu_message = "已同步到飞书"
                                else:
                                    # 虽然返回成功，但URL不存在，可能因为URL已存在被跳过了
                                    logger.warning(f"飞书同步返回成功，但URL不存在于表格中: {url}")
                                    feishu_message = "飞书同步状态未知"
                            else:
                                logger.error(f"保存网站数据到飞书失败: {url}")
                                feishu_message = "同步到飞书失败"
                    except Exception as e:
                        logger.error(f"保存网站数据到飞书时出错: {e}")
                        feishu_message = f"同步到飞书时出错: {str(e)}"
            
            # 构建响应消息
            message = "成功爬取网站信息"
            if file_locked_warning:
                message += f"，但{file_locked_warning}"
            if feishu_message:
                message += f"。{feishu_message}"
            
            return jsonify({
                'success': True, 
                'data': website_info,
                'type': 'website',
                'message': message,
                'excel_file': output_file,
                'excel_locked': bool(file_locked_warning),
                'feishu_synced': save_to_feishu and feishu_manager and "已同步到飞书" in feishu_message,
                'feishu_skipped': url_already_exists_in_feishu
            })
    
    except Exception as e:
        logger.error(f"自动爬取失败: {e}")
        return jsonify({'success': False, 'message': f'爬取失败: {str(e)}'}), 500


@app.route('/api/data/github', methods=['GET'])
def get_github_data():
    """
    获取 GitHub 数据
    """
    try:
        import pandas as pd
        
        if not os.path.exists(GITHUB_DATA_FILE):
            return jsonify({'success': True, 'data': [], 'message': '暂无数据'})
        
        # 读取 Excel 文件
        df = pd.read_excel(GITHUB_DATA_FILE)
        
        # 转换为 JSON 格式
        records = df.to_dict('records')
        
        return jsonify({
            'success': True, 
            'data': records,
            'message': f'成功获取 {len(records)} 条 GitHub 数据'
        })
    
    except Exception as e:
        logger.error(f"获取 GitHub 数据失败: {e}")
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}), 500


@app.route('/api/data/website', methods=['GET'])
def get_website_data():
    """
    获取网站数据
    """
    try:
        import pandas as pd
        import numpy as np
        import json
        
        if not os.path.exists(WEBSITE_DATA_FILE):
            return jsonify({'success': True, 'data': [], 'message': '暂无数据'})
        
        # 读取 Excel 文件
        df = pd.read_excel(WEBSITE_DATA_FILE)
        
        # 处理DataFrame中的NaN值，将其转换为None
        df = df.replace({np.nan: None})
        
        # 转换为 JSON 格式
        records = df.to_dict('records')
        
        # 额外处理：确保所有None和NaN值在JSON序列化时被转换为null
        class NaNHandler(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, float) and np.isnan(obj):
                    return None
                return super().default(obj)
        
        # 使用自定义encoder进行序列化
        safe_records = json.loads(json.dumps(records, cls=NaNHandler))
        
        logger.info(f"成功获取网站数据: {len(safe_records)}条记录")
        
        return jsonify({
            'success': True, 
            'data': safe_records,
            'message': f'成功获取 {len(safe_records)} 条网站数据'
        })
    
    except Exception as e:
        logger.error(f"获取网站数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}), 500


@app.route('/api/delete', methods=['POST'])
def delete_record():
    """
    删除记录
    """
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'message': '未提供URL'}), 400
        
        # 执行删除操作
        success, message = delete_url(url)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    
    except Exception as e:
        logger.error(f"删除记录失败: {e}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@app.route('/api/clean', methods=['POST'])
def clean_data():
    """
    清理和去重数据
    """
    try:
        data = request.json
        data_type = data.get('type')  # 'github' 或 'website'
        
        if not data_type or data_type not in ['github', 'website']:
            return jsonify({'success': False, 'message': '无效的数据类型'}), 400
        
        if not feishu_manager:
            return jsonify({'success': False, 'message': '飞书管理器未初始化'}), 500
        
        # 执行清理操作
        if data_type == 'github':
            result = feishu_manager.clean_and_deduplicate_github_sheet()
        else:
            result = feishu_manager.clean_and_deduplicate_website_sheet()
        
        if result:
            return jsonify({'success': True, 'message': f'成功清理 {data_type} 数据'})
        else:
            return jsonify({'success': False, 'message': f'清理 {data_type} 数据失败'}), 400
    
    except Exception as e:
        logger.error(f"清理数据失败: {e}")
        return jsonify({'success': False, 'message': f'清理失败: {str(e)}'}), 500


@app.route('/api/feishu/status', methods=['GET'])
def feishu_status():
    """
    获取飞书连接状态
    """
    try:
        if not feishu_manager:
            logger.error("飞书管理器未初始化")
            return jsonify({'success': False, 'connected': False, 'message': '飞书管理器未初始化'}), 500
        
        # 获取配置信息
        config = {
            'app_id': feishu_manager.app_id,
            'github_spreadsheet_token': feishu_manager.github_spreadsheet_token,
            'github_sheet_id': feishu_manager.github_sheet_id,
            'website_spreadsheet_token': feishu_manager.website_spreadsheet_token,
            'website_sheet_id': feishu_manager.website_sheet_id
        }
        
        # 检查飞书连接状态
        try:
            # 检查飞书连接状态 - 尝试获取访问令牌
            token = feishu_manager.get_access_token()
            connected = token is not None
            
            # 默认设置GitHub和网站连接状态同主连接状态
            github_connected = connected
            website_connected = connected
            
            # 如果token获取成功，再验证一下能否访问电子表格
            if connected:
                logger.info("Token获取成功，验证能否访问电子表格")
                try:
                    # 尝试读取GitHub表格以验证连接是否真的有效
                    github_data = feishu_manager.read_github_data()
                    if github_data is not None:  # 如果能读取数据，说明GitHub连接正常
                        logger.info("成功读取GitHub电子表格数据，连接正常")
                        github_connected = True
                    else:
                        logger.warning("无法读取GitHub电子表格数据")
                        github_connected = False
                except Exception as github_error:
                    logger.error(f"验证GitHub电子表格访问时出错: {github_error}")
                    github_connected = False
                    
                try:
                    # 尝试读取网站表格以验证连接是否真的有效  
                    website_data = feishu_manager.read_website_data()
                    if website_data is not None:  # 如果能读取数据，说明网站连接正常
                        logger.info("成功读取网站电子表格数据，连接正常")
                        website_connected = True
                    else:
                        logger.warning("无法读取网站电子表格数据")
                        website_connected = False
                except Exception as website_error:
                    logger.error(f"验证网站电子表格访问时出错: {website_error}")
                    website_connected = False
            
            return jsonify({
                'success': True,
                'connected': connected,
                'github_connected': github_connected,
                'website_connected': website_connected,
                'config': config,
                'message': '飞书连接正常' if connected else '飞书连接失败'
            })
        except Exception as token_error:
            logger.error(f"获取飞书访问令牌时出错: {token_error}")
            return jsonify({
                'success': False,
                'connected': False,
                'github_connected': False,
                'website_connected': False,
                'config': config,
                'message': f'飞书连接失败: {str(token_error)}'
            }), 500
    
    except Exception as e:
        logger.error(f"获取飞书状态失败: {e}")
        return jsonify({
            'success': False, 
            'connected': False, 
            'github_connected': False,
            'website_connected': False,
            'message': f'获取飞书状态失败: {str(e)}'
        }), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """
    获取系统设置
    """
    try:
        # 读取配置信息
        from utils.config import get_config
        config_obj = get_config()
        
        # 将Config对象转换为字典
        config = {
            'github_token': config_obj.github_token,  # 返回实际的token值，让前端决定如何显示
            'use_proxy': config_obj.use_proxy,
            'http_proxy': config_obj.http_proxy,
            'https_proxy': config_obj.https_proxy,
            'request_timeout': config_obj.request_timeout,
            'max_retries': config_obj.max_retries,
            'retry_delay': config_obj.retry_delay,
            'max_threads': config_obj.max_threads,
            'request_delay': config_obj.request_delay,
            'feishu_app_id': config_obj.feishu_app_id,
            'feishu_app_secret': '********' if config_obj.feishu_app_secret else '',
            'feishu_github_spreadsheet_token': config_obj.feishu_github_spreadsheet_token,
            'feishu_github_sheet_id': config_obj.feishu_github_sheet_id,
            'feishu_website_spreadsheet_token': config_obj.feishu_website_spreadsheet_token,
            'feishu_website_sheet_id': config_obj.feishu_website_sheet_id,
            'auto_save_to_feishu': config_obj.auto_save_to_feishu
        }
        
        return jsonify({
            'success': True,
            'data': config,
            'message': '成功获取系统设置'
        })
    
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'获取系统设置失败: {str(e)}'}), 500


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """
    保存系统设置
    """
    try:
        data = request.json
        
        # 保存配置信息
        from utils.config import Config  # 导入Config类
        config_obj = Config()  # 获取Config实例
        result = config_obj.update_config(**data)  # 使用Config实例的update_config方法
        
        if result:
            return jsonify({
                'success': True,
                'message': '成功保存系统设置'
            })
        else:
            logger.warning("更新配置返回失败")
            return jsonify({
                'success': False,
                'message': '保存系统设置失败：配置更新失败'
            }), 500
    
    except ImportError as e:
        logger.error(f"导入Config类失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'保存系统设置失败: 导入Config类错误 - {str(e)}'}), 500
    except Exception as e:
        logger.error(f"保存系统设置失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'保存系统设置失败: {str(e)}'}), 500


@app.route('/api/feishu/sync/history', methods=['GET'])
def feishu_sync_history():
    """
    获取飞书同步历史记录
    """
    try:
        # 由于当前版本没有实现记录同步历史的功能，返回一个空列表
        return jsonify({
            'success': True,
            'data': [],
            'message': '同步历史记录功能尚未实现'
        })
    
    except Exception as e:
        logger.error(f"获取飞书同步历史失败: {e}")
        return jsonify({'success': False, 'message': f'获取飞书同步历史失败: {str(e)}'}), 500


@app.route('/api/feishu/sync/github', methods=['POST'])
def sync_github_to_feishu():
    """
    将本地GitHub数据同步到飞书
    """
    try:
        if not feishu_manager:
            return jsonify({'success': False, 'message': '飞书管理器未初始化'}), 500
        
        import pandas as pd
        import os
        
        # 检查GitHub数据文件是否存在
        if not os.path.exists(GITHUB_DATA_FILE):
            return jsonify({'success': False, 'message': 'GitHub数据文件不存在'}), 404
        
        # 读取Excel文件
        try:
            github_df = pd.read_excel(GITHUB_DATA_FILE)
            if github_df.empty:
                return jsonify({'success': True, 'message': 'GitHub数据为空，无需同步'})
                
            # 记录数据信息
            logger.info(f"成功读取GitHub数据: {len(github_df)}行, 列: {github_df.columns.tolist()}")
        except Exception as e:
            logger.error(f"读取GitHub数据文件失败: {e}")
            return jsonify({'success': False, 'message': f'读取GitHub数据文件失败: {str(e)}'}), 500
        
        # 将数据转换为字典列表
        try:
            github_data = github_df.to_dict('records')
            logger.info(f"数据类型: {type(github_data)}, 长度: {len(github_data)}")
            if github_data:
                logger.info(f"第一条记录类型: {type(github_data[0])}")
        except Exception as e:
            logger.error(f"转换GitHub数据失败: {e}")
            return jsonify({'success': False, 'message': f'转换GitHub数据失败: {str(e)}'}), 500
        
        # 同步到飞书
        try:
            result = feishu_manager.append_github_data(github_data)
        except Exception as e:
            logger.error(f"同步GitHub数据到飞书时发生异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500
        
        if result:
            return jsonify({
                'success': True,
                'message': f'成功同步 {len(github_data)} 条GitHub数据到飞书'
            })
        else:
            return jsonify({
                'success': False,
                'message': '同步GitHub数据到飞书失败'
            }), 500
    
    except Exception as e:
        logger.error(f"同步GitHub数据到飞书失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500


@app.route('/api/feishu/sync/website', methods=['POST'])
def sync_website_to_feishu():
    """
    将本地网站数据同步到飞书
    """
    try:
        if not feishu_manager:
            return jsonify({'success': False, 'message': '飞书管理器未初始化'}), 500
        
        import pandas as pd
        import os
        
        # 检查网站数据文件是否存在
        if not os.path.exists(WEBSITE_DATA_FILE):
            return jsonify({'success': False, 'message': '网站数据文件不存在'}), 404
        
        # 读取Excel文件
        try:
            website_df = pd.read_excel(WEBSITE_DATA_FILE)
            if website_df.empty:
                return jsonify({'success': True, 'message': '网站数据为空，无需同步'})
                
            # 记录数据信息
            logger.info(f"成功读取网站数据: {len(website_df)}行, 列: {website_df.columns.tolist()}")
        except Exception as e:
            logger.error(f"读取网站数据文件失败: {e}")
            return jsonify({'success': False, 'message': f'读取网站数据文件失败: {str(e)}'}), 500
        
        # 将数据转换为字典列表
        try:
            website_data = website_df.to_dict('records')
            logger.info(f"数据类型: {type(website_data)}, 长度: {len(website_data)}")
            if website_data:
                logger.info(f"第一条记录类型: {type(website_data[0])}")
        except Exception as e:
            logger.error(f"转换网站数据失败: {e}")
            return jsonify({'success': False, 'message': f'转换网站数据失败: {str(e)}'}), 500
        
        # 同步到飞书
        try:
            result = feishu_manager.append_website_data(website_data)
        except Exception as e:
            logger.error(f"同步网站数据到飞书时发生异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500
        
        if result:
            return jsonify({
                'success': True,
                'message': f'成功同步 {len(website_data)} 条网站数据到飞书'
            })
        else:
            return jsonify({
                'success': False,
                'message': '同步网站数据到飞书失败'
            }), 500
    
    except Exception as e:
        logger.error(f"同步网站数据到飞书失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500


@app.route('/api/feishu/clean/<data_type>', methods=['POST'])
def clean_feishu_data(data_type):
    """
    清理并去重飞书表格数据
    
    :param data_type: 数据类型，'github'或'website'
    """
    try:
        if not feishu_manager:
            return jsonify({'success': False, 'message': '飞书管理器未初始化'}), 500
        
        if data_type not in ['github', 'website']:
            return jsonify({'success': False, 'message': '无效的数据类型'}), 400
        
        # 执行清理去重操作
        if data_type == 'github':
            result = feishu_manager.clean_and_deduplicate_github_sheet()
            message_text = '成功清理GitHub数据表'
        else:
            result = feishu_manager.clean_and_deduplicate_website_sheet()
            message_text = '成功清理网站数据表'
        
        if result:
            return jsonify({
                'success': True,
                'message': message_text,
                'removed_count': result.get('removed_count', 0)
            })
        else:
            return jsonify({
                'success': False,
                'message': f'清理{data_type}数据失败'
            }), 500
    
    except Exception as e:
        logger.error(f"清理{data_type}数据失败: {e}")
        return jsonify({'success': False, 'message': f'清理失败: {str(e)}'}), 500


@app.route('/api/feishu/config', methods=['POST'])
def update_feishu_config():
    """
    更新飞书配置
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'message': '未提供配置数据'}), 400
        
        # 获取配置信息
        from utils.config import update_feishu_config
        
        # 更新配置
        result = update_feishu_config(
            app_id=data.get('app_id'),
            app_secret=data.get('app_secret'),
            github_spreadsheet_token=data.get('github_spreadsheet_token'),
            github_sheet_id=data.get('github_sheet_id'),
            website_spreadsheet_token=data.get('website_spreadsheet_token'),
            website_sheet_id=data.get('website_sheet_id')
        )
        
        if result:
            # 重新初始化飞书管理器
            global feishu_manager
            try:
                feishu_manager = FeishuManager()
            except Exception as e:
                logger.error(f"重新初始化飞书管理器失败: {e}")
                return jsonify({'success': False, 'message': f'配置已保存，但重新初始化飞书管理器失败: {str(e)}'}), 500
            
            return jsonify({
                'success': True,
                'message': '成功更新飞书配置'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新飞书配置失败'
            }), 500
    
    except Exception as e:
        logger.error(f"更新飞书配置失败: {e}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    获取系统统计数据
    """
    try:
        import pandas as pd
        import os
        from datetime import datetime
        
        # 统计GitHub仓库数量
        github_count = 0
        if os.path.exists(GITHUB_DATA_FILE):
            try:
                github_df = pd.read_excel(GITHUB_DATA_FILE)
                github_count = len(github_df)
            except Exception as e:
                logger.error(f"读取GitHub数据失败: {e}")
        
        # 统计网站数量
        website_count = 0
        if os.path.exists(WEBSITE_DATA_FILE):
            try:
                website_df = pd.read_excel(WEBSITE_DATA_FILE)
                website_count = len(website_df)
            except Exception as e:
                logger.error(f"读取网站数据失败: {e}")
                
        # 获取最后爬取时间
        # 这里简化处理，取两个数据文件的最新修改时间
        last_scrape_time = None
        files_to_check = [GITHUB_DATA_FILE, WEBSITE_DATA_FILE]
        for file_path in files_to_check:
            if os.path.exists(file_path):
                mod_time = os.path.getmtime(file_path)
                mod_time_dt = datetime.fromtimestamp(mod_time)
                if last_scrape_time is None or mod_time_dt > last_scrape_time:
                    last_scrape_time = mod_time_dt
        
        # 格式化时间
        last_scrape_time_str = None
        if last_scrape_time:
            last_scrape_time_str = last_scrape_time.isoformat()
            
        return jsonify({
            'success': True,
            'data': {
                'github_count': github_count,
                'website_count': website_count,
                'last_scrape_time': last_scrape_time_str
            },
            'message': '获取统计数据成功'
        })
    
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({'success': False, 'message': f'获取统计数据失败: {str(e)}'}), 500


@app.route('/api/recent_items', methods=['GET'])
def get_recent_items():
    """
    获取最近爬取的项目
    """
    try:
        import pandas as pd
        import os
        
        recent_items = []
        
        # 获取GitHub数据
        if os.path.exists(GITHUB_DATA_FILE):
            try:
                github_df = pd.read_excel(GITHUB_DATA_FILE)
                # 只取最近的5条记录
                recent_github = github_df.tail(5).to_dict('records')
                for item in recent_github:
                    item['type'] = 'github'
                    # 确保存在URL字段
                    if 'repository_url' in item:
                        item['url'] = item['repository_url']
                    # 截断描述
                    if 'description' in item and item['description'] and len(str(item['description'])) > 100:
                        item['description'] = str(item['description'])[:100] + '...'
                recent_items.extend(recent_github)
            except Exception as e:
                logger.error(f"读取GitHub数据失败: {e}")
        
        # 获取网站数据
        if os.path.exists(WEBSITE_DATA_FILE):
            try:
                website_df = pd.read_excel(WEBSITE_DATA_FILE)
                # 只取最近的5条记录
                recent_websites = website_df.tail(5).to_dict('records')
                for item in recent_websites:
                    item['type'] = 'website'
                    # 确保存在URL字段
                    if 'website_url' in item:
                        item['url'] = item['website_url']
                    # 截断描述
                    if 'description' in item and item['description'] and len(str(item['description'])) > 100:
                        item['description'] = str(item['description'])[:100] + '...'
                recent_items.extend(recent_websites)
            except Exception as e:
                logger.error(f"读取网站数据失败: {e}")
        
        # 按时间排序，取最近的10条记录
        # 这里简化处理，假设没有明确的时间字段，直接取最新的记录
        recent_items = recent_items[-10:] if len(recent_items) > 10 else recent_items
            
        return jsonify({
            'success': True,
            'data': recent_items,
            'message': '获取最近爬取项目成功'
        })
    
    except Exception as e:
        logger.error(f"获取最近爬取项目失败: {e}")
        return jsonify({'success': False, 'message': f'获取最近爬取项目失败: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': '请求的资源不存在'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500


if __name__ == '__main__':
    # 设置端口，默认为 5000
    port = int(os.environ.get('PORT', 5000))
    
    # 启动服务器
    app.run(host='0.0.0.0', port=port, debug=False) 