import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

# Regex pattern for basic email validation
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
TARGET_PAGES = ['contact', 'about', 'team', 'leadership']

def format_url(url):
    url = str(url).strip()
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def get_email_type(email):
    general_prefixes = ['contact', 'info', 'support', 'hello', 'sales', 'admin', 'careers']
    prefix = email.split('@')[0].lower()
    if prefix in general_prefixes:
        return "General"
    return "Personal"

def extract_emails_from_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = soup.get_text(separator=' ')
        found_emails = set(re.findall(EMAIL_REGEX, text))
        
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            full_url = urljoin(url, href)
            if urlparse(full_url).netloc == urlparse(url).netloc:
                links.append(full_url)
                
        return found_emails, set(links)
    except Exception as e:
        print(f"  [!] Could not access {url}")
        return set(), set()

def process_company(company_name, base_url):
    print(f"Scraping {company_name} at {base_url} ...")
    formatted_url = format_url(base_url)
    
    home_emails, internal_links = extract_emails_from_page(formatted_url)
    extracted_data = []
    
    def add_emails(emails, source_page):
        # Only add the VERY FIRST email we find
        for email in emails:
            if len(extracted_data) == 0:
                email = email.lower()
                extracted_data.append({
                    "company_name": company_name,
                    "website_url": base_url,
                    "email": email,
                    "email_type": get_email_type(email),
                    "source_page": source_page
                })
                break # Stop processing other emails on this page

    # 1. Check Homepage first
    add_emails(home_emails, "Home / Footer")
    
    # 2. If no email found on homepage, check sub-pages
    if len(extracted_data) == 0:
        pages_to_crawl = set()
        for link in internal_links:
            if any(keyword in link.lower() for keyword in TARGET_PAGES):
                pages_to_crawl.add(link)
                
        for page_url in pages_to_crawl:
            # If we already found an email on a previous sub-page, stop crawling!
            if len(extracted_data) > 0:
                break
                
            page_emails, _ = extract_emails_from_page(page_url)
            source_name = page_url.strip('/').split('/')[-1].title() + " Page"
            add_emails(page_emails, source_name)
        
    # 3. If STILL no emails were found, add the "Not Found" row
    if len(extracted_data) == 0:
        extracted_data.append({
            "company_name": company_name,
            "website_url": base_url,
            "email": "Not Found",
            "email_type": "N/A",
            "source_page": "N/A"
        })
        
    return extracted_data

def main():
    # Input file name
    input_file = 'Summer-Intern-Company-Data - Sheet1.csv'
    
    # NEW output file name so it creates a completely fresh CSV sheet
    output_file = 'Final_Output_1_Email_Per_Row.csv'

    try:
        input_df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: '{input_file}' not found. Please make sure it is in the same folder.")
        return

    all_results = []
    
    # Smart column detection (figures out which column is the URL automatically)
    col_0_val = str(input_df.iloc[0, 0]).lower()
    if 'http' in col_0_val or 'www' in col_0_val or '.com' in col_0_val:
        website_col = input_df.columns[0]
        company_col = input_df.columns[1]
    else:
        company_col = input_df.columns[0]
        website_col = input_df.columns[1]

    # Process each row
    for index, row in input_df.iterrows():
        company_name = row[company_col]
        website_url = row[website_col]
        
        if pd.notna(company_name) and pd.notna(website_url):
            company_data = process_company(company_name, website_url)
            all_results.extend(company_data)

    # Save to the new CSV file
    if all_results:
        output_df = pd.DataFrame(all_results)
        columns = ["company_name", "website_url", "email", "email_type", "source_page"]
        output_df = output_df[columns]
        
        output_df.to_csv(output_file, index=False)
        print(f"\nSuccess! The brand new CSV sheet has been created and saved as: {output_file}")
    else:
        print("\nNo data to process.")

if __name__ == "__main__":
    main()
