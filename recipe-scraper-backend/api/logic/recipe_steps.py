import re
import logging
from constants import *
from .recipe_context import RecipeContext

def extract_recipe_steps_labelled(context: RecipeContext) -> list:
    """Extract recipe steps when elements are labelled with ID or class."""
    logging.info("DEBUG: extract_recipe_steps_labelled")
    recipe_steps = []
    step_positions = []
    extracted_steps = set()  

    # Find steps with instruction/direction/step labels
    recipe_steps_html = context.find_elements_by_pattern('li', r'.*(instruction|direction|step).*')
    recipe_steps_html = [step.get_text(strip=True) for step in recipe_steps_html]
    
    # Check if steps contain cooking-related words
    has_cooking_related_words = any(any(word in step.lower() for word in cooking_action_words) 
                                  for step in recipe_steps_html)
    
    if has_cooking_related_words:
        for element in recipe_steps_html:
            text = element.strip()
            if text.strip() not in extracted_steps:
                recipe_steps.append(text.strip())
                step_positions.append(recipe_steps_html.index(element))
                extracted_steps.add(text.strip())
    return recipe_steps

def extract_recipe_steps_manual(context: RecipeContext) -> list:
    """Extract recipe steps when no labels are present."""
    recipe_steps = []

    # Find headers containing directions/instructions keywords
    target_headers = context.get_target_headers(['directions', 'instructions', 'method', 'how to make'])

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

def extract_recipe_steps(context: RecipeContext) -> list:
    """Extract recipe steps using the provided context."""
    # Try to find steps by labels first
    recipe_steps = extract_recipe_steps_labelled(context)

    # If no labelled steps found, try manual extraction
    if not recipe_steps:
        recipe_steps = extract_recipe_steps_manual(context)

    return recipe_steps