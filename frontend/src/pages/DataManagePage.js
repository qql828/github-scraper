import React, { useState, useEffect } from 'react';
import { Card, Tabs, Button, Table, Space, Typography, message, Popconfirm, Modal, Upload } from 'antd';
import { UploadOutlined, DeleteOutlined, ExportOutlined, InfoCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Paragraph } = Typography;
const { TabPane } = Tabs;

const DataManagePage = () => {
  const [activeTab, setActiveTab] = useState('github');
  const [githubData, setGithubData] = useState([]);
  const [websiteData, setWebsiteData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importType, setImportType] = useState('github');
  const [importFileList, setImportFileList] = useState([]);
  const [uploading, setUploading] = useState(false);

  // 表格列 - GitHub
  const githubColumns = [
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
      title: '星标数',
      dataIndex: 'stars',
      key: 'stars',
      sorter: (a, b) => a.stars - b.stars,
    },
    {
      title: 'Fork数',
      dataIndex: 'forks',
      key: 'forks',
      sorter: (a, b) => a.forks - b.forks,
    },
    {
      title: '主要语言',
      dataIndex: 'language',
      key: 'language',
    },
    {
      title: '最后更新',
      dataIndex: 'last_updated',
      key: 'last_updated',
      sorter: (a, b) => new Date(a.last_updated) - new Date(b.last_updated),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Popconfirm
          title="确定要删除这条记录吗?"
          onConfirm={() => handleDelete(record.repository_url)}
          okText="是"
          cancelText="否"
        >
          <Button type="link" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  // 表格列 - 网站
  const websiteColumns = [
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
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Popconfirm
          title="确定要删除这条记录吗?"
          onConfirm={() => handleDelete(record.website_url)}
          okText="是"
          cancelText="否"
        >
          <Button type="link" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  // 首次加载时获取数据
  useEffect(() => {
    fetchData();
  }, []);

  // 获取数据
  const fetchData = async () => {
    setLoading(true);
    try {
      // 同时获取GitHub和网站数据
      const [githubResponse, websiteResponse] = await Promise.all([
        axios.get('/api/data/github'),
        axios.get('/api/data/website')
      ]);

      if (githubResponse.data.success) {
        setGithubData(githubResponse.data.data || []);
      }

      if (websiteResponse.data.success) {
        setWebsiteData(websiteResponse.data.data || []);
      }
    } catch (err) {
      message.error('获取数据失败: ' + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 处理数据删除
  const handleDelete = async (url) => {
    try {
      const response = await axios.post('/api/delete', { url });
      if (response.data.success) {
        message.success(response.data.message);
        // 刷新数据
        fetchData();
      } else {
        message.error(response.data.message);
      }
    } catch (err) {
      message.error('删除失败: ' + (err.response?.data?.message || err.message));
    }
  };

  // 处理数据导出
  const handleExport = (type) => {
    window.open(`/api/data/${type}/export`, '_blank');
  };

  // 处理批量导入
  const handleImport = (type) => {
    setImportType(type);
    setImportModalVisible(true);
    setImportFileList([]);
  };

  // 处理上传文件变化
  const handleUploadChange = ({ fileList }) => {
    setImportFileList(fileList);
  };

  // 处理文件上传
  const handleFileUpload = async () => {
    if (importFileList.length === 0) {
      message.error('请选择要上传的Excel文件');
      return;
    }

    const formData = new FormData();
    formData.append('file', importFileList[0].originFileObj);

    setUploading(true);
    try {
      const response = await axios.post(`/api/data/${importType}/import`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        message.success(response.data.message);
        setImportModalVisible(false);
        fetchData();
      } else {
        message.error(response.data.message);
      }
    } catch (err) {
      message.error('导入失败: ' + (err.response?.data?.message || err.message));
    } finally {
      setUploading(false);
    }
  };

  // 处理清空数据
  const handleClearData = async (type) => {
    try {
      const response = await axios.post(`/api/data/${type}/clear`);
      if (response.data.success) {
        message.success(response.data.message);
        // 清空对应的数据
        if (type === 'github') {
          setGithubData([]);
        } else {
          setWebsiteData([]);
        }
      } else {
        message.error(response.data.message);
      }
    } catch (err) {
      message.error('清空数据失败: ' + (err.response?.data?.message || err.message));
    }
  };

  return (
    <div>
      <Title level={2}>数据管理</Title>
      <Paragraph>
        管理已爬取的GitHub仓库和网站数据，支持查看、导出、导入和删除操作。
      </Paragraph>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        tabBarExtraContent={
          <Space>
            <Button 
              icon={<UploadOutlined />}
              onClick={() => handleImport(activeTab)}
            >
              导入Excel
            </Button>
            <Button 
              type="primary" 
              icon={<ExportOutlined />} 
              onClick={() => handleExport(activeTab)}
              disabled={(activeTab === 'github' ? githubData : websiteData).length === 0}
            >
              导出Excel
            </Button>
            <Popconfirm
              title={`确定要清空所有${activeTab === 'github' ? 'GitHub' : '网站'}数据吗?`}
              description="此操作不可撤销，请谨慎操作!"
              onConfirm={() => handleClearData(activeTab)}
              okText="确定"
              cancelText="取消"
              icon={<InfoCircleOutlined style={{ color: 'red' }} />}
            >
              <Button 
                danger 
                disabled={(activeTab === 'github' ? githubData : websiteData).length === 0}
              >
                清空数据
              </Button>
            </Popconfirm>
          </Space>
        }
      >
        <TabPane tab="GitHub仓库" key="github">
          <Table
            columns={githubColumns}
            dataSource={githubData.map(item => ({ ...item, key: item.repository_url }))}
            loading={loading && activeTab === 'github'}
            pagination={{ pageSize: 10 }}
            scroll={{ x: true }}
          />
        </TabPane>
        <TabPane tab="网站数据" key="website">
          <Table
            columns={websiteColumns}
            dataSource={websiteData.map(item => ({ ...item, key: item.website_url }))}
            loading={loading && activeTab === 'website'}
            pagination={{ pageSize: 10 }}
            scroll={{ x: true }}
          />
        </TabPane>
      </Tabs>

      {/* 导入数据模态框 */}
      <Modal
        title={`导入${importType === 'github' ? 'GitHub' : '网站'}数据`}
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={[
          <Button key="back" onClick={() => setImportModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={uploading}
            onClick={handleFileUpload}
          >
            上传并导入
          </Button>,
        ]}
      >
        <Upload
          fileList={importFileList}
          onChange={handleUploadChange}
          beforeUpload={() => false}
          maxCount={1}
          accept=".xlsx,.xls"
        >
          <Button icon={<UploadOutlined />}>选择Excel文件</Button>
        </Upload>
        <div style={{ marginTop: 16 }}>
          <p>注意事项：</p>
          <ul>
            <li>仅支持Excel文件(.xlsx或.xls)</li>
            <li>请确保Excel文件的格式与导出的格式一致</li>
            <li>上传的数据将替换或合并到现有数据中</li>
          </ul>
        </div>
      </Modal>
    </div>
  );
};

export default DataManagePage; 