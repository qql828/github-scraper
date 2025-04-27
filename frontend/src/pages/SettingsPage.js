import React, { useState, useEffect } from 'react';
import { Card, Typography, Form, Input, Button, Switch, InputNumber, message, Divider, Space } from 'antd';
import { SettingOutlined, SaveOutlined, ReloadOutlined, GithubOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Paragraph, Text } = Typography;

const SettingsPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testingToken, setTestingToken] = useState(false);
  
  // 加载配置
  useEffect(() => {
    loadSettings();
  }, []);
  
  // 加载设置
  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/settings');
      
      // 设置表单初始值
      if (response.data && response.data.success && response.data.data) {
        // 将API返回的配置项映射到表单字段
        const apiConfig = response.data.data;
        
        // 添加日志以便调试
        console.log('从API加载的配置:', apiConfig);
        
        // 准备表单数据
        const formData = {
          github_token: apiConfig.github_token || '',
          use_proxy: apiConfig.use_proxy || false,
          http_proxy: apiConfig.http_proxy || '',
          https_proxy: apiConfig.https_proxy || '',
          threads: apiConfig.max_threads || 5,
          timeout: apiConfig.request_timeout || 30,
          retries: apiConfig.max_retries || 3,
          auto_save_to_feishu: apiConfig.auto_save_to_feishu || false
        };
        
        // 设置表单值
        form.setFieldsValue(formData);
      } else {
        message.warning('获取设置数据格式异常');
        console.warn('API响应格式异常:', response.data);
      }
    } catch (error) {
      console.error('加载设置失败:', error);
      message.error('加载设置失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 保存设置
  const handleSaveSettings = async (values) => {
    try {
      setLoading(true);
      
      // 将表单值转换为API需要的格式
      const apiData = {
        github_token: values.github_token,
        use_proxy: values.use_proxy,
        http_proxy: values.http_proxy,
        https_proxy: values.https_proxy,
        max_threads: values.threads,
        request_timeout: values.timeout,
        max_retries: values.retries,
        auto_save_to_feishu: values.auto_save_to_feishu
      };
      
      // 添加日志以便调试
      console.log('提交到API的配置:', apiData);
      
      // 发送到API
      const response = await axios.post('/api/settings', apiData);
      
      if (response.data && response.data.success) {
        message.success('设置保存成功');
      } else {
        message.error('保存设置失败: ' + (response.data.message || '未知错误'));
      }
    } catch (error) {
      console.error('保存设置失败:', error);
      message.error('保存设置失败: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };
  
  // 测试GitHub Token
  const handleTestGithubToken = async () => {
    const token = form.getFieldValue('github_token');
    
    if (!token) {
      message.error('请先输入GitHub Token');
      return;
    }
    
    try {
      setTestingToken(true);
      const response = await axios.post('/api/test/github_token', { token });
      
      if (response.data.valid) {
        message.success('GitHub Token 有效，用户名: ' + response.data.username);
      } else {
        message.error('GitHub Token 无效: ' + response.data.message);
      }
    } catch (error) {
      console.error('测试GitHub Token失败:', error);
      message.error('测试GitHub Token失败');
    } finally {
      setTestingToken(false);
    }
  };
  
  return (
    <div>
      <Title level={2}>
        <SettingOutlined style={{ marginRight: 8 }} />
        系统设置
      </Title>
      <Paragraph>
        设置爬虫系统的常用配置，包括代理设置、GitHub Token、并发线程等参数。
      </Paragraph>
      
      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveSettings}
          initialValues={{
            use_proxy: false,
            threads: 5,
            timeout: 30,
            retries: 3
          }}
        >
          <Divider orientation="left">
            <GithubOutlined /> GitHub API设置
          </Divider>
          
          <Form.Item
            label="GitHub API Token"
            name="github_token"
            extra="用于GitHub API，获取更高的请求频率限制和访问私有仓库"
          >
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item noStyle name="github_token">
                <Input.Password placeholder="请输入GitHub API Token" />
              </Form.Item>
              <Button 
                loading={testingToken} 
                onClick={handleTestGithubToken}
              >
                测试Token
              </Button>
            </Space.Compact>
          </Form.Item>
          
          <Divider>代理设置</Divider>
          
          <Form.Item
            label="使用代理"
            name="use_proxy"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          
          <Form.Item
            label="代理地址"
            name="proxy_url"
            extra="格式：http://host:port 或 socks5://host:port"
            dependencies={['use_proxy']}
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!getFieldValue('use_proxy') || value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('请输入代理地址'));
                },
              }),
            ]}
          >
            <Input placeholder="请输入代理地址，例如: http://127.0.0.1:7890" />
          </Form.Item>
          
          <Form.Item
            label="代理用户名"
            name="proxy_username"
            extra="如代理需要身份验证，请提供用户名"
            dependencies={['use_proxy']}
          >
            <Input placeholder="可选" />
          </Form.Item>
          
          <Form.Item
            label="代理密码"
            name="proxy_password"
            extra="如代理需要身份验证，请提供密码"
            dependencies={['use_proxy']}
          >
            <Input.Password placeholder="可选" />
          </Form.Item>
          
          <Divider>爬虫设置</Divider>
          
          <Form.Item
            label="并发线程数"
            name="threads"
            extra="同时运行的爬虫线程数，过高可能导致被封IP"
            rules={[{ required: true, message: '请输入并发线程数' }]}
          >
            <InputNumber min={1} max={20} />
          </Form.Item>
          
          <Form.Item
            label="请求超时(秒)"
            name="timeout"
            extra="单个请求的超时时间，单位为秒"
            rules={[{ required: true, message: '请输入请求超时时间' }]}
          >
            <InputNumber min={5} max={120} />
          </Form.Item>
          
          <Form.Item
            label="失败重试次数"
            name="retries"
            extra="请求失败后的重试次数"
            rules={[{ required: true, message: '请输入失败重试次数' }]}
          >
            <InputNumber min={0} max={10} />
          </Form.Item>
          
          <Divider>其他设置</Divider>
          
          <Form.Item
            label="自动保存到飞书"
            name="auto_save_to_feishu"
            valuePropName="checked"
            extra="爬取数据后自动保存到飞书电子表格"
          >
            <Switch />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                icon={<SaveOutlined />}
                loading={loading}
              >
                保存设置
              </Button>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={loadSettings}
                loading={loading}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default SettingsPage; 