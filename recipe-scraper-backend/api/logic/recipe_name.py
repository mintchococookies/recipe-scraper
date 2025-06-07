import re
from urllib.parse import urlparse
from constants import *
from util.emoji_helper import emoji_map
from .recipe_context import RecipeContext

def extract_recipe_name(context: RecipeContext) -> str:
    """Extract recipe name using the provided context."""
    # Parse the URL to extract the recipe name
    recipe_url = context.recipe_url[:-1] if context.recipe_url.endswith('/') else context.recipe_url
    parsed_url = urlparse(recipe_url)
    path_components = parsed_url.path.split('/')
    recipe_name_from_url = path_components[-1].replace('-', ' ').title()
    recipe_name_from_url = recipe_name_from_url.split('.')
    recipe_name_from_url = recipe_name_from_url[0]

    # Find titles with ID or class labels
    title_elements = context.find_elements_by_pattern(['h1', 'h2'], r'.*(title|heading|recipe-name).*')
    title_html = [title.text.strip() + " " for title in title_elements]
    recipe_name_list = [item.strip() for item in title_html if item.strip().istitle()]

    # Compare titles with URL to find best match
    matched_name = None
    for item in recipe_name_list:
        # Skip titles that are too generic (like category pages)
        if item.lower().endswith(('ideas', 'recipes', 'collection')):
            continue
            
        words1 = set(item.lower().split())
        words2 = set(recipe_name_from_url.lower().split())
        intersection = words1.intersection(words2)
        similarity = len(intersection) / max(len(words1), len(words2))
        if similarity >= 0.4:
            matched_name = item.strip()
            break  # stop after first good match

    # Use matched_name if found, else fallback
    name = matched_name if matched_name else recipe_name_from_url.strip()

    # Add emoji if applicable
    lower_name = name.lower()
    for key in emoji_map:
        if key.lower() in lower_name:
            name = emoji_map[key] + " " + name
            break  # add emoji only once for first match

    return name