# storage.py
import json
import os
from datetime import datetime
from config import LOG_FILE

class HistoryManager:
    def __init__(self):
        self.log_file = LOG_FILE
        # 内存索引：{ clean_url: { "title": ..., "status": ..., "full_data": ... } }
        self.tasks_map = {}
        # 已完成/已存在的 URL 集合，用于实时去重
        self.seen_urls = set()
        
        self._load_from_file()

    def _normalize_url(self, url):
        """简单的 URL 归一化，移除参数用于去重"""
        return url.split('?')[0].strip()

    def _load_from_file(self):
        """
        全量扫描 JSONL 文件。
        采用“最后一行覆盖”策略，自动获取每个 URL 的最新状态。
        """
        if not os.path.exists(self.log_file):
            return

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    record = json.loads(line)
                    url = record.get("stream_url")
                    if not url: continue
                    
                    clean_url = self._normalize_url(url)
                    # 存储/更新该 URL 的最新记录
                    self.tasks_map[clean_url] = record
                    
                    # 如果状态是 OK 或 Exists，加入去重集合
                    status = record.get("status")
                    if status in ["OK", "Exists"]:
                        self.seen_urls.add(clean_url)
                except json.JSONDecodeError:
                    continue
        
        print(f"[Storage] 加载完成: 历史记录总数 {len(self.tasks_map)}, 已完成 {len(self.seen_urls)}")

    def get_pending_tasks(self):
        """获取所有记录过但未成功推送的任务"""
        pending = []
        for clean_url, record in self.tasks_map.items():
            if record.get("status") not in ["OK", "Exists"]:
                pending.append(record)
        return pending

    def is_seen(self, url):
        """检查 URL 是否已经处理成功过"""
        return self._normalize_url(url) in self.seen_urls

    def save_record(self, stream_url, title, page_url, status):
        """
        追加一条记录到日志文件，并更新内存状态。
        """
        clean_url = self._normalize_url(stream_url)
        record = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "title": title,
            "page_url": page_url,
            "stream_url": stream_url,
            "status": status
        }
        
        # 1. 写入文件 (Append 模式)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        # 2. 更新内存索引
        self.tasks_map[clean_url] = record
        if status in ["OK", "Exists"]:
            self.seen_urls.add(clean_url)

    def update_status(self, stream_url, new_status):
        """
        仅更新状态。为了保持日志完整性，我们依然采用追加模式记录状态变更。
        """
        clean_url = self._normalize_url(stream_url)
        if clean_url in self.tasks_map:
            old_record = self.tasks_map[clean_url]
            self.save_record(
                stream_url=stream_url,
                title=old_record.get("title", "Unknown"),
                page_url=old_record.get("page_url", ""),
                status=new_status
            )