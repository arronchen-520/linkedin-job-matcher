import os
from utils.file_path import EXTENSION_DIR, USER_DATA_DIR
from playwright.sync_api import sync_playwright
import tempfile
import shutil


user_data_dir = USER_DATA_DIR
extension_dir = EXTENSION_DIR

p = sync_playwright().start()

temp_dir = tempfile.mkdtemp()

context = p.chromium.launch_persistent_context(
        temp_dir,
        headless=False,  
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 
        viewport={"width": 1920, "height": 1280}, 
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            f"--disable-extensions-except={extension_dir}",
            f"--load-extension={extension_dir}",
            '--disable-dev-shm-usage'
        ]
    )

page = context.new_page()

page.goto('chrome-extension://mbgjopdedgonlbpikjfibkccpmhjbnag/options.html#/profile')

page.get_by_role('button', name= 'Import Profile').click()


page.get_by_role('button', name = 'Apply').click()

page.get_by_role('button', name = 'Autofill with Resume').click()

page.get_by_role('button', name = 'Sign In').last.click()

page.get_by_label('Email Address').fill('Arronchen520@gmail.com')

page.get_by_label('Password').fill('Pipiyu520,')

shutil.rmtree(temp_dir)