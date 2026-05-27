# monitor.py
import asyncio
from playwright.async_api import async_playwright
from config import (
    PAGE_DOMAINS, CHROME_CDP_URL, COLLECTION_WINDOW, 
    DEFAULT_UA, ENABLE_API
)
from utils import (
    clean_filename, get_resolution_score, 
    is_stream_in_whitelist, remove_query_params
)
from api_client import downloader

class BrowserMonitor:
    def __init__(self, history_manager):
        self.history = history_manager
        self.browser = None
        self.context = None

    async def connect(self):
        """连接到现有的 Chrome 实例"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.connect_over_cdp(CHROME_CDP_URL)
            self.context = self.browser.contexts[0]
            print(f"[Monitor] 成功连接到浏览器: {CHROME_CDP_URL}")
            return True
        except Exception as e:
            print(f"[Monitor] 连接浏览器失败: {e}")
            return False

    async def _close_page_safely(self, page, reason=""):
        """处理完成后自动关闭标签页"""
        try:
            if not page.is_closed():
                await page.close()
                if reason:
                    print(f"   [Monitor] 已自动关闭标签页 ({reason})")
        except:
            pass

    async def _process_video_capture(self, page, first_url, user_agent):
        """
        核心捕获逻辑：发现第一个流后，等待一段时间收集所有候选流，并选出最优解。
        """
        try:
            raw_title = await page.title()
            safe_title = clean_filename(raw_title)
        except:
            safe_title = "unknown_video"

        candidates = [first_url]

        # 内部监听器：在窗口期内继续收集其他流链接（例如不同分辨率的流）
        async def capture_more(response):
            try:
                u = response.url
                if (".m3u8" in u.lower() or ".mpd" in u.lower()) and is_stream_in_whitelist(u):
                    candidates.append(u)
            except:
                pass

        page.on("response", capture_more)
        await asyncio.sleep(COLLECTION_WINDOW)
        page.remove_listener("response", capture_more)

        if not candidates:
            page._is_processing = False
            return

        # 选出质量得分最高的链接
        unique_links = list(set(candidates))
        unique_links.sort(key=get_resolution_score, reverse=True)
        best_link = unique_links[0]
        
        clean_best_link = remove_query_params(best_link)

        # 再次检查去重（防止收集期间重复）
        if self.history.is_seen(clean_best_link):
            print(f"   [Monitor] 忽略重复视频: {safe_title[:20]}...")
            page._is_processing = False 
            return
        
        # 推送到下载器
        print(f"   [Monitor] 正在推送最佳流: {safe_title[:20]}...")
        success, status_label = await downloader.push(
            url=best_link, 
            name=safe_title, 
            referer=page.url, 
            user_agent=user_agent
        )
        
        # 记录日志
        self.history.save_record(best_link, safe_title, page.url, status_label)

        if success:
            await self._close_page_safely(page, reason="任务推送成功")
        else:
            print(f"   [Monitor] 推送失败，保留页面以便排查")
            page._is_processing = False

    async def _monitor_page(self, page):
        """为单个页面挂载监听逻辑"""
        if getattr(page, "_is_monitored", False): return
        page._is_monitored = True

        # 获取 UA
        try: ua = await page.evaluate("navigator.userAgent")
        except: ua = DEFAULT_UA

        async def response_handler(response):
            # 基础过滤：排除静态资源
            if response.request.resource_type in ["image", "stylesheet", "font", "script"]:
                return
            
            url = response.url
            u_low = url.split("?")[0].lower()

            # 检查是否为视频流格式
            if ".m3u8" not in u_low and ".mpd" not in u_low:
                return

            # 1. 网页域名白名单检查
            try:
                if page.is_closed(): return
                if not any(domain in page.url for domain in PAGE_DOMAINS):
                    return
            except: return

            # 2. 流域名白名单检查
            if not is_stream_in_whitelist(url):
                return

            # 3. 如果该页面正在处理中，则跳过，避免竞争
            if getattr(page, "_is_processing", False):
                return
            
            # 4. 去重检查
            if self.history.is_seen(url):
                return

            # 确认捕获
            page._is_processing = True
            print(f"\n[Monitor] 发现目标流: {page.url[:50]}...")
            asyncio.create_task(self._process_video_capture(page, url, ua))
            
        page.on("response", response_handler)

    async def start(self):
        """启动监控主循环"""
        if not self.context:
            if not await self.connect(): return

        print(f"[Monitor] 服务已启动。")
        print(f"   - 网页白名单: {PAGE_DOMAINS}")

        # 1. 对当前已打开的所有标签页挂载监听
        for page in self.context.pages:
            asyncio.create_task(self._monitor_page(page))

        # 2. 监听后续新打开的标签页
        self.context.on("page", lambda p: asyncio.create_task(self._monitor_page(p)))

        # 保持运行，直到浏览器断开
        disconnected = asyncio.Future()
        self.browser.on("disconnected", lambda: disconnected.set_result(True))
        await disconnected
        print("[Monitor] 浏览器已断开连接。")