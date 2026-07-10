# RedCache — Chrome 扩展(纯本地,无需服务器)

这是 RedCache 的 **纯浏览器插件版**:采集、存储、分类、整理界面**全部在插件里**,数据存在你浏览器的 IndexedDB —— **不需要跑任何本地服务器,不需要终端,不存密码**。

This is the **pure-extension** build of RedCache: capture, storage, classification, and the curation UI all live inside the extension, with data in your browser's IndexedDB. **No local server, no terminal, no password.**

## 安装(加载已解压扩展)

1. 打开 Chrome,地址栏输入 `chrome://extensions`
2. 右上角打开「**开发者模式 / Developer mode**」
3. 点「**加载已解压的扩展程序 / Load unpacked**」
4. 选择这个 `extension/` 文件夹
5. 工具栏出现 RedCache 图标即安装成功

## 使用

1. **先登录**:在浏览器里正常登录 xiaohongshu.com / rednote.com。
2. 点 RedCache 图标打开弹窗 →「检查登录」确认已登录。
3. 「检测收藏夹」自动填好你的收藏夹地址(或手动粘贴)。
4. 「**导入收藏**」——插件会在后台打开你的收藏页、滚动、把全部收藏读进本地库。
5. 「**打开资料库**」进入整理界面:按分类筛选、逐条 保留/移除/长期/归档、点开原帖。
6. 缺标题的帖子点「补全标题」;要移除的在「移除复查」里逐条取消收藏。

## 工作原理

| 层 | 做什么 |
|---|---|
| `content-script.js` | 注入到已登录的站点页面,读收藏页 DOM、读笔记标题、点收藏按钮取消收藏 |
| `background.js` (service worker) | 编排:开标签页、调 content script、把结果灌进 IndexedDB |
| `src/lib/` | `extraction`(URL 规范化/去重/token 刷新)、`classifier` + `categories`(关键词分类)、`db`(IndexedDB)、`ingest`(入库管线)——从 Python 后端移植 |
| `dashboard.html` / `popup.html` | 整理界面 + 控制面板 |

采集用的是**你当前已登录的会话**,比自动化浏览器更像真人、风险更低。所有数据只存在本机浏览器,清除浏览器数据即清空。

## 隐私

不收集、不上传任何数据;不索取密码;除非你在「移除复查」里明确操作,否则不会取消任何收藏。

## 开发 / 测试

```bash
cd extension && node tests/lib.test.mjs   # 纯逻辑单测(分类器/抽取)
```

已验证:分类器、抽取/去重/token 刷新、入库管线、资料库界面渲染均在真实浏览器中通过。**在真实小红书页面上的采集需要你加载插件后实测**(受站点改版影响时,选择器可能需微调,见 `content-script.js`)。

## 与本地服务器版的关系

仓库根目录的 `backend/` + `frontend/` 是需要本地运行的完整版(功能更全,如直接写 Obsidian 库、文件备份)。本插件是**零服务器**的替代形态,导出改为浏览器下载。两者数据不互通。
