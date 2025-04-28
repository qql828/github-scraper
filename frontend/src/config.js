// API配置
const config = {
  // API基础URL，根据环境设置不同的值
  apiBaseUrl: process.env.NODE_ENV === 'production' 
    ? process.env.REACT_APP_API_URL || 'http://localhost:5000'
    : '',  // 开发环境中使用proxy配置，这里留空
};

export default config; 