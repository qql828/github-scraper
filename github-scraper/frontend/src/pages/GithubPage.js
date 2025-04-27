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
      // 检查URL是否已存在
      if (response.data.url_exists) {
        message.warning(response.data.message || '该URL已存在，请勿重复爬取');
      }
      // 检查是否跳过了保存（URL已存在于飞书表格中）
      else if (saveToFeishu && response.data.feishu_skipped) {
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