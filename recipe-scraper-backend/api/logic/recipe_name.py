import re
from urllib.parse import urlparse
from constants import *
from util.emoji_helper import emoji_map

def extract_recipe_name(soup, recipe_url):
    # Parse the URL to extract the recipe name
    recipe_url = recipe_url[:-1] if recipe_url.endswith('/') else recipe_url
    parsed_url = urlparse(recipe_url)
    path_components = parsed_url.path.split('/')
    recipe_name_from_url = path_components[-1].replace('-', ' ').title()
    recipe_name_from_url = recipe_name_from_url.split('.')
    recipe_name_from_url = recipe_name_from_url[0]

    # labelled with ID or class
    title_html = [title.text.strip() + " " for title in soup.find_all(['h1', 'h2'], {'id': re.compile(r'.*(title|heading).*', re.I)})]
    title_html += [title.text.strip() + " " for title in soup.find_all(['h1', 'h2'], {'class': re.compile(r'.*(title|heading).*', re.I)})]
    recipe_name_list = [item for item in title_html if item.strip().istitle()]

    # compare which title/heading is most similar to the url cause the url usually has the recipe name in it
    matched_name = None
    for item in recipe_name_list:
        words1 = set(item.lower().split())
        words2 = set(recipe_name_from_url.lower().split())
        intersection = words1.intersection(words2)
        similarity = len(intersection) / max(len(words1), len(words2))
        if similarity >= 0.3:
            matched_name = item.strip()
            break  # stop after first good match

    # Use matched_name if found, else fallback
    name = matched_name if matched_name else recipe_name_from_url.strip()

    # Check if any emoji_map key is a substring in name (case-insensitive)
    lower_name = name.lower()
    for key in emoji_map:
        if key.lower() in lower_name:
            name = emoji_map[key] + " " + name
            break  # add emoji only once for first match

    return name