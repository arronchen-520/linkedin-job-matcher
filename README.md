# 🤖 CareerCopilot

> **Automate your job hunt — discover better roles, faster, and apply with confidence.**
> 自动化你的求职流程 — 更快发现更合适的岗位，并自信投递。

[![GitHub stars](https://img.shields.io/github/stars/arronchen-520/CareerCopilot?style=social)](https://github.com/arronchen-520/CareerCopilot) [![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#) [![License](https://img.shields.io/badge/license-Apache--2.0-green)](#)

---

## 🚀 Hook — Why CareerCopilot actually works（吸引点）

**English (Top):**

* Cut through noise: CareerCopilot doesn't just scrape — it **structures** LinkedIn postings into a ready-to-analyze table (title, company, posted_time, is_repost, raw_salary_text, normalized_salary_range) so you immediately get clean data to filter and visualize.
* Explainable decisions: For every job we return a **Match Score** (0–100), a short **Reasoning** explaining *why* the score was given, and a `Missing Skills` list you can act on.
* Salary-savvy: LLM-powered salary extraction normalizes messy salary text into min/max numeric ranges and currency (supports ranges, yearly/monthly/hourly, and common abbreviations).
* Faster, cheaper, and safer: Local LLMs for parse-heavy tasks reduce API cost; token-size guards and summarization protect you from runaway bills.

**中文 (Bottom)：**

* 明确结构化：CareerCopilot 不只是爬取网页内容——它把 LinkedIn 的职位信息**表格化**（`title, company, posted_time, is_repost, raw_salary_text, normalized_salary_range`），方便筛选与可视化。
* 可解释的申请建议：每条职位都会输出 **Match Score（0–100）**、简短的 **Reasoning（为什么）**，以及 `Missing Skills` 列表，方便你立刻采取行动。
* 薪资智能解析：用 LLM 自动把乱七八糟的薪资字段解析并标准化为 `min/max + currency + period`（支持年薪/月薪/时薪等常见格式和缩写）。
* 更快、更省、更稳健：将解析型任务放在本地 LLM，减少 API 成本；对长文本做自动摘要来避免昂贵调用。

---

## ✨ Features / 功能亮点（快速浏览）

**English:**

* 🗂️ **LinkedIn → Table**: Standardizes each job into row fields: `job_title`, `company`, `location`, `posted_time`, `is_repost`, `raw_salary_text`, `min_salary`, `max_salary`, `currency`, `period`.
* 🧠 **LLM Salary Extraction**: Auto-extract and normalize salary into numeric ranges and period with confidence flags.
* 📈 **Scoring + Explanation**: `match_score`, `reasoning`, `missing_skills` — score + human-readable explanation for each job.
* 🔁 **De-dup & Repost detection**: Mark reposts and near-duplicates so you focus on fresh listings.
* ⚠️ **Token & Cost Guards**: Auto-summarize long JDs and split requests to protect against high API costs.

**中文：**

* 🗂️ **表格化输出**：把每条职位标准化为字段，方便导出为 CSV/Excel 或用于 BI 工具。
* 🧠 **LLM 薪资解析**：将原始薪资文本自动解析为数值区间并输出置信度与原始文本。
* 📈 **评分与解释**：每条岗位含 `match_score`、可读的 `reasoning` 与 `missing_skills`，支持自动筛选与人工复核。
* 🔁 **去重与 repost 识别**：标注 repost，优先查看新岗位。
* ⚠️ **成本保护**：长文本自动摘要、分片调用，降低付费 API 的不确定开销。

---

## ⚡ Quickstart — one-liner to get started / 快速开始

**English:**

```bash
git clone https://github.com/arronchen-520/CareerCopilot.git && cd CareerCopilot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env  # fill creds
python main.py --config data/config/example.yaml
```

**中文：**

```bash
git clone https://github.com/arronchen-520/CareerCopilot.git && cd CareerCopilot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env 
python main.py --config data/config/example.yaml
```

---

## 📁 Structure / 项目结构

```
CareerCopilot/
├── data/            # config, sample resumes, user_data (cookies)
│   ├── config/
│   └── resumes/
├── docs/            # demo GIFs, usage notes, parsing docs
├── src/             # scraper, parsers, matcher implementation
├── output/          # raw/filtered CSV results
├── main.py          # pipeline entrypoint
├── requirements.txt # recommended deps
└── .env             # credentials template
```

---

## 🔧 Config example / 配置示例（保留并增强）

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
repost: false (ignore reposted jobs)
companies: (list of companies that you are interested in; only jobs from these companies will be returned; you can leave it empty to keep all jobs)
  - "Google"
  - "Shopify"
  - "Airbnb"
salary: true (only jobs that have posted salaries will be returned)

```

## 🧾 Output schema / 输出字段示例

* `job_title` — 职位标题
* `company` — 公司名
* `location` — 地址/城市
* `posted_time` — 发布时间（原文+标准化 ISO 时间）
* `is_repost` — 是否为重复/转发（bool）
* `raw_salary_text` — 页面原文中抓到的薪资字段
* `min_salary` — 标准化最小薪资（数值）
* `max_salary` — 标准化最大薪资（数值）
* `currency` — 货币（USD/CAD/GBP/…）
* `period` — 年/月/小时（year/month/hour）
* `match_score` — 0–100 推荐分
* `recommend_apply` — 布尔（例如 `match_score >= 80`）
* `reasoning` — 简短的匹配解释（可用于复盘或自动化决策）
* `missing_skills` — 列表/字符串，表明缺失的关键技能

---

## 🧾 Why Score + Reasoning + Missing Skills matters / 保留解释

* Match Score: prioritize high-potential roles quickly.
* Reasoning: provides actionable text you can reuse in cover letters or interview prep.
* Missing Skills: quickly decide if a gap is short-term fixable or a hard blocker.

---

## 🧪 Example usage patterns / 常见使用场景（保留）

* Daily job pull with preferred companies highlighted.
* Salary heatmaps and market research via `min_salary`/`max_salary`.
* Auto-notifications

---

## 🛠 Troubleshooting / 常见问题（保留）

* Captcha/blocked: run with `headless: False`, authenticate once to persist `user_data_dir`.
* Playwright browser missing: run `python -m playwright install chromium`.
* Ollama connection: ensure `ollama serve` is running if used.

---

## Disclaimer / 免责声明（中英）

**English:**

* This project is provided for personal, educational, and research purposes only. It is **not** legal advice. You are responsible for ensuring that your use complies with LinkedIn's Terms of Service and all applicable laws and regulations in your jurisdiction. Scraping websites may violate terms and could result in account restrictions or legal consequences.
* Do NOT share your real account credentials in public repositories. Store secrets locally and securely (e.g., use environment variables and do not commit `.env`).
* Salary parsing and match scoring are heuristic and may be inaccurate. The LLM and automated parsers can make mistakes — always verify salary and job details on the original posting before applying or negotiating. Use `reasoning` as guidance, not definitive judgement.
* Use at your own risk. The maintainers are not liable for losses, damages, or legal issues arising from use of the project.

**中文：**

* 本项目仅供个人、教育与研究用途，并非法律意见。你须自行确保使用行为遵守 LinkedIn 服务条款及所在司法辖区的相关法律法规。爬取网站可能违反条款，可能导致账号受限或法律风险。
* 请勿在公共仓库中共享真实账户凭证。请安全保存密钥（例如使用环境变量），不要提交 `.env` 等包含敏感信息的文件。
* 薪资解析与匹配评分具有启发性，可能不准确。LLM 与自动化解析可能出现错误 — 在申请或谈薪前请务必在原始岗位页面核实薪资与岗位信息。将 `reasoning` 作为参考而非最终结论。
* 自行承担风险。维护者对因使用本项目导致的任何损失、损害或法律问题不承担责任。

---

## License / 许可证

Apache-2.0