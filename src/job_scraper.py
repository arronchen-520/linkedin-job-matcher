import os
import time
import logging
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from utils.config_loader import get_run_parameters
from utils.logger import setup_logging
from utils.file_path import USER_DATA_DIR, CONFIG_DIR, COMPLETE_FILE_PATH, FILTERED_FILE_PATH
from playwright_stealth import stealth_sync
from playwright.sync_api import sync_playwright, Page, BrowserContext, Locator, expect

class LinkedInScraper:
    """
    Orchestrates the end-to-end automation for scraping job postings from LinkedIn.
    
    Responsibilities:
    - Manages the Playwright browser lifecycle (start, context, close).
    - Handles user authentication via environment variables.
    - Executes job searches with configurable filters (location, date, distance).
    - Parses job cards to extract metadata, descriptions, and salary info.
    - Filters and persists data to CSV formats.
    """

    def __init__(self):
        """
        Initializes the scraper instance and sets up empty state containers.
        """
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.job_list: List[Dict] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_tracing = False

    def start_browser(self, headless: bool = False, enable_tracing: bool = False):
        """
        Initializes the Playwright engine and launches a persistent browser context.
        
        Uses a persistent context to maintain cookies and local storage (session data),
        minimizing the need for repeated logins.
        
        Args:
            headless (bool): If True, runs the browser in the background without a UI.
        """
        self.logger.info("Initializing Playwright and launching browser...")
        try:
            self.playwright = sync_playwright().start()
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,  # Persist cookies and login session
                channel="chrome", 
                headless=headless,    
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 
                viewport={"width": 1920, "height": 1280}, 
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            # Start tracing if enabled
            if enable_tracing:
                self.is_tracing = True
                self.context.tracing.start(
                    name="linkedin_scraping_trace",
                    screenshots=True,
                    snapshots=True,
                    sources=True
                )
                self.logger.info("Tracing started.")
            self.page = self.context.new_page()
            # stealth_sync(self.page)
            self.logger.info("Browser session started successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to launch browser: {e}")
            raise

    def sign_in(self):
        """
        Navigates to the LinkedIn login portal and handles authentication.
        
        Checks if the user is already logged in via cookies. If not, it attempts
        to log in using credentials stored in the .env file.
        Includes a pause handler for manual intervention if a security check is detected.
        """
        self.logger.info("Navigating to LinkedIn job search page...")
        try:
            self.page.goto('https://www.linkedin.com/jobs/')
            
            # Check for sign-in button visibility
            if self.page.get_by_role('button', name='Sign in').is_visible():
                self.logger.info("Sign-in button detected. Attempting authentication...")
                self.logger.info("Loading email and password from .env.")
                try:
                    load_dotenv()
                    email = os.getenv("LINKEDIN_EMAIL")
                    password = os.getenv("LINKEDIN_PASSWORD")
                    self.logger.info("Successfully loading email and password from .env.")
                except:
                    self.logger.critical("Error loading email and password from .env.")
                    raise
                self.page.get_by_label('Email or phone').fill(email)
                self.page.get_by_label('Password').first.fill(password)
                self.page.get_by_role('button', name='Sign in').click()

                self.logger.info("Credentials submitted.")

            else:
                self.logger.info("Sign-in button not found. User may already be logged in.")
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise

        if self.page.get_by_text('security check').is_visible():
            self.logger.warning("Bot check detected. Pausing to wait for user input...")
            input("Press Enter after completing the bot check on the page...")
            self.logger.info("Resuming after bot check.")


    def search_jobs(self, keywords: str, city: str):
        """
        Executes a job search query using the provided keywords and location.
        
        Args:
            keywords (str): Job title or skills (e.g., "Python Developer").
            city (str): The location for the search (e.g., "Toronto, ON").
        """
        self.logger.info(f"Executing search for keywords: '{keywords}' in '{city}'")
        try:
            search_box = self.page.get_by_placeholder('Describe the job you want')
            search_box.fill(keywords + ' in ' + city)
            search_box.press('Enter')
        except Exception as e:
            self.logger.error(f"Search execution failed: {e}")

    def set_distance(self, distance: int):
        """
        Applies a radius filter to the search results.
        
        Args:
            distance (int): The search radius in kilometers. 
                            Note: The UI slider snaps to specific increments, so the value 
                            is rounded to the nearest multiple of 5.
        """
        distance = int(round(distance / 5) * 5) # Ensure distance is a multiple of 5 compatible with UI.
        self.logger.info(f"Setting location filter: {distance}km")
        try:
            location_bpx = self.page.locator('svg#location-marker-small')
            location_bpx.wait_for()
            location_bpx.click()
            # Set Distance
            self.page.locator("svg#edit-small").click()
            slider = self.page.locator('input[type="range"][aria-label^="Slider"]')
            slider.fill(str(distance))
            time.sleep(0.5)
            self.page.get_by_role('button', name='Show results').click()
            self.logger.info("Location filters applied successfully.")
        except Exception as e:
            self.logger.error(f"Failed to set location filters: {e}")

    def filter_period(self, period: str):
        """
        Filters search results by the date posted.
        
        Args:
            period (str): One of ['Past 24 hours', 'Past week', 'Past month'].
                          Defaults to 'Past 24 hours' if invalid.
        """
        self.logger.info(f"Applying time filter: {period}")
        valid_periods = ['Past 24 hours', 'Past week', 'Past month']
        
        if period not in valid_periods:
            self.logger.warning(f"Invalid period '{period}'. Defaulting to 'Past 24 hours'. Valid options: {valid_periods}")
            period = 'Past 24 hours'

        try:
            self.page.get_by_label('Date posted').locator('..').click()
            self.page.get_by_role('radio', name=period).click() 
            self.page.get_by_role('button', name='Show results').click()
        except Exception as e:
            self.logger.warning(f"Failed to apply time filter: {e}")

    def scrape_available_jobs(self, max_page):
        """
        Iterates through search pagination and extracts job data from each card.

        Args:
            max_page (int): The maximum number of pages to scrape before stopping.

        Returns:
            None: Extracted data is handled via _process_single_job.

        Workflow:
        1. Validates presence of SearchResultsMainContent.
        2. Locates all job cards using data-view-name attributes.
        3. Sequentially processes cards via _process_single_job.
        4. Detects and clicks the 'Next' pagination button.
        5. Terminates if max_page is reached or the 'Next' button is missing.
        """
        self.logger.info("Starting job scraping sequence...")
        exit_loop = False
        cnt_page = 1

        while not exit_loop:
            try:
                self.page.locator('div[componentkey = "SearchResultsMainContent"]').wait_for()
                self.logger.info('Page content loaded. Extracting job cards...')
                
                # Retrieve job cards
                jobs = self.page.locator('div[data-view-name = "job-search-job-card"] div[role = "button"]').all()
                self.logger.info(f"Found {len(jobs)} jobs on the current page.")
                
                for i, job in enumerate(jobs, 1):
                    self.logger.debug(f"Processing job {i}...")
                    self._process_single_job(job, i)
                
                # Handle Pagination
                next_button = self.page.locator("button[data-testid *= 'pagination-controls-next-button-visible']")
                if next_button.count() == 0:
                    self.logger.info('Pagination end reached. Terminating scrape loop.')
                    exit_loop = True
                elif cnt_page == max_page:
                    self.logger.info('Max page reached. Terminating scrape loop.')
                    exit_loop = True
                else:
                    self.logger.info('Navigating to next page...')
                    next_button.first.click()
                    cnt_page += 1
                    
            except Exception as e:
                self.logger.error(f"Unexpected error during pagination loop: {e}")
                exit_loop = True

    def _process_single_job(self, job_element: Locator, count: int):
        """
        Extracts detailed information from a single job card.
        
        Actions:
        - Parses title, company, location, and post date from the card text.
        - Clicks the card to load the details panel.
        - Extracts the full job description.
        - Identifies salary information (if present in text).
        - Detects 'Reposted' status.
        
        Args:
            job_element (Locator): The Playwright locator for the job card.
            count (int): The current job index for logging purposes.
        """
        job_element.scroll_into_view_if_needed()
        
        try:
            job_text = job_element.inner_text()
        except Exception as e:
            self.logger.warning(f"Failed to read text for job #{count}: {e}")
            return

        # Basic Parsing
        try:
            parts = job_text.split('\n\n') # Might consider updating to locator
            job_title = parts[0].split('\n')[-1]
            company = parts[1]
            location = parts[2]
            # Clean posted time
            posted_text = '\n'.join([t for t in parts if 'ago' in t or 'just posted' in t.lower()])
            posted_text = posted_text.split('\n')
            for time_text in posted_text:
                if 'Posted on' in time_text:
                    time_text = time_text.replace('Posted on ', '')
                    posted_time = pd.to_datetime(time_text)
                elif 'ago' in time_text or 'now' in time_text:
                    posted_ago = time_text
                else:
                    posted_time = None
                    posted_ago = None
            # Text cleaning
            job_title = job_title.replace('\u00a0', ' ')
            company = company.replace('\u00a0', ' ')
            location = location.replace('\u00a0', ' ')
        except IndexError:
            self.logger.warning(f"Job #{count} has an unexpected text structure. Skipping.")
            return

        # Detail Extraction
        job_description = ''
        salary = ''
        url = ''
        
        try:
            job_element.click()

            # Check whether or not this is a reposted job
            reposted = self.page.get_by_text('Reposted').count()
            if reposted == 0:
                reposted = False
            else:
                reposted = True

            # Extract description/salary
            try:
                try:
                    details = self.page.get_by_role('heading', name = 'About the job').locator('..').locator('..')
                    details.wait_for()
                    desc_text = details.inner_text()
                except:
                    desc_text = ''
                    self.logger.warning(f"Could not extract description details for {job_title} at {company}.")
                if desc_text != '':
                    job_description = '\n'.join([line for line in desc_text.split('\n') if line.strip()])
                    # Salary extraction logic
                    salary = []
                    salary_lines = job_description.split('\n')
                    for line in salary_lines:
                        if ('$' not in line) & ('CAD' not in line):
                            continue
                        sentences = line.split('. ')
                        for sentence in sentences:
                            if ('$' in sentence or 'CAD' in sentence) & (' raise' not in sentence):
                                sentence = sentence.strip()
                                if len(sentence) < 100:
                                    salary.append(sentence)
                    salary = ' | '.join(salary)
            except Exception:
                self.logger.debug(f"Could not extract description details for {job_title} at {company}.")

            # Extract URL
            try:
                url = self.page.locator("a[data-view-name = 'job-apply-button']").get_attribute('href')
            except Exception:
                pass

        except Exception as e:
            self.logger.warning(f"Interaction failed for {job_title} at {company}")
            return

        # Store Data
        self.job_list.append({
            'Job Title': job_title,
            'Company': company,
            'Location': location,
            'Posted Time': posted_time,
            'Posted Ago': posted_ago,
            'Reposted': reposted,
            'Salary': salary,
            'URL': url,
            'Job Description': job_description
        })
        self.logger.info(f"Successfully scraped: {job_title} at {company}")

    def save_to_csv(self, filepath: Path, search): 
        """
        Persists the collected job list to a CSV file.
        
        Args:
            filepath (Path): The directory path to save the file.
            search (Dict): Search parameters to construct the filename.
        """
        if not self.job_list:
            self.logger.warning("No jobs were collected. Skipping CSV generation.")
            return
        
        current_date = datetime.now().strftime("%Y%m%d")
        filepath = Path(filepath / f"{current_date}_{search['keyword']}_{search['city']}_{search['period']}.csv")
        self.logger.info(f"Saving {len(self.job_list)} jobs to {filepath}...")
        
        try:
            pd.DataFrame(self.job_list).to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info("File saved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to save CSV to {filepath}: {e}")

    def filter_eligible_jobs(self, filepath: Path, params: dict):
        """
        Filters the raw job list based on user preferences and saves a secondary CSV.
        
        Filter Logic:
        1. Keep job if Company is in `params['company_list']` OR if the job has `Salary` info.
        2. Filter based on the `Reposted` status preference.
        
        Args:
            filepath (Path): Directory path for the filtered output.
            params (dict): Configuration dictionary containing 'company_list', 'user_name', and 'repost'.
        """
        df = pd.DataFrame(self.job_list)
        company_list = params['company_list']
        user = params['user_name']

        if company_list == []:
            self.logger.info(f"No company list provided. ")
            if not params['salary']:
                self.logger.info(f"No salary boolean provided. ")
            else:
                self.logger.info(f"Filtering jobs with salaries... ")
                df = df[df['Salary'] != '']
        else:
            if not params['salary']:
                self.logger.info(f"No salary boolean provided. ")
                df = df[df['Company'].isin(company_list)]
            else:
                self.logger.info(f"Filtering jobs with either intested companies or presented salaries... ")
                df = df[(df['Salary'] != '') | (df['Company'].isin(company_list))]
        
        # if not params['salary']:
        #     self.logger.info(f"No salary boolean provided. ")
        # else:
        #     self.logger.info(f"Filtering jobs with salaries... ")
        #     df = df[df['Salary'] != '']

        if params['repost']:
            self.logger.info(f"No repost boolean provided. ")
        else:
            self.logger.info(f"Filtering newly posted jobs... ")
            df = df[~df['Reposted']]

        current_date = datetime.now().strftime("%Y%m%d")
        search = params['search']
        filepath = Path(filepath / f"{current_date}_{user}_{search['keyword']}_filtered.csv")
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        self.logger.info(f"Filtered {len(df)} eligible jobs and saved to {filepath}")
        return df
    
    def run(self, params):
        """
        Main entry point for the scraper execution flow.
        
        Args:
            params (dict): Run configuration loaded from YAML.
        """
        try:
            search = params['search']
            self.logger.info(f"Starting task for [{params['user_name']}]: {search['keyword']} in {search['city']}")
            self.start_browser(headless=params['headless'], enable_tracing=params['tracing'])
            self.sign_in()
            self.search_jobs(search['keyword'], search['city'])
            self.filter_period(search['period'])
            self.set_distance(search['distance'])
            self.scrape_available_jobs(params['max_page'])
            self.save_to_csv(COMPLETE_FILE_PATH, search)
            result = self.filter_eligible_jobs(FILTERED_FILE_PATH, params)
            self.logger.info("Task completed successfully.")
            return result
        except KeyboardInterrupt:
            self.logger.warning("Process interrupted by user.")
            return None
        except Exception as e:
            self.logger.critical(f"Unexpected error: {e}", exc_info=True)
            return None

    def close(self, trace_path: str = "trace.zip"):
        """
        Gracefully terminates the browser context and stops the Playwright engine.
        """
        self.logger.info("Closing browser resources.")
        if self.context:
            if self.is_tracing:
                self.context.tracing.stop(path=trace_path)
                self.logger.info(f"Trace saved to {trace_path}")
            if self.page:
                self.page.close()
            self.context.close()
        if self.playwright:
            self.playwright.stop()

# if __name__ == '__main__':
#     setup_logging()
#     logger = logging.getLogger(__name__)
#     params = get_run_parameters(CONFIG_DIR / 'config_arron.yaml')
#     scraper = LinkedInScraper()
#     scraper.run(params)
#     scraper.close()