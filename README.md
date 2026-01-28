# 🤖 CareerCopilot

> **Automate your job hunt — discover better roles, faster, and apply with confidence.**
> 自动化你的求职流程 — 更快发现更合适的岗位，并自信投递。

[![GitHub stars](https://img.shields.io/github/stars/arronchen-520/CareerCopilot?style=social)](https://github.com/arronchen-520/CareerCopilot) [![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#) [![License](https://img.shields.io/badge/license-Apache--2.0-green)](#)

---

## 🚀 Hook — Why this repo will actually help you（吸引点）

**English (Top):**

* Tired of sifting through noisy job boards? CareerCopilot connects the whole loop: high-fidelity scraping, LLM-powered parsing, resume↔JD matching, and auto-fill — all configurable and reproducible.
* Built for speed and signal: local LLMs reduce API costs, token guards avoid waste; the matcher explains *why* a job fits (or doesn't) so you can decide fast.
* Designed by an engineer: clear configs, robust session persistence (avoid repeat captchas), CSV outputs ready for dashboards or interviews.

**中文 (Bottom)：**

* 是否厌倦了海量低质量岗位？CareerCopilot 将整个流程串联起来：高质量爬取 → LLM 解析 → 简历与职位匹配 → 自动填表，全部可配置、可复现。
* 以效率与信号为核心：本地 LLM 降低 API 成本，token 限制避免浪费；匹配器会给出**为什么**适合或不适合的理由，帮助你快速决策。
* 工程师友好：配置明确、会话持久化（减少验证码），输出 CSV 可直接用于可视化或面试展示。

---

## ✨ What it does / 功能亮点（快速浏览）

**English:**

* 🤖 Hybrid LLM stack: local Ollama (Llama3) for parse-heavy tasks + remote matcher for high-quality reasoning.
* 🧭 Config-first pipeline: YAML driven searches; re-run experiments deterministically.
* 🛡️ Safe-by-default: token-size guards, rate limits and optional headful mode for manual captcha solves.
* 📊 Outputs: `output/filtered/` CSV with `Match Score`, `Reasoning`, `Missing Skills` — ready for dashboards.

**中文：**

* 🤖 LLM 混合设计：本地 Ollama（Llama3）处理解析任务；远程 matcher 提供高质量推理。
* 🧭 配置优先：YAML 驱动搜索；实验可复现。
* 🛡️ 默认安全：token/大小校验、速率限制，可选有头浏览以人工通过验证码。
* 📊 输出：`output/filtered/` CSV（包含 Match Score、Reasoning、Missing Skills），可直接做数据展示。

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

---

## 📁 Structure / 项目结构
```
CareerCopilot/
├── data/            # config, sample resumes, user_data (cookies)
├── docs/            # demo GIFs, usage notes
├── src/             # scraper, parsers, matcher implementation
├── output/          # raw/filtered CSV results
├── main.py          # pipeline entrypoint
├── requirements.txt # recommended deps
└── .env.example     # credentials template
```

---

## 🔧 Config example / 配置示例

**English:**

`data/config/example.yaml`

```yaml
user: "Arron"
resume: "data/resumes/Arron_Resume.pdf"
headless: False
max_page: 6
search:
  keyword: "Data Scientist"
  city: "Toronto, Ontario, Canada"
  distance: 10
  period: "Past 24 hours"
```

---

## 🧾 Output & interpretation / 输出与解读

* `Match Score` (0-100) — 高分（>=60）表示推荐申请；
* `Reasoning` — 匹配解释，写明哪些经验命中或缺失；
* `Missing Skills` — 自动列出需要补的关键技能。

---

## 🛠️ Implementation notes / 实现要点

* Playwright + persistent `user_data_dir`（减少重复登录与 Captcha）。
* Ollama local model for salary / entity extraction; remote matcher for high-quality reasoning.
* Token-size safeguards: long JDs auto-summarized before sending to paid APIs.

---

## 🧾 License & closing / 许可证与结语

Apache-2.0

