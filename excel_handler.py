#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Excel 处理模块

此模块负责将爬取到的 GitHub 仓库信息保存到 Excel 文件中。
"""

import os
import pandas as pd
from typing import Dict, Any, List
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('excel_handler')

class ExcelHandler:
    """Excel 处理类，用于管理 GitHub 仓库数据的保存和读取"""
    
    def __init__(self, excel_path: str = "github项目.xlsx"):
        """
        初始化 Excel 处理器
        
        参数:
            excel_path: Excel 文件路径，默认为 "github项目.xlsx"
        """
        self.excel_path = excel_path
        self.columns = [
            '仓库URL', '仓库名称', '仓库描述', 'Star数量', 
            'Fork数量', 'Issue数量', '项目简介/README内容'
        ]
    
    def save_repo_info(self, repo_info: Dict[str, Any]) -> bool:
        """
        将仓库信息保存到 Excel 文件
        
        参数:
            repo_info: 包含仓库信息的字典
            
        返回:
            bool: 保存是否成功
        """
        try:
            # 转换数据格式
            data = {
                '仓库URL': repo_info['repo_url'],
                '仓库名称': repo_info['repo_name'],
                '仓库描述': repo_info['description'],
                'Star数量': repo_info['star_count'],
                'Fork数量': repo_info['fork_count'],
                'Issue数量': repo_info['issue_count'],
                '项目简介/README内容': repo_info['readme_content']
            }
            
            # 检查文件是否存在
            if os.path.exists(self.excel_path):
                # 检查文件是否可写
                if not os.access(self.excel_path, os.W_OK):
                    logger.error(f"无权限写入 Excel 文件: {self.excel_path}")
                    return False
                
                # 尝试检查文件是否被其他程序打开
                try:
                    # 尝试以写入模式打开文件，测试是否可写
                    with open(self.excel_path, 'a+b') as f:
                        f.seek(0, os.SEEK_END)  # 移动到文件末尾
                        # 如果文件可以打开进行写入，则继续处理
                except IOError as e:
                    logger.error(f"无法访问 Excel 文件，可能被其他程序打开: {e}")
                    return False
                
                logger.info(f"发现现有 Excel 文件: {self.excel_path}")
                # 检查是否已存在相同 URL 的仓库
                existing_df = pd.read_excel(self.excel_path)
                if '仓库URL' in existing_df.columns:
                    for i, row in existing_df.iterrows():
                        if pd.notna(row['仓库URL']) and row['仓库URL'] == repo_info['repo_url']:
                            logger.info(f"发现相同 URL 的仓库，将更新现有记录: {repo_info['repo_url']}")
                            return self.update_repo_info(repo_info['repo_url'], repo_info)
                
                return self._append_to_existing_file(data)
            else:
                logger.info(f"创建新的 Excel 文件: {self.excel_path}")
                return self._create_new_file(data)
                
        except PermissionError as e:
            logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开: {e}")
            return False
        except Exception as e:
            logger.error(f"保存仓库信息时发生错误: {e}")
            return False
    
    def update_repo_info(self, repo_url: str, new_info: Dict[str, Any]) -> bool:
        """
        更新已有仓库的信息
        
        参数:
            repo_url: 仓库 URL，用于查找要更新的行
            new_info: 包含新仓库信息的字典
            
        返回:
            bool: 更新是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(self.excel_path):
                logger.error(f"Excel 文件不存在: {self.excel_path}")
                return False
            
            # 检查文件是否可写
            if not os.access(self.excel_path, os.W_OK):
                logger.error(f"无权限写入 Excel 文件: {self.excel_path}")
                return False
                
            # 尝试检查文件是否被其他程序打开
            try:
                # 尝试以写入模式打开文件，测试是否可写
                with open(self.excel_path, 'a+b') as f:
                    f.seek(0, os.SEEK_END)  # 移动到文件末尾
                    # 如果文件可以打开进行写入，则继续处理
            except IOError as e:
                logger.error(f"无法访问 Excel 文件，可能被其他程序打开: {e}")
                return False
            
            # 读取现有文件
            df = pd.read_excel(self.excel_path)
            
            # 确认列标题一致性
            if list(df.columns) != self.columns:
                logger.warning("现有文件的列结构与预期不符，将调整列结构")
                df = df.reindex(columns=self.columns)
            
            # 查找指定 URL 的行
            found = False
            for i, row in df.iterrows():
                if pd.notna(row['仓库URL']) and row['仓库URL'] == repo_url:
                    # 更新该行的信息
                    df.at[i, '仓库名称'] = new_info['repo_name']
                    df.at[i, '仓库描述'] = new_info['description']
                    df.at[i, 'Star数量'] = new_info['star_count']
                    df.at[i, 'Fork数量'] = new_info['fork_count']
                    df.at[i, 'Issue数量'] = new_info['issue_count']
                    df.at[i, '项目简介/README内容'] = new_info['readme_content']
                    found = True
                    logger.info(f"已更新仓库信息: {repo_url}, 行号: {i+1}")
                    break
            
            if not found:
                logger.warning(f"未找到需要更新的仓库: {repo_url}")
                return False
            
            # 保存到文件
            try:
                df.to_excel(self.excel_path, index=False)
                return True
            except PermissionError:
                logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开")
                return False
            except Exception as e:
                logger.error(f"保存 Excel 文件时出错: {e}")
                return False
            
        except PermissionError as e:
            logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开: {e}")
            return False
        except Exception as e:
            logger.error(f"更新仓库信息时发生错误: {e}")
            return False
    
    def _create_new_file(self, data: Dict[str, Any]) -> bool:
        """
        创建新的 Excel 文件并写入数据
        
        参数:
            data: 要写入的数据
            
        返回:
            bool: 操作是否成功
        """
        try:
            # 检查目录是否存在且可写
            directory = os.path.dirname(self.excel_path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except PermissionError:
                    logger.error(f"无权限创建目录: {directory}")
                    return False
                except Exception as e:
                    logger.error(f"创建目录时出错: {e}")
                    return False
            
            # 如果文件已存在，检查是否可写
            if os.path.exists(self.excel_path):
                if not os.access(self.excel_path, os.W_OK):
                    logger.error(f"无权限写入 Excel 文件: {self.excel_path}")
                    return False
            # 如果文件不存在，检查目录是否可写
            elif directory and not os.access(directory, os.W_OK):
                logger.error(f"无权限写入目录: {directory}")
                return False
                
            # 创建 DataFrame
            df = pd.DataFrame([data], columns=self.columns)
            
            # 保存到 Excel
            try:
                df.to_excel(self.excel_path, index=False)
                logger.info(f"成功创建新文件并写入数据")
                return True
            except PermissionError:
                logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开")
                return False
            except Exception as e:
                logger.error(f"保存 Excel 文件时出错: {e}")
                return False
        except PermissionError as e:
            logger.error(f"权限被拒绝: 可能无法创建或写入文件: {e}")
            return False
        except Exception as e:
            logger.error(f"创建 Excel 文件失败: {e}")
            return False
    
    def _append_to_existing_file(self, data: Dict[str, Any]) -> bool:
        """
        将数据追加到现有 Excel 文件中的第一个空行
        
        参数:
            data: 要追加的数据
            
        返回:
            bool: 操作是否成功
        """
        try:
            # 读取现有文件
            df = pd.read_excel(self.excel_path)
            
            # 确认列标题一致性
            if list(df.columns) != self.columns:
                logger.warning("现有文件的列结构与预期不符，将调整列结构")
                df = df.reindex(columns=self.columns)
            
            # 查找第一个空行
            first_empty_row = None
            for i in range(len(df)):
                if pd.isna(df.iloc[i, 0]):  # 检查第一列是否为空
                    first_empty_row = i
                    break
            
            # 如果没有空行，则在末尾添加
            if first_empty_row is None:
                df.loc[len(df)] = [data[col] for col in self.columns]
                logger.info(f"在文件末尾添加新数据，行号: {len(df)}")
            else:
                # 在空行插入数据
                for j, col in enumerate(self.columns):
                    df.iloc[first_empty_row, j] = data[col]
                logger.info(f"在空行添加新数据，行号: {first_empty_row + 1}")
            
            # 保存到文件
            try:
                df.to_excel(self.excel_path, index=False)
                return True
            except PermissionError:
                logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开")
                return False
            except Exception as e:
                logger.error(f"保存 Excel 文件时出错: {e}")
                return False
            
        except PermissionError as e:
            logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开: {e}")
            return False
        except Exception as e:
            logger.error(f"向现有文件追加数据失败: {e}")
            return False
    
    def get_all_repos(self) -> List[Dict[str, Any]]:
        """
        获取 Excel 文件中所有的仓库信息
        
        返回:
            List[Dict]: 包含所有仓库信息的列表
        """
        try:
            if not os.path.exists(self.excel_path):
                logger.warning(f"Excel 文件不存在: {self.excel_path}")
                return []
            
            # 读取 Excel 文件
            df = pd.read_excel(self.excel_path)
            
            # 转换为字典列表
            repos = []
            for _, row in df.iterrows():
                if pd.notna(row['仓库URL']):  # 跳过空行
                    repo = {
                        'repo_url': row['仓库URL'],
                        'repo_name': row['仓库名称'],
                        'description': row['仓库描述'],
                        'star_count': row['Star数量'],
                        'fork_count': row['Fork数量'],
                        'issue_count': row['Issue数量'],
                        'readme_content': row['项目简介/README内容']
                    }
                    repos.append(repo)
            
            return repos
            
        except Exception as e:
            logger.error(f"获取仓库信息列表失败: {e}")
            return []
            
    def delete_repo(self, repo_name: str) -> bool:
        """
        根据仓库名称删除仓库信息
        
        参数:
            repo_name: 仓库名称
            
        返回:
            bool: 删除是否成功，如果仓库不存在则返回False
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(self.excel_path):
                logger.error(f"Excel 文件不存在: {self.excel_path}")
                return False
            
            # 检查文件是否可写
            if not os.access(self.excel_path, os.W_OK):
                logger.error(f"无权限写入 Excel 文件: {self.excel_path}")
                return False
                
            # 尝试检查文件是否被其他程序打开
            try:
                # 尝试以写入模式打开文件，测试是否可写
                with open(self.excel_path, 'a+b') as f:
                    f.seek(0, os.SEEK_END)  # 移动到文件末尾
                    # 如果文件可以打开进行写入，则继续处理
            except IOError as e:
                logger.error(f"无法访问 Excel 文件，可能被其他程序打开: {e}")
                return False
            
            # 读取 Excel 文件
            df = pd.read_excel(self.excel_path)
            
            # 查找匹配的仓库
            found = False
            matched_rows = []
            
            # 记录所有匹配的行号
            for i, row in df.iterrows():
                if pd.notna(row['仓库名称']) and row['仓库名称'] == repo_name:
                    matched_rows.append(i)
                    found = True
            
            if not found:
                logger.warning(f"未找到名为 '{repo_name}' 的仓库")
                return False
            
            # 删除匹配的行
            df = df.drop(matched_rows)
            
            # 重置索引
            df = df.reset_index(drop=True)
            
            # 保存到文件
            try:
                df.to_excel(self.excel_path, index=False)
                logger.info(f"已删除仓库 '{repo_name}' 的信息")
                return True
            except PermissionError:
                logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开")
                return False
            except Exception as e:
                logger.error(f"保存 Excel 文件时出错: {e}")
                return False
            
        except PermissionError as e:
            logger.error(f"权限被拒绝: Excel 文件可能被其他程序（如 Microsoft Excel）打开: {e}")
            return False
        except Exception as e:
            logger.error(f"删除仓库信息时发生错误: {e}")
            return False