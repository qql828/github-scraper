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
      // 检查URL是否已存在
      if (response.data.url_exists) {
        message.warning(response.data.message || '该URL已存在，请勿重复爬取');
      }
      // 检查是否跳过了保存（URL已存在于飞书表格中）
      else if (saveToFeishu && response.data.feishu_skipped) {
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