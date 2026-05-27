# api_client.py
import asyncio
import requests
from config import ENABLE_API, API_URL, SAVE_PATH, DEFAULT_UA

class DownloaderAPI:
    def __init__(self):
        self.api_url = API_URL
        self.enabled = ENABLE_API
        # 设置请求不使用系统代理，防止本地 API 请求被转发到梯子
        self.proxies = {"http": None, "https": None}

    def _sync_post(self, payload):
        """同步发送 POST 请求的具体实现"""
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.api_url, 
                json=payload, 
                timeout=10, 
                proxies=self.proxies, 
                headers=headers
            )
            try:
                return response.status_code, response.json()
            except:
                return response.status_code, {"Code": -1, "Msg": response.text}
        except requests.exceptions.ConnectionError:
            return None, {"Code": -1, "Msg": "ConnectionError"}
        except Exception as e:
            return None, {"Code": -1, "Msg": str(e)}

    async def push(self, url, name, referer, user_agent=None):
        """
        异步推送任务到下载器。
        返回: (bool 成功与否, str 状态标签)
        """
        if not self.enabled:
            return False, "Disabled"

        ua = user_agent or DEFAULT_UA
        payload = {
            "url": url,
            "name": name,
            "savepath": SAVE_PATH,
            "headers": {
                "User-Agent": ua,
                "Referer": referer
            }
        }

        # 在线程池中执行同步 IO 请求，避免阻塞事件循环
        status_code, data = await asyncio.to_thread(self._sync_post, payload)

        # 1. 连接异常处理
        if data.get("Msg") == "ConnectionError":
            print(f"   [API] 警告: 无法连接到下载器 (请检查 API 端口 {self.api_url})")
            return False, "ConnectError"

        # 2. HTTP 状态码异常
        if status_code != 200:
            print(f"   [API] HTTP 错误: {status_code}")
            return False, f"HTTP_{status_code}"

        # 3. 解析 API 业务逻辑
        api_code = data.get("Code")
        api_msg = data.get("Msg", "")

        if api_code == 0:
            print(f"   [API] 推送成功: {name[:30]}...")
            return True, "OK"
        
        elif api_code == 1 and ("已经存在" in api_msg or "exists" in api_msg.lower()):
            print(f"   [API] 任务已存在: {name[:30]}...")
            return True, "Exists"
        
        else:
            print(f"   [API] 推送被拒绝: {api_msg}")
            # 返回具体错误信息的前20个字符作为状态标签
            return False, f"Error: {api_msg[:20]}"

# 实例化单例
downloader = DownloaderAPI()