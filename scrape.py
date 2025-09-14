from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_jobs_from_remoteok(keyword,location=""):
    # Clean up keyword for URL
    keyword = keyword.lower().strip().replace(" ", "-")
    url = f"https://remoteok.com/remote-{keyword}-jobs"

    # Set headless Chrome options for Streamlit
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    jobs = []

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.job'))
        )

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, 'tr.job')

        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, 'td.position h2').text
                company = card.find_element(By.CSS_SELECTOR, 'td.company h3').text
                link_element = card.find_element(By.CSS_SELECTOR, 'a.preventLink')
                full_link = link_element.get_attribute('href')
                try:
                    location = card.find_element(By.CSS_SELECTOR, 'div.location').text
                except:
                    location = "Remote"

                job_posting = f"{title} role at {company} in {location}."

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": full_link,
                    "location": location,
                    "job_posting": job_posting
                })
            except Exception:
                continue

    finally:
        driver.quit()

    return jobs
