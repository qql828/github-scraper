import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Switch, Tooltip, Row, Col, message } from 'antd';
import { GithubOutlined, GlobalOutlined, SendOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { isValidUrl, normalizeUrl, isGithubUrl, isWebsiteUrl } from '../utils/urlHelper';

/**
 * URL输入表单组件，用于输入URL并提交爬取请求
 * 
 * @param {Object} props - 组件属性
 * @param {Function} props.onSubmit - 提交表单的回调函数
 * @param {boolean} props.loading - 是否正在加载中
 * @param {string} props.urlType - URL类型限制：'github', 'website' 或 'auto'
 * @param {boolean} props.defaultSaveToFeishu - 默认的保存到飞书设置
 * @param {Function} props.onSaveToFeishuChange - 保存到飞书设置变更的回调函数
 */
const UrlInputForm = ({ 
  onSubmit, 
  loading, 
  urlType = 'auto', 
  defaultSaveToFeishu = false,
  onSaveToFeishuChange
}) => {
  const [url, setUrl] = useState('');
  const [saveToFeishu, setSaveToFeishu] = useState(defaultSaveToFeishu);
  const [urlStatus, setUrlStatus] = useState('');
  
  // 当defaultSaveToFeishu改变时更新状态
  useEffect(() => {
    setSaveToFeishu(defaultSaveToFeishu);
  }, [defaultSaveToFeishu]);
  
  // 验证URL并设置状态
  const validateUrl = (inputUrl) => {
    if (!inputUrl) {
      setUrlStatus('');
      return;
    }
    
    const normalizedUrl = normalizeUrl(inputUrl);
    
    if (!isValidUrl(normalizedUrl)) {
      setUrlStatus('invalid');
      return;
    }
    
    if (urlType === 'github' && !isGithubUrl(normalizedUrl)) {
      setUrlStatus('not_github');
      return;
    }
    
    if (urlType === 'website' && !isWebsiteUrl(normalizedUrl)) {
      setUrlStatus('not_website');
      return;
    }
    
    // 自动检测URL类型
    if (isGithubUrl(normalizedUrl)) {
      setUrlStatus('github');
    } else if (isWebsiteUrl(normalizedUrl)) {
      setUrlStatus('website');
    } else {
      setUrlStatus('unknown');
    }
  };
  
  // 处理URL输入变化
  const handleUrlChange = (e) => {
    const inputUrl = e.target.value;
    setUrl(inputUrl);
    validateUrl(inputUrl);
  };
  
  // 处理表单提交
  const handleSubmit = () => {
    if (!url) {
      message.error('请输入URL');
      return;
    }
    
    const normalizedUrl = normalizeUrl(url);
    
    if (!isValidUrl(normalizedUrl)) {
      message.error('请输入有效的URL');
      return;
    }
    
    if (urlType === 'github' && !isGithubUrl(normalizedUrl)) {
      message.error('请输入有效的GitHub仓库URL');
      return;
    }
    
    if (urlType === 'website' && !isWebsiteUrl(normalizedUrl)) {
      message.error('请输入有效的网站URL');
      return;
    }
    
    // 提交表单
    onSubmit({
      url: normalizedUrl,
      saveToFeishu
    });
  };
  
  // 处理保存到飞书设置变更
  const handleSaveToFeishuChange = (checked) => {
    setSaveToFeishu(checked);
    if (onSaveToFeishuChange) {
      onSaveToFeishuChange(checked);
    }
  };
  
  // 获取URL输入框的状态和图标
  const getUrlInputStatus = () => {
    if (!url) return {};
    
    switch (urlStatus) {
      case 'github':
        return {
          suffix: <GithubOutlined style={{ color: '#1890ff' }} />,
          status: 'success'
        };
      case 'website':
        return {
          suffix: <GlobalOutlined style={{ color: '#52c41a' }} />,
          status: 'success'
        };
      case 'invalid':
        return { status: 'error' };
      case 'not_github':
        return { status: 'error' };
      case 'not_website':
        return { status: 'error' };
      default:
        return {};
    }
  };
  
  // 获取URL输入框下方的提示文本
  const getUrlHelp = () => {
    switch (urlStatus) {
      case 'invalid':
        return '请输入有效的URL';
      case 'not_github':
        return '请输入GitHub仓库URL，例如: https://github.com/username/repo';
      case 'not_website':
        return '请输入网站URL，例如: https://example.com';
      case 'unknown':
        return '无法识别的URL类型';
      default:
        return '';
    }
  };
  
  const { suffix, status } = getUrlInputStatus();
  const urlHelp = getUrlHelp();
  
  return (
    <Form className="scrape-form" layout="vertical">
      <Form.Item
        label="URL地址"
        help={urlHelp}
        validateStatus={status}
      >
        <Input
          placeholder={
            urlType === 'github'
              ? '输入GitHub仓库URL，例如: https://github.com/username/repo'
              : urlType === 'website'
              ? '输入网站URL，例如: https://example.com'
              : '输入URL，将自动识别GitHub仓库或网站'
          }
          value={url}
          onChange={handleUrlChange}
          suffix={suffix}
          size="large"
        />
      </Form.Item>
      
      <Row gutter={16}>
        <Col xs={24} sm={12}>
          <Form.Item>
            <Tooltip title="开启后将同步保存数据到飞书电子表格">
              <Switch
                checked={saveToFeishu}
                onChange={handleSaveToFeishuChange}
                checkedChildren="保存到飞书"
                unCheckedChildren="仅保存到本地"
              />
              <span style={{ marginLeft: 8 }}>
                保存到飞书
                <QuestionCircleOutlined style={{ marginLeft: 4 }} />
              </span>
            </Tooltip>
          </Form.Item>
        </Col>
        <Col xs={24} sm={12} style={{ textAlign: 'right' }}>
          <Form.Item>
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={loading}
              onClick={handleSubmit}
              size="large"
            >
              开始爬取
            </Button>
          </Form.Item>
        </Col>
      </Row>
    </Form>
  );
};

export default UrlInputForm; 