import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Table, Alert, Spin, Space, Typography, Switch, message } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Paragraph } = Typography;
const { Search } = Input;

const WebsitePage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState([]);
  const [saveToFeishu, setSaveToFeishu] = useState(false);
  const [fetchingData, setFetchingData] = useState(false);

  // 页面加载时获取数据
  useEffect(() => {
    console.log('WebsitePage组件加载，准备获取数据...');
    fetchWebsiteData();
    loadAutoSaveConfig();
  }, []);

  // 加载自动保存到飞书配置
  const loadAutoSaveConfig = async () => {
    try {
      const response = await axios.get('/api/settings');
      if (response.data && response.data.success && response.data.data) {
        const { auto_save_to_feishu } = response.data.data;
        setSaveToFeishu(auto_save_to_feishu || false);
        console.log('从配置加载的自动保存到飞书设置:', auto_save_to_feishu);
      }
    } catch (error) {
      console.error('加载自动保存配置失败:', error);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '网站URL',
      dataIndex: 'website_url',
      key: 'website_url',
      render: (text) => <a href={text} target="_blank" rel="noopener noreferrer">{text}</a>,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      ellipsis: true,
      render: (text) => text ? text.split(',').join(', ') : '',
    },
    {
      title: '图标',
      dataIndex: 'favicon',
      key: 'favicon',
      render: (text) => text ? <img src={text} alt="图标" style={{ maxWidth: 24, maxHeight: 24 }} /> : '',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="link" danger onClick={() => handleDelete(record.website_url)}>
          删除
        </Button>
      ),
    },
  ];

  // 获取网站数据
  const fetchWebsiteData = async () => {
    console.log('开始获取网站数据...');
    message.info('正在获取网站数据...');
    setFetchingData(true);
    try {
      console.log('发送请求: GET /api/data/website');
      const response = await axios.get('/api/data/website');
      console.log('接收到网站数据响应:', response.data);
      console.log('响应数据类型:', typeof response.data);
      console.log('data字段类型:', typeof response.data.data);
      console.log('data字段是否为数组:', Array.isArray(response.data.data));
      if (response.data.data) {
        console.log('数据内容详情:', JSON.stringify(response.data.data, null, 2));
      }
      
      if (response.data.success) {
        console.log(`成功获取${response.data.data?.length || 0}条网站数据`);
        if (Array.isArray(response.data.data)) {
          // 确保NaN值被转换为空字符串
          const processedData = response.data.data.map(item => {
            const processedItem = {...item};
            // 处理可能存在的NaN值
            Object.keys(processedItem).forEach(key => {
              if (processedItem[key] !== null && typeof processedItem[key] === 'number' && isNaN(processedItem[key])) {
                console.log(`检测到NaN值，字段:${key}，将转换为空字符串`);
                processedItem[key] = '';
              }
              // 添加额外检查，确保所有数据都是有效的JSON
              if (typeof processedItem[key] === 'undefined') {
                console.log(`检测到undefined值，字段:${key}，将转换为空字符串`);
                processedItem[key] = '';
              }
            });
            return processedItem;
          });
          
          console.log('处理后的数据:', processedData);
          if (processedData.length > 0) {
            message.success(`成功获取到${processedData.length}条网站数据`);
          } else {
            message.warning('获取到的网站数据为空');
          }
          setData(processedData);
        } else {
          console.warn('API返回的data字段不是数组:', response.data.data);
          message.warning('API返回的data字段不是数组');
          setData([]);
        }
      } else {
        console.warn('获取网站数据失败:', response.data.message);
        message.error('获取网站数据失败: ' + response.data.message);
      }
    } catch (err) {
      console.error('获取网站数据出错:', err);
      console.error('错误详情:', JSON.stringify(err, Object.getOwnPropertyNames(err)));
      message.error('获取数据失败: ' + (err.response?.data?.message || err.message));
    } finally {
      setFetchingData(false);
      console.log('网站数据获取完成');
    }
  };

  // 处理删除
  const handleDelete = async (url) => {
    try {
      const response = await axios.post('/api/delete', { url });
      if (response.data.success) {
        message.success(response.data.message);
        // 刷新数据
        fetchWebsiteData();
      } else {
        message.error(response.data.message);
      }
    } catch (err) {
      message.error('删除失败: ' + (err.response?.data?.message || err.message));
    }
  };

  // 爬取网站
  const handleScrape = async (url) => {
    if (!url) {
      setError('请输入有效的网站URL');
      return;
    }

    if (url.includes('github.com')) {
      setError('请在GitHub页面爬取GitHub仓库');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/scrape/website', {
        url,
        save_to_feishu: saveToFeishu
      });

      if (response.data.success) {
        // 检查是否跳过了保存（URL已存在于飞书表格中）
        if (saveToFeishu && response.data.feishu_skipped) {
          message.warning(`网站爬取成功，但该URL已存在于飞书表格中，无需重复添加!`);
        } else {
          message.success(response.data.message || '网站爬取成功!');
        }
        // 刷新数据
        fetchWebsiteData();
      } else {
        setError(response.data.message || '爬取失败，请检查URL是否正确');
      }
    } catch (err) {
      setError(err.response?.data?.message || err.message || '发生错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 导出数据为Excel
  const handleExport = () => {
    window.open('/api/data/website/export', '_blank');
  };

  return (
    <div>
      <Title level={2}>网站信息爬取</Title>
      <Paragraph>
        爬取网站基本信息，包括标题、描述、关键词、图标等元数据。
      </Paragraph>

      <Card title="爬取网站信息" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="输入网站URL，例如: https://example.com"
            enterButton={<Button type="primary" icon={<SearchOutlined />}>爬取</Button>}
            size="large"
            onSearch={handleScrape}
            loading={loading}
          />

          <div style={{ marginTop: 8 }}>
            <Switch 
              checked={saveToFeishu} 
              onChange={(checked) => setSaveToFeishu(checked)} 
              checkedChildren="保存到飞书" 
              unCheckedChildren="仅保存到本地"
            />
            <span style={{ marginLeft: 8 }}>
              {saveToFeishu ? '同时保存到飞书电子表格' : '仅保存到本地Excel文件'}
            </span>
          </div>
        </Space>
      </Card>

      {loading && (
        <Card>
          <Spin tip="正在爬取网站数据，请稍候..." spinning={true}>
            <div style={{ padding: '30px 50px', minHeight: '100px' }} />
          </Spin>
        </Card>
      )}

      {error && (
        <Alert
          message="爬取失败"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Card 
        title="网站数据" 
        extra={
          <Space>
            <Button type="primary" onClick={fetchWebsiteData} loading={fetchingData}>
              刷新数据
            </Button>
            <Button type="primary" onClick={handleExport} disabled={data.length === 0}>
              导出Excel
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={data.map(item => ({ ...item, key: item.website_url }))}
          loading={fetchingData}
          pagination={{ pageSize: 10 }}
          scroll={{ x: true }}
          locale={{ emptyText: '暂无数据，请爬取网站或点击"刷新数据"按钮' }}
        />
      </Card>
    </div>
  );
};

export default WebsitePage;
 