from playwright.sync_api import sync_playwright
import pandas as pd

playwright = sync_playwright().start()
browser = playwright.chromium.launch(
    headless=False, args = ['--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
)
context = browser.new_context(no_viewport=True)
page = context.new_page()
# page.set_viewport_size({"width": 1920, "height": 1080})
page.goto('https://www.linkedin.com/jobs/')

# Sign in
if page.get_by_role('button', name = 'Sign in').is_visible():
    email = page.get_by_label('Email or phone')
    email.fill('1300218673@qq.com')
    password = page.get_by_label('Password').first
    password.fill('Arronchen0401')
    signin = page.get_by_role('button', name = 'Sign in')
    signin.click()

# Search job
keywords = 'Machine Learning'
search = page.get_by_placeholder('Describe the job you want')
search.fill(keywords)
search.press('Enter')

# City and distance
city = 'Toronto, Ontario, Canada'
distance = 10 # km
page.locator("svg#location-marker-small").click()
location_box = page.locator("div[role='textbox']")
location_box.fill(city)

page.locator("svg#edit-small").click()
distance_box = page.locator("input[aria-label*='Slider']")
distance_box.focus()
count_left = int(round((80 - distance)/5,0))
for _ in range(count_left): 
    distance_box.press("ArrowLeft")
page.get_by_role('button', name = 'Show results').click()

# Input period
period = 'Past 24 hours'
if period not in ['Past 24 hours', 'Past week', 'Past month']:
    print("Please enter a valid period ('Past 24 hours', 'Past week', 'Past month').")
period_box = page.get_by_label('Date posted').locator('..')
period_box.click()
page.get_by_role('radio', name = period).click() 
page.get_by_role('button', name = 'Show results').click()

exit = False
job_list = []
while not exit:
    page.locator('div[componentkey = "SearchResultsMainContent"]').wait_for()
    print('Start processing the current page...')
    # Scrape job
    jobs = page.locator('div[componentkey = "SearchResultsMainContent"] div[role = "button"]')
    jobs = jobs.all()[:-3] # Remove the last three structure elements
    c = 1

    for job in jobs:
        print(f'Start processing the {c}th job')
        job.scroll_into_view_if_needed()
        try:
            job_text = job.inner_text() # Pull job summary
        except:
            print(f"Failed to retrieve the {c}th job posting.")
            continue
        job_text = job_text.split('\n\n') # Split different sections
        job_title = job_text[0].split('\n')[-1] # Job title
        company = job_text[1] # Company name
        location = job_text[2] # Job location
        posted_time = ', '.join([i for i in job_text if 'ago' in i or 'just posted' in i.lower()])# Posted time
        try:
            job.click() # Click to load job description
            try:
                job_description = page.locator('div[componentkey*="JobDetails"]').nth(1).inner_text() # Job description
                job_description = '\n'.join([line for line in job_description.split('\n') if line.strip()]) # Remove multple \n
                salary = ', '.join([i.strip() for i in job_description.split('\n') if '$' in i]) # Salary information (first seperated by \n)
                if '. ' in salary:
                    salary = ', '.join([i.strip() for i in job_description.split('. ') if '$' in i]) # Salary information (second sepeated by comma)
            except:
                print(f"Error extracting the {c}th job description. ")
                job_description = ''
                salary = ''
            try:
                url = page.locator("a[data-view-name = 'job-apply-button']").get_attribute('href') # Apply URL
            except:
                url = ''
        except:
            print(f"Error extracting the {c}th job description. ")
        new_row = {
            'Job Title': job_title,
            'Company': company,
            'Location': location,
            'Posted Time': posted_time,
            'Salary': salary,
            'URL': url,
            'Job Description': job_description}
        print(f"Appending the {c}th job. ")
        job_list.append(new_row)
        c+=1
    # next_page = page.get_by_role('button', name = 'Next')
    next_page = page.locator("button[data-testid *= 'pagination-controls-next-button-visible']")
    if next_page.count() == 0:
        print('No next page button found. Ending the process...')
        exit = True
    else:
        print('Clicking next page...')
        next_page.first.click()
        print('Next page...')
jobs_df = pd.DataFrame(job_list)
try:
    jobs_df.to_csv('./data/job_posts/linkedin_jobs.csv', index = False)
except:
    jobs_df.to_csv('linkedin_jobs.csv', index = False)

browser.close()
playwright.stop()