import os
import re
import json
import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

"""
URL and file for saving output
"""
url = "https://ura.go.ug/"
json_export = 'data/ura_faqs.json'

log_directory = 'logs'
log_file = 'faq_scraper.log'
os.makedirs(log_directory, exist_ok=True)

"""
Logger setup
"""
logging.basicConfig(
    filename="logs/faq_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()

"""
Webdriver initializer
"""
def init_webdriver(headless=True):
    """
    Initialize the Selenium WebDriver with optional headless mode.
    """
    print("Initializing WebDriver.")
    options = Options()
    if headless:
        options.add_argument('--headless') 
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')  
        options.add_argument('--remote-debugging-port=9222')  
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--window-size=1920,1080')  
        options.add_argument('--disable-setuid-sandbox')
    try:
        service = Service(verbose=True)
        driver = webdriver.Chrome(service=service, options=options)
        print("WebDriver initialized successfully.")
        logger.info("WebDriver initialized successfully.")
        return driver
    except WebDriverException as e:
        print(f"Failed to initialize WebDriver: {e}")
        logger.error(f"Failed to initialize WebDriver: {e}")
        return None
    
def clean_section_name(section_name):
    """
    Remove unwanted characters and whitespaces
    """
    cleaned_name = re.sub(r"[«»]", "", section_name).strip()
    cleaned_name = re.sub(r"\s+", " ", cleaned_name)
    return cleaned_name

def click_faq_dropdown(driver):
    """
    FAQ dropdown button manipulator
    """
    try:
        print(f"Opening URL: {url}")
        logger.info(f"Opening URL: {url}")
        
        driver.get(url)

        wait = WebDriverWait(driver, 10)

        # Wait for FAQ button to be clickable
        faq_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'dropdown-toggle') and contains(., 'FAQs')]"))
        )
        
        print("Clicking FAQ dropdown button.")
        logger.info("Clicking FAQ dropdown button.")
        
        faq_button.click()

        # dropdown menu is visible
        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".faqs-global-sec-menu-items"))
        )
        
        print("FAQ dropdown displayed successfully.")
        logger.info("FAQ dropdown displayed successfully.")

    except Exception as e:
        print(f"Failed to click FAQ dropdown: {e}")
        logger.error(f"Failed to click FAQ dropdown: {e}")
        raise

def extract_faq_links(driver):
    """
    Extract FAQ links
    """
    
    try:
        print("Extracting FAQ section links from the dropdown.")
        logger.info("Extracting FAQ section links from the dropdown.")
        
        dropdown_menu = driver.find_element(By.CSS_SELECTOR, ".faqs-global-sec-menu-items")
        faq_items = dropdown_menu.find_elements(By.XPATH, "./li")

        # Extract links and section names
        faq_urls = []
        for item in faq_items:
            try:
                link = item.find_element(By.TAG_NAME, 'a')
                raw_section_name = link.text.strip()
                section_url = link.get_attribute('href')

                if link.get_attribute('data-bs-toggle') == 'dropdown':
                    parent_section_name = clean_section_name(raw_section_name)
                    print(f"Found parent section: '{parent_section_name}' with URL: {section_url}")
                    logger.info(f"Found parent section: '{parent_section_name}' with URL: {section_url}")

                    # Find the nested submenu
                    try:
                        submenu = item.find_element(By.CSS_SELECTOR, "ul.submenu")
                        submenu_links = submenu.find_elements(By.TAG_NAME, 'a')
                        for submenu_link in submenu_links:
                            submenu_section_name = parent_section_name
                            submenu_url = submenu_link.get_attribute('href')
                            faq_urls.append({"url": submenu_url, "section": submenu_section_name})
                            print(f"Found subsection: '{submenu_section_name}' with URL: {submenu_url}")
                            logger.info(f"Found subsection: '{submenu_section_name}' with URL: {submenu_url}")

                    except Exception as e:
                        print(f"No submenu found for parent section: '{parent_section_name}' - {e}")
                        logger.warning(f"No submenu found for parent section: '{parent_section_name}' - {e}")
                else:
                    # It's an actual FAQ link
                    cleaned_section_name = clean_section_name(raw_section_name)

                    if cleaned_section_name:  
                        faq_urls.append({"url": section_url, "section": cleaned_section_name})
                        print(f"Found section: '{cleaned_section_name}' with URL: {section_url}")
                        logger.info(f"Found section: '{cleaned_section_name}' with URL: {section_url}")
                    else:
                        print(f"Found section link with empty name - URL: {section_url}")
                        logger.warning(f"Found section link with empty name - URL: {section_url}")
            except Exception as e:
                print(f"Failed to process a dropdown item - {e}")
                logger.warning(f"Failed to process a dropdown item - {e}")

        print(f"Total FAQ sections found: {len(faq_urls)}")
        logger.info(f"Total FAQ sections found: {len(faq_urls)}")

        return faq_urls

    except Exception as e:
        print(f"Failed to extract FAQ links: {e}")
        raise


def extract_faqs_from_page(driver, page_url, section_name):
    """
    Extract FAQs from a single page
    """
    try:
        print(f"Extracting FAQs from section: {section_name} - URL: {page_url}")
        logger.info(f"Extracting FAQs from section: {section_name} - URL: {page_url}")

        driver.get(page_url)

        wait = WebDriverWait(driver, 10)
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'accordion-header'))
        )
        
        time.sleep(3)

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        faqs = []
        headings = soup.find_all('h2', {'class': 'accordion-header'})

        for heading in headings:
            if 'flush' in heading.get('id',''):
                question = heading.find('button', class_='accordion-button').get_text(strip=True)

                question_cleaned = re.sub(r"^\d+\.?\s*", "", question)
                
                collapse_id = heading.find('button')['data-bs-target'].replace('#', '')
                answer_div = soup.find('div', {'id': collapse_id})

                if answer_div:
                    answer = answer_div.find('div', class_='accordion-body').get_text(strip=True)
                    faqs.append({"question": question_cleaned, "answer": answer, "section": section_name})
                    print(f"Extracted FAQ - Question: {question_cleaned}, Section: {section_name}")
                    logger.info(f"Extracted FAQ - Question: {question_cleaned}, Section: {section_name}")

        print(f"Extracted {len(faqs)} FAQs from section: {section_name}")
        logger.info(f"Extracted {len(faqs)} FAQs from section: {section_name}")
        
        return faqs

    except Exception as e:
        print(f"Failed to extract FAQs from {page_url}: {e}")
        logger.error(f"Failed to extract FAQs from {page_url}: {e}")
        raise

def save_faqs_to_json(faqs, filename=json_export):
    """
    Save the extracted FAQs to a JSON file
    """
    try:
        print(f"Saving {len(faqs)} FAQs to JSON file: {filename}")
        with open(filename, 'w') as file:
            json.dump(faqs, file, indent=4)
        print(f"FAQs successfully saved to {filename}")
    except Exception as e:
        print(f"Failed to save FAQs to JSON: {e}")
        raise

if __name__ == "__main__": 

    print("Starting FAQ scraping process.")
    logger.info("Starting FAQ scraping process.")

    driver=None

    try:
        driver = init_webdriver(headless=True)

        if driver is None:
            logger.error("WebDriver initialization failed. Exiting scraping process.")
            exit(1)

        # Print chrome and ChromeDriver versions for verification
        chrome_version = driver.capabilities['browserVersion']
        chromedriver_version = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
        print(f"Using Chrome version: {chrome_version}")
        print(f"Using ChromeDriver version: {chromedriver_version}")
        logger.info(f"Using Chrome version: {chrome_version}")
        logger.info(f"Using ChromeDriver version: {chromedriver_version}")
            
        click_faq_dropdown(driver)        
        faq_urls = extract_faq_links(driver)        
        print(f"Collected {len(faq_urls)} FAQ URLs.")
        logger.info(f"Collected {len(faq_urls)} FAQ URLs.")

        all_faqs = []

        for page in faq_urls:
            faqs = extract_faqs_from_page(driver, page["url"], page["section"])
            all_faqs.extend(faqs)

        save_faqs_to_json(all_faqs)

    except Exception as e:
        print(f"Error during FAQ scraping: {e}")
        logger.error(f"Error during FAQ scraping: {e}")

    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")
            logger.info("WebDriver closed.")
        else:
            print("WebDriver was not initialized; skipping quit.")
            logger.warning("WebDriver was not initialized; skipping quit.")

