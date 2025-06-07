import re
import logging
from bs4 import BeautifulSoup
from constants import *
from .recipe_context import RecipeContext

unit_pattern = re.compile(r'\b(?:' + '|'.join(common_units) + r')\b', re.IGNORECASE)

def extract_ingredients(context: RecipeContext) -> list:
    """Extract ingredients using the provided context."""
    ingredients = []

    # Try to find ingredients by ID or class labels
    ingredients_html = context.find_elements_by_pattern('li', r'.*(ingredient).*')
    ingredients_html = [ingredient.text.strip() + " " for ingredient in ingredients_html]
    if ingredients_html:
        logging.info("DEBUG: method 1 ingredients")
        return sorted(set(ingredients_html))

    # Try to find ingredients list with class label
    for element in context.soup.find_all(['ol', 'ul', 'div'], {'class': re.compile(r'ingredient', re.I)}):
        logging.info("DEBUG: method 2 ingredients")
        for item in element.find_all('li'):
            ingredient_text = item.get_text(strip=True)
            if ingredient_text not in ingredients:
                ingredients.append(ingredient_text) if ingredient_text else None

    # Manual search for ingredients if no labels found
    if not ingredients:
        logging.info("DEBUG: method 3 ingredients")
        target_headers = context.get_target_headers(['ingredients'])

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
