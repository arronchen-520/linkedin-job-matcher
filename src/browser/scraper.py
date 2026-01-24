import os
import time
import logging
import pandas as pd
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext, Locator

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
        # self._is_active = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def start(self, headless: bool = False):
        """
        Initializes the Playwright engine and launches the browser instance.
        
        Args:
            headless (bool): If True, runs the browser without a visible UI.
        """
        self.logger.info("Initializing Playwright and launching browser...")
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=headless, 
                args=['--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            )
            self.context = self.browser.new_context(no_viewport=True)
            self.page = self.context.new_page()
            # self._is_active = True
            self.logger.info("Browser session started successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to launch browser: {e}")
            raise

    def sign_in(self, email: str, password: str):
        """
        Navigates to the login portal and authenticates the user.
        """
        self.logger.info("Navigating to LinkedIn job search page...")
        try:
            self.page.goto('https://www.linkedin.com/jobs/')
            
            # Check for sign-in button visibility
            if self.page.get_by_role('button', name='Sign in').is_visible():
                self.logger.info("Sign-in button detected. Attempting authentication...")
                
                self.page.get_by_label('Email or phone').fill(email)
                self.page.get_by_label('Password').first.fill(password)
                self.page.get_by_role('button', name='Sign in').click()
                
                self.logger.info("Credentials submitted.")
            else:
                self.logger.info("Sign-in button not found. User may already be logged in.")
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise

    def search_jobs(self, keywords: str):
        """
        Executes a search query with the provided keywords.
        """
        self.logger.info(f"Executing search for keywords: '{keywords}'")
        try:
            search_box = self.page.get_by_placeholder('Describe the job you want')
            search_box.fill(keywords)
            search_box.press('Enter')
        except Exception as e:
            self.logger.error(f"Search execution failed: {e}")

    def set_location_and_distance(self, city: str, distance: int):
        """
        Applies location and radius filters to the search results.
        
        Args:
            city (str): The target city string.
            distance (int): The search radius in kilometers (the value should be a multiple of 5).
        """
        self.logger.info(f"Setting location filter: {city} (Radius: {distance}km)")
        try:
            # Set City
            self.page.locator("svg#location-marker-small").click()
            self.page.locator("div[role='textbox']").fill(city)

            # Set Distance via slider manipulation
            self.page.locator("svg#edit-small").click()
            distance_box = self.page.locator("input[aria-label*='Slider']")
            distance_box.focus()
            
            # Calculate key presses needed
            steps = int(round((80 - distance) / 5, 0))
            for _ in range(steps): 
                distance_box.press("ArrowLeft")
                time.sleep(0.1)
                
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
            self.logger.warning(f"Invalid period '{period}'. Skipping filter. Valid options: {valid_periods}")
            return

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
            job_text_raw = job_element.inner_text()
        except Exception as e:
            self.logger.warning(f"Failed to read text for job #{count}: {e}")
            return

        # Basic Parsing
        try:
            parts = job_text_raw.split('\n\n') # Might consider updating to locator
            job_title = parts[0].split('\n')[-1]
            company = parts[1]
            location = parts[2]
            posted_time = ', '.join([t for t in parts if 'ago' in t or 'just posted' in t.lower()])
        except IndexError:
            self.logger.warning(f"Job #{count} has an unexpected text structure. Skipping.")
            return

        # Detail Extraction
        job_description = ''
        salary = ''
        url = ''
        
        try:
            job_element.click()
            
            # Extract description/salary
            try:
                self.page.locator('div[componentkey*="JobDetails"]').wait_for()
                details = self.page.locator('div[componentkey*="JobDetails"]').nth(1)
                desc_text = details.inner_text()
                job_description = '\n'.join([line for line in desc_text.split('\n') if line.strip()])
                
                # Salary extraction logic
                salary_lines = [line.strip() for line in job_description.split('\n') if '$' in line]
                salary = ', '.join(salary_lines)
                if '. ' in salary_lines:
                    salary = ', '.join([i.strip() for i in salary_lines.split('. ') if '$' in i])
            except Exception:
                self.logger.debug(f"Could not extract description details for job #{count}.")

            # Extract URL
            try:
                url = self.page.locator("a[data-view-name = 'job-apply-button']").get_attribute('href')
            except Exception:
                pass

        except Exception as e:
            self.logger.warning(f"Interaction failed for job #{count}: {e}")
            return

        # Store Data
        self.job_list.append({
            'Job Title': job_title,
            'Company': company,
            'Location': location,
            'Posted Time': posted_time,
            'Salary': salary,
            'URL': url,
            'Job Description': job_description
        })
        self.logger.info(f"Successfully scraped: {job_title} at {company}")

    def save_to_csv(self, filepath: str):  # 把 filename 改成 filepath
        """
        Persists collected job data to a CSV file.
        Args:
            filepath (str): Full path including filename (e.g., /app/data/jobs.csv)
        """
        if not self.job_list:
            self.logger.warning("No jobs were collected. Skipping CSV generation.")
            return

        self.logger.info(f"Saving {len(self.job_list)} jobs to {filepath}...")
        
        try:
            pd.DataFrame(self.job_list).to_csv(filepath, index=False)
            self.logger.info("File saved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to save CSV to {filepath}: {e}")

    def close(self):
        """
        Gracefully terminates the browser session.
        """
        self.logger.info("Closing browser resources.")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()