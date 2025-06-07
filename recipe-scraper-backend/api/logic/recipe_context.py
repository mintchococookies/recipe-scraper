from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RecipeContext:
    """Context class that holds all shared data needed for recipe extraction."""
    soup: BeautifulSoup
    recipe_url: str
    headers: List = None
    lists: List = None
    paragraphs: List = None
    
    def __post_init__(self):
        """Initialize common elements after instance creation."""
        if self.headers is None:
            self.headers = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if self.lists is None:
            self.lists = self.soup.find_all(['ol', 'ul'])
        if self.paragraphs is None:
            self.paragraphs = self.soup.find_all('p')
    
    def get_target_headers(self, keywords: List[str]) -> List:
        """Get headers that contain any of the given keywords."""
        return [header for header in self.headers 
                if any(keyword.lower() in header.text.lower() for keyword in keywords)]
    
    def find_elements_by_pattern(self, tag: str, pattern: str, case_insensitive: bool = True) -> List:
        """Find elements by tag and pattern in id/class."""
        import re
        flags = re.I if case_insensitive else 0
        return self.soup.find_all(tag, id=re.compile(pattern, flags)) + \
               self.soup.find_all(tag, {'class': re.compile(pattern, flags)}) 