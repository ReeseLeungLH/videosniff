# utils.py
import re
from config import MAX_FILENAME_LENGTH, STREAM_DOMAINS

def clean_filename(text, max_len=MAX_FILENAME_LENGTH):
    """
    清理文件名，去除系统非法字符并限制长度
    """
    if not text:
        return "unknown_video"
    # 去除 Windows/Linux 非法路径字符
    text = re.sub(r'[\\/*?:"<>|]', "_", text)
    # 去除控制字符
    text = re.sub(r'[\x00-\x1f]', '', text)
    # 合并连续空格
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(" _")
    
    if len(text) > max_len:
        text = text[:max_len]
    return text

def remove_query_params(url):
    """
    移除 URL 参数，用于归一化处理和去重
    """
    if not url:
        return ""
    return url.split('?')[0].strip()

def get_resolution_score(url):
    """
    对视频流链接进行质量评分：
    1. 包含 master/playlist/manifest 的通常是索引文件，得分最高。
    2. 包含 1080, 720 等分辨率数字的加分。
    3. MPD 格式通常优于单一 M3U8 片段，加分。
    """
    score = 0
    lower_url = url.lower()
    
    # 索引文件优先
    if any(k in lower_url for k in ["master", "playlist", "manifest"]):
        score += 10000
    
    # 格式优先
    if ".mpd" in lower_url:
        score += 5000
        
    # 分辨率匹配
    nums = re.findall(r'(\d{3,4})', url)
    if nums:
        # 过滤掉像年份(2023)或随机ID，只保留常见分辨率范围
        valid_res = [int(n) for n in nums if 300 <= int(n) <= 4320 and not (1980 <= int(n) <= 2030)]
        if valid_res:
            score += max(valid_res)
            
    return score

def is_stream_in_whitelist(url):
    """
    检查视频流 URL 是否符合域名白名单。
    如果 STREAM_DOMAINS 为空，则默认全部通过。
    """
    if not STREAM_DOMAINS:
        return True
    
    u_low = url.lower()
    return any(domain.lower() in u_low for domain in STREAM_DOMAINS)