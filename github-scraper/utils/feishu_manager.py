"""
飞书电子表格管理模块 - 提供飞书电子表格的API操作功能
"""
import os
import json
import requests
import pandas as pd
import logging
from typing import Optional, Dict, List, Tuple, Any, Union
from dotenv import load_dotenv
import traceback
import time  # 添加time模块导入，因为在_write_in_batches方法中使用了time.sleep

# 修改为适合新目录结构的相对导入
from . import get_logger
from .config import get_config

# 获取日志记录器
logger = get_logger('feishu_manager')

class FeishuManager:
    """飞书电子表格管理类"""
    
    def __init__(self):
        """初始化飞书管理器"""
        try:
            # 获取配置
            config = get_config()
            feishu_config = config.get_feishu_config()
            
            # 从配置获取飞书应用凭证
            self.app_id = feishu_config['app_id']
            self.app_secret = feishu_config['app_secret']
            
            # 检查应用凭证是否存在
            if not self.app_id or not self.app_secret:
                logger.error("飞书应用凭证缺失，请在.env文件中配置FEISHU_APP_ID和FEISHU_APP_SECRET")
                raise ValueError("飞书应用凭证缺失，请在.env文件中配置FEISHU_APP_ID和FEISHU_APP_SECRET")
            
            # 获取电子表格配置
            github_sheet_config = config.get_feishu_github_sheet_config()
            website_sheet_config = config.get_feishu_website_sheet_config()
            
            # 保存表格配置
            self.github_spreadsheet_token = github_sheet_config['spreadsheet_token']
            self.github_sheet_id = github_sheet_config['sheet_id']
            self.website_spreadsheet_token = website_sheet_config['spreadsheet_token']
            self.website_sheet_id = website_sheet_config['sheet_id']
            
            # 飞书API接口
            self.auth_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
            self.sheets_url = "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/"
            
            # 获取访问令牌 - 添加重试机制
            self.tenant_access_token = None
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    self.tenant_access_token = self._get_tenant_access_token()
                    if self.tenant_access_token:
                        break
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"获取访问令牌失败，第 {retry_count} 次重试: {e}")
                    if retry_count >= max_retries:
                        logger.error(f"获取访问令牌失败，已达到最大重试次数")
                        break
                    import time
                    time.sleep(1)  # 等待1秒再重试
            
            # 定义关键字段列表
            self.KEY_FIELDS = ['repository_url', 'website_url', 'name', 'description', 'url']
            
            # 验证初始化是否成功
            if not self.tenant_access_token:
                logger.warning("初始化飞书管理器时，无法获取访问令牌，但仍然继续创建实例")
                
        except Exception as e:
            logger.error(f"初始化飞书管理器时出错: {e}")
            traceback.print_exc()
            raise
    
    def get_access_token(self) -> str:
        """
        获取当前访问令牌，如果不存在则重新获取
        
        Returns:
            str: 租户访问令牌
        """
        try:
            if not self.tenant_access_token:
                logger.info("访问令牌不存在，正在重新获取...")
                self.tenant_access_token = self._get_tenant_access_token()
            
            # 验证token是否有效
            if self.tenant_access_token:
                # 简单测试token - 尝试获取电子表格元数据
                test_url = f"{self.sheets_url}{self.github_spreadsheet_token}/sheets/{self.github_sheet_id}"
                headers = {
                    "Authorization": f"Bearer {self.tenant_access_token}"
                }
                
                try:
                    response = requests.get(test_url, headers=headers, timeout=5)
                    
                    # 如果token无效，会返回401或者其他错误码
                    if response.status_code == 401 or (response.json().get("code") == 99991663):
                        logger.info("访问令牌已过期，正在刷新...")
                        self.tenant_access_token = self._get_tenant_access_token()
                    elif response.status_code >= 400:
                        logger.warning(f"测试访问令牌时返回错误状态码: {response.status_code}")
                        # 非401错误可能表示其他问题，但我们仍然尝试刷新
                        self.tenant_access_token = self._get_tenant_access_token()
                except Exception as e:
                    logger.warning(f"测试访问令牌时出错: {e}")
                    # 发生异常，尝试刷新令牌
                    self.tenant_access_token = self._get_tenant_access_token()
            
            return self.tenant_access_token
        except Exception as e:
            logger.error(f"获取访问令牌时出错: {e}")
            return None
    
    def _get_tenant_access_token(self) -> str:
        """
        获取飞书租户访问令牌
        
        Returns:
            str: 租户访问令牌
        """
        try:
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(self.auth_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                return result.get("tenant_access_token")
            else:
                logger.error(f"获取飞书访问令牌失败: {result}")
                raise Exception(f"获取飞书访问令牌失败: {result}")
        except Exception as e:
            logger.error(f"获取飞书访问令牌时出错: {e}")
            raise
    
    def _refresh_token_if_needed(self, response) -> bool:
        """
        检查API响应，如果令牌过期则刷新
        
        Args:
            response: API响应对象或响应的JSON结果
            
        Returns:
            bool: 是否刷新了令牌
        """
        # 处理传入的是response对象的情况
        if hasattr(response, 'status_code') and hasattr(response, 'json'):
            status_code = response.status_code
            try:
                response_json = response.json()
            except:
                response_json = {}
        # 处理传入的是已解析的JSON字典的情况
        elif isinstance(response, dict):
            status_code = 200  # 默认值
            response_json = response
        else:
            logger.error(f"无法处理的响应类型: {type(response)}")
            return False
        
        # 检查是否需要刷新token
        if status_code == 401 or response_json.get("code") == 99991663:
            self.tenant_access_token = self._get_tenant_access_token()
            return True
        return False
    
    def _truncate_large_fields(self, data: Union[pd.DataFrame, List[Dict], List[List]]) -> Union[pd.DataFrame, List[Dict], List[List]]:
        """
        处理超过飞书单元格大小限制的字段
        
        Args:
            data: 要处理的数据
            
        Returns:
            处理后的数据，保证所有字段不超过飞书单元格大小限制
        """
        # 降低安全限制，更激进地截断内容
        max_bytes = 30000  # 降低到30000字节，比原来的45000更安全
        max_cell_size = 25000  # 对于没有明确标记为大文本的字段，如果超过此大小也截断
        
        # 对DataFrame进行处理
        if isinstance(data, pd.DataFrame):
            for col in data.columns:
                # 特别关注这些可能包含大量文本的字段
                is_large_text_field = col.lower() in ['readme', 'description', 'content', 'text', 'text_content', 
                                                     'meta_description', 'seo_text', 'main_links', 'contacts']
                for idx in data.index:
                    value = data.at[idx, col]
                    if value and isinstance(value, str):
                        # 计算字符串的字节大小
                        byte_size = len(value.encode('utf-8'))
                        
                        # 如果是已知的大文本字段，或者任何字段超过最大限制，都进行截断
                        if (is_large_text_field and byte_size > max_bytes) or byte_size > max_cell_size:
                            # 截断字符串，确保截断后的字节大小不超过限制
                            truncated = value
                            while len(truncated.encode('utf-8')) > max_bytes:
                                # 更激进的截断：每次减少20%而不是10%
                                truncated = truncated[:int(len(truncated)*0.8)]
                            
                            # 添加提示信息，提示更简短
                            truncated = truncated + "\n... (内容已截断)"
                            data.at[idx, col] = truncated
                            logger.info(f"字段 {col} 已截断，原始大小: {byte_size} 字节，截断后大小: {len(truncated.encode('utf-8'))} 字节")
        
        # 对字典列表进行处理
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            for item in data:
                for key, value in list(item.items()):  # 使用list()复制键列表，避免在迭代中修改字典
                    # 检查所有字符串类型字段
                    if value and isinstance(value, str):
                        byte_size = len(value.encode('utf-8'))
                        is_large_text_field = key.lower() in ['readme', 'description', 'content', 'text', 'text_content', 
                                                           'meta_description', 'seo_text', 'main_links', 'contacts']
                        
                        # 如果是已知的大文本字段，或者任何字段超过最大限制，都进行截断
                        if (is_large_text_field and byte_size > max_bytes) or byte_size > max_cell_size:
                            # 截断字符串
                            truncated = value
                            while len(truncated.encode('utf-8')) > max_bytes:
                                truncated = truncated[:int(len(truncated)*0.8)]
                            
                            # 添加提示信息
                            truncated = truncated + "\n... (内容已截断)"
                            item[key] = truncated
                            logger.info(f"字段 {key} 已截断，原始大小: {byte_size} 字节，截断后大小: {len(truncated.encode('utf-8'))} 字节")
        
        # 对嵌套列表进行处理
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            # 假设第一行是表头
            headers = data[0] if len(data) > 0 else []
            for row_idx in range(1, len(data)):
                row = data[row_idx]
                for col_idx in range(len(row)):
                    value = row[col_idx]
                    if value and isinstance(value, str):
                        byte_size = len(value.encode('utf-8'))
                        
                        # 尝试从表头中获取字段名称
                        field_name = headers[col_idx] if col_idx < len(headers) else f"column_{col_idx}"
                        is_large_text_field = str(field_name).lower() in ['readme', 'description', 'content', 'text', 'text_content', 
                                                                      'meta_description', 'seo_text', 'main_links', 'contacts']
                        
                        # 如果是已知的大文本字段，或者任何字段超过最大限制，都进行截断
                        if (is_large_text_field and byte_size > max_bytes) or byte_size > max_cell_size:
                            # 截断字符串
                            truncated = value
                            while len(truncated.encode('utf-8')) > max_bytes:
                                truncated = truncated[:int(len(truncated)*0.8)]
                            
                            # 添加提示信息
                            truncated = truncated + "\n... (内容已截断)"
                            data[row_idx][col_idx] = truncated
                            logger.info(f"字段 {field_name} 已截断，原始大小: {byte_size} 字节，截断后大小: {len(truncated.encode('utf-8'))} 字节")
        
        return data

    def write_to_feishu_sheet(self, spreadsheet_token: str, sheet_id: str, data: Union[pd.DataFrame, List[Dict]], start_cell: str = "A1") -> bool:
        """
        将数据写入飞书电子表格
        
        Args:
            spreadsheet_token: 电子表格的token
            sheet_id: 工作表ID
            data: 要写入的数据，可以是pandas DataFrame或字典列表
            start_cell: 起始单元格，默认为A1
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 先进行数据截断处理，确保不超过飞书单元格限制
            data = self._truncate_large_fields(data)
            
            if isinstance(data, pd.DataFrame):
                # DataFrame情况
                headers = list(data.columns)
                values = []
                
                # 添加表头
                values.append(headers)
                
                # 添加数据
                for _, row in data.iterrows():
                    # 再次确保每个单元格不超过限制
                    row_values = []
                    for col in headers:
                        value = row[col]
                        # 对所有字符串值进行额外检查
                        if isinstance(value, str) and len(value.encode('utf-8')) > 30000:
                            # 进行更激进的截断
                            truncated = value
                            while len(truncated.encode('utf-8')) > 30000:
                                truncated = truncated[:int(len(truncated)*0.8)]
                            value = truncated + "\n... (内容已截断)"
                            logger.info(f"在写入过程中额外截断字段 {col}，确保安全")
                        row_values.append(value)
                    values.append(row_values)
                
                # 请求体
                request_data = {
                    "valueRange": {
                        "range": f"{sheet_id}!{start_cell}",
                        "values": values
                    }
                }
                
                # 发送请求
                url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.get_access_token()}'
                }
                
                logger.info(f"正在写入数据到飞书表格: {url}")
                response = requests.put(url, headers=headers, json=request_data)
                
                # 检查响应
                response_json = response.json()
                if response_json.get("code") == 0:
                    logger.info(f"成功写入数据到飞书表格: {spreadsheet_token}, 共 {len(values)-1} 行")
                    return True
                else:
                    # 尝试刷新token并重试
                    if self._refresh_token_if_needed(response_json):
                        headers['Authorization'] = f'Bearer {self.get_access_token()}'
                        response = requests.put(url, headers=headers, json=request_data)
                        response_json = response.json()
                        
                        if response_json.get("code") == 0:
                            logger.info(f"刷新token后成功写入数据到飞书表格: {spreadsheet_token}")
                            return True
                    
                    # 第二次失败，尝试批量API写入
                    logger.warning(f"使用单一值范围API写入失败，尝试使用批量更新API: {response_json}")
                    return self._write_with_batch_update(spreadsheet_token, sheet_id, values)
            
            elif isinstance(data, list):
                # 字典列表情况
                if not data:
                    logger.warning("没有数据需要写入飞书表格")
                    return True
                
                if isinstance(data[0], dict):
                    # 提取所有键作为表头
                    headers = list(data[0].keys())
                    values = [headers]  # 第一行是表头
                    
                    # 添加数据行
                    for item in data:
                        # 再次确保每个单元格不超过限制
                        row_values = []
                        for key in headers:
                            value = item.get(key, "")
                            # 对所有字符串值进行额外检查
                            if isinstance(value, str) and len(value.encode('utf-8')) > 30000:
                                # 进行更激进的截断
                                truncated = value
                                while len(truncated.encode('utf-8')) > 30000:
                                    truncated = truncated[:int(len(truncated)*0.8)]
                                value = truncated + "\n... (内容已截断)"
                                logger.info(f"在写入过程中额外截断字段 {key}，确保安全")
                            row_values.append(value)
                        values.append(row_values)
                else:
                    # 已经是二维列表
                    values = data
                    
                    # 再次确保每个单元格不超过限制
                    for i in range(len(values)):
                        for j in range(len(values[i])):
                            value = values[i][j]
                            if isinstance(value, str) and len(value.encode('utf-8')) > 30000:
                                # 进行更激进的截断
                                truncated = value
                                while len(truncated.encode('utf-8')) > 30000:
                                    truncated = truncated[:int(len(truncated)*0.8)]
                                values[i][j] = truncated + "\n... (内容已截断)"
                                field_name = values[0][j] if i > 0 and j < len(values[0]) else f"column_{j}"
                                logger.info(f"在写入过程中额外截断字段 {field_name}，确保安全")
                
                # 请求体
                request_data = {
                    "valueRange": {
                        "range": f"{sheet_id}!{start_cell}",
                        "values": values
                    }
                }
                
                # 发送请求
                url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.get_access_token()}'
                }
                
                logger.info(f"正在写入数据到飞书表格: {url}")
                response = requests.put(url, headers=headers, json=request_data)
                
                # 检查响应
                response_json = response.json()
                if response_json.get("code") == 0:
                    logger.info(f"成功写入数据到飞书表格: {spreadsheet_token}, 共 {len(values)-1} 行")
                    return True
                else:
                    # 尝试刷新token并重试
                    if self._refresh_token_if_needed(response_json):
                        headers['Authorization'] = f'Bearer {self.get_access_token()}'
                        response = requests.put(url, headers=headers, json=request_data)
                        response_json = response.json()
                        
                        if response_json.get("code") == 0:
                            logger.info(f"刷新token后成功写入数据到飞书表格: {spreadsheet_token}")
                            return True
                    
                    # 第二次失败，尝试批量API写入
                    logger.warning(f"使用单一值范围API写入失败，尝试使用批量更新API: {response_json}")
                    return self._write_with_batch_update(spreadsheet_token, sheet_id, values)
            else:
                logger.error(f"不支持的数据类型: {type(data)}")
                return False
                
        except Exception as e:
            logger.error(f"写入飞书表格失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def read_from_feishu_sheet(self, spreadsheet_token: str, sheet_id: str, cell_range: str = None) -> Optional[pd.DataFrame]:
        """
        从飞书电子表格读取数据
        
        Args:
            spreadsheet_token (str): 电子表格的token，形如"shtcn******"
            sheet_id (str): 工作表ID，形如"0b******"
            cell_range (str, optional): 单元格范围，例如"A1:F10"，默认为整个表格
            
        Returns:
            Optional[pd.DataFrame]: 包含表格数据的DataFrame，失败时返回None
        """
        try:
            # 构建API请求
            if cell_range:
                url = f"{self.sheets_url}{spreadsheet_token}/values/{sheet_id}!{cell_range}"
            else:
                url = f"{self.sheets_url}{spreadsheet_token}/values/{sheet_id}"
            
            headers = {
                "Authorization": f"Bearer {self.tenant_access_token}"
            }
            
            # 发送请求
            response = requests.get(url, headers=headers)
            
            # 检查是否需要刷新令牌
            if self._refresh_token_if_needed(response):
                # 更新授权头并重试请求
                headers["Authorization"] = f"Bearer {self.tenant_access_token}"
                response = requests.get(url, headers=headers)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                values = result.get("data", {}).get("valueRange", {}).get("values", [])
                
                if not values:
                    logger.warning(f"飞书表格 {spreadsheet_token}/{sheet_id} 没有数据")
                    return pd.DataFrame()
                
                # 将值列表转换为DataFrame
                df = pd.DataFrame(values[1:], columns=values[0])
                logger.info(f"成功读取飞书表格: {spreadsheet_token}/{sheet_id}")
                return df
            else:
                logger.error(f"读取飞书表格失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"读取飞书表格时出错: {e}")
            return None
    
    def append_to_feishu_sheet(self, spreadsheet_token: str, sheet_id: str, data: Union[pd.DataFrame, List[Dict], List[List]], append_type: str = "after") -> bool:
        """
        向飞书电子表格追加数据
        
        Args:
            spreadsheet_token (str): 电子表格的token
            sheet_id (str): 工作表ID
            data (Union[pd.DataFrame, List[Dict], List[List]]): 要追加的数据
            append_type (str, optional): 追加类型，'after' 表示追加到最后一行的后面，'overwrite' 表示覆盖已有数据
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 首先，获取当前表格的数据，确定起始单元格
            url = f"{self.sheets_url}{spreadsheet_token}/values/{sheet_id}"
            headers = {
                "Authorization": f"Bearer {self.tenant_access_token}"
            }
            
            response = requests.get(url, headers=headers)
            
            # 检查是否需要刷新令牌
            if self._refresh_token_if_needed(response):
                headers["Authorization"] = f"Bearer {self.tenant_access_token}"
                response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"获取表格数据失败: {response.text}")
                return False
            
            result = response.json()
            existing_values = []
            
            if result.get("code") == 0:
                existing_values = result.get("data", {}).get("valueRange", {}).get("values", [])
                logger.info(f"成功获取表格数据，行数: {len(existing_values)}")
            else:
                logger.error(f"获取表格数据失败: {result}")
                return False
            
            # 准备要追加的数据
            values_to_append = None
            
            # 根据数据类型转换为适当的格式
            if isinstance(data, pd.DataFrame):
                # 获取列名作为表头
                headers = data.columns.tolist()
                values_to_append = [headers]  # 表头作为第一行
                
                # 将DataFrame数据转换为列表
                for _, row in data.iterrows():
                    values_to_append.append(row.tolist())
            elif isinstance(data, list) and data:
                if isinstance(data[0], dict):
                    # 提取字典的键作为表头
                    headers = list(data[0].keys())
                    values_to_append = [headers]  # 表头作为第一行
                    
                    # 将字典数据转换为列表
                    for item in data:
                        row = [item.get(key, "") for key in headers]
                        values_to_append.append(row)
                elif isinstance(data[0], list):
                    # 如果已经是嵌套列表格式，直接使用
                    values_to_append = data
            
            if not values_to_append:
                logger.error("没有有效的数据可追加")
                return False
            
            # 保存原始数据和表头
            original_values_to_append = values_to_append.copy() if isinstance(values_to_append, list) else values_to_append
            original_headers = None
            if len(existing_values) > 0:
                original_headers = existing_values[0]
            
            # 飞书API有时会对A2这样的单元格范围有问题，直接使用重写整个表格的方式
            # 即使对于追加操作，我们仍然准备整个表格的数据，从A1开始重写
            if len(existing_values) > 0 and len(values_to_append) > 0:
                # 已有数据，且有表头
                existing_header = existing_values[0] if existing_values else None
                append_header = values_to_append[0] if values_to_append else None
                
                # 检查headers是否匹配
                headers_match = False
                if existing_header and append_header and len(existing_header) == len(append_header):
                    headers_match = all(str(append_header[i]) == str(existing_header[i]) for i in range(len(existing_header)))
                
                if headers_match:
                    logger.info("表头匹配，合并数据重写整个表格")
                    # 构建完整数据，保留表头
                    complete_data = [existing_header]  # 使用原表头
                    # 添加原有数据（除表头外）
                    if len(existing_values) > 1:
                        complete_data.extend(existing_values[1:])
                    # 添加新数据（除表头外）
                    if len(values_to_append) > 1:
                        complete_data.extend(values_to_append[1:])
                else:
                    logger.warning("表头不匹配，尝试覆盖重写整个表格")
                    # 如果表头不匹配，默认使用新数据的表头和内容
                    complete_data = values_to_append
            else:
                # 如果表格为空或新数据为空，直接使用新数据
                logger.info("表格为空或新数据为空，直接写入新数据")
                complete_data = values_to_append
            
            # 使用批量更新API直接写入整个表格
            batch_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update"
            batch_payload = {
                "valueRanges": [
                    {
                        "range": f"{sheet_id}",  # 从整个表格开始，而不是A2
                        "values": complete_data
                    }
                ]
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.tenant_access_token}"
            }
            
            logger.info(f"使用批量更新API重写整个表格: {batch_url}")
            logger.info(f"请求头: {headers}")
            logger.info(f"数据行数: {len(complete_data)}")
            
            batch_response = requests.post(batch_url, headers=headers, json=batch_payload)
            
            # 检查是否需要刷新令牌
            if self._refresh_token_if_needed(batch_response):
                headers["Authorization"] = f"Bearer {self.tenant_access_token}"
                batch_response = requests.post(batch_url, headers=headers, json=batch_payload)
            
            batch_response_text = batch_response.text
            logger.info(f"飞书批量更新API响应: {batch_response_text}")
            
            if batch_response.status_code >= 200 and batch_response.status_code < 300:
                try:
                    batch_result = batch_response.json()
                    if batch_result.get("code") == 0:
                        logger.info(f"成功写入飞书表格: {spreadsheet_token}/{sheet_id}")
                        return True
                    else:
                        logger.error(f"写入飞书表格失败: {batch_result}")
                        return False
                except Exception as json_error:
                    logger.error(f"解析批量更新响应JSON时出错: {json_error}, 原始响应: {batch_response_text}")
                    return False
            else:
                logger.error(f"批量更新请求失败，状态码: {batch_response.status_code}, 响应: {batch_response_text}")
                return False
            
        except Exception as e:
            logger.error(f"追加到飞书表格时出错: {e}")
            traceback.print_exc()
            return False

    def _extract_url_from_complex_value(self, value: Any) -> str:
        """
        从复杂URL值（如字典或列表）中提取纯URL
        
        Args:
            value (Any): 复杂的URL值，可能是字典、列表或字符串
            
        Returns:
            str: 提取的URL字符串
        """
        try:
            # 处理字典情况
            if isinstance(value, dict) and 'link' in value:
                return value['link']
            
            # 处理列表情况
            elif isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict) and 'link' in value[0]:
                    return value[0]['link']
                else:
                    # 尝试将列表转换为字符串并返回
                    return str(value[0]) if len(value) > 0 else ""
            
            # 处理字符串情况
            elif isinstance(value, str):
                # 检查是否是JSON字符串
                if value.startswith('{') or value.startswith('['):
                    try:
                        import json
                        parsed = json.loads(value)
                        # 递归处理
                        return self._extract_url_from_complex_value(parsed)
                    except:
                        pass
                return value
            
            # 其他情况，转换为字符串
            return str(value)
        except Exception as e:
            logger.error(f"提取URL时出错: {e}, 值: {value}")
            return str(value)

    def delete_record_optimized(self, spreadsheet_token: str, sheet_id: str, filter_column: str, filter_value: str, 
                                 force_delete_all: bool = False) -> bool:
        """
        使用行删除API删除匹配的记录，无备用方法
        
        Args:
            spreadsheet_token (str): 电子表格token
            sheet_id (str): 工作表ID
            filter_column (str): 过滤列名
            filter_value (str): 过滤值
            force_delete_all (bool): 是否强制删除所有匹配的记录
            
        Returns:
            bool: 操作是否成功
        """
        # Step 1: 读取电子表格数据
        data = self.read_from_feishu_sheet(spreadsheet_token, sheet_id)
        if data is None or (hasattr(data, 'empty') and data.empty):
            logger.warning("表格为空或读取失败，无需删除")
            print("表格为空或读取失败，无需删除")
            return True
        
        # Step 2: 检查过滤列是否存在
        if filter_column not in data.columns:
            logger.error(f"过滤列 '{filter_column}' 不存在于表格中")
            print(f"❌ 过滤列 '{filter_column}' 不存在于表格中")
            return False
        
        # Step 3: 标准化URL字段，确保比较时一致
        if filter_column in ['repository_url', 'website_url', 'url']:
            data[filter_column] = data[filter_column].apply(self._extract_url_from_complex_value)
            filter_value = self._extract_url_from_complex_value(filter_value)
        
        try:
            # 找出所有匹配的行
            matching_indices = []
            for i, row in data.iterrows():
                if row[filter_column] == filter_value:
                    # 注意：API中行索引从1开始，1是表头，所以数据行从索引2开始
                    matching_indices.append(i + 2)  # +2 是因为索引1是表头，数据从2开始
                    if not force_delete_all:
                        break
            
            if not matching_indices:
                logger.info(f"未找到匹配记录: {filter_column}={filter_value}")
                print(f"✅ 未找到匹配记录，无需删除")
                return True
            
            print(f"找到 {len(matching_indices)} 条匹配记录，索引: {matching_indices}")
            logger.info(f"找到 {len(matching_indices)} 条匹配记录需要删除，API行索引: {matching_indices}")
            
            # 按索引从大到小排序，避免删除时索引偏移
            matching_indices.sort(reverse=True)
            
            # 逐行删除匹配的记录
            for idx in matching_indices:
                success = self._delete_single_row_with_official_api(spreadsheet_token, sheet_id, idx)
                if not success:
                    logger.error(f"删除行索引 {idx} 失败")
                    print(f"❌ 删除行索引 {idx} 失败")
                    return False  # 立即返回错误，不再继续
            
            logger.info("成功删除所有匹配记录")
            print("✅ 成功删除所有匹配记录")
            return True
                
        except Exception as e:
            logger.error(f"行删除API操作出错: {e}")
            print(f"❌ 行删除API出错: {str(e)}")
            return False

    def _delete_single_row_with_official_api(self, spreadsheet_token: str, sheet_id: str, row_index: int) -> bool:
        """
        使用飞书官方API删除指定的单行数据
        
        Args:
            spreadsheet_token (str): 电子表格token
            sheet_id (str): 工作表ID
            row_index (int): 要删除的行索引，注意API中索引1是表头，数据行从索引2开始
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 构建正确的API URL，注意使用DELETE请求
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/dimension_range"
            
            # 构建请求体，根据官方文档设置
            # https://open.feishu.cn/document/server-docs/docs/sheets-v3/sheet-rowcol/-delete-rows-or-columns
            payload = {
                "dimension": {
                    "sheetId": sheet_id,
                    "majorDimension": "ROWS",
                    "startIndex": row_index,      # 开始的位置
                    "endIndex": row_index         # 结束的位置 - 设置为与startIndex相同，只删除一行
                }
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.tenant_access_token}"
            }
            
            logger.info(f"发送DELETE请求删除行: {row_index}, 请求体: {payload}")
            print(f"发送删除请求，行索引: {row_index}, 请求体: {payload}")
            
            # 发送DELETE请求
            response = requests.delete(url, headers=headers, json=payload)
            
            # 检查是否需要刷新token
            if self._refresh_token_if_needed(response):
                headers["Authorization"] = f"Bearer {self.tenant_access_token}"
                response = requests.delete(url, headers=headers, json=payload)
            
            # 检查响应状态码
            if response.status_code == 404:
                logger.error(f"API端点不存在，HTTP状态码: {response.status_code}")
                print(f"❌ API端点不存在，请检查API文档")
                return False
                
            # 尝试解析JSON响应
            if response.text and response.text.strip():
                try:
                    result = response.json()
                    logger.info(f"删除行API响应: {result}")
                    
                    if result.get("code") == 0:
                        logger.info(f"成功删除行 {row_index}")
                        print(f"✅ 成功删除行 {row_index}")
                        return True
                    else:
                        error_msg = result.get("msg", "未知错误")
                        logger.error(f"删除行API返回错误: {error_msg}")
                        print(f"❌ 删除行失败: {error_msg}")
                        return False
                except Exception as json_error:
                    logger.error(f"解析API响应时出错: {json_error}, 响应内容: {response.text}")
            else:
                # 响应为空时的处理
                logger.warning("API返回空响应")
                
            # 根据HTTP状态码判断是否成功
            if 200 <= response.status_code < 300:
                logger.info(f"基于HTTP状态码 {response.status_code} 判断删除操作成功")
                return True
            else:
                logger.error(f"删除操作失败，HTTP状态码: {response.status_code}, 响应: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"删除行时发生异常: {e}")
            print(f"❌ 删除行时发生异常: {str(e)}")
            return False

    def delete_website_record(self, website_url: str, force_delete_all: bool = False) -> bool:
        """
        从网站数据表中删除指定的网站记录
        
        Args:
            website_url (str): 要删除的网站URL
            force_delete_all (bool, optional): 即使会清空表格也强制删除所有匹配记录
            
        Returns:
            bool: 操作是否成功
        """
        print(f"正在从网站数据表中删除网站: {website_url}")
        return self.delete_record_optimized(
            self.website_spreadsheet_token,
            self.website_sheet_id,
            "website_url",
            website_url,
            force_delete_all
        )
        
    def delete_github_record(self, repository_url: str, force_delete_all: bool = False) -> bool:
        """
        从GitHub数据表中删除指定的仓库记录
        
        Args:
            repository_url (str): 要删除的仓库URL
            force_delete_all (bool, optional): 即使会清空表格也强制删除所有匹配记录
            
        Returns:
            bool: 操作是否成功
        """
        print(f"正在从GitHub数据表中删除仓库: {repository_url}")
        return self.delete_record_optimized(
            self.github_spreadsheet_token,
            self.github_sheet_id,
            "repository_url",
            repository_url,
            force_delete_all
        )

    def _normalize_url_fields(self, df: pd.DataFrame, url_columns: List[str]) -> pd.DataFrame:
        """
        标准化DataFrame中的URL字段，将复杂URL转换为简单字符串
        
        Args:
            df (pd.DataFrame): 要处理的数据框
            url_columns (List[str]): 包含URL的列名列表
            
        Returns:
            pd.DataFrame: 处理后的数据框
        """
        if df is None or df.empty:
            return df
            
        # 复制DataFrame避免修改原始数据
        processed_df = df.copy()
        
        for col in url_columns:
            if col in processed_df.columns:
                # 应用转换函数到每个URL单元格
                processed_df[col] = processed_df[col].apply(self._extract_url_from_complex_value)
        
        return processed_df 

    def clean_and_deduplicate_sheet(self, spreadsheet_token: str, sheet_id: str, url_column: str = None) -> bool:
        """
        清理飞书表格中的重复数据
        
        Args:
            spreadsheet_token (str): 电子表格的token，形如"shtcn******"
            sheet_id (str): 工作表ID，形如"0b******"
            url_column (str, optional): URL列名，如果指定了这个参数，将根据这个列进行去重
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 读取当前表格数据
            df = self.read_from_feishu_sheet(spreadsheet_token, sheet_id)
            
            if df is None or df.empty:
                logger.warning(f"表格为空或读取失败，无法清理")
                return False
            
            original_rows = len(df)
            logger.info(f"清理前表格有 {original_rows} 行")
            
            # 如果指定了URL列，根据URL去重
            if url_column and url_column in df.columns:
                # 将复杂URL列转换为纯文本
                extracted_urls = []
                for i, row in df.iterrows():
                    cell_value = row[url_column]
                    extracted_url = self._extract_url_from_complex_value(cell_value)
                    extracted_urls.append(extracted_url)
                
                # 存储已处理的URL和对应的行索引
                processed_urls = {}
                keep_rows = []
                
                # 第一遍标记要保留的行
                for i, url in enumerate(extracted_urls):
                    if url not in processed_urls:
                        processed_urls[url] = i
                        keep_rows.append(True)
                    else:
                        keep_rows.append(False)
                
                # 筛选需要保留的行
                df_deduped = df[keep_rows]
            else:
                # 否则，根据所有列去重
                df_deduped = df.drop_duplicates()
            
            # 如果没有发现重复行，直接返回
            if len(df_deduped) == original_rows:
                logger.info("未发现重复数据")
                return True
            
            logger.info(f"清理后表格有 {len(df_deduped)} 行，移除了 {original_rows - len(df_deduped)} 行重复数据")
            
            # 清空表格 - 修复：使用正确的方式确保表格被完全清空
            # 首先获取表格的元数据，以确定表格的大小
            meta_url = f"{self.sheets_url}{spreadsheet_token}/sheets/{sheet_id}"
            headers = {
                "Authorization": f"Bearer {self.tenant_access_token}"
            }
            
            meta_response = requests.get(meta_url, headers=headers)
            
            # 检查是否需要刷新令牌
            if self._refresh_token_if_needed(meta_response):
                headers["Authorization"] = f"Bearer {self.tenant_access_token}"
                meta_response = requests.get(meta_url, headers=headers)
            
            meta_response.raise_for_status()
            meta_result = meta_response.json()
            
            if meta_result.get("code") == 0:
                # 获取行数和列数
                grid_data = meta_result.get("data", {}).get("sheet", {}).get("grid_data", {})
                row_count = 100  # 默认清空100行
                col_count = 10   # 默认清空10列
                
                if grid_data:
                    row_count = grid_data.get("row_count", row_count)
                    col_count = grid_data.get("column_count", col_count)
                
                # 创建一个全空的二维数组
                empty_values = [["" for _ in range(col_count)] for _ in range(row_count)]
                
                # 清空整个表格范围
                empty_payload = {
                    "valueRange": {
                        "range": f"{sheet_id}!A1:{chr(65+col_count-1)}{row_count}",
                        "values": empty_values
                    }
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.tenant_access_token}"
                }
                
                clear_url = f"{self.sheets_url}{spreadsheet_token}/values"
                clear_response = requests.put(clear_url, headers=headers, json=empty_payload)
                
                # 检查是否需要刷新令牌
                if self._refresh_token_if_needed(clear_response):
                    headers["Authorization"] = f"Bearer {self.tenant_access_token}"
                    clear_response = requests.put(clear_url, headers=headers, json=empty_payload)
                
                clear_response.raise_for_status()
                
                # 等待清空操作完成
                import time
                time.sleep(1)
                
                # 写回去重后的数据
                return self.write_to_feishu_sheet(spreadsheet_token, sheet_id, df_deduped)
            else:
                logger.error(f"获取表格元数据失败: {meta_result}")
                return False
                
        except Exception as e:
            logger.error(f"清理表格时出错: {e}")
            return False
            
    def clean_github_data(self) -> bool:
        """清理GitHub数据表中的重复记录"""
        return self.clean_and_deduplicate_sheet(self.github_spreadsheet_token, self.github_sheet_id, "repository_url")

    def clean_website_data(self) -> bool:
        """清理网站数据表中的重复记录"""
        return self.clean_and_deduplicate_sheet(self.website_spreadsheet_token, self.website_sheet_id, "website_url")
    
    def clean_and_deduplicate_github_sheet(self) -> bool:
        """清理GitHub数据表中的重复记录"""
        return self.clean_github_data()
    
    def clean_and_deduplicate_website_sheet(self) -> bool:
        """清理网站数据表中的重复记录"""
        return self.clean_website_data()

    # 便捷方法，用于常用表格操作
    
    def write_github_data(self, data: Union[pd.DataFrame, List[Dict]], start_cell: str = "A1") -> bool:
        """将GitHub数据写入飞书表格"""
        return self.write_to_feishu_sheet(
            self.github_spreadsheet_token, 
            self.github_sheet_id, 
            data, 
            start_cell
        )
    
    def read_github_data(self, cell_range: str = None) -> Optional[pd.DataFrame]:
        """从飞书表格读取GitHub数据"""
        return self.read_from_feishu_sheet(
            self.github_spreadsheet_token,
            self.github_sheet_id,
            cell_range
        )
    
    def append_github_data(self, data: Union[pd.DataFrame, List[Dict]]) -> bool:
        """
        将GitHub数据追加到飞书电子表格
        
        Args:
            data (Union[pd.DataFrame, List[Dict]]): 要追加的数据，可以是pandas DataFrame或字典列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 处理超过飞书单元格大小限制的字段
            data = self._truncate_large_fields(data)
            
            # 过滤掉已存在的URL
            filtered_data = []
            
            if isinstance(data, pd.DataFrame):
                # 确保repository_url列存在
                if 'repository_url' not in data.columns:
                    logger.error("数据中缺少repository_url列，无法进行URL检查")
                    return False
                
                # 检查每一行
                for _, row in data.iterrows():
                    url = row['repository_url']
                    
                    # 检查URL是否已存在于飞书表格
                    exists = self._url_exists_in_sheet(
                        self.github_spreadsheet_token,
                        self.github_sheet_id,
                        'repository_url',
                        url
                    )
                    
                    if exists:
                        logger.info(f"URL已存在于飞书表格，跳过: {url}")
                    else:
                        # 再次处理该行数据，确保单元格大小不超过限制
                        row_dict = row.to_dict()
                        processed_row = self._truncate_large_fields([row_dict])[0]
                        filtered_data.append(processed_row)
            else:
                # 字典列表情况
                for item in data:
                    if 'repository_url' not in item:
                        logger.error("数据项中缺少repository_url字段，无法进行URL检查")
                        continue
                        
                    url = item['repository_url']
                    
                    # 检查URL是否已存在于飞书表格
                    exists = self._url_exists_in_sheet(
                        self.github_spreadsheet_token,
                        self.github_sheet_id,
                        'repository_url',
                        url
                    )
                    
                    if exists:
                        logger.info(f"URL已存在于飞书表格，跳过: {url}")
                    else:
                        # 再次处理该数据项，确保单元格大小不超过限制
                        processed_item = self._truncate_large_fields([item])[0]
                        filtered_data.append(processed_item)
            
            # 如果没有新数据需要追加，直接返回成功
            if not filtered_data:
                logger.info("没有新数据需要追加到飞书表格")
                return True
            
            # 进行最终安全检查，确保所有字段大小都在限制范围内
            final_data = self._truncate_large_fields(filtered_data)
            
            # 追加到电子表格
            result = self.append_to_feishu_sheet(
                self.github_spreadsheet_token,
                self.github_sheet_id,
                final_data
            )
            
            return result
        except Exception as e:
            logger.error(f"追加GitHub数据到飞书失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def write_website_data(self, data: Union[pd.DataFrame, List[Dict]], start_cell: str = "A1") -> bool:
        """将网站数据写入飞书表格"""
        return self.write_to_feishu_sheet(
            self.website_spreadsheet_token, 
            self.website_sheet_id, 
            data, 
            start_cell
        )
    
    def read_website_data(self, cell_range: str = None) -> Optional[pd.DataFrame]:
        """从飞书表格读取网站数据"""
        return self.read_from_feishu_sheet(
            self.website_spreadsheet_token,
            self.website_sheet_id,
            cell_range
        )
    
    def append_website_data(self, data: Union[pd.DataFrame, List[Dict]]) -> bool:
        """
        向飞书表格追加网站数据，避免重复URL
        
        Args:
            data: 要追加的数据，可以是DataFrame或字典列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 处理超过飞书单元格大小限制的字段
            data = self._truncate_large_fields(data)
            
            # 过滤掉已存在的URL
            filtered_data = []
            
            if isinstance(data, pd.DataFrame):
                # 如果是DataFrame，逐行检查URL是否存在
                for _, row in data.iterrows():
                    if 'website_url' in row:
                        url = row['website_url']
                        if not self._url_exists_in_sheet(
                            self.website_spreadsheet_token, 
                            self.website_sheet_id, 
                            'website_url', 
                            url
                        ):
                            filtered_data.append(row.to_dict())
                
                # 如果没有新数据需要添加，直接返回成功
                if not filtered_data:
                    logger.info("所有网站URL已存在，无需添加")
                    return True
                
                # 转换回DataFrame
                filtered_df = pd.DataFrame(filtered_data)
                return self.append_to_feishu_sheet(
                    self.website_spreadsheet_token,
                    self.website_sheet_id,
                    filtered_df
                )
            
            elif isinstance(data, list) and data:
                # 如果是字典列表，逐个检查URL是否存在
                for item in data:
                    if isinstance(item, dict) and 'website_url' in item:
                        url = item['website_url']
                        if not self._url_exists_in_sheet(
                            self.website_spreadsheet_token, 
                            self.website_sheet_id, 
                            'website_url', 
                            url
                        ):
                            filtered_data.append(item)
                
                # 如果没有新数据需要添加，直接返回成功
                if not filtered_data:
                    logger.info("所有网站URL已存在，无需添加")
                    return True
                
                return self.append_to_feishu_sheet(
                    self.website_spreadsheet_token,
                    self.website_sheet_id,
                    filtered_data
                )
            
            # 无有效数据
            return False
        except Exception as e:
            logger.error(f"向飞书表格追加网站数据时出错: {e}")
            return False
    
    def _url_exists_in_sheet(self, spreadsheet_token: str, sheet_id: str, url_column: str, url_value: str) -> bool:
        """
        检查指定的URL是否已存在于飞书表格中
        
        Args:
            spreadsheet_token (str): 电子表格的token
            sheet_id (str): 工作表ID
            url_column (str): URL列名
            url_value (str): 要检查的URL值
            
        Returns:
            bool: URL是否已存在
        """
        try:
            # 读取当前表格数据
            df = self.read_from_feishu_sheet(spreadsheet_token, sheet_id)
            
            if df is None or df.empty or url_column not in df.columns:
                return False
            
            # 标准化URL
            url_value = self._extract_url_from_complex_value(url_value)
            
            # 检查URL是否已存在
            for index, row in df.iterrows():
                if url_column in row:
                    existing_url = self._extract_url_from_complex_value(row[url_column])
                    if existing_url == url_value:
                        logger.info(f"URL已存在于飞书表格中: {url_value}")
                        return True
            
            return False
        except Exception as e:
            logger.error(f"检查URL是否存在时出错: {e}")
            return False 

    def _write_with_batch_update(self, spreadsheet_token: str, sheet_id: str, values: List[List]) -> bool:
        """
        使用批量更新API写入数据到飞书表格
        
        Args:
            spreadsheet_token: 电子表格的token
            sheet_id: 工作表ID
            values: 要写入的数据，二维列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 构建请求
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.get_access_token()}'
            }
            
            # 检查每个单元格的大小，进行最终检查
            for i in range(len(values)):
                for j in range(len(values[i])):
                    value = values[i][j]
                    if isinstance(value, str) and len(value.encode('utf-8')) > 30000:
                        # 进行极为激进的截断
                        truncated = value
                        while len(truncated.encode('utf-8')) > 30000:
                            truncated = truncated[:int(len(truncated)*0.7)]  # 减少30%
                        values[i][j] = truncated + "\n... (内容已截断)"
                        field_name = values[0][j] if i > 0 and j < len(values[0]) else f"column_{j}"
                        logger.info(f"在批量写入过程中极限截断字段 {field_name}，确保安全")
            
            # 构建请求体
            request_data = {
                "valueRanges": [
                    {
                        "range": f"{sheet_id}!A1",
                        "values": values
                    }
                ]
            }
            
            logger.info(f"正在使用批量更新API写入数据到飞书表格: {url}")
            response = requests.post(url, headers=headers, json=request_data)
            
            # 检查响应
            response_json = response.json()
            if response_json.get("code") == 0:
                logger.info(f"成功使用批量更新API写入数据到飞书表格: {spreadsheet_token}, 共 {len(values)-1} 行")
                return True
            else:
                # 尝试刷新token并重试
                if self._refresh_token_if_needed(response):
                    headers['Authorization'] = f'Bearer {self.get_access_token()}'
                    response = requests.post(url, headers=headers, json=request_data)
                    response_json = response.json()
                    
                    if response_json.get("code") == 0:
                        logger.info(f"刷新token后成功使用批量更新API写入数据到飞书表格: {spreadsheet_token}")
                        return True
                
                # 尝试分批写入数据
                logger.warning(f"批量更新API失败，尝试分批写入数据: {response_json}")
                return self._write_in_batches(spreadsheet_token, sheet_id, values)
        
        except Exception as e:
            logger.error(f"使用批量更新API写入数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _write_in_batches(self, spreadsheet_token: str, sheet_id: str, values: List[List]) -> bool:
        """
        将数据分批写入飞书表格
        
        Args:
            spreadsheet_token: 电子表格的token
            sheet_id: 工作表ID
            values: 要写入的数据，二维列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not values:
                logger.warning("没有数据需要写入")
                return True
            
            # 分批处理，先写入表头
            headers = values[0] if values else []
            success = self._write_single_batch(spreadsheet_token, sheet_id, [headers], "A1")
            if not success:
                logger.error("写入表头失败")
                return False
            
            # 分批写入数据，每批50行
            batch_size = 50
            for i in range(1, len(values), batch_size):
                end_idx = min(i + batch_size, len(values))
                batch = values[i:end_idx]
                
                # 为每一批极限截断数据
                for row_idx in range(len(batch)):
                    for col_idx in range(len(batch[row_idx])):
                        value = batch[row_idx][col_idx]
                        if isinstance(value, str) and len(value.encode('utf-8')) > 20000:
                            # 进行极限截断
                            truncated = value
                            while len(truncated.encode('utf-8')) > 20000:
                                truncated = truncated[:int(len(truncated)*0.6)]  # 减少40%
                            batch[row_idx][col_idx] = truncated + "\n... (内容已极限截断)"
                
                # 计算起始单元格
                start_cell = f"A{i+1}"
                
                # 写入这一批数据
                success = self._write_single_batch(spreadsheet_token, sheet_id, batch, start_cell)
                if not success:
                    logger.error(f"写入第{i}到{end_idx}行数据失败")
                    return False
                
                # 短暂延迟，避免API限制
                time.sleep(0.5)
            
            logger.info(f"成功分批写入数据到飞书表格: {spreadsheet_token}, 共 {len(values)-1} 行")
            return True
            
        except Exception as e:
            logger.error(f"分批写入数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _write_single_batch(self, spreadsheet_token: str, sheet_id: str, batch: List[List], start_cell: str) -> bool:
        """
        写入单批数据到飞书表格
        
        Args:
            spreadsheet_token: 电子表格的token
            sheet_id: 工作表ID
            batch: 要写入的数据批次，二维列表
            start_cell: 起始单元格
            
        Returns:
            bool: 操作是否成功
        """
        try:
            url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.get_access_token()}'
            }
            
            request_data = {
                "valueRange": {
                    "range": f"{sheet_id}!{start_cell}",
                    "values": batch
                }
            }
            
            logger.info(f"正在写入单批数据到飞书表格，起始单元格: {start_cell}, 行数: {len(batch)}")
            response = requests.put(url, headers=headers, json=request_data)
            
            response_json = response.json()
            if response_json.get("code") == 0:
                logger.info(f"成功写入单批数据到飞书表格，起始单元格: {start_cell}")
                return True
            else:
                # 尝试刷新token并重试
                if self._refresh_token_if_needed(response):
                    headers['Authorization'] = f'Bearer {self.get_access_token()}'
                    response = requests.put(url, headers=headers, json=request_data)
                    response_json = response.json()
                    
                    if response_json.get("code") == 0:
                        logger.info(f"刷新token后成功写入单批数据到飞书表格，起始单元格: {start_cell}")
                        return True
                
                logger.error(f"写入单批数据失败，起始单元格: {start_cell}, 错误: {response_json}")
                return False
                
        except Exception as e:
            logger.error(f"写入单批数据失败，起始单元格: {start_cell}, 错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False 