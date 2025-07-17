from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_page_text(url):
    """
    Scrape entire page text and divide into lines
    """
    driver = setup_driver()
    
    try:
        print(f"Scraping: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Get all page text
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # Split into lines
        lines = page_text.split('\n')
        
        print(f"Found {len(lines)} lines")
        print("="*50)
        
        # Print each line with line number
        for i, line in enumerate(lines):
            line = line.strip()
            if line:  # Only print non-empty lines
                print(f"{i:3d}: {line}")
        
        return lines
        
    except Exception as e:
        print(f"Error: {e}")
        return []
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test URL - replace with any VLR match URL
    url = "https://www.vlr.gg/487992/apeks-vs-giantx-esports-world-cup-2025-lr1"
    
    lines = scrape_page_text(url)
    
    # Optional: Save to file
    with open('page_text.txt', 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines):
            if line.strip():
                f.write(f"{i:3d}: {line.strip()}\n")