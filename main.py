# main.py
import asyncio
import sys
from config import CHROME_CDP_URL, ENABLE_API
from storage import HistoryManager
from api_client import downloader
from monitor import BrowserMonitor

async def run_supplementary_tasks(history: HistoryManager):
    """
    启动时的补单逻辑：尝试重新推送之前失败的任务
    """
    pending_tasks = history.get_pending_tasks()
    if not pending_tasks:
        print("[Main] 没有发现待补单的任务。")
        return

    if not ENABLE_API:
        print("[Main] API 推送功能已关闭，跳过补单。")
        return

    print(f"[Main] 发现 {len(pending_tasks)} 条待处理记录，准备补单...")
    
    count = 0
    for record in pending_tasks:
        # 尝试推送
        success, status_label = await downloader.push(
            url=record["stream_url"],
            name=record["title"],
            referer=record["page_url"]
        )
        
        # 更新状态 (追加记录)
        history.update_status(record["stream_url"], status_label)
        
        if success:
            count += 1
        
        # 核心优化：如果连不上 API，直接中止补单，不浪费后续尝试
        if status_label == "ConnectError":
            print("[Main] 监测到 API 未开启，已中止补单流程。")
            break
            
        # 补单频率控制，避免瞬间冲击 API
        await asyncio.sleep(0.2)

    print(f"[Main] 补单结束，成功同步 {count} 条记录。")

async def main():
    print("="*50)
    print("  视频嗅探助手 v2.0 (模块化重构版)")
    print("="*50)

    # 1. 初始化存储层
    history = HistoryManager()

    # 2. 执行补单逻辑 (启动时运行一次)
    await run_supplementary_tasks(history)

    # 3. 启动实时监控逻辑
    monitor = BrowserMonitor(history)
    
    print(f"\n[Main] 正在监听浏览器请求 ({CHROME_CDP_URL})...")
    print("[Main] 提示：请确保 Chrome 已带参数 --remote-debugging-port=9222 启动。")

    while True:
        try:
            # 启动监控 (此方法会一直运行直到浏览器断开)
            await monitor.start()
        except Exception as e:
            print(f"\n[Main] 运行时错误: {e}")
        
        # 如果浏览器关闭或报错，等待后尝试重连
        print("[Main] 正在尝试重新连接浏览器...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Main] 服务已由用户手动停止。")
        sys.exit(0)