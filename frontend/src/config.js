// API配置
const config = {
  // API基础URL，根据环境设置不同的值
  apiBaseUrl: process.env.NODE_ENV === 'production' 
    ? (
        // 如果是Docker环境且有容器API URL（主要用于容器之间的通信）
        process.env.REACT_APP_CONTAINER_API_URL || 
        // 如果没有容器API URL，则使用普通API URL（用于外部访问）
        process.env.REACT_APP_API_URL || 
        // 默认值
        'http://localhost:5000'
      )
    : '',  // 开发环境中使用proxy配置，这里留空
};

export default config; 