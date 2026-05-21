# Automated Business Email Scraper

![Python]
![Pandas]
![BeautifulSoup]
## 📖 Table of Contents
- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Usage Guide](#usage-guide)
- [Data Dictionary (Output)](#data-dictionary-output)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)

---

## 📝 Project Overview
This project is an automated Python web scraping tool developed as part of **Week 1 - Exploration** for my Summer Internship. 

The objective of this script is to ingest a CSV containing a list of target companies and their website URLs, actively crawl their web pages (including targeted sub-pages like Home, Contact, About, Team, and Leadership), and extract publicly available email addresses. The final output is a clean, structured CSV file mapping the extracted emails back to their respective companies, categorized by email type.

---

## 🛠️ Tech Stack
* **Language:** Python 3
* **Data Manipulation:** `pandas`
* **HTTP Requests:** `requests`
* **HTML Parsing:** `beautifulsoup4`
* **Pattern Matching:** `re` (Regular Expressions)
* **URL Parsing:** `urllib.parse`

---

## ✨ Key Features
1. **Targeted Web Crawling:** Automatically hunts for standard contact and about pages via internal links rather than only scanning the homepage.
2. **Regex Email Extraction:** Utilizes Regular Expressions to identify and securely pull email string formats out of raw HTML text.
3. **Smart Categorization:** Automatically flags extracted emails as `General` (e.g., info@, support@) or `Personal` (e.g., firstname.lastname@) based on the prefix.
4. **Resilient Data Parsing:** Features dynamic column detection to automatically identify which column contains the URL and which contains the Company Name, preventing runtime crashes.
5. **Data Completeness Guarantee:** If a website blocks the scraper or uses hidden forms, the script still logs the company with a "Not Found" status, ensuring the output row count perfectly mirrors the input sheet.

---

## 📂 Project Structure
```text
📁 Project Directory
 ├── 📄 scraper.py                              # The main Python extraction script
 ├── 📄 Summer-Intern-Company-Data - Sheet1.csv # Input data (List of companies & URLs)
 ├── 📄 New_Scraped_Emails.csv                  # Auto-generated output data
 └── 📄 README.md                               # Project documentation
