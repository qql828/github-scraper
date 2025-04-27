import axios from 'axios';

/**
 * 爬取GitHub仓库信息
 * 
 * @param {string} url - GitHub仓库URL
 * @param {Object} options - 附加选项，如代理设置、保存到飞书等
 * @returns {Promise<Object>} 爬取结果
 */
export const scrapeGithubRepo = async (url, options = {}) => {
  try {
    const response = await axios.post(`/api/scrape/github`, {
      url,
      ...options
    });
    return response.data;
  } catch (error) {
    console.error('爬取GitHub仓库失败:', error);
    throw error;
  }
};

/**
 * 爬取网站信息
 * 
 * @param {string} url - 网站URL
 * @param {Object} options - 附加选项，如代理设置、保存到飞书等
 * @returns {Promise<Object>} 爬取结果
 */
export const scrapeWebsite = async (url, options = {}) => {
  try {
    const response = await axios.post(`/api/scrape/website`, {
      url,
      ...options
    });
    return response.data;
  } catch (error) {
    console.error('爬取网站失败:', error);
    throw error;
  }
};

/**
 * 自动识别URL类型并爬取
 * 
 * @param {string} url - URL地址
 * @param {Object} options - 附加选项，如代理设置、保存到飞书等
 * @returns {Promise<Object>} 爬取结果及URL类型
 */
export const scrapeAutoDetect = async (url, options = {}) => {
  try {
    const response = await axios.post(`/api/scrape/auto`, {
      url,
      ...options
    });
    return response.data;
  } catch (error) {
    console.error('自动爬取URL失败:', error);
    throw error;
  }
};

/**
 * 批量爬取URL
 * 
 * @param {Array<string>} urls - URL列表
 * @param {Object} options - 附加选项，如代理设置、保存到飞书等
 * @returns {Promise<Object>} 爬取结果
 */
export const batchScrape = async (urls, options = {}) => {
  try {
    const response = await axios.post(`/api/scrape/batch`, {
      urls,
      ...options
    });
    return response.data;
  } catch (error) {
    console.error('批量爬取失败:', error);
    throw error;
  }
}; 