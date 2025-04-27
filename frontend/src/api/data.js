import axios from 'axios';

/**
 * 获取GitHub仓库数据
 * 
 * @param {Object} filters - 过滤条件
 * @returns {Promise<Array>} 仓库数据列表
 */
export const getGithubData = async (filters = {}) => {
  try {
    const response = await axios.get(`/api/data/github`, { params: filters });
    return response.data;
  } catch (error) {
    console.error('获取GitHub数据失败:', error);
    throw error;
  }
};

/**
 * 获取网站数据
 * 
 * @param {Object} filters - 过滤条件
 * @returns {Promise<Array>} 网站数据列表
 */
export const getWebsiteData = async (filters = {}) => {
  try {
    const response = await axios.get(`/api/data/website`, { params: filters });
    return response.data;
  } catch (error) {
    console.error('获取网站数据失败:', error);
    throw error;
  }
};

/**
 * 删除数据记录
 * 
 * @param {string} url - 要删除的URL
 * @param {boolean} forceDeleteAll - 是否强制删除所有匹配记录
 * @returns {Promise<Object>} 删除结果
 */
export const deleteRecord = async (url, forceDeleteAll = false) => {
  try {
    const response = await axios.post(`/api/delete`, { 
      url, 
      force_delete_all: forceDeleteAll 
    });
    return response.data;
  } catch (error) {
    console.error('删除记录失败:', error);
    throw error;
  }
};

/**
 * 清理并去重数据
 * 
 * @param {string} dataType - 数据类型：'github'或'website'
 * @returns {Promise<Object>} 清理结果
 */
export const cleanData = async (dataType) => {
  try {
    const response = await axios.post(`/api/clean`, { 
      data_type: dataType 
    });
    return response.data;
  } catch (error) {
    console.error('清理数据失败:', error);
    throw error;
  }
};

/**
 * 导出数据为Excel文件
 * 
 * @param {string} dataType - 数据类型：'github'或'website'
 * @param {Object} filters - 过滤条件
 * @returns {Promise<Blob>} Excel文件的Blob对象
 */
export const exportToExcel = async (dataType, filters = {}) => {
  try {
    const response = await axios.get(`/api/export/${dataType}`, {
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error('导出数据失败:', error);
    throw error;
  }
}; 