import re
import logging
from bs4 import BeautifulSoup
from constants import *

unit_pattern = re.compile(r'\b(?:' + '|'.join(common_units) + r')\b', re.IGNORECASE)

def extract_ingredients(soup):
    ingredients = []

    # Found id or class labels for the ingredient li
    ingredients_html = [ingredient.text.strip() + " " for ingredient in soup.find_all('li', id=re.compile(r'.*(ingredient).*', re.I))]
    ingredients_html += [" ".join(ingredient.text.split()) for ingredient in soup.find_all(['p', 'li'], {'class': re.compile(r'ingredient', re.I)}) if ingredient.text.strip()]
    if ingredients_html:
        print("DEBUG: method 1 ingredients")
        return sorted(set(ingredients_html))

    # Found ingredients list (ol/ul) but li is not labelled
    for element in soup.find_all(['ol', 'ul', 'div'], {'class': re.compile(r'ingredient', re.I)}):
        print("DEBUG: method 2 ingredients")
        for item in element.find_all('li'):  # Find all list items within the <ol> or <ul>
            ingredient_text = item.get_text(strip=True)
            if ingredient_text not in ingredients:
                ingredients.append(ingredient_text) if ingredient_text else None # Append each list item to the ingredients list

    # Manually search for what looks like ingredients (current limitation is if the ingredients list totally got no labelling anywhere in the whole page then cannot)
    if not ingredients:
        print("DEBUG: method 3 ingredients")
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        target_headers = [header for header in headers if any(keyword.lower() in header.text.lower() for keyword in ['ingredients'])]

        for header in target_headers:
            current_element = header.parent
            
            while current_element:
                ul_element = current_element.find('ul')
                if ul_element:
                    for li in ul_element.find_all('li'):
                        ingredient_text = li.get_text(strip=True)
                        if ingredient_text and ingredient_text not in ingredients:
                            ingredients.append(ingredient_text)
                    break
                if ingredients:
                    return ingredients

                # Fallback: check for <p> elements if no list found
                p_elements = current_element.find_all('p', recursive=False)

                # Check if any p contains a common unit
                if any(unit_pattern.search(p.get_text()) for p in p_elements):
                    for p in p_elements:
                        ingredient_text = p.get_text(strip=True)
                        if ingredient_text and ingredient_text not in ingredients:
                            ingredients.append(ingredient_text)

                if ingredients:
                    break

                current_element = current_element.find_next()

    return ingredients
