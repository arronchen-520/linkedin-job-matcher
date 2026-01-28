# 🤖 CareerCopilot

> **Automate your job hunt — discover better roles, faster, and apply with confidence.**
> 自动化你的求职流程 — 更快发现更合适的岗位，并自信投递。

[![GitHub stars](https://img.shields.io/github/stars/arronchen-520/CareerCopilot?style=social)](https://github.com/arronchen-520/CareerCopilot) [![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#) [![License](https://img.shields.io/badge/license-Apache--2.0-green)](#)

---

## 🚀 Why CareerCopilot? / 为什么选择 CareerCopilot？

**English:**
* **Cut through noise**: CareerCopilot doesn't just scrape — it **structures** LinkedIn postings into a ready-to-analyze table (title, company, posted_time, normalized_salary_range) so you immediately get clean data.
* **Explainable decisions**: For every job, we return a **Match Score** (0–100), a short **Reasoning** explaining *why*, and a `Missing Skills` list.
* **Salary-savvy**: LLM-powered extraction normalizes messy salary text into min/max numeric ranges (supports yearly/monthly/hourly and common abbreviations).
* **Faster & Safer**: Local LLMs (Ollama) reduce API costs; token-size guards and summarization protect you from runaway bills.

**中文：**
* **明确结构化**：不只是爬取内容，而是将 LinkedIn 职位**表格化**，方便直接进行筛选与数据分析。
* **可解释的申请建议**：每条职位输出 **Match Score (0–100)**、匹配理由 **Reasoning** 以及 **Missing Skills**，辅助决策。
* **薪资智能解析**：利用 LLM 将非标薪资文本标准化为 `min/max + currency + period`，支持多种周期和缩写。
* **更省更稳健**：支持本地 LLM 降低成本；内置 Token 长度守护与自动摘要功能，防止 API 账单爆表。

---

## ✨ Features / 功能亮点

**English:**
* 🗂️ **LinkedIn → Table**: Standardizes jobs into: `job_title`, `company`, `location`, `posted_time`, `is_repost`, etc.
* 🧠 **LLM Salary Extraction**: Auto-normalize salary into numeric ranges and currency types.
* 📈 **Scoring + Explanation**: Human-readable reasoning and skill-gap analysis for every role.
* 🔁 **De-dup & Repost Detection**: Focus on fresh listings by marking duplicates and reposts.
* ⚠️ **Token & Cost Guards**: Auto-summarize long JDs to minimize LLM context costs.

**中文：**
* 🗂️ **表格化输出**：将职位标准化为结构化字段，方便导出为 CSV/Excel 或用于分析工具。
* 🧠 **LLM 薪资解析**：自动将复杂的薪资描述解析为数值区间、货币和周期。
* 📈 **评分与解释**：为每个职位提供 `match_score`、可读的匹配理由以及缺失技能列表。
* 🔁 **去重与转发识别**：标注重复或转发（Repost）的职位，让你专注于新鲜岗位。
* ⚠️ **成本保护机制**：对长文本 JD 自动摘要，降低 LLM Token 消耗和 API 开销。

---

## 🧾 Output Schema / 输出字段示例

| Field / 字段 | Description / 描述 |
| :--- | :--- |
| `job_title` | Job title / 职位标题 |
| `company` | Company name / 公司名称 |
| `location` | Location or city / 地址或城市 |
| `posted_time` | Original and ISO standardized time / 发布时间（原文+标准 ISO 时间） |
| `is_repost` | Boolean: is it a reposted listing? / 是否为重复/转发（布尔值） |
| `raw_salary_text` | Original salary text from page / 页面原文中的薪资字段 |
| `min_salary` | Standardized minimum salary / 标准化最小薪资（数值） |
| `max_salary` | Standardized maximum salary / 标准化最大薪资（数值） |
| `currency` | Currency (USD/CAD/GBP/...) / 货币类型 |
| `period` | Salary period (year/month/hour) / 薪资周期（年/月/时） |
| `match_score` | Recommendation score (0–100) / 0–100 推荐评分 |
| `recommend_apply` | Boolean (e.g., `match_score >= 80`) / 是否建议申请 |
| `reasoning` | Short explanation for the match / 简短的匹配解释 |
| `missing_skills` | List of missing key skills / 缺失的关键技能列表 |

> **Pro Tips:**
> * **Match Score**: Prioritize high-potential roles quickly. / 快速锁定高潜力职位。
> * **Reasoning**: Actionable text for cover letters or interview prep. / 可直接用于求职信或面试准备。
> * **Missing Skills**: Quickly decide if a gap is fixable or a hard blocker. / 判断技能差距是否为硬伤。

---

## 🧪 Usage Patterns / 常见使用场景

* **Daily Monitoring**: Daily job pull with preferred companies highlighted. / **每日监控：** 定时抓取并高亮心仪公司。
* **Market Analysis**: Salary heatmaps and market research via `min_salary/max_salary`. / **市场分析：** 通过标准薪资字段进行行业调研。
* **Auto-Notifications**: Connect to webhooks for high-match roles. / **自动通知：** 针对高匹配度职位设置自动推送。

---

## ⚡ Quickstart / 快速开始

```bash
# Clone and setup / 克隆与安装
git clone [https://github.com/arronchen-520/CareerCopilot.git](https://github.com/arronchen-520/CareerCopilot.git) && cd CareerCopilot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# Configuration / 配置
cp .env.example .env  # Fill your credentials / 填写凭据
python main.py --config data/config/example.yaml
```

---

## 🔧 Config example / 配置示例

`config/default_setting.yaml`（演示）

```yaml
user: "Arron"
resume: "data/resumes/Arron_Resume.pdf"
headless: False

max_page: 6
search:
  keyword: "Data Scientist"
  city: "Toronto, Ontario, Canada"
  distance: 25
  period: "Past 7 days"
repost: false  # ignore reposted jobs
companies:     # filter by specific companies; leave empty to keep all
  - "Google"
  - "Shopify"
  - "Airbnb"
salary: true   # only jobs that have posted salaries

```

---

## 📁 Structure / 项目结构

```
CareerCopilot/
├── browser_user/
├── config/
├── data/            # config, sample resumes, user_data (cookies)
│   ├── job_posts/
│   │   ├── complete_posts/
│   │   └── filtered_posts/
│   ├── log/
│   └── resumes/
├── src/             # scraper, parsers, matcher implementation
│   └── utils/
├── requirements.txt # recommended deps
└── .env             # credentials template
```

---

## 🛠 Troubleshooting / 常见问题

* Captcha/Blocked: Run with headless: False to authenticate once and persist user_data_dir. / 验证码/被封锁：设置 headless: False 手动登录一次以保存 Session。
* Playwright Browser Missing: Run python -m playwright install chromium. / 浏览器缺失：请执行 Playwright 浏览器安装命令
* Ollama Connection: Ensure ollama serve is running if using local LLMs. / Ollama 连接：如使用本地模型，请确保 Ollama 服务已启动。

---

## Disclaimer / 免责声明（中英）

English: This project is for personal research only. You are responsible for complying with LinkedIn's Terms of Service. Scraping may result in account restrictions. Use at your own risk.

中文： 本项目仅供科研用途。你须自行确保遵守 LinkedIn 服务条款，爬取行为可能导致账号受限。请自行承担风险。

---

## License / 许可证

Apache-2.0