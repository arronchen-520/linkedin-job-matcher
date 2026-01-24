# LinkedIn Job Scraper & Auto-Applier

> Automate LinkedIn job discovery, structured parsing, and data preparation for downstream resume matching (educational / research use only).

## Problem

Job searching is tedious and repetitive. This tool automates the discovery phase (scraping), parses job postings into structured data, and prepares clean outputs for analysis or resume–JD matching.

## Key Features

* Headless browser automation with Playwright to collect job listings and details
* YAML-based configuration for running multiple profiles and search strategies
* Structured CSV outputs for easy analysis with Pandas, vector stores, or LLMs

## Architecture

**Stack:** Python + Playwright + LLM (OpenAI / Gemini)

1. **Scraper** — Uses Playwright to collect job metadata (title, company, location, posting time, description, apply link)
2. **Controller** — Config-driven execution pipeline suitable for multiple user profiles
3. **Data Layer** — Saves structured job data to CSV under `./data/job_posts/`

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.9+
* Google Chrome / Chromium (or Playwright-managed browsers)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/linkedin-scraper.git
cd linkedin-scraper

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (example: chromium only)
playwright install chromium
# Or install all supported browsers
# playwright install
```

### 3. requirements.txt (Example)

```text
playwright>=1.40.0
pandas>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
typing-extensions>=4.5.0
# Optional: LLM client
# openai>=1.0.0
```

## Configuration

**Important:** Never commit `.env` files or credentials to version control.

### Step A — Credentials (`.env`)

Create a `.env` file in the project root to store sensitive information:

```
# .env (example)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
# Optional: OPENAI_API_KEY=sk-...
```

### Step B — User Preferences (YAML)

Create a config file under `./config/`, for example `config_arron.yaml`:

```yaml
task:
  keyword: "Machine Learning Engineer"
  city: "Toronto, Ontario, Canada"
  distance: 10                # Radius in km
  period: "Past 24 hours"    # Options: "Past 24 hours", "Past week", "Past month"

settings:
  headless: true              # Set to false to see the browser
  max_results: 100            # Optional: maximum number of jobs to scrape
  rate_limit: 1.0             # Optional: delay (seconds) between actions
```

## Usage

### Run with a configuration file

```bash
python main.py --config ./config/config_arron.yaml
```

### Run with command-line arguments (legacy mode)

```bash
python main.py --keyword "Data Scientist" --city "Vancouver"
```

### Output

* **Data:** CSV files are saved to `./data/job_posts/`, e.g.
  `jobs_Arron_Machine_Learning_20231027.csv`
* **Logs:** Execution logs are stored in `./log/scraper_run.log`

## Development & Debugging

* Set `headless: false` to observe browser behavior during runs
* Tune `rate_limit` and `max_results` to reduce the risk of triggering platform defenses

## ⚠️ Disclaimer

* **For educational purposes only.** Scraping LinkedIn may violate their Terms of Service. Use this tool responsibly and at your own risk.
* Avoid aggressive scraping behavior (high frequency or concurrency).
* Do not commit `.env` files or any credentials to public repositories.

## Optional Extensions

* Persist results to a database (SQLite / Postgres) instead of CSV
* Parse job descriptions into structured fields (responsibilities, requirements)
* Integrate local or hosted LLMs (e.g., Qwen, Llama, OpenAI) for resume–JD matching

---
