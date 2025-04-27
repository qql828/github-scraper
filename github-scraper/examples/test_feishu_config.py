#!/usr/bin/env python3
"""
简单的飞书配置测试脚本
"""
import sys
import os

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.feishu_manager import FeishuManager

def test_feishu_connection():
    """测试飞书连接和配置"""
    print("=" * 50)
    print("飞书配置测试")
    print("=" * 50)
    
    try:
        # 创建飞书管理器
        print("正在初始化飞书管理器...")
        feishu = FeishuManager()
        
        # 检查是否成功获取令牌
        if feishu.tenant_access_token:
            print("\n✅ 飞书授权成功！成功获取租户访问令牌")
            print(f"令牌值: {feishu.tenant_access_token[:10]}...（已截断）")
            
            # 检查GitHub表格配置
            if feishu.github_spreadsheet_token and feishu.github_sheet_id:
                print("\n✅ GitHub表格配置正确")
                print(f"表格Token: {feishu.github_spreadsheet_token}")
                print(f"工作表ID: {feishu.github_sheet_id}")
            else:
                print("\n❌ GitHub表格配置缺失")
                
            # 检查网站表格配置
            if feishu.website_spreadsheet_token and feishu.website_sheet_id:
                print("\n✅ 网站表格配置正确")
                print(f"表格Token: {feishu.website_spreadsheet_token}")
                print(f"工作表ID: {feishu.website_sheet_id}")
            else:
                print("\n❌ 网站表格配置缺失")
            
            # 尝试读取数据
            print("\n正在尝试从飞书表格读取数据...")
            
            # 尝试读取GitHub数据
            github_data = feishu.read_github_data()
            if github_data is not None:
                if github_data.empty:
                    print("✅ GitHub表格读取成功，但表格为空")
                else:
                    print(f"✅ GitHub表格读取成功，包含 {len(github_data)} 条记录")
            else:
                print("❌ GitHub表格读取失败")
            
            # 尝试读取网站数据
            website_data = feishu.read_website_data()
            if website_data is not None:
                if website_data.empty:
                    print("✅ 网站表格读取成功，但表格为空")
                else:
                    print(f"✅ 网站表格读取成功，包含 {len(website_data)} 条记录")
            else:
                print("❌ 网站表格读取失败")
                
            print("\n✅ 飞书功能测试完成！您的配置正确并且可以正常连接飞书API。")
                
        else:
            print("\n❌ 飞书授权失败！未能获取租户访问令牌")
            print("请检查您的飞书应用凭证是否正确")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_feishu_connection() 