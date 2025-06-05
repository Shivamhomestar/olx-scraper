import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def random_sleep(a, b):
    time.sleep(random.uniform(a, b))

def extract_phone_numbers(text):
    # Regex for Indian phone numbers (adjust as needed)
    return re.findall(r'\b[789]\d{9}\b', text)

def scrape_olx(keyword, city='mumbai', max_results=20):
    leads = []
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    base_url = f'https://www.olx.in/{city}/q-{keyword.replace(" ", "-")}/'
    driver.get(base_url)
    random_sleep(3, 5)

    # Scroll to load more if necessary
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_sleep(2, 4)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # DEBUG: print all li classes to update selector if needed
    # print([tag['class'] for tag in soup.find_all('li') if tag.has_attr('class')])

    listings = soup.find_all('li', class_='EIR5N')[:max_results]
    for listing in listings:
        try:
            title_tag = listing.find('span')
            title = title_tag.text.strip() if title_tag else "No Title"
            link_tag = listing.find('a', href=True)
            detail_url = urljoin(base_url, link_tag['href']) if link_tag else None

            phone = "Not Found"
            name = "Unknown"

            if detail_url:
                driver.get(detail_url)
                random_sleep(3, 5)
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

                text = detail_soup.get_text(separator=' ', strip=True)
                phones_found = extract_phone_numbers(text)
                if phones_found:
                    phone = phones_found[0]

                # Try to find seller name
                name_tag = detail_soup.find('h4') or detail_soup.find('h3')
                if name_tag and name_tag.text.strip():
                    name = name_tag.text.strip()
                else:
                    possible_names = detail_soup.find_all(string=re.compile(r'Seller|Posted by', re.I))
                    if possible_names:
                        sibling = possible_names[0].find_next()
                        if sibling and hasattr(sibling, 'text') and sibling.text.strip():
                            name = sibling.text.strip()

            leads.append({
                'Name': name,
                'Phone': phone,
                'Title': title,
                'Source': 'OLX'
            })
        except Exception as e:
            print(f"Error processing a listing: {e}")
            continue

    driver.quit()
    return leads