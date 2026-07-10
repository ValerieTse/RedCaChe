# RedCache

**本地优先的小红书 / RedNote 收藏管理工具。** 把你收藏的帖子导入本地、按关键词自动分类、手动 review，全程只在你自己的电脑上运行——不上传、不存密码。

**A local-first curator for your saved Xiaohongshu / RedNote (小红书) posts.** Import your favorites, auto-sort them into categories, and review them privately — everything runs on your own machine. No uploads, no passwords stored.

> 🌏 **语言 / Language** — 中文教程在上半部分，English guide is in the lower half ([jump to English](#english-guide)). 两个版本内容一致，看你熟悉的语言即可。

---

# 中文教程（零基础版）

这份教程假设你**从没配置过任何开发环境**。跟着一步步做就行，不需要懂编程。

## 这是什么

RedCache 帮你整理小红书 / RedNote 里"收藏"的帖子：
- 把收藏的帖子导入到你电脑上的本地数据库。
- 按标题关键词自动归类（美妆、穿搭、手工、健身、美食…共 20+ 分类，可自定义）。
- 提供一个网页界面，让你逐条决定：保留、移除、长期收藏、归档。
- 可以把整理结果导出成 Markdown（用于 Obsidian 等笔记软件）。

## 它不会做什么（隐私）

- ❌ 不会索要或保存你的小红书密码。
- ❌ 不会把你的任何数据上传到网上——全部只存在你自己的电脑。
- ❌ 不会绕过验证码、风控、私有接口。
- ❌ 除非你**明确点击确认**，否则不会取消任何收藏。

## 免责声明

RedCache 是一个**整理你自己账号**收藏的个人工具。它在本地运行，浏览器自动化除了「你明确确认的取消收藏」外都是只读的。你的登录信息只存在本机的浏览器档案里，永不上传。平台页面结构会变，所以偶尔可能需要更新选择器。请在遵守平台服务条款的前提下使用。

---

## 第 0 步：先准备好三样东西

RedCache 由两部分组成：**后端**（Python 写的，负责抓取和数据库）和**前端**（网页界面）。所以你需要先装好运行它们的基础软件。

你需要装三样东西：**Python**、**Node.js**、以及（可选的）**Git**。下面按你的系统分别说。

### 怎么打开"终端"（Terminal / 命令行）

后面所有命令都要在"终端"里输入。

- **Mac**：按 `Command (⌘) + 空格`，输入 `Terminal`，回车。会弹出一个黑底或白底的文字窗口，这就是终端。
- **Windows**：按 `开始`，搜索 `PowerShell`，点开它。

> 💡 命令的用法：把下面代码框里的文字**复制**，粘贴到终端，按 `回车` 执行。一次粘一行。

### 1）安装 Python（3.11 或更高版本）

- **Mac / Windows 通用做法**：打开 [python.org/downloads](https://www.python.org/downloads/)，下载最新版 Python，双击安装。
  - ⚠️ **Windows 用户特别注意**：安装第一屏，一定要勾选 **"Add Python to PATH"**（把 Python 加入环境变量），再点 Install。
- 装完后，在终端输入下面这行验证（Mac 用 `python3`，Windows 用 `python`）：
  ```bash
  python3 --version
  ```
  看到类似 `Python 3.11.x` 或更高就成功了。

### 2）安装 Node.js（18 或更高版本）

- 打开 [nodejs.org](https://nodejs.org/)，下载 **LTS** 版本，双击安装，一路"下一步"。
- 装完后，在终端验证：
  ```bash
  node --version
  npm --version
  ```
  两行都能显示版本号就成功了。

### 3）安装 Git（可选——用来下载代码）

如果你不想装 Git，可以直接下载 ZIP 压缩包（见第 1 步的"方式二"），跳过这步。

- **Mac**：终端输入 `git --version`，如果没装它会提示你安装，按提示点确认即可。
- **Windows**：打开 [git-scm.com/download/win](https://git-scm.com/download/win) 下载安装。

---

## 第 1 步：把代码下载到电脑

**方式一（推荐，用 Git）**：在终端输入：
```bash
git clone https://github.com/ValerieTse/RedCaChe.git
cd RedCaChe
```

**方式二（不用 Git，下载 ZIP）**：
1. 打开 [github.com/ValerieTse/RedCaChe](https://github.com/ValerieTse/RedCaChe)。
2. 点绿色的 **Code** 按钮 → **Download ZIP**。
3. 解压，然后在终端 `cd` 进入解压出来的文件夹（可以先输入 `cd ` 加一个空格，再把文件夹拖进终端窗口，回车）。

> 之后所有命令都假设你**已经在项目文件夹里**（即 `RedCaChe` 目录）。

---

## 第 2 步：安装并启动

### 🍎 Mac / Linux 用户：一条命令搞定

在项目文件夹里运行：
```bash
./scripts/dev.sh
```
第一次运行它会自动：建好 Python 环境、装依赖、装浏览器、装前端依赖，然后同时启动前后端。（第一次可能要等几分钟，请耐心等。）

看到前端在 `http://localhost:5173` 启动后，跳到 [第 3 步](#第-3-步第一次使用配置向导)。按 `Ctrl + C` 可以停止。

> 如果提示 `permission denied`，先运行 `chmod +x scripts/dev.sh` 再重试。

### 🪟 Windows 用户（或想手动操作）：分两步

`dev.sh` 脚本在 Windows 上不能直接跑，请按下面手动来。你需要开**两个终端窗口**，一个跑后端、一个跑前端。

**终端 A —— 启动后端：**
```bash
cd backend
python -m venv .venv
```
然后激活虚拟环境（这一步 Mac 和 Windows 命令不同）：
```bash
# Mac / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```
接着安装依赖并启动（激活成功后行首会出现 `(.venv)`）：
```bash
pip install -e ".[dev]"
python -m playwright install chromium
python -m uvicorn app.main:app
```
看到 `Application startup complete` 就说明后端起来了。**这个窗口保持开着别关。**

**终端 B —— 启动前端**（新开一个终端，`cd` 回到项目文件夹）：
```bash
cd frontend
npm install
npm run dev
```
看到类似 `Local: http://localhost:5173/` 就成功了。

### 打开应用

用浏览器（Chrome / Edge / Safari 都行）打开：**http://localhost:5173**

---

## 第 3 步：第一次使用——配置向导

第一次打开会出现一个 4 步的引导向导，跟着点就行，**不需要改任何配置文件**：

1. **选地区**：海外 / 全球用户选 **RedNote**；中国大陆用户选 **Xiaohongshu（小红书）**。
2. **登录**：点"打开登录浏览器"，会弹出一个浏览器窗口，**在里面手动登录你的账号**（RedCache 看不到你的密码）。登录后回到向导，点"检查登录状态"，显示"已登录"即可下一步。
3. **选分类**：勾选你想要的分类。也可以在下面"自定义分类"里加自己的（比如"航空"），填几个命中词（如 `航空,飞机,机场`）它就能自动归类。
4. **导入**：RedCache 会自动检测你的收藏夹地址，然后在后台把你所有收藏导入到"资料库"。这一步可能要一两分钟，请保持窗口打开。

导入完成后点"进入 RedCache"，就进入主界面了。

---

## 日常使用

- **每日整理（Daily Review）**：点"更新"会在后台悄悄抓取你的新收藏（不会弹窗），你逐条决定保留 / 移除 / 长期收藏 / 归档。没判定的会一直留在这里。每天当地时间 22:30 也会自动抓一次（前提是后端在运行）。
- **资料库（Library）**：你"保留"的帖子在这里，可随时改分类。
- **移除收藏（Remove Check）**：选中帖子点"移除收藏"，会先本地备份，再在后台悄悄从平台取消收藏（不弹窗，带转圈提示）。
- **导出**：可以把整理结果导出成 Markdown。

---

## 常见问题（Troubleshooting）

- **输入命令后提示 `command not found: python3` / `node` / `npm`**：说明对应软件没装好，回到 [第 0 步](#第-0-步先准备好三样东西)重装，Windows 记得勾"Add to PATH"。
- **`permission denied: ./scripts/dev.sh`**：先运行 `chmod +x scripts/dev.sh`。
- **端口被占用（address already in use / port 5173 is in use）**：说明已经有一个在跑了，先关掉旧的（对应终端按 `Ctrl + C`）再重启。
- **登录后又跳回登录页 / 检查登录一直不是"已登录"**：在项目根目录创建一个 `.env` 文件，写入一行 `XHS_USE_SYSTEM_CHROME=true`，然后重启后端，再重新登录。这会用你系统自带的 Chrome，兼容性更好。
- **导入数量很少或"no_candidates_found"**：确认"检查登录"显示"已登录"；用从已登录浏览器里复制的真实收藏夹地址；如果出现验证码，在弹出的浏览器里手动过掉再重试。
- **想重新走一遍配置向导**：运行 `sqlite3 backend/data/xhs_curator.db "UPDATE app_config SET onboarding_completed=0;"`，然后刷新页面。

## 给开发者的提示

```bash
cd backend && pytest              # 后端测试
cd frontend && npm run test:links # 前端测试
```
用户级配置（站点、收藏夹地址、分类）存在数据库里，通过向导设置；`.env` 只放基础设施默认值（见 `.env.example`）。

---
---

<a name="english-guide"></a>
# English Guide (Zero-Experience Version)

This guide assumes you have **never set up a development environment before**. Just follow the steps — no coding knowledge required.

## What is this

RedCache helps you organize the posts you've **saved** on Xiaohongshu / RedNote:
- Imports your saved posts into a local database on your computer.
- Auto-sorts them by title keywords (Beauty, Fashion, Handcraft, Fitness, Food… 20+ categories, customizable).
- Gives you a web UI to decide, per post: keep, remove, evergreen, or archive.
- Can export your curated notes to Markdown (for Obsidian and similar apps).

## What it does NOT do (privacy)

- ❌ Never asks for or stores your Xiaohongshu password.
- ❌ Never uploads any of your data — everything stays on your own machine.
- ❌ Never bypasses CAPTCHAs, anti-bot checks, or private APIs.
- ❌ Never unfavorites anything unless you **explicitly confirm** it.

## Disclaimer

RedCache is a personal tool for organizing saves on **your own** account. It runs locally; browser automation is read-only apart from an explicitly confirmed unfavorite action. Your login lives only in a local browser profile and is never uploaded. Platform markup changes over time, so selectors may occasionally need updating. Use it in accordance with the platform's Terms of Service.

---

## Step 0: Install three things first

RedCache has two parts: a **backend** (written in Python, does the crawling and database) and a **frontend** (the web UI). So you first need the basic software to run them: **Python**, **Node.js**, and (optionally) **Git**.

### How to open a "Terminal" (command line)

Every command below is typed into a Terminal.

- **Mac**: press `Command (⌘) + Space`, type `Terminal`, hit Enter.
- **Windows**: click `Start`, search for `PowerShell`, open it.

> 💡 To run a command: **copy** the text in the code box, paste it into the Terminal, press `Enter`. One line at a time.

### 1) Install Python (3.11 or newer)

- **Mac / Windows**: go to [python.org/downloads](https://www.python.org/downloads/), download the latest Python, and run the installer.
  - ⚠️ **Windows users**: on the first screen, you **must** check **"Add Python to PATH"** before clicking Install.
- Verify in the Terminal (`python3` on Mac, `python` on Windows):
  ```bash
  python3 --version
  ```
  Seeing `Python 3.11.x` or higher means success.

### 2) Install Node.js (18 or newer)

- Go to [nodejs.org](https://nodejs.org/), download the **LTS** version, run the installer, click through.
- Verify:
  ```bash
  node --version
  npm --version
  ```

### 3) Install Git (optional — to download the code)

If you'd rather download a ZIP (see Step 1, "Option B"), you can skip this.

- **Mac**: type `git --version`; if not installed it will prompt you to install it.
- **Windows**: download from [git-scm.com/download/win](https://git-scm.com/download/win).

---

## Step 1: Download the code

**Option A (recommended, with Git):**
```bash
git clone https://github.com/ValerieTse/RedCaChe.git
cd RedCaChe
```

**Option B (no Git, download ZIP):**
1. Open [github.com/ValerieTse/RedCaChe](https://github.com/ValerieTse/RedCaChe).
2. Click the green **Code** button → **Download ZIP**.
3. Unzip it, then `cd` into the extracted folder (tip: type `cd ` with a space, then drag the folder into the Terminal window, and press Enter).

> All later commands assume you are **inside the project folder** (the `RedCaChe` directory).

---

## Step 2: Install and run

### 🍎 Mac / Linux: one command

From inside the project folder:
```bash
./scripts/dev.sh
```
On first run this automatically creates the Python environment, installs dependencies, installs the browser, installs frontend packages, and starts both servers. (The first run can take a few minutes — please be patient.)

Once the frontend starts on `http://localhost:5173`, jump to [Step 3](#step-3-first-run--the-setup-wizard). Press `Ctrl + C` to stop.

> If you get `permission denied`, run `chmod +x scripts/dev.sh` first, then retry.

### 🪟 Windows (or manual setup): two steps

The `dev.sh` script doesn't run on Windows directly, so do it manually. You'll need **two Terminal windows** — one for the backend, one for the frontend.

**Terminal A — start the backend:**
```bash
cd backend
python -m venv .venv
```
Then activate the virtual environment (this command differs by OS):
```bash
# Mac / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```
Then install and start (once activated, your prompt shows `(.venv)`):
```bash
pip install -e ".[dev]"
python -m playwright install chromium
python -m uvicorn app.main:app
```
`Application startup complete` means the backend is up. **Keep this window open.**

**Terminal B — start the frontend** (open a new Terminal, `cd` back into the project folder):
```bash
cd frontend
npm install
npm run dev
```
`Local: http://localhost:5173/` means success.

### Open the app

In any browser (Chrome / Edge / Safari), open: **http://localhost:5173**

---

## Step 3: First run — the setup wizard

The first time you open it, a 4-step wizard appears — just click through it, **no config files to edit**:

1. **Region**: Overseas / Global → **RedNote**; Mainland China → **Xiaohongshu (小红书)**.
2. **Log in**: click "Open login browser" — a browser window pops up. **Log in to your account there manually** (RedCache never sees your password). Back in the wizard, click "Check login status"; once it says "Logged in", continue.
3. **Categories**: tick the categories you want. You can also add your own under "Add your own" (e.g. "Aviation") with a few keywords (like `flight, airport, airline`) so it auto-classifies too.
4. **Import**: RedCache auto-detects your saved/favorites URL, then imports all your saves into the Library in the background. This can take a minute or two — keep the window open.

When it finishes, click "Enter RedCache" to reach the main app.

---

## Daily use

- **Daily Review**: click "Update" to quietly fetch new saves in the background (no popup window), then decide per post: keep / remove / evergreen / archive. Undecided ones stay here. It also auto-fetches once a day at 22:30 local time (while the backend is running).
- **Library**: your "kept" posts live here; you can re-categorize any time.
- **Remove Check**: select posts and click "Remove favorites" — it backs them up locally, then quietly unfavorites them on the platform in the background (no popup, with a spinner).
- **Export**: export your curated notes to Markdown.

---

## Troubleshooting

- **`command not found: python3` / `node` / `npm`**: the tool isn't installed correctly — redo [Step 0](#step-0-install-three-things-first); on Windows remember "Add to PATH".
- **`permission denied: ./scripts/dev.sh`**: run `chmod +x scripts/dev.sh` first.
- **Port in use (`address already in use` / `port 5173 is in use`)**: something is already running — stop the old one (`Ctrl + C` in its Terminal) and restart.
- **Login keeps returning to the login page / status never becomes "Logged in"**: create a `.env` file in the project root with the single line `XHS_USE_SYSTEM_CHROME=true`, restart the backend, and log in again. This uses your system Chrome for better compatibility.
- **Very few posts imported, or "no_candidates_found"**: confirm "Check login" shows "Logged in"; use the real favorites URL copied from the logged-in browser; if a CAPTCHA appears, solve it manually in the popup browser and retry.
- **Want to redo the setup wizard**: run `sqlite3 backend/data/xhs_curator.db "UPDATE app_config SET onboarding_completed=0;"`, then refresh the page.

## Notes for developers

```bash
cd backend && pytest              # backend tests
cd frontend && npm run test:links # frontend tests
```
User-level config (site, favorites URL, categories) lives in the database and is set via the wizard; `.env` only holds infrastructure defaults (see `.env.example`).

## License

MIT — see [LICENSE](LICENSE).
