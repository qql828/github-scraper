import axios from 'axios';

/**
 * 获取飞书同步状态
 * 
 * @returns {Promise<Object>} 飞书同步状态信息
 */
export const getFeishuStatus = async () => {
  try {
    const response = await axios.get('/api/feishu/status');
    return response.data;
  } catch (error) {
    console.error('获取飞书状态失败:', error);
    throw error;
  }
};

/**
 * 将GitHub数据同步到飞书
 * 
 * @returns {Promise<Object>} 同步结果
 */
export const syncGithubToFeishu = async () => {
  try {
    const response = await axios.post('/api/feishu/sync/github');
    return response.data;
  } catch (error) {
    console.error('同步GitHub数据到飞书失败:', error);
    throw error;
  }
};

/**
 * 将网站数据同步到飞书
 * 
 * @returns {Promise<Object>} 同步结果
 */
export const syncWebsiteToFeishu = async () => {
  try {
    const response = await axios.post('/api/feishu/sync/website');
    return response.data;
  } catch (error) {
    console.error('同步网站数据到飞书失败:', error);
    throw error;
  }
};

/**
 * 清理飞书数据
 * 
 * @param {string} type - 清理类型：'github'或'website'
 * @returns {Promise<Object>} 清理结果
 */
export const cleanFeishuData = async (type) => {
  try {
    const response = await axios.post('/api/feishu/clean', { type });
    return response.data;
  } catch (error) {
    console.error('清理飞书数据失败:', error);
    throw error;
  }
};

/**
 * 更新飞书配置信息
 * 
 * @param {Object} config - 飞书配置信息
 * @returns {Promise<Object>} 更新结果
 */
export const updateFeishuConfig = async (config) => {
  try {
    const response = await axios.post('/api/feishu/config', config);
    return response.data;
  } catch (error) {
    console.error('更新飞书配置失败:', error);
    throw error;
  }
};

/**
 * 获取飞书同步历史记录
 * 
 * @returns {Promise<Array>} 同步历史记录
 */
export const getFeishuSyncHistory = async () => {
  try {
    const response = await axios.get('/api/feishu/sync/history');
    return response.data;
  } catch (error) {
    console.error('获取飞书同步历史失败:', error);
    throw error;
  }
}; 