from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class BrowserFetcher:
    headless: bool = True
    page_wait_sec: int = 5

    def _build_driver(self) -> webdriver.Chrome:
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--window-size=1280,1000")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        return driver

    def fetch_after_click(self, url: str, click_xpath: str) -> str:
        driver = self._build_driver()
        try:
            driver.get(url)
            # wait for presence and click
            WebDriverWait(driver, self.page_wait_sec).until(
                EC.element_to_be_clickable((By.XPATH, click_xpath))
            ).click()
            # wait for navigation/content change
            WebDriverWait(driver, self.page_wait_sec).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            html = driver.page_source
            return html
        finally:
            driver.quit()

