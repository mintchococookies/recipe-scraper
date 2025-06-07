import re
import logging
from constants import *

# Function to extract the recipe steps when there's some labelling (id/class) on the html elements that indicates its the recipe
def extract_recipe_steps_labelled(soup):
    logging.info("DEBUG: extract_recipe_steps_labelled")
    recipe_steps = []
    step_positions = []
    extracted_steps = set()  

    recipe_steps_html = soup.find_all('li', id=re.compile(r'.*(instruction|direction|step).*', re.I))
    recipe_steps_html += soup.find_all(['p', 'li'], {'class': re.compile(r'instruction|direction|step', re.I)} )
    recipe_steps_html = [step.get_text(strip=True) for step in recipe_steps_html]
    has_cooking_related_words = any(any(word in step.lower() for word in cooking_action_words) for step in recipe_steps_html)
    if has_cooking_related_words:
        for element in recipe_steps_html:
            text = element.strip()
            if text.strip() not in extracted_steps:
                recipe_steps.append(text.strip())
                step_positions.append(recipe_steps_html.index(element))
                extracted_steps.add(text.strip())
    return recipe_steps

# Function to extract the recipe steps when there is no labelling (id/class) on the html elements at all to indicate that its the recipe
def extract_recipe_steps_manual(soup):
    recipe_steps = []

    # DOM traversal starting from any heading containing directions, instructions, method, or how to make
    if not recipe_steps:
        logging.info("DEBUG: extract_recipe_steps_manual")
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        target_headers = [header for header in headers if any(keyword.lower() in header.text.lower() for keyword in ['directions', 'instructions', 'method', 'how to make'])]

        for header in target_headers:
            current_element = header.parent
            while current_element:
                ol_element = current_element.find('ol')
                if ol_element:
                    for li in ol_element.find_all('li'):
                        step_text = li.get_text(strip=True)
                        if step_text not in recipe_steps:
                            recipe_steps.append(step_text)
                    break
                current_element = current_element.find_next()
    
    return recipe_steps

def extract_recipe_steps(soup):
    # Try to find the recipe by the class/id labels
    recipe_steps = extract_recipe_steps_labelled(soup)

    # If there's no labelling found
    if not recipe_steps:
        recipe_steps = extract_recipe_steps_manual(soup)

    return recipe_steps