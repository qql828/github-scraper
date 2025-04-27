import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Table, Alert, Spin, Space, Typography, Switch, message, Modal } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Paragraph } = Typography;
const { Search } = Input;

const GithubPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState([]);
  const [saveToFeishu, setSaveToFeishu] = useState(false);
  const [fetchingData, setFetchingData] = useState(false);

  // 页面加载时获取数据
  useEffect(() => {
    fetchGithubData();
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
      title: '仓库URL',
      dataIndex: 'repository_url',
      key: 'repository_url',
      render: (text) => <a href={text} target="_blank" rel="noopener noreferrer">{text}</a>,
    },
    {
      title: '仓库名称',
      dataIndex: 'repository_name',
      key: 'repository_name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Stars',
      dataIndex: 'stars',
      key: 'stars',
      sorter: (a, b) => a.stars - b.stars,
    },
    {
      title: 'Forks',
      dataIndex: 'forks',
      key: 'forks',
      sorter: (a, b) => a.forks - b.forks,
    },
    {
      title: '语言',
      dataIndex: 'language',
      key: 'language',
    },
    {
      title: '最后更新',
      dataIndex: 'last_updated',
      key: 'last_updated',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="link" danger onClick={() => handleDelete(record.repository_url)}>
          删除
        </Button>
      ),
    },
  ];

  // 获取GitHub数据
  const fetchGithubData = async () => {
    setFetchingData(true);
    try {
      const response = await axios.get('/api/data/github');
      if (response.data.success) {
        setData(response.data.data || []);
      }
    } catch (err) {
      message.error('获取数据失败: ' + (err.response?.data?.message || err.message));
    } finally {
      setFetchingData(false);
    }
  };

  // 处理删除
  const handleDelete = async (url) => {
    try {
      const response = await axios.post('/api/delete', { url });
      if (response.data.success) {
        message.success(response.data.message);
        // 刷新数据
        fetchGithubData();
      } else {
        message.error(response.data.message);
      }
    } catch (err) {
      message.error('删除失败: ' + (err.response?.data?.message || err.message));
    }
  };

  // 爬取GitHub仓库
  const handleScrape = async (url) => {
    if (!url) {
      setError('请输入有效的GitHub仓库URL');
      return;
    }

    if (!url.includes('github.com')) {
      setError('请输入正确的GitHub仓库URL');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/scrape/github', {
        url,
        save_to_feishu: saveToFeishu
      });

      if (response.data.success) {
        // 检查是否跳过了保存（URL已存在于飞书表格中）
        if (saveToFeishu && response.data.feishu_skipped) {
          message.warning(`GitHub仓库爬取成功，但该URL已存在于飞书表格中，无需重复添加!`);
        } 
        // 处理成功响应，但可能有警告信息
        else if (response.data.data && response.data.data.excel_locked) {
          // Excel文件被锁定的情况
          Modal.warning({
            title: '文件访问警告',
            content: (
              <div>
                <p>{response.data.message}</p>
                <p>请关闭正在使用Excel的应用程序(WPS Office, Microsoft Excel等)后再尝试。</p>
                {response.data.data.excel_file && (
                  <p>临时文件保存在: {response.data.data.excel_file}</p>
                )}
              </div>
            ),
            okText: '知道了'
          });
        } else {
          // 普通成功情况
          message.success(response.data.message);
        }
        
        // 无论如何刷新数据
        fetchGithubData();
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
    window.open('/api/data/github/export', '_blank');
  };

  return (
    <div>
      <Title level={2}>GitHub仓库信息爬取</Title>
      <Paragraph>
        爬取GitHub仓库信息，包括名称、描述、Star数量、Fork数量、最后更新时间、主要编程语言等。
      </Paragraph>

      <Card title="爬取GitHub仓库" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="输入GitHub仓库URL，例如: https://github.com/username/repo"
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
          <Spin tip="正在爬取GitHub仓库数据，请稍候..." spinning={true}>
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
        title="GitHub仓库数据" 
        extra={
          <Button type="primary" onClick={handleExport} disabled={data.length === 0}>
            导出Excel
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={data.map(item => ({ ...item, key: item.repository_url }))}
          loading={fetchingData}
          pagination={{ pageSize: 10 }}
          scroll={{ x: true }}
        />
      </Card>
    </div>
  );
};

export default GithubPage; 