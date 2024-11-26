import urllib.parse

def convert_query_to_bioproject_link(query):
    base_url = "https://www.ncbi.nlm.nih.gov/bioproject/?term="
    encoded_query = urllib.parse.quote(query)
    return f"{base_url}{encoded_query}"

# Example usage
query = 'Dengue[All Fields] AND ("method sequencing"[Filter] AND "org human"[Filter])'
bio_project_link = convert_query_to_bioproject_link(query)

print("Generated BioProject Link:", bio_project_link)





import csv  # Import CSV module to write data to file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re  # Import the regex module to clean GEO ID

# Set up Chrome options (optional, for headless mode or other settings)
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment to run in headless mode

# Path to the ChromeDriver
driver_path = "/Users/kushalsinghnareda/Downloads/chromedriver-mac-arm642/chromedriver"  # Make sure this path is correct

# Define base URL globally so it can be accessed after restarting the browser


def start_driver():
    # Initialize ChromeDriver using the Service class
    service = Service(driver_path)
    return webdriver.Chrome(service=service, options=chrome_options)

# Function to extract Accession ID, Description, and GEO ID from a BioProject page
def extract_accession_description_and_geo(driver):
    # Use BeautifulSoup to parse the page source
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find the Accession ID in the 'CTcontent' class
    accession_tag = soup.find('td', class_='CTcontent')
    accession_id = accession_tag.get_text(strip=True) if accession_tag else "No Accession ID found"

    # Find the Description in the 'DescrAll' div (hidden content)
    description_tag = soup.find('div', {'id': 'DescrAll'})
    description = description_tag.get_text(strip=True) if description_tag else "No description available"

    # Check if there is a GEO ID in the Accession ID (if 'GEO:' is found)
    geo_id = None
    if "GEO:" in accession_id:
        # Extract GEO ID (removing any 'GEO:', ':', or ';')
        geo_id = re.search(r'GEO:\s*(GSE\d+)', accession_id)
        if geo_id:
            geo_id = geo_id.group(1)  # Extract the GEO ID (e.g., GSE253542)
        # Clean the Accession ID (remove GEO ID and any extra semicolons or colons)
        accession_id = re.sub(r'GEO:\s*GSE\d+;?', '', accession_id).strip()

    return accession_id, description, geo_id

# Function to scrape all BioProject entries on the current page
def scrape_bioprojects(driver, writer):
    while True:
        try:
            # Wait until the BioProject search results are visible
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.title a"))
            )

            # Find all BioProject links on the current page
            project_links = driver.find_elements(By.CSS_SELECTOR, "p.title a")

            # Loop over each BioProject link on the current page
            for index in range(len(project_links)):
                # Refresh the list of project links after coming back to the main page
                project_links = driver.find_elements(By.CSS_SELECTOR, "p.title a")

                # Get the project title and click on the project link
                project_title = project_links[index].text
                print(f"Scraping BioProject {index + 1}: {project_title}")

                # Click on the link to go to the BioProject page
                project_links[index].click()

                # Add a static delay (increase the wait time as needed)
                time.sleep(5)

                # Wait for the BioProject page to load (look for either the description or accession id)
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div#Descrread, td.CTcontent"))
                    )
                except TimeoutException:
                    print(f"Timeout on BioProject {index + 1}: {project_title}. Skipping...\n")
                    driver.back()
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "p.title a"))
                    )
                    continue

                # Extract Accession ID, Description, and GEO ID
                accession_id, description, geo_id = extract_accession_description_and_geo(driver)
                print(f"Accession ID: {accession_id}")
                print(f"Description: {description}")
                print(f"GEO ID: {geo_id if geo_id else 'No GEO ID'}\n")

                # Write the extracted data (Title, Accession ID, Description, GEO) to the CSV file
                writer.writerow([project_title, accession_id, description, geo_id if geo_id else ""])  # GEO included in the row

                # Navigate back to the main search results page
                driver.back()

                # Add a short delay before trying to interact with the main page again
                time.sleep(2)

                # Wait until the search results are visible again before continuing with the next result
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "p.title a"))
                )

            # Check if there's a "Next" button to go to the next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a.active.page_link.next")
                print("Navigating to the next page...")
                next_button.click()

                # Add a short delay after navigating to the next page
                time.sleep(3)

            except:
                # If no "Next" button is found, exit the loop
                print("No more pages. Scraping complete.")
                break
        except Exception as e:
            print(f"Error: {e}. Restarting the browser.")
            driver.quit()
            driver = start_driver()
            driver.get(bio_project_link)

# Main function to run the scraping process
if __name__ == "__main__":
    # Start the driver
    driver = start_driver()

    # Open the CSV file
    with open('bioproject_data_all_pages.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the headers (columns) for the CSV
        writer.writerow(['Title', 'Accession ID', 'Description', 'GEO'])  # Added 'GEO' column

        # Start the scraping process
        scrape_bioprojects(driver, writer)

    # Close the browser after scraping
    driver.quit()
