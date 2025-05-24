import re
import logging
from bs4 import BeautifulSoup
from constants import *

def extract_ingredients(soup):
    ingredients = []

    # Found id or class labels for the ingredient li
    ingredients_html = [ingredient.text.strip() + " " for ingredient in soup.find_all('li', id=re.compile(r'.*(ingredient).*', re.I))]
    ingredients_html += [" ".join(ingredient.text.split()) for ingredient in soup.find_all(['p', 'li'], {'class': re.compile(r'ingredient', re.I)}) if ingredient.text.strip()]
    if ingredients_html:
        logging.info("DEBUG: method 1 ingredients")
        return sorted(set(ingredients_html))

    # Found ingredients list (ol/ul) but li is not labelled
    elif not ingredients_html:
        for element in soup.find_all(['ol', 'ul', 'div'], {'class': re.compile(r'ingredient', re.I)}):
            logging.info("DEBUG: method 2 ingredients")
            for item in element.find_all('li'):  # Find all list items within the <ol> or <ul>
                ingredient_text = item.get_text(strip=True)
                if ingredient_text not in ingredients:
                    ingredients.append(ingredient_text) if ingredient_text else None # Append each list item to the ingredients list

    # Manually search for what looks like ingredients (current limitation is if the ingredients list totally got no labelling anywhere in the whole page then cannot)
    if not ingredients:
        logging.info("DEBUG: method 3 ingredients")
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        target_headers = [header for header in headers if any(keyword.lower() in header.text.lower() for keyword in ['ingredients'])]

        for header in target_headers:
            current_element = header.parent    
            while current_element:
                ol_element = current_element.find('ul')
                if ol_element:
                    for li in ol_element.find_all('li'):
                        ingredient_text = li.get_text(strip=True)
                        if ingredient_text not in ingredients:
                            ingredients.append(ingredient_text) if ingredient_text else None
                    break

                current_element = current_element.find_next()

    return ingredients