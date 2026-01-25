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
    Encapsulates the automation logic for scraping job postings from LinkedIn.
    Manages browser state, authentication, search parameters, and data extraction.
    """

    def __init__(self):
        """
        Initializes the scraper instance with default state containers.
        """
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.job_list: List[Dict] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def start_browser(self, headless: bool = False):
        """
        Initializes the Playwright engine and launches the browser instance.
        
        Args:
            headless (bool): If True, runs the browser without a visible UI.
        """
        self.logger.info("Initializing Playwright and launching browser...")
        try:
            self.playwright = sync_playwright().start()
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,  # Saved cookie and log-in
                channel="chrome", 
                headless=headless,    
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 
                viewport={"width": 1920, "height": 1280}, 
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            # self.context = self.browser.new_context(no_viewport=True)
            self.page = self.context.new_page()
            # stealth_sync(self.page)
            self.logger.info("Browser session started successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to launch browser: {e}")
            raise

    def sign_in(self):
        """
        Navigates to the login portal and authenticates the user.
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
        Executes a search query with the provided keywords.
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
        Applies radius filters to the search results.
        
        Args:
            distance (int): The search radius in kilometers (the value should be a multiple of 5).
        """
        distance = int(round(distance / 5) * 5) # Make sure the distance is a multiple of 5.
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
        Filters search results by the job posting date.
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
            self.logger.error(f"Failed to apply time filter: {e}")

    def scrape_available_jobs(self):
        """
        Iterates through pagination and collects job data from each page.
        """
        self.logger.info("Starting job scraping sequence...")
        exit_loop = False
        
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
                else:
                    self.logger.info('Navigating to next page...')
                    next_button.first.click()
            except Exception as e:
                self.logger.error(f"Unexpected error during pagination loop: {e}")
                exit_loop = True

    def _process_single_job(self, job_element: Locator, count: int):
        """
        Helper method to extract details from a single job element.
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
                    details = self.page.get_by_text('About the job').locator('..').locator('..')
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
        Persists collected job data to a CSV file.
        Args:
            filepath (Path): Full path not including file name.
            search (Dict): Search parameters.
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
        Filters collected jobs based on company eligibility and salary information.
        
        Keeps jobs that match either of these criteria:
        - Company is in the provided company_list
        - Job posting includes salary information

        - And whether or not the job is reposted based on the user config.
        
        Args:
            filepath (str): Full path where filtered results will be saved (e.g., /app/data/filtered_jobs.csv)
            params (dict): Config parameters
        
        Returns:
            pd.DataFrame: Filtered job data as a pandas DataFrame

        """
        df = pd.DataFrame(self.job_list)
        company_list = params['company_list']
        user = params['user_name']

        if company_list == []:
            self.logger.info(f"No company list provided. No filter was applied to the output. ")
        else:
            df = df.loc[((df['Company'].isin(company_list)) | (df['Salary'] != '')) & (df['Reposted'] == params['repost'])]
        current_date = datetime.now().strftime("%Y%m%d")
        search = params['search']
        filepath = Path(filepath / f"{current_date}_{user}_{search['keyword']}_{search['city']}_{search['period']}_filtered.csv")
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        self.logger.info(f"Filtered {len(df)} eligible jobs and saved to {filepath}")
    
    def run(self, params):
        try:
            search = params['search']
            self.logger.info(f"Starting task for [{params['user_name']}]: {search['keyword']} in {search['city']}")
            self.start_browser(headless=params['headless'])
            self.sign_in()
            self.search_jobs(search['keyword'], search['city'])
            self.filter_period(search['period'])
            self.set_distance(search['distance'])
            self.scrape_available_jobs()
            self.save_to_csv(COMPLETE_FILE_PATH, search)
            self.filter_eligible_jobs(FILTERED_FILE_PATH, params)
            self.logger.info("Task completed successfully.")
        except KeyboardInterrupt:
            self.logger.warning("Process interrupted by user.")
        except Exception as e:
            self.logger.critical(f"Unexpected error: {e}", exc_info=True)

    def close(self):
        """
        Gracefully terminates the browser session.
        """
        self.logger.info("Closing browser resources.")
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

if __name__ == '__main__':
    setup_logging()
    logger = logging.getLogger(__name__)
    params = get_run_parameters(CONFIG_DIR / 'config_arron.yaml')
    scraper = LinkedInScraper()
    scraper.run(params)
    scraper.close()