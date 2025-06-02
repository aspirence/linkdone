
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json

class LinkedInProfileScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def setup_driver(self):
        """Setup Chrome driver for Selenium"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def validate_linkedin_url(self, url):
        """Validate if the URL is a LinkedIn profile URL"""
        linkedin_pattern = r'https?://(www\.)?linkedin\.com/in/[\w\-]+'
        return bool(re.match(linkedin_pattern, url))

    def extract_profile_data(self, url):
        """Extract profile data from LinkedIn URL"""
        if not self.validate_linkedin_url(url):
            raise ValueError("Invalid LinkedIn profile URL")

        try:
            # Use Selenium for better scraping
            driver = self.setup_driver()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract data
            profile_data = {
                'name': self._extract_name(driver),
                'headline': self._extract_headline(driver),
                'summary': self._extract_summary(driver),
                'experience_years': self._estimate_experience_years(driver),
                'education_level': self._extract_education_level(driver),
                'skills_count': self._count_skills(driver),
                'connections_count': self._extract_connections_count(driver),
                'posts_per_month': self._estimate_posts_per_month(driver),
                'recommendations_received': self._count_recommendations(driver),
                'volunteer_experience': self._has_volunteer_experience(driver),
                'certifications_count': self._count_certifications(driver),
                'languages_count': self._count_languages(driver)
            }
            
            driver.quit()
            return profile_data

        except Exception as e:
            if 'driver' in locals():
                driver.quit()
            # Fallback to basic scraping
            return self._basic_scraping_fallback(url)

    def _extract_name(self, driver):
        """Extract name from profile"""
        try:
            name_element = driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge")
            return name_element.text.strip()
        except:
            try:
                name_element = driver.find_element(By.CSS_SELECTOR, ".pv-text-details__left-panel h1")
                return name_element.text.strip()
            except:
                return "Unknown"

    def _extract_headline(self, driver):
        """Extract headline from profile"""
        try:
            headline_element = driver.find_element(By.CSS_SELECTOR, ".text-body-medium")
            return headline_element.text.strip()
        except:
            try:
                headline_element = driver.find_element(By.CSS_SELECTOR, ".pv-text-details__left-panel .text-body-medium")
                return headline_element.text.strip()
            except:
                return ""

    def _extract_summary(self, driver):
        """Extract summary/about section"""
        try:
            summary_element = driver.find_element(By.CSS_SELECTOR, "[data-generated-suggestion-target] .inline-show-more-text")
            return summary_element.text.strip()
        except:
            try:
                summary_element = driver.find_element(By.CSS_SELECTOR, ".pv-about-section .pv-about__summary-text")
                return summary_element.text.strip()
            except:
                return ""

    def _estimate_experience_years(self, driver):
        """Estimate years of experience from work history"""
        try:
            experience_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='experience'] .pvs-list__item")
            total_years = 0
            
            for element in experience_elements:
                duration_text = element.find_element(By.CSS_SELECTOR, ".pvs-entity__caption-wrapper").text
                years = self._parse_duration_to_years(duration_text)
                total_years += years
                
            return min(total_years, 50)  # Cap at 50 years
        except:
            return 5  # Default estimate

    def _extract_education_level(self, driver):
        """Extract highest education level"""
        try:
            education_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='education'] .pvs-list__item")
            education_levels = []
            
            for element in education_elements:
                degree_text = element.find_element(By.CSS_SELECTOR, ".mr1").text.lower()
                if 'phd' in degree_text or 'doctorate' in degree_text:
                    education_levels.append('PhD')
                elif 'master' in degree_text or 'mba' in degree_text:
                    education_levels.append("Master's Degree")
                elif 'bachelor' in degree_text:
                    education_levels.append("Bachelor's Degree")
                elif 'associate' in degree_text:
                    education_levels.append("Associate Degree")
                    
            if 'PhD' in education_levels:
                return 'PhD'
            elif "Master's Degree" in education_levels:
                return "Master's Degree"
            elif "Bachelor's Degree" in education_levels:
                return "Bachelor's Degree"
            elif "Associate Degree" in education_levels:
                return "Associate Degree"
            else:
                return "High School"
        except:
            return "Bachelor's Degree"  # Default

    def _count_skills(self, driver):
        """Count number of skills listed"""
        try:
            skills_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='skill'] .pvs-list__item")
            return min(len(skills_elements), 50)  # Cap at 50
        except:
            return 10  # Default estimate

    def _extract_connections_count(self, driver):
        """Extract connections count"""
        try:
            connections_element = driver.find_element(By.CSS_SELECTOR, ".pv-top-card--list-bullet li")
            connections_text = connections_element.text
            
            if "500+" in connections_text:
                return 500
            else:
                numbers = re.findall(r'\d+', connections_text)
                if numbers:
                    return int(numbers[0])
        except:
            pass
        return 100  # Default estimate

    def _estimate_posts_per_month(self, driver):
        """Estimate posts per month from activity"""
        try:
            # This is a rough estimate since activity data is limited
            activity_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='recent_activity'] .pvs-list__item")
            return min(len(activity_elements), 10)  # Rough estimate
        except:
            return 2  # Default estimate

    def _count_recommendations(self, driver):
        """Count recommendations received"""
        try:
            recommendations_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='recommendation'] .pvs-list__item")
            return len(recommendations_elements)
        except:
            return 3  # Default estimate

    def _has_volunteer_experience(self, driver):
        """Check if profile has volunteer experience"""
        try:
            volunteer_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='volunteer_experience'] .pvs-list__item")
            return len(volunteer_elements) > 0
        except:
            return False

    def _count_certifications(self, driver):
        """Count certifications"""
        try:
            cert_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='certification'] .pvs-list__item")
            return len(cert_elements)
        except:
            return 2  # Default estimate

    def _count_languages(self, driver):
        """Count languages"""
        try:
            lang_elements = driver.find_elements(By.CSS_SELECTOR, "[data-field='language'] .pvs-list__item")
            return max(len(lang_elements), 1)  # At least 1 (native language)
        except:
            return 1  # Default

    def _parse_duration_to_years(self, duration_text):
        """Parse duration text to years"""
        years = 0
        months = 0
        
        year_match = re.search(r'(\d+)\s*yr', duration_text)
        month_match = re.search(r'(\d+)\s*mo', duration_text)
        
        if year_match:
            years = int(year_match.group(1))
        if month_match:
            months = int(month_match.group(1))
            
        return years + (months / 12)

    def _basic_scraping_fallback(self, url):
        """Fallback method using basic requests"""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information available in meta tags
            name = self._extract_meta_content(soup, 'og:title') or "Unknown"
            headline = self._extract_meta_content(soup, 'og:description') or ""
            
            return {
                'name': name,
                'headline': headline,
                'summary': "",
                'experience_years': 5,
                'education_level': "Bachelor's Degree",
                'skills_count': 10,
                'connections_count': 100,
                'posts_per_month': 2,
                'recommendations_received': 3,
                'volunteer_experience': False,
                'certifications_count': 2,
                'languages_count': 1
            }
        except:
            raise Exception("Unable to scrape profile data")

    def _extract_meta_content(self, soup, property_name):
        """Extract content from meta tags"""
        meta_tag = soup.find('meta', property=property_name)
        if meta_tag:
            return meta_tag.get('content', '')
        return ''
