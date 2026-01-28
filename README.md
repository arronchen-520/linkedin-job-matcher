🤖 AI CareerCopilot
CareerCopilot is an automated job search agent. It scrapes LinkedIn job postings, standardizes salary data using local LLMs (Llama 3), and utilizes the DeepSeek-V3 model to score and match your resume against specific Job Descriptions (JDs).

📖 Overview
Job hunting is tedious. CareerCopilot automates the entire pipeline:

Scraper: Navigates LinkedIn using a stealth browser to aggregate jobs based on complex filters (location, radius, date).

Salary Parser: Uses a local Llama 3.1 model (via Ollama) to extract and normalize salary ranges (hourly/monthly → annual) from unstructured text.

Matcher: Uses the DeepSeek-V3 API to act as a "Technical Recruiter," scoring the candidate's resume against every specific JD and providing a "Recommend Apply" boolean.

🚀 Features
Anti-Detection Scraping: Uses playwright-stealth and persistent user contexts (cookies) to survive LinkedIn's bot checks.

Cost-Effective AI:

Zero-cost local inference for high-volume tasks (Salary Parsing) using Ollama.

Low-cost, high-intelligence API (DeepSeek) only for the final high-value matching step.

Smart Filtering: Automatically removes "Reposted" jobs to ensure fresh opportunities.

Token Safety: Checks token counts before API calls to prevent cost overruns on massive JDs.

🛠️ Prerequisites
Before running this project, ensure you have the following installed:

Python 3.10+

Ollama: Required for local salary parsing.

Download Ollama

Run in terminal: ollama pull llama3.1

DeepSeek API Key: Required for the reasoning/matching engine.

LinkedIn Account: Valid credentials for scraping.

📦 Installation
Clone the Repository

Bash
git clone https://github.com/yourusername/CareerCopilot.git
cd CareerCopilot
Install Python Dependencies

Bash
pip install -r requirements.txt
Install Browser Binaries Playwright requires the Chromium browser to function:

Bash
playwright install chromium
Environment Setup Create a .env file in the root directory and add your credentials:

代码段
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
DEEPSEEK_API_KEY=sk-your-deepseek-key
⚙️ Configuration
Create a YAML configuration file in data/config/ (e.g., config_arron.yaml).

Template:

YAML
user: "Jack"
user_name: "Jack"
# Path to your PDF resume
resume: "data/resumes/Kack_Resume.pdf" 

# Browser Settings
headless: False  # Set to True to run invisibly (background)
tracing: False   # Set to True for debugging logs
max_page: 8      # Maximum number of pages to scrape per run

# Search Parameters
search:
  keyword: "Python Developer"
  city: "Toronto, Ontario, Canada"
  distance: 25            # Radius in km
  period: "Past 24 hours" # Options: Past 24 hours, Past week, Past month

# Filter Logic
repost: False    # Set False to ignore "Reposted" jobs
company_list: [] # Whitelist: If not empty, only these companies are kept.
▶️ Usage
Ensure Ollama is running in the background, then execute the main script:

Bash
python main.py
Application Flow:
Scraper: Launches the browser, logs in, scrapes jobs based on your config, and saves a raw CSV.

Salary Parser: Reads the raw CSV and uses Llama 3.1 to extract specific salary numbers.

Matcher: Reads your PDF resume and calls DeepSeek API to score every job.

Result: The final processed file is saved in output/filtered/.

🏗️ Project Structure
Plaintext
CareerCopilot/
├── data/
│   ├── config/          # YAML search configurations
│   ├── resumes/         # Candidate PDF resumes
│   └── user_data/       # Browser cookies/cache (managed by Playwright)
├── output/              # Scraped and processed CSVs
├── utils/               # Helper modules (logger, paths, file loading)
├── job_scraper.py       # LinkedIn automation logic
├── salary_parser.py     # Local LLM salary extraction
├── deepseek_jd_resume_matcher.py  # Resume matching logic
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
└── .env                 # API Keys and Credentials
⚠️ Disclaimer
Educational Use Only: This tool is intended for personal and educational use.

Terms of Service: Scraping LinkedIn may violate their User Agreement.

Risk: Do not set max_page too high or run the script continuously to avoid account flagging. The developers are not responsible for any account restrictions.

Troubleshooting
Q: The browser opens but gets stuck on a Captcha/Security Check. A: The script uses a persistent user_data_dir. On the first run, you may need to manually solve the captcha in the browser window. Subsequent runs will use the saved session cookies and skip login.

Q: Salary Parser error: "Connection Refused"? A: Ensure Ollama is installed and running (ollama serve).

Q: DeepSeek API errors? A: Verify your API key in the .env file and check your credit balance.