/**
 * 判断是否为GitHub仓库URL
 * 
 * @param {string} url - 要判断的URL
 * @returns {boolean} 是否为GitHub仓库URL
 */
export const isGithubUrl = (url) => {
  if (!url) return false;
  
  const pattern = /^https?:\/\/(?:www\.)?github\.com\/[^/]+\/[^/]+\/?.*$/i;
  return pattern.test(url);
};

/**
 * 判断是否为一般网站URL
 * 
 * @param {string} url - 要判断的URL
 * @returns {boolean} 是否为一般网站URL
 */
export const isWebsiteUrl = (url) => {
  if (!url) return false;
  
  // 排除GitHub URL，匹配其他网站
  const githubPattern = /^https?:\/\/(?:www\.)?github\.com\//i;
  const websitePattern = /^https?:\/\/(?:www\.)?[^/]+\.[^/]+\/?.*$/i;
  
  return !githubPattern.test(url) && websitePattern.test(url);
};

/**
 * 检查URL格式是否有效
 * 
 * @param {string} url - 要检查的URL
 * @returns {boolean} URL是否有效
 */
export const isValidUrl = (url) => {
  if (!url) return false;
  
  try {
    new URL(url);
    return true;
  } catch (err) {
    return false;
  }
};

/**
 * 规范化URL格式
 * 
 * @param {string} url - 要规范化的URL
 * @returns {string} 规范化后的URL
 */
export const normalizeUrl = (url) => {
  if (!url) return '';
  
  // 添加协议前缀
  if (!/^https?:\/\//i.test(url)) {
    url = 'https://' + url;
  }
  
  try {
    // 规范化URL
    const urlObj = new URL(url);
    return urlObj.toString();
  } catch (err) {
    // 如果无法解析为URL，返回原始输入
    return url;
  }
};

/**
 * 提取GitHub仓库所有者和名称
 * 
 * @param {string} url - GitHub仓库URL
 * @returns {Object|null} 包含owner和repo的对象，如果不是有效的GitHub URL则返回null
 */
export const extractGithubRepoInfo = (url) => {
  if (!isGithubUrl(url)) return null;
  
  const pattern = /^https?:\/\/(?:www\.)?github\.com\/([^/]+)\/([^/]+)\/?.*$/i;
  const match = url.match(pattern);
  
  if (match && match.length >= 3) {
    return {
      owner: match[1],
      repo: match[2]
    };
  }
  
  return null;
};

/**
 * 提取网站的域名
 * 
 * @param {string} url - 网站URL
 * @returns {string|null} 网站域名，如果不是有效URL则返回null
 */
export const extractDomain = (url) => {
  if (!isValidUrl(url)) return null;
  
  try {
    const urlObj = new URL(url);
    return urlObj.hostname;
  } catch (err) {
    return null;
  }
}; 