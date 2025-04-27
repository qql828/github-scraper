import React, { useState, useEffect } from 'react';
import { Typography, Row, Col, Card, Statistic, Space, Button, List, Divider, Empty, message } from 'antd';
import { 
  GithubOutlined, 
  GlobalOutlined, 
  DatabaseOutlined,
  ApiOutlined,
  RocketOutlined,
  ArrowRightOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { getStats, getRecentItems } from '../api/stats';

const { Title, Paragraph } = Typography;

const HomePage = () => {
  const [stats, setStats] = useState({
    github_count: 0,
    website_count: 0,
    last_scrape_time: null
  });
  const [loading, setLoading] = useState(true);
  const [recentItems, setRecentItems] = useState([]);

  // 获取统计数据和最近项目
  const fetchData = async () => {
    try {
      console.log('开始获取首页统计数据和最近项目...');
      setLoading(true);
      
      // 获取统计数据
      const response = await getStats();
      console.log('统计数据响应:', response);
      if (response.success) {
        setStats(response.data);
        console.log('统计数据更新成功:', response.data);
      } else {
        console.warn('获取统计数据失败:', response.message);
      }
      
      // 获取最近爬取的项目
      const recentResponse = await getRecentItems();
      console.log('最近项目响应:', recentResponse);
      if (recentResponse.success) {
        setRecentItems(recentResponse.data || []);
        console.log('最近项目更新成功, 项目数:', recentResponse.data?.length || 0);
      } else {
        console.warn('获取最近项目失败:', recentResponse.message);
      }
    } catch (error) {
      console.error('获取首页数据失败', error);
      message.error('获取数据失败，请重试');
    } finally {
      setLoading(false);
      console.log('首页数据获取完成');
    }
  };

  useEffect(() => {
    console.log('HomePage组件加载，准备获取数据...');
    fetchData();
  }, []);

  // 格式化时间
  const formatDate = (dateString) => {
    if (!dateString) return '从未';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 手动刷新数据
  const handleRefresh = () => {
    console.log('手动刷新首页数据...');
    fetchData();
    message.info('正在刷新数据...');
  };

  // 功能卡片数据
  const features = [
    {
      title: 'GitHub 仓库爬虫',
      icon: <GithubOutlined style={{ fontSize: 24 }} />,
      description: '爬取GitHub仓库的详细信息，包括仓库名称、描述、星标数、Fork数等',
      link: '/github'
    },
    {
      title: '网站信息爬虫',
      icon: <GlobalOutlined style={{ fontSize: 24 }} />,
      description: '爬取网站的基本信息，包括标题、描述、关键词、favicon等',
      link: '/website'
    },
    {
      title: '数据管理',
      icon: <DatabaseOutlined style={{ fontSize: 24 }} />,
      description: '管理已爬取的GitHub仓库和网站数据，支持导入、导出和删除操作',
      link: '/data'
    },
    {
      title: '飞书集成',
      icon: <ApiOutlined style={{ fontSize: 24 }} />,
      description: '与飞书表格集成，自动同步爬取的数据到飞书多维表格中',
      link: '/feishu'
    }
  ];

  return (
    <div className="home-page">
      <div className="hero-section" style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title>GitHub & 网站信息爬虫</Title>
        <Paragraph style={{ fontSize: '16px' }}>
          一个强大的爬虫工具，用于爬取 GitHub 仓库和网站信息，并支持与飞书表格集成
        </Paragraph>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={handleRefresh} 
          loading={loading}
          style={{ marginTop: 8 }}
        >
          刷新数据
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
        <Col xs={24} sm={8}>
          <Card loading={loading}>
            <Statistic 
              title="GitHub 仓库数量" 
              value={stats.github_count} 
              prefix={<GithubOutlined />} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card loading={loading}>
            <Statistic 
              title="网站数量" 
              value={stats.website_count} 
              prefix={<GlobalOutlined />} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card loading={loading}>
            <Statistic 
              title="最后爬取时间" 
              value={formatDate(stats.last_scrape_time)} 
              prefix={<RocketOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      {/* 最近爬取项目 */}
      <Card 
        title="最近爬取的项目" 
        style={{ marginBottom: 48 }}
        loading={loading}
        extra={
          <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
            刷新
          </Button>
        }
      >
        {recentItems.length > 0 ? (
          <List
            itemLayout="horizontal"
            dataSource={recentItems}
            renderItem={item => (
              <List.Item>
                <List.Item.Meta
                  avatar={item.type === 'github' ? <GithubOutlined /> : <GlobalOutlined />}
                  title={
                    <a 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                    >
                      {item.repository_name || item.title || item.url}
                    </a>
                  }
                  description={
                    <Space direction="vertical" size={0}>
                      <span>{item.description || '无描述'}</span>
                      <span style={{ color: 'rgba(0,0,0,0.45)', fontSize: '12px' }}>
                        类型: {item.type === 'github' ? 'GitHub仓库' : '网站'}
                      </span>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty description="暂无数据，请先爬取GitHub仓库或网站" />
        )}
      </Card>

      {/* 功能卡片 */}
      <Divider orientation="left">主要功能</Divider>
      <Row gutter={[24, 24]}>
        {features.map((feature, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card 
              variant="hoverable" 
              style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
              styles={{ body: { flex: 1, display: 'flex', flexDirection: 'column' } }}
            >
              <div style={{ marginBottom: 16, color: '#1890ff' }}>
                {feature.icon}
              </div>
              <Title level={4}>{feature.title}</Title>
              <Paragraph style={{ marginBottom: 16, flex: 1 }}>
                {feature.description}
              </Paragraph>
              <Link to={feature.link}>
                <Button type="primary" ghost icon={<ArrowRightOutlined />} style={{ marginTop: 'auto' }}>
                  立即使用
                </Button>
              </Link>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default HomePage; 