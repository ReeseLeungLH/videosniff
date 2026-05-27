# M3U8 嗅探脚本

基于 Playwright 的自动化视频流嗅探工具，通过Chrome 远程调试协议（CDP）连接现有浏览器，实现“网页浏览 -> 自动嗅探 -> 自动推送下载”的闭环。


#### 1. 环境准备
```bash
pip install requirements.txt
playwright install chromium
```

#### 2. 启动 Chrome (调试模式)
通过命令行启动：

```cmd
# Windows
chrome.exe --remote-debugging-port=9222
```

#### 3. 管理开启 [M3U8Downloader_H](https://github.com/Harlan-H/M3u8Downloader_H)

管理员开启，确保API开启，所有下载和聚合均依赖 **M3U8Download_H**

#### 4. 配置与运行
*   **白名单**：修改 `config.py` 中的 `PAGE_DOMAINS`（目标网站）和 `API_URL`（下载器地址）。
*   运行主程序：

```bash
python main.py
```

### 项目结构
*   `main.py`: 启动入口，负责初始化与历史补单。
*   `monitor.py`: 嗅探引擎，处理请求拦截与智能关页逻辑。
*   `storage.py`: 数据层，管理 JSONL 日志与去重。
*   `api_client.py`: 通信层，异步推送任务至下载器。
*   `utils.py`: 工具集，负责打分、清洗文件名及白名单校验。
*   `config.py`: 核心配置文件。

### 注意事项
*   **补单逻辑**：启动时会自动检查 `video_tasks.jsonl`，若 `status` 不是 `OK` 或 `Exists`，则会自动重新尝试推送。
*   **智能关闭**：如果推送成功后发现页面没关，请尝试切换一下标签页，脚本检测到 `hidden` 状态后会立即执行清理。
