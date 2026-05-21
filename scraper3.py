import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import urllib3

# Strict Email Regex (Avoids grabbing random image files like .png or .webp)
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
TARGET_PAGES = ['contact', 'about', 'team', 'leadership', 'support']

# Blacklist dummy emails and background tech platforms
IGNORE_DOMAINS = ['wix.com', 'shopify.com', 'squarespace.com', 'sentry.io', 'example.com', 'morphcopy.com']

def format_url(url):
    url = str(url).strip()
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def get_email_type(email):
    general_prefixes = ['contact', 'info', 'support', 'hello', 'sales', 'admin', 'careers', 'help', 'questions']
    prefix = email.split('@')[0].lower()
    if prefix in general_prefixes:
        return "General"
    return "Personal"

def extract_emails_from_page(url):
    try:
        # Advanced Chrome headers to bypass basic bot protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        
        # Strict 10-second timeout to avoid hanging on dead URLs
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        found_emails = set()
        
        # Scan raw response.text to catch emails hidden inside JS/React variables
        raw_matches = re.findall(EMAIL_REGEX, response.text)
        for match in raw_matches:
            email_clean = match.lower().strip()
            # Exclude obvious non-emails grabbed by regex (like image files)
            if not email_clean.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                found_emails.add(email_clean)
            
        # Extract hidden "mailto:" links properly
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            
            # Check for mailto
            if href.lower().startswith('mailto:'):
                email = href[7:].split('?')[0].strip().lower() # remove ?subject= if present
                if re.match(EMAIL_REGEX, email):
                    found_emails.add(email)
                    
            # Collect internal links for sub-page crawling
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
    
    # Extract base domain to compare against emails
    parsed_domain = urlparse(formatted_url).netloc.lower()
    base_domain = parsed_domain.replace('www.', '')
    
    home_emails, internal_links = extract_emails_from_page(formatted_url)
    collected_emails = []
    
    # Strict Domain Ranking System
    def rank_email(email):
        domain = email.split('@')[-1]
        if domain in IGNORE_DOMAINS:
            return 99 # Blacklisted, completely ignore
        if base_domain in domain or domain in base_domain:
            return 1 # Perfect match (e.g. @company.com)
        if domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'mac.com', 'me.com']:
            return 2 # Acceptable small business fallback
        return 3 # Different domain entirely, lowest priority
        
    def process_found(emails, source):
        for e in emails:
            r = rank_email(e)
            if r < 99:
                collected_emails.append({
                    "company_name": company_name,
                    "website_url": base_url,
                    "email": e,
                    "email_type": get_email_type(e),
                    "source_page": source,
                    "rank": r
                })

    # 1. Check Homepage
    process_found(home_emails, "Home / Footer")
    
    # 2. If we didn't find a Perfect Match (Rank 1), check the sub-pages
    if not any(d['rank'] == 1 for d in collected_emails):
        pages_to_crawl = set()
        for link in internal_links:
            if any(keyword in link.lower() for keyword in TARGET_PAGES):
                pages_to_crawl.add(link)
                
        for page_url in pages_to_crawl:
            page_emails, _ = extract_emails_from_page(page_url)
            source_name = page_url.strip('/').split('/')[-1].title() + " Page"
            process_found(page_emails, source_name)
            
            # Stop crawling pages early if we find a perfect match
            if any(d['rank'] == 1 for d in collected_emails):
                break
                
    # 3. Sort by rank and return ONLY the single best email
    if collected_emails:
        collected_emails.sort(key=lambda x: x['rank'])
        best_email_dict = collected_emails[0]
        del best_email_dict['rank'] # remove the rank key before saving to CSV
        return [best_email_dict]
        
    # 4. If absolutely nothing was found
    return [{
        "company_name": company_name,
        "website_url": base_url,
        "email": "Email_not_found",
        "email_type": "N/A",
        "source_page": "N/A"
    }]

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Suppress SSL warnings

    input_file = 'Summer-Intern-Company-Data - Sheet1.csv'
    
    # --- AUTOMATICALLY CREATE A BRAND NEW CSV FILE EVERY RUN ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'Scraped_Emails_{timestamp}.csv'
    # -----------------------------------------------------------

    try:
        input_df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: '{input_file}' not found. Please ensure it is in the same folder.")
        return

    # Smart column detection
    col_0_val = str(input_df.iloc[0, 0]).lower()
    if 'http' in col_0_val or 'www' in col_0_val or '.com' in col_0_val:
        website_col = input_df.columns[0]
        company_col = input_df.columns[1]
    else:
        company_col = input_df.columns[0]
        website_col = input_df.columns[1]

    # Remove Duplicates automatically
    initial_count = len(input_df)
    input_df = input_df.drop_duplicates(subset=[website_col])
    new_count = len(input_df)
    if initial_count > new_count:
        print(f"\n[INFO] Removed {initial_count - new_count} duplicate URLs from the input file!\n")

    all_results = []
    for index, row in input_df.iterrows():
        company_name = row[company_col]
        website_url = row[website_col]
        
        if pd.notna(company_name) and pd.notna(website_url):
            company_data = process_company(company_name, website_url)
            all_results.extend(company_data)

    if all_results:
        output_df = pd.DataFrame(all_results)
        columns = ["company_name", "website_url", "email", "email_type", "source_page"]
        output_df = output_df[columns]
        
        # Save to the brand new unique CSV file
        output_df.to_csv(output_file, index=False)
        print(f"\nSuccess! Your data has been saved to a brand new CSV file: {output_file}")
    else:
        print("\nNo data to process.")

if __name__ == "__main__":
    main()