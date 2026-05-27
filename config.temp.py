# config.py

# ================= 1. 网页过滤配置 =================

# 只有在这些网站打开的标签页，才会启动嗅探
PAGE_DOMAINS = [
    "example.local",   # 网页
    "example"          # 关键字
]

# 视频流域名白名单 (m3u8/mpd 链接本身必须包含这些字符)
# 如果不确定视频存储在哪个 CDN，请保持此列表为空 []，即抓取所有发现的流链接
STREAM_DOMAINS = [
    "cdn.example.com",
    "hls.example"
]

# ================= 2. 嗅探行为配置 =================

# 发现第一个流链接后，继续收集并比对清晰度的时间窗口（秒）
COLLECTION_WINDOW = 3

# 保存到下载器时的文件名最大长度
MAX_FILENAME_LENGTH = 80

# 备用 User-Agent (当无法从浏览器动态获取时使用)
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ================= 3. 智能关页配置 =================

# 是否启用智能关闭：True = 待用户离开/切换标签页后再关闭；False = 推送成功后立即关闭
SMART_CLOSE = True 

# 检查页面是否被隐藏/用户是否离开的频率（秒）
VISIBILITY_CHECK_INTERVAL = 2

# ================= 4. 存储配置 =================

# 任务日志文件名 (JSONL 格式：一行一个 JSON 对象，便于补单解析)
LOG_FILE = "video_tasks.jsonl"

# ================= 5. 下载器 API 配置 =================

# 是否开启 API 推送
ENABLE_API = True

# 本地下载器的 API 地址
API_URL = "http://127.0.0.1:65432/downloadbyurl"

# 下载器保存文件的物理路径 (注意 Windows 路径建议使用双斜杠 \\)
SAVE_PATH = "E:\\dll"

# ================= 6. 浏览器连接配置 =================

# Chrome 远程调试地址 (启动 Chrome 需带参数 --remote-debugging-port=9222)
CHROME_CDP_URL = "http://localhost:9222"