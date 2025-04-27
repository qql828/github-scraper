import axios from 'axios';

// 获取系统设置
export const getSettings = async () => {
  try {
    const response = await axios.get('/api/settings');
    return response.data;
  } catch (error) {
    console.error('获取设置失败:', error);
    throw error;
  }
};

// 保存系统设置
export const saveSettings = async (settings) => {
  try {
    const response = await axios.post('/api/settings', settings);
    return response.data;
  } catch (error) {
    console.error('保存设置失败:', error);
    throw error;
  }
};

// 测试GitHub Token
export const testGithubToken = async (token) => {
  try {
    const response = await axios.post('/api/test/github_token', { token });
    return response.data;
  } catch (error) {
    console.error('测试GitHub Token失败:', error);
    throw error;
  }
}; 