import React, { useState } from 'react';
import { Table, Button, Input, Space, Popconfirm, Tag, Typography, Tooltip } from 'antd';
import { 
  SearchOutlined, 
  DeleteOutlined, 
  ExportOutlined, 
  EyeOutlined, 
  LinkOutlined,
  GithubOutlined,
  GlobalOutlined,
  StarOutlined
} from '@ant-design/icons';
import Highlighter from 'react-highlight-words';

const { Text, Paragraph } = Typography;

/**
 * 数据表格组件，用于展示GitHub仓库或网站数据
 * 
 * @param {Object} props
 * @param {Array} props.dataSource - 数据源
 * @param {string} props.dataType - 数据类型：'github'或'website'
 * @param {Function} props.onDelete - 删除数据的回调函数
 * @param {Function} props.onExport - 导出数据的回调函数
 * @param {Function} props.onView - 查看详情的回调函数
 * @param {boolean} props.loading - 是否正在加载
 */
const DataTable = ({ 
  dataSource = [], 
  dataType = 'github', 
  onDelete, 
  onExport,
  onView,
  loading = false
}) => {
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');
  
  // 处理搜索
  const handleSearch = (selectedKeys, confirm, dataIndex) => {
    confirm();
    setSearchText(selectedKeys[0]);
    setSearchedColumn(dataIndex);
  };
  
  // 重置搜索
  const handleReset = (clearFilters) => {
    clearFilters();
    setSearchText('');
  };
  
  // 获取字段搜索组件
  const getColumnSearchProps = (dataIndex, title) => ({
    filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
      <div style={{ padding: 8 }}>
        <Input
          placeholder={`搜索 ${title}`}
          value={selectedKeys[0]}
          onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
          onPressEnter={() => handleSearch(selectedKeys, confirm, dataIndex)}
          style={{ width: 188, marginBottom: 8, display: 'block' }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm, dataIndex)}
            icon={<SearchOutlined />}
            size="small"
            style={{ width: 90 }}
          >
            搜索
          </Button>
          <Button
            onClick={() => handleReset(clearFilters)}
            size="small"
            style={{ width: 90 }}
          >
            重置
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered) => (
      <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    onFilter: (value, record) => {
      const text = record[dataIndex] ? record[dataIndex].toString() : '';
      return text.toLowerCase().includes(value.toLowerCase());
    },
    render: (text) => 
      searchedColumn === dataIndex ? (
        <Highlighter
          highlightStyle={{ backgroundColor: '#ffc069', padding: 0 }}
          searchWords={[searchText]}
          autoEscape
          textToHighlight={text ? text.toString() : ''}
        />
      ) : (
        text
      ),
  });
  
  // 创建GitHub数据表格列定义
  const getGithubColumns = () => [
    {
      title: '仓库',
      dataIndex: 'repository_name',
      key: 'repository_name',
      ...getColumnSearchProps('repository_name', '仓库名称'),
      render: (text, record) => (
        <Space>
          <GithubOutlined />
          <a href={record.repository_url} target="_blank" rel="noopener noreferrer">
            {text}
          </a>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: {
        showTitle: false,
      },
      ...getColumnSearchProps('description', '描述'),
      render: (text) => (
        <Tooltip title={text}>
          <Paragraph ellipsis={{ rows: 2 }}>{text || '无描述'}</Paragraph>
        </Tooltip>
      ),
    },
    {
      title: 'Stars',
      dataIndex: 'stars',
      key: 'stars',
      sorter: (a, b) => a.stars - b.stars,
      render: (text) => (
        <Space>
          <StarOutlined style={{ color: '#fadb14' }} />
          {text}
        </Space>
      ),
    },
    {
      title: '语言',
      dataIndex: 'language',
      key: 'language',
      filters: [
        { text: 'JavaScript', value: 'JavaScript' },
        { text: 'Python', value: 'Python' },
        { text: 'Java', value: 'Java' },
        { text: 'Go', value: 'Go' },
        { text: 'TypeScript', value: 'TypeScript' },
        { text: 'C++', value: 'C++' },
        { text: 'PHP', value: 'PHP' },
      ],
      onFilter: (value, record) => record.language === value,
      render: (text) => (
        <Tag color="blue">{text || '未知'}</Tag>
      ),
    },
    {
      title: '最后更新',
      dataIndex: 'last_updated',
      key: 'last_updated',
      sorter: (a, b) => new Date(a.last_updated) - new Date(b.last_updated),
      render: (text) => text ? new Date(text).toLocaleDateString() : '未知'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="text" 
            icon={<EyeOutlined />} 
            onClick={() => onView && onView(record)}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => onDelete && onDelete(record.repository_url)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  
  // 创建网站数据表格列定义
  const getWebsiteColumns = () => [
    {
      title: '网站',
      dataIndex: 'title',
      key: 'title',
      ...getColumnSearchProps('title', '网站标题'),
      render: (text, record) => (
        <Space>
          <GlobalOutlined />
          <a href={record.website_url} target="_blank" rel="noopener noreferrer">
            {text || extractDomain(record.website_url)}
          </a>
        </Space>
      ),
    },
    {
      title: '网址',
      dataIndex: 'website_url',
      key: 'website_url',
      ...getColumnSearchProps('website_url', '网址'),
      render: (text) => (
        <Space>
          <LinkOutlined />
          <Text ellipsis style={{ maxWidth: 250 }}>{text}</Text>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: {
        showTitle: false,
      },
      ...getColumnSearchProps('description', '描述'),
      render: (text) => (
        <Tooltip title={text}>
          <Paragraph ellipsis={{ rows: 2 }}>{text || '无描述'}</Paragraph>
        </Tooltip>
      ),
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      ...getColumnSearchProps('keywords', '关键词'),
      render: (text) => {
        if (!text) return '无关键词';
        const keywords = typeof text === 'string' ? text.split(',') : text;
        return (
          <>
            {keywords.map((tag, index) => (
              <Tag key={index}>{tag.trim()}</Tag>
            ))}
          </>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="text" 
            icon={<EyeOutlined />} 
            onClick={() => onView && onView(record)}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => onDelete && onDelete(record.website_url)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  
  // 提取网站域名（辅助函数）
  const extractDomain = (url) => {
    if (!url) return '未知网站';
    try {
      const domain = new URL(url).hostname;
      return domain;
    } catch (error) {
      return url;
    }
  };
  
  // 根据数据类型选择表格列定义
  const columns = dataType === 'github' ? getGithubColumns() : getWebsiteColumns();
  
  // 表格底部工具栏
  const tableFooter = () => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Text>共 {dataSource.length} 条记录</Text>
      <Space>
        <Button 
          icon={<ExportOutlined />} 
          onClick={() => onExport && onExport()}
        >
          导出到Excel
        </Button>
      </Space>
    </div>
  );
  
  return (
    <Table
      className="data-table"
      columns={columns}
      dataSource={dataSource.map((item, index) => ({ ...item, key: index }))}
      pagination={{ pageSize: 10 }}
      loading={loading}
      footer={tableFooter}
      scroll={{ x: 'max-content' }}
    />
  );
};

export default DataTable; 