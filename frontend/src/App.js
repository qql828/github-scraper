import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography } from 'antd';
import {
  HomeOutlined,
  GithubOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  SettingOutlined,
  CloudSyncOutlined
} from '@ant-design/icons';

// 导入页面组件
import HomePage from './pages/HomePage';
import GithubPage from './pages/GithubPage';
import WebsitePage from './pages/WebsitePage';
import DataManagePage from './pages/DataManagePage';
import FeishuPage from './pages/FeishuPage';
import SettingsPage from './pages/SettingsPage';

// 导入样式
import './assets/App.css';

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

// 创建一个内部组件来使用路由钩子
const AppContent = () => {
  const location = useLocation();
  const [current, setCurrent] = useState('home');

  // 根据当前路径更新选中的菜单项
  useEffect(() => {
    const pathname = location.pathname;
    if (pathname === '/') setCurrent('home');
    else if (pathname === '/github') setCurrent('github');
    else if (pathname === '/website') setCurrent('website');
    else if (pathname === '/data') setCurrent('data');
    else if (pathname === '/feishu') setCurrent('feishu');
    else if (pathname === '/settings') setCurrent('settings');
  }, [location]);

  const handleClick = (e) => {
    setCurrent(e.key);
  };

  return (
    <Layout className="layout" style={{ minHeight: '100vh' }}>
      <Header>
        <div className="logo" style={{ color: 'white', fontWeight: 'bold' }}>
          GitHub爬虫工具
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[current]}
          onClick={handleClick}
          items={[
            { key: 'home', icon: <HomeOutlined />, label: <Link to="/">首页</Link> },
            { key: 'github', icon: <GithubOutlined />, label: <Link to="/github">GitHub</Link> },
            { key: 'website', icon: <GlobalOutlined />, label: <Link to="/website">网站</Link> },
            { key: 'data', icon: <DatabaseOutlined />, label: <Link to="/data">数据管理</Link> },
            { key: 'feishu', icon: <CloudSyncOutlined />, label: <Link to="/feishu">飞书同步</Link> },
            { key: 'settings', icon: <SettingOutlined />, label: <Link to="/settings">设置</Link> },
          ]}
        />
      </Header>
      <Content style={{ padding: '0 50px' }}>
        <div className="site-layout-content" style={{ margin: '16px 0' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/github" element={<GithubPage />} />
            <Route path="/website" element={<WebsitePage />} />
            <Route path="/data" element={<DataManagePage />} />
            <Route path="/feishu" element={<FeishuPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        GitHub爬虫工具 ©2025 Created by AI与用户合作开发
      </Footer>
    </Layout>
  );
};

// 主App组件
const App = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App; 