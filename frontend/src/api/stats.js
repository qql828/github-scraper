import axios from 'axios';

/**
 * 获取系统统计数据
 * 
 * @returns {Promise<Object>} 统计数据
 */
export const getStats = async () => {
  console.log('调用API: 获取系统统计数据');
  try {
    console.log('发送请求: GET /api/stats');
    const response = await axios.get('/api/stats');
    console.log('获取统计数据成功:', response.data);
    return response.data;
  } catch (error) {
    console.error('获取统计数据失败:', error);
    console.error('错误详情:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * 获取最近爬取的项目
 * 
 * @returns {Promise<Array>} 最近爬取的项目列表
 */
export const getRecentItems = async () => {
  console.log('调用API: 获取最近爬取的项目');
  try {
    console.log('发送请求: GET /api/recent_items');
    const response = await axios.get('/api/recent_items');
    console.log('获取最近项目成功，项目数:', response.data?.data?.length || 0);
    return response.data;
  } catch (error) {
    console.error('获取最近爬取项目失败:', error);
    console.error('错误详情:', error.response?.data || error.message);
    throw error;
  }
}; 