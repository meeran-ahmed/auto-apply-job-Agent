import requests
import re
from urllib.parse import quote_plus
from typing import List, Dict
from loguru import logger
from bs4 import BeautifulSoup


class RecruiterScout:
    """
    Scouts Technical Recruiters, Talent Acquisition Leads, and Engineering Managers
    for target hiring companies using public search endpoints.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def find_contacts(self, company_name: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Discovers recruiter and tech lead contacts for a given company.
        """
        clean_company = re.sub(r'[\(\)\{\}\[\]\.\,]', '', company_name).strip()
        contacts = []

        query = f'site:linkedin.com/in/ ("Technical Recruiter" OR "Talent Acquisition" OR "Engineering Manager") "{clean_company}"'
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        try:
            resp = requests.get(search_url, headers=self.headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                results = soup.find_all('div', class_='result')

                for res in results[:max_results]:
                    title_elem = res.find('a', class_='result__snippet') or res.find('a', class_='result__url')
                    header_elem = res.find('h2', class_='result__title')
                    
                    header_text = header_elem.get_text(strip=True) if header_elem else ""
                    snippet = title_elem.get_text(strip=True) if title_elem else ""

                    # Extract candidate name from title: "John Doe - Technical Recruiter at Company | LinkedIn"
                    name_match = re.match(r'^([^|\-–]+)', header_text)
                    name = name_match.group(1).strip() if name_match else "Hiring Lead"
                    
                    # Extract role
                    role_match = re.search(r'(Technical Recruiter|Talent Acquisition[^\-|–]*|Engineering Manager[^\-|–]*)', header_text, re.IGNORECASE)
                    role = role_match.group(1).strip() if role_match else "Recruiter / Engineering Lead"

                    # Extract profile link
                    link_elem = res.find('a', class_='result__url') or header_elem.find('a') if header_elem else None
                    profile_url = link_elem.get('href', '') if link_elem else ""
                    if "uddg=" in profile_url:
                        from urllib.parse import parse_qs, urlparse
                        parsed = parse_qs(urlparse(profile_url).query)
                        profile_url = parsed.get("uddg", [profile_url])[0]

                    if name and "LinkedIn" not in name:
                        contacts.append({
                            "name": name,
                            "role": role,
                            "profile_url": profile_url,
                            "company": clean_company
                        })

        except Exception as e:
            logger.debug(f"[RecruiterScout] Search note for {company_name}: {e}")

        # Fallback structured placeholder if external search is throttled
        if not contacts:
            contacts.append({
                "name": f"{clean_company} Talent Acquisition Team",
                "role": "Recruiting & Engineering Hiring",
                "profile_url": f"https://www.linkedin.com/company/{clean_company.lower().replace(' ', '-')}/people/",
                "company": clean_company
            })

        return contacts[:max_results]
