import axios from 'axios';

// 设置API基础URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
axios.defaults.baseURL = API_URL;

// 添加请求拦截器
axios.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    const method = config.method.toUpperCase();
    const url = config.url;
    
    // 记录请求信息
    console.log(`🚀 发送请求: ${method} ${url}`);
    
    // 记录请求体（如果有）
    if (config.data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      console.log('📦 请求数据:', config.data);
    }
    
    return config;
  },
  error => {
    // 对请求错误做些什么
    console.error('❌ 请求配置错误:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器
axios.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    const method = response.config.method.toUpperCase();
    const url = response.config.url;
    const status = response.status;
    
    // 记录响应信息
    console.log(`✅ 收到响应: ${method} ${url} - ${status}`);
    
    // 记录响应数据（可选，数据量可能很大）
    if (process.env.NODE_ENV === 'development') {
      console.log('📄 响应数据:', response.data);
    }
    
    return response;
  },
  error => {
    // 对响应错误做点什么
    if (error.response) {
      // 服务器返回了错误状态码
      const status = error.response.status;
      const method = error.config?.method?.toUpperCase() || 'UNKNOWN';
      const url = error.config?.url || 'UNKNOWN';
      const message = error.response.data?.message || '未知错误';
      
      console.error(`❌ 请求失败: ${method} ${url} - ${status} - ${message}`);
      console.error('📄 错误响应数据:', error.response.data);
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      console.error('⚠️ 未收到服务器响应，请检查API服务器是否运行');
      console.error('📄 请求信息:', error.request);
    } else {
      // 设置请求时发生了错误
      console.error('🔴 请求配置错误:', error.message);
    }
    
    // 将错误信息添加到控制台
    console.error('🔍 完整错误信息:', error);
    
    return Promise.reject(error);
  }
);

// 添加超时设置
axios.defaults.timeout = 30000; // 30秒

// 添加内容类型
axios.defaults.headers.common['Content-Type'] = 'application/json';

export default axios; 