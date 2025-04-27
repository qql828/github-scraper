"""
测试配置更新功能
"""
import logging
import sys
from utils.config import update_config, get_config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """测试配置更新功能"""
    # 获取当前配置
    config = get_config()
    logger.info(f"当前GitHub Token: {config.github_token}")
    
    # 创建新的配置
    new_config = {
        'github_token': 'test_token_123',
        'max_threads': 10,
        'request_delay': 2.0,
        'invalid_key': 'this_should_be_ignored'
    }
    
    # 更新配置
    result = update_config(new_config)
    if result:
        logger.info("配置更新成功")
    else:
        logger.error("配置更新失败")
        return
    
    # 重新获取配置验证更新
    updated_config = get_config()
    logger.info(f"更新后GitHub Token: {updated_config.github_token}")
    logger.info(f"更新后最大线程数: {updated_config.max_threads}")
    logger.info(f"更新后请求延迟: {updated_config.request_delay}")
    
    # 恢复原始配置（可选）
    restore_config = {
        'github_token': config.github_token,
        'max_threads': config.max_threads,
        'request_delay': config.request_delay
    }
    
    update_config(restore_config)
    logger.info("配置已还原")

if __name__ == "__main__":
    main() 