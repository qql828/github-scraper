import React, { useState, useEffect, useCallback } from 'react';
import { Card, Typography, Button, Statistic, Row, Col, message, Divider, Table, Tag, Switch, Spin, Form, Input, Space, Empty } from 'antd';
import { 
  TeamOutlined, 
  SyncOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  SettingOutlined,
  SaveOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  GithubOutlined,
  GlobalOutlined,
  ClearOutlined
} from '@ant-design/icons';

import { 
  getFeishuStatus, 
  syncGithubToFeishu, 
  syncWebsiteToFeishu, 
  cleanFeishuData, 
  updateFeishuConfig,
  getFeishuSyncHistory 
} from '../api/feishu';

const { Title, Paragraph, Text } = Typography;

const FeishuPage = () => {
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState({
    status: false,
    syncGithub: false,
    syncWebsite: false,
    cleanGithub: false,
    cleanWebsite: false,
    history: false
  });
  const [configForm] = Form.useForm();
  const [showConfig, setShowConfig] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  
  // 使用useCallback包装函数
  const loadFeishuStatus = useCallback(async () => {
    setLoading(prev => ({ ...prev, status: true }));
    try {
      const response = await getFeishuStatus();
      
      // 检查响应是否成功
      if (response && response.success) {
        setStatus(response);
        
        // 检查response.config是否存在且格式正确
        if (response.config && typeof response.config === 'object') {
          const config = response.config;
          
          // 设置配置表单的初始值
          configForm.setFieldsValue({
            app_id: config.app_id || '',
            app_secret: '',  // 出于安全考虑，不显示原有密钥
            github_spreadsheet_token: config.github_spreadsheet_token || '',
            github_sheet_id: config.github_sheet_id || '',
            website_spreadsheet_token: config.website_spreadsheet_token || '',
            website_sheet_id: config.website_sheet_id || ''
          });
        } else if (response.type === 'undefined') {
          // 处理特殊情况，当config是{type: 'undefined'}的情况
          console.log('飞书配置数据未设置，需要配置飞书应用');
          message.info('请配置飞书应用信息');
        } else {
          console.log('飞书配置数据格式不正确，请正确设置配置信息');
          message.info('请正确设置飞书配置信息');
        }
      } else {
        console.log('获取飞书状态失败，请检查网络连接');
        message.warning('获取飞书状态失败，请检查网络连接');
      }
    } catch (error) {
      console.error('获取飞书状态失败:', error);
      message.error('获取飞书状态失败');
    } finally {
      setLoading(prev => ({ ...prev, status: false }));
    }
  }, [configForm]);
  
  // 加载同步历史
  const loadSyncHistory = useCallback(async () => {
    setLoading(prev => ({ ...prev, history: true }));
    try {
      const response = await getFeishuSyncHistory();
      setHistory(response.data || []);
    } catch (error) {
      console.error('获取同步历史失败:', error);
      message.error('获取同步历史失败');
    } finally {
      setLoading(prev => ({ ...prev, history: false }));
    }
  }, []);
  
  // 使用useCallback包装loadData函数
  const loadData = useCallback(async () => {
    await Promise.all([
      loadFeishuStatus(),
      loadSyncHistory()
    ]);
  }, [loadFeishuStatus, loadSyncHistory]);
  
  // 加载飞书状态和同步历史
  useEffect(() => {
    loadData();
  }, [loadData]);
  
  // 同步GitHub数据到飞书
  const handleSyncGithub = async () => {
    setLoading(prev => ({ ...prev, syncGithub: true }));
    try {
      await syncGithubToFeishu();
      message.success('GitHub数据同步到飞书成功');
      
      // 重新加载数据
      await loadData();
    } catch (error) {
      console.error('同步GitHub数据失败:', error);
      message.error('同步GitHub数据到飞书失败');
    } finally {
      setLoading(prev => ({ ...prev, syncGithub: false }));
    }
  };
  
  // 同步网站数据到飞书
  const handleSyncWebsite = async () => {
    setLoading(prev => ({ ...prev, syncWebsite: true }));
    try {
      await syncWebsiteToFeishu();
      message.success('网站数据同步到飞书成功');
      
      // 重新加载数据
      await loadData();
    } catch (error) {
      console.error('同步网站数据失败:', error);
      message.error('同步网站数据到飞书失败');
    } finally {
      setLoading(prev => ({ ...prev, syncWebsite: false }));
    }
  };
  
  // 清理GitHub数据
  const handleCleanGithub = async () => {
    setLoading(prev => ({ ...prev, cleanGithub: true }));
    try {
      const result = await cleanFeishuData('github');
      message.success(`GitHub数据清理成功，共删除 ${result.removed_count} 条重复记录`);
      
      // 重新加载数据
      await loadData();
    } catch (error) {
      console.error('清理GitHub数据失败:', error);
      message.error('清理GitHub数据失败');
    } finally {
      setLoading(prev => ({ ...prev, cleanGithub: false }));
    }
  };
  
  // 清理网站数据
  const handleCleanWebsite = async () => {
    setLoading(prev => ({ ...prev, cleanWebsite: true }));
    try {
      const result = await cleanFeishuData('website');
      message.success(`网站数据清理成功，共删除 ${result.removed_count} 条重复记录`);
      
      // 重新加载数据
      await loadData();
    } catch (error) {
      console.error('清理网站数据失败:', error);
      message.error('清理网站数据失败');
    } finally {
      setLoading(prev => ({ ...prev, cleanWebsite: false }));
    }
  };
  
  // 更新飞书配置
  const handleUpdateConfig = async (values) => {
    setSavingConfig(true);
    try {
      await updateFeishuConfig(values);
      message.success('飞书配置更新成功');
      
      // 重新加载状态
      await loadFeishuStatus();
      
      // 隐藏配置表单
      setShowConfig(false);
    } catch (error) {
      console.error('更新飞书配置失败:', error);
      message.error('更新飞书配置失败');
    } finally {
      setSavingConfig(false);
    }
  };
  
  // 同步历史表格列定义
  const historyColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: '操作类型',
      dataIndex: 'operation',
      key: 'operation',
      render: (text) => {
        let color = 'blue';
        let icon = <SyncOutlined />;
        
        if (text.includes('sync')) {
          color = 'blue';
          icon = <SyncOutlined />;
        } else if (text.includes('clean')) {
          color = 'orange';
          icon = <DeleteOutlined />;
        }
        
        return <Tag icon={icon} color={color}>{text}</Tag>;
      },
    },
    {
      title: '数据类型',
      dataIndex: 'data_type',
      key: 'data_type',
      render: (text) => {
        const color = text === 'github' ? 'purple' : 'green';
        const icon = text === 'github' ? <GithubOutlined /> : <GlobalOutlined />;
        return <Tag icon={icon} color={color}>{text}</Tag>;
      },
    },
    {
      title: '结果',
      dataIndex: 'success',
      key: 'success',
      render: (success) => {
        return success ? 
          <Tag icon={<CheckCircleOutlined />} color="success">成功</Tag> : 
          <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>;
      },
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
    },
  ];
  
  // 渲染状态卡片
  const renderStatusCard = () => {
    if (loading.status) {
      return (
        <Card title="连接状态" className="feishu-status-card">
          <div style={{ textAlign: 'center', padding: '30px 50px' }}>
            <Spin spinning={true} tip="加载中...">
              <div style={{ minHeight: '50px' }} />
            </Spin>
          </div>
        </Card>
      );
    }
    
    if (!status) {
      return (
        <Card title="连接状态" className="feishu-status-card">
          <Empty description="无法获取飞书连接状态" />
        </Card>
      );
    }
    
    return (
      <>
        <Card title="连接状态" className="feishu-status-card">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={8}>
              <Statistic
                title="飞书应用连接状态"
                value={status.connected ? '已连接' : '未连接'}
                valueStyle={{ color: status.connected ? '#52c41a' : '#ff4d4f' }}
                prefix={status.connected ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              />
            </Col>
            
            <Col xs={24} sm={12} md={8}>
              <Statistic
                title="应用 ID"
                value={status.config?.app_id || '未设置'}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
            
            <Col xs={24} sm={12} md={8}>
              <Statistic
                title="上次同步时间"
                value={status.last_sync ? new Date(status.last_sync).toLocaleString() : '从未同步'}
                prefix={<ClockCircleOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Statistic 
                title="同步记录数" 
                value={status.sync_count || 0} 
                prefix={<SyncOutlined />}
              />
            </Col>
          </Row>
        </Card>
        
        <Divider />
        
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12}>
            <Card title="GitHub数据表格" variant="outlined" styles={{ body: { padding: 16 } }}>
              <Paragraph>
                <Text strong>电子表格ID：</Text> {status.config?.github_spreadsheet_token || '未设置'}
              </Paragraph>
              <Paragraph>
                <Text strong>Sheet ID：</Text> {status.config?.github_sheet_id || '未设置'}
              </Paragraph>
              <Paragraph>
                <Text strong>连接状态：</Text> 
                {status.github_connected ? 
                  <Tag icon={<CheckCircleOutlined />} color="success">已连接</Tag> : 
                  <Tag icon={<CloseCircleOutlined />} color="error">未连接</Tag>
                }
              </Paragraph>
              <div style={{ marginTop: 16 }}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<SyncOutlined />} 
                    loading={loading.syncGithub}
                    onClick={handleSyncGithub}
                    disabled={!status.connected}
                  >
                    同步到飞书
                  </Button>
                  <Button 
                    icon={<ClearOutlined />} 
                    loading={loading.cleanGithub}
                    onClick={handleCleanGithub}
                    disabled={!status.connected}
                  >
                    清理去重
                  </Button>
                </Space>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12}>
            <Card title="网站数据表格" variant="outlined" styles={{ body: { padding: 16 } }}>
              <Paragraph>
                <Text strong>电子表格ID：</Text> {status.config?.website_spreadsheet_token || '未设置'}
              </Paragraph>
              <Paragraph>
                <Text strong>Sheet ID：</Text> {status.config?.website_sheet_id || '未设置'}
              </Paragraph>
              <Paragraph>
                <Text strong>连接状态：</Text> 
                {status.website_connected ? 
                  <Tag icon={<CheckCircleOutlined />} color="success">已连接</Tag> : 
                  <Tag icon={<CloseCircleOutlined />} color="error">未连接</Tag>
                }
              </Paragraph>
              <div style={{ marginTop: 16 }}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<SyncOutlined />} 
                    loading={loading.syncWebsite}
                    onClick={handleSyncWebsite}
                    disabled={!status.connected}
                  >
                    同步到飞书
                  </Button>
                  <Button 
                    icon={<ClearOutlined />} 
                    loading={loading.cleanWebsite}
                    onClick={handleCleanWebsite}
                    disabled={!status.connected}
                  >
                    清理去重
                  </Button>
                </Space>
              </div>
            </Card>
          </Col>
        </Row>
      </>
    );
  };
  
  // 渲染飞书配置表单
  const renderConfigForm = () => {
    return (
      <Card
        title="飞书配置"
        extra={
          <Switch 
            checkedChildren="隐藏" 
            unCheckedChildren="显示" 
            checked={showConfig} 
            onChange={setShowConfig} 
          />
        }
        style={{ marginTop: 16, display: showConfig ? 'block' : 'none' }}
      >
        <Form
          form={configForm}
          layout="vertical"
          onFinish={handleUpdateConfig}
        >
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="飞书应用 App ID"
                name="app_id"
                rules={[{ required: true, message: '请输入飞书应用 App ID' }]}
              >
                <Input placeholder="请输入飞书应用 App ID" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                label="飞书应用 App Secret"
                name="app_secret"
                extra="留空表示不修改现有密钥"
              >
                <Input.Password placeholder="请输入飞书应用 App Secret" />
              </Form.Item>
            </Col>
          </Row>
          
          <Divider>GitHub数据表格设置</Divider>
          
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="GitHub数据电子表格Token"
                name="github_spreadsheet_token"
                rules={[{ required: true, message: '请输入GitHub数据电子表格Token' }]}
              >
                <Input placeholder="请输入电子表格Token" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                label="GitHub数据Sheet ID"
                name="github_sheet_id"
                rules={[{ required: true, message: '请输入GitHub数据Sheet ID' }]}
              >
                <Input placeholder="请输入Sheet ID" />
              </Form.Item>
            </Col>
          </Row>
          
          <Divider>网站数据表格设置</Divider>
          
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="网站数据电子表格Token"
                name="website_spreadsheet_token"
                rules={[{ required: true, message: '请输入网站数据电子表格Token' }]}
              >
                <Input placeholder="请输入电子表格Token" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                label="网站数据Sheet ID"
                name="website_sheet_id"
                rules={[{ required: true, message: '请输入网站数据Sheet ID' }]}
              >
                <Input placeholder="请输入Sheet ID" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              icon={<SaveOutlined />}
              loading={savingConfig}
            >
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    );
  };
  
  return (
    <div>
      <Title level={2}>
        <TeamOutlined style={{ marginRight: 8 }} />
        飞书同步管理
      </Title>
      <Paragraph>
        管理与飞书电子表格的数据同步，支持手动同步、清理去重和配置修改等功能。
      </Paragraph>
      
      <Card className="options-card" style={{ marginBottom: 16 }}>
        <Space>
          <Button 
            icon={<SyncOutlined />} 
            onClick={loadData}
            loading={loading.history}
          >
            刷新状态
          </Button>
          <Button 
            icon={<SettingOutlined />} 
            onClick={() => setShowConfig(!showConfig)}
          >
            {showConfig ? '隐藏配置' : '显示配置'}
          </Button>
        </Space>
      </Card>
      
      {renderStatusCard()}
      
      {renderConfigForm()}
      
      <Card title="同步历史记录" style={{ marginTop: 16 }}>
        <Table 
          columns={historyColumns} 
          dataSource={history.map((item, index) => ({ ...item, key: index }))} 
          pagination={{ pageSize: 10 }}
          loading={loading.history}
        />
      </Card>
    </div>
  );
};

export default FeishuPage; 