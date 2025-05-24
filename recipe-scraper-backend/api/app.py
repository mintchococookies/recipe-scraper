import re
import requests
import logging
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from copy import deepcopy
from flask import Flask, request, session
from flask_cors import CORS
from flask_restx import Api, Resource
from urllib.parse import urlparse

# Local imports
from util.auth import *
from util.model_helper import *
from constants import *
from util.logging import logger

CORS(app, 
     origins=["https://recipescraper.mintchococookies.com", "http://localhost:8000"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"])

# Configure session
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
)

# Get models from util
recipe_url_model, unit_type_model, serving_size_model = create_models(api)

class RecipeState:
    def __init__(self):
        self.recipe_url = None
        self.ingredients = None
        self.servings = None
        self.ingredients_pre_conversion = None
        self.converted = False
        self.requested_serving_size = None
        self.original_unit_type = None
        self.unit_type = None
    
    def to_dict(self):
        return {
            'recipe_url': self.recipe_url,
            'ingredients': self.ingredients,
            'servings': self.servings,
            'ingredients_pre_conversion': self.ingredients_pre_conversion,
            'converted': self.converted,
            'requested_serving_size': self.requested_serving_size,
            'original_unit_type': self.original_unit_type,
            'unit_type': self.unit_type
        }
    
    def from_dict(self, data):
        self.recipe_url = data.get('recipe_url')
        self.ingredients = data.get('ingredients')
        self.servings = data.get('servings')
        self.ingredients_pre_conversion = data.get('ingredients_pre_conversion')
        self.converted = data.get('converted')
        self.requested_serving_size = data.get('requested_serving_size')
        self.original_unit_type = data.get('original_unit_type')
        self.unit_type = data.get('unit_type')

def get_recipe_state():
    if 'recipe_state' not in session:
        session['recipe_state'] = RecipeState().to_dict()
    
    recipe_state = RecipeState()
    recipe_state.from_dict(session['recipe_state'])
    session.modified = True
    
    return recipe_state

def save_recipe_state(recipe_state):
    session['recipe_state'] = recipe_state.to_dict()

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

def extract_ingredients(soup):
    ingredients = []

    # Found id or class labels for the ingredient li
    ingredients_html = [ingredient.text.strip() + " " for ingredient in soup.find_all('li', id=re.compile(r'.*(ingredient).*', re.I))]
    ingredients_html += [" ".join(ingredient.text.split()) for ingredient in soup.find_all(['p', 'li'], {'class': re.compile(r'ingredient', re.I)})]
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
                    ingredients.append(ingredient_text)  # Append each list item to the ingredients list

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
                            ingredients.append(ingredient_text)
                    break

                current_element = current_element.find_next()

    return ingredients

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
    for item in recipe_name_list:
        words1 = set(item.lower().split())
        words2 = set(recipe_name_from_url.lower().split())
        intersection = words1.intersection(words2)
        similarity = len(intersection) / max(len(words1), len(words2))
        if similarity >= 0.3:
            return item.strip()
    
    return recipe_name_from_url.strip()

# FUNCTION TO GET THE SERVING SIZE OF THE RECIPE ON THE WEBSITE
def get_serving_size(soup):
    servings = None
    elements = soup.find_all(['p', 'span', 'em', 'div'])
    target_elements = [element for element in elements if any(keyword.lower() in element.text.lower() for keyword in ['serves', 'servings', 'yield', 'serving'])]

    for element in target_elements:
        numbers = re.findall(r'\d+', element.get_text())
        if numbers:
            text = element.get_text()
            # check if the serving number is inside the same element as the word servings or yield etc
            match = re.search(r'(?:Yields:|Serves:|Servings:|Yield:|Serving:)\s*(.+)', text, re.IGNORECASE)
            if match:
                text = match.group(1)
                text = text.split(',') # split it just in case it comes together with the prep time etc
                # if after splitting its still very long, then split it again by spaces cause it probably still contains some other irrelevant information
                if len(text[0]) > 12:
                    text[0] = text[0].split(' ', 1)
                    return text[0][0]
                else:
                    return text[0]
            # if not, check whether it is at the same level in the DOM structure (for both this and next method, extract a digit once its found)
            else:
                current_element = element.find_next()
                while current_element:
                    numbers = re.findall(r'\d+', current_element.get_text())
                    if numbers and len(current_element.get_text()) < 10:
                        servings = int(list(filter(str.isdigit, current_element.get_text()))[0])
                        break
                    current_element = current_element.find_next()
                if servings is not None:
                    break
                # if also not, then check the next elements within the same parent
                else:
                    current_element = element.parent
                    while current_element:
                        numbers = re.findall(r'\d+', current_element.get_text())
                        if numbers and len(current_element.get_text()) < 10:
                            servings = int(list(filter(str.isdigit, current_element.get_text()))[0])
                            break
                        current_element = current_element.find_next()
                    if servings is not None:
                        break
    return servings

def postprocess_list(lst):
    if lst:
        return [re.sub(r'^\s*▢\s*', '', item) for item in lst]
    else:
        return None

def postprocess_text(txt):
    return txt.strip()

def standardize_units(ingredients):
    def clean_unit(unit):
        # Remove any trailing periods and extra spaces
        if unit:
            unit = re.sub(r'\s*\.\s*', '', unit)
            unit = unit.strip().lower()
        return unit
    
    for ingredient in ingredients:
        unit = clean_unit(ingredient[1])
        if ingredient and unit in unit_standardization_mapping:
            standardized_unit = unit_standardization_mapping[unit]
            ingredient[1] = standardized_unit
        else:
            pass

    return ingredients

# FUNCTIONS TO POSTPROCESS THE INGREDIENTS LIST - DOESN'T WORK WITH 3 TO 4, 1 TO 2 ETC. eg: https://www.simplyrecipes.com/recipes/spaghetti_alla_carbonara/
def extract_units(ingredients):
    parsed_ingredients = []
    for ingredient in ingredients:
        match = re.match(r'^((?:\d+\s*)?(?:\d*½|\d*¼|\d*[¾¾]|\d*⅛|\d*⅔|\d+\s*[/–-]|to\s*\d+)?[\s\d/–-]*)?[\s]*(?:([a-zA-Z]+)\b)?[\s]*(.*)$', ingredient)
        quantity, unit, name = match.groups()

        if '-' in str(quantity):
            quantity = str(quantity).replace(" ", "")
        elif 'to' in str(quantity):
            quantity = str(quantity).replace(" ", "")
            quantity = quantity.split('to')
            quantity = '-'.join(quantity)
        else:
            quantity = quantity.strip() if quantity else None
            for fraction, decimal in fraction_conversions.items():
                quantity = str(quantity).replace(fraction, decimal) if quantity else None
        
        if unit:
            modified_unit = re.split(r'^({})'.format('|'.join(common_units)), unit)
            unit = modified_unit[1] if len(modified_unit) > 1 else modified_unit[0]
            name = modified_unit[2] + " " + name if len(modified_unit) > 1 else name

        else:
            logging.info("DEBUG: Unit is NoneType:", name)
        
        if unit and unit.lower() not in common_units:
            name = unit + " " + name
            unit = None
        
        parsed_ingredients.append([quantity, unit, name.strip()])

    standardized_ingredients = standardize_units(parsed_ingredients)
    ingredients_pre_conversion = deepcopy(standardized_ingredients)
    
    if any(i[1] in to_si_conversion for i in ingredients_pre_conversion):
        original_unit_type = "metric"
    elif any(i[1] in to_metric_conversion for i in ingredients_pre_conversion):
        original_unit_type = "si"
    else:
        original_unit_type = ""

    return standardized_ingredients, original_unit_type, ingredients_pre_conversion

def calculate_servings(ingredients, servings, requested_serving_size):
    for ingredient in ingredients:
        quantity = ingredient[0]
        if not quantity:
            continue

        for separator in quantity_separators:
            if separator in str(quantity):
                quantity = str(quantity).replace(" ", "")
                quantity = quantity.split(separator)
                break

        def convert_fraction(q):
            for unicode_fraction, decimal in fraction_conversions.items():
                q = str(q).replace(unicode_fraction, decimal)
            return q

        def adjust_quantity(q):
            q = sum(float(num_str) for num_str in q.split(" "))
            base_quantity = q / float(servings)
            temp_quantity = round((base_quantity * requested_serving_size), 3)
            temp_quantity = str(temp_quantity)
            # Convert decimals to fractions using the fraction_conversions dictionary
            for decimal, fraction in fraction_conversions.items():
                if decimal.replace("0.", ".") in temp_quantity:
                    temp_quantity = temp_quantity.replace(decimal.replace("0.", "."), " " + fraction)
            return temp_quantity[:-2] if temp_quantity.endswith(".0") else temp_quantity

        if isinstance(quantity, list):
            new_quantity = [adjust_quantity(convert_fraction(q)) for q in quantity]
            ingredient[0] = '-'.join(new_quantity)
        else:
            ingredient[0] = adjust_quantity(convert_fraction(quantity))

    return ingredients

def convert_units(ingredients, unit_type, requested_serving_size, servings, original_unit_type, ingredients_pre_conversion):
    def convert_large_vals(converted_unit, converted_q):
        # if the cup value is super small, change to teaspoons (1 cup = 48 teaspoons)
        # if teaspoons is too much, change to tablespoons
        if converted_unit == "cups" and converted_q < 0.1:
            converted_unit = "tsp"
            converted_q *= teaspoons_per_cup

            if converted_q >= 3:
                converted_unit = "tbsp"
                converted_q /= teaspoons_per_tablespoon # 1 tablespoon = 3 teaspoons

        # if oz is greater than 32, change to pounds (1lb = 16oz)
        if converted_unit == "oz" and converted_q >= 32:
            converted_q /= ounces_per_pound 
            converted_unit = "lb"
        return converted_unit, converted_q

    # check if ingredients is populated or not first
    if not ingredients:
        return None
    
    conversion_dict = to_si_conversion if unit_type == "si" else to_metric_conversion
    
    # if they want to convert back to the original unit, must maintain the original units
    if original_unit_type == unit_type:
        if requested_serving_size is None or requested_serving_size == servings:
            logging.info("DEBUG: Conversion method 1")
            return ingredients_pre_conversion
        else:
            logging.info("DEBUG: Conversion method 2")
            ingredients = calculate_servings(deepcopy(ingredients_pre_conversion), servings, requested_serving_size)
            return ingredients
            
    # only do the conversion if they want a different unit
    else:
        for ingredient in ingredients:
            convert_to = None
            quantity = ingredient[0]
            if quantity: 
                # handle cases where the quantity is a range
                quantity = str(quantity).replace(" ", "")
                for separator in quantity_separators:
                    if separator in quantity:
                        quantity = quantity.split(separator)
                        break
                else:
                    # convert fractions to decimals
                    for fraction, decimal in fraction_conversions.items():
                        quantity = str(quantity).replace(fraction, decimal)
                    quantity_parts = quantity.split(" ")
                    quantity = sum(float(num_str) for num_str in quantity_parts)
                    
            unit = ingredient[1]
            name = ingredient[2]

            if quantity and unit and unit in [key for key, value in conversion_dict.items()]:
                # convert liquids from cups/tsp/tbsp to ml and solids to g
                if unit in ["cup", "cups", "tsp", "tbsp"]:
                    if any(liquid in name for liquid in liquids):
                        convert_to = "ml" 
                    else:
                        convert_to = "g"
                # convert grams of flour to cups of flour and not oz of flour
                if any(solid in name for solid in solids) and unit in ['g']:
                    convert_to = "cups"
                converted_unit = convert_to if convert_to else [key for key, value in conversion_dict[unit].items()][0]
                
                # handle cases where the quantity is a range
                if isinstance(quantity, list):
                    converted_quantities = []
                    for q in quantity:
                        converted_q = float(q) * conversion_dict[unit][converted_unit]
                        converted_unit, converted_q = convert_large_vals(converted_unit, converted_q)
                        temp = round(converted_q, 2)
                        converted_quantities.append(str(temp))
                    converted_quantity = '-'.join(converted_quantities)
                    ingredient[0] = converted_quantity
                # handle normal single number quantities
                else:
                    converted_quantity = float(quantity) * conversion_dict[unit][converted_unit]
                    converted_unit, converted_quantity = convert_large_vals(converted_unit, converted_quantity)
                    ingredient[0] = round(converted_quantity, 2)
                ingredient[1] = converted_unit
        logging.info("DEBUG: Conversion method 3")

    return ingredients

# ============= APIs =============
@api.route('/convert-recipe-units')
class ConvertUnits(Resource):
    @api.doc(description="Convert between SI and metric units")
    @api.doc(security='basicAuth')
    @api.doc(params={'Authorization': {'in': 'header', 'description': 'Bearer <JWT token>', 'type': 'string'}})
    @api.expect(unit_type_model)
    @token_required
    def post(self, current_user):
        recipe_state = get_recipe_state()
        data = request.get_json()
        recipe_state.unit_type = data.get('unit_type')

        result = convert_units(
            recipe_state.ingredients, 
            recipe_state.unit_type, 
            recipe_state.requested_serving_size, 
            recipe_state.servings, 
            recipe_state.original_unit_type, 
            recipe_state.ingredients_pre_conversion
        )
        
        if result:
            recipe_state.ingredients = result
            save_recipe_state(recipe_state)
        
        logger.log("ConvertUnits response for " + recipe_state.recipe_url + "\nResponse: " + str(result), {"endpoint": "convertUnits"})
        return result

@api.route('/calculate-serving-ingredients')
class MultiplyServingSize(Resource):
    @api.doc(description="Calculate the amount of ingredients based on the serving size wanted")
    @api.expect(serving_size_model)
    @api.doc(security='basicAuth')
    @api.doc(params={'Authorization': {'in': 'header', 'description': 'Bearer <JWT token>', 'type': 'string'}})
    @token_required
    def post(self, current_user):
        recipe_state = get_recipe_state()
        data = request.get_json()
        recipe_state.requested_serving_size = float(data.get('serving_size'))

        if not recipe_state.servings:
            return None
        
        # clean up the servings numbers
        recipe_state.servings = float(re.search("\\d+", str(recipe_state.servings))[0])

        if recipe_state.original_unit_type == recipe_state.unit_type:
            recipe_state.ingredients = calculate_servings(
                deepcopy(recipe_state.ingredients_pre_conversion), 
                recipe_state.servings, 
                recipe_state.requested_serving_size
            )
        else:
            temp = convert_units(
                deepcopy(recipe_state.ingredients_pre_conversion), 
                recipe_state.unit_type, 
                recipe_state.requested_serving_size, 
                recipe_state.servings, 
                recipe_state.original_unit_type, 
                recipe_state.ingredients_pre_conversion
            )
            recipe_state.ingredients = calculate_servings(
                temp, 
                recipe_state.servings, 
                recipe_state.requested_serving_size
            )
    
        save_recipe_state(recipe_state)
        response = recipe_state.ingredients
        logger.log("MultiplyServingSize response for " + recipe_state.recipe_url + "\nResponse: " + str(response), {"endpoint": "multiplyServingSize"})
        return response

@api.route('/scrape-recipe-steps')
class ScrapeRecipeSteps(Resource):
    @api.doc(description="Recipe steps scraping")
    @api.expect(recipe_url_model)
    @api.doc(security='basicAuth')
    @api.doc(params={'Authorization': {'in': 'header', 'description': 'Bearer <JWT token>', 'type': 'string'}})
    @token_required
    def post(self, current_user):
        recipe_state = get_recipe_state()
        data = request.get_json()
        recipe_url = data.get('recipe_url')
        recipe_state.recipe_url = recipe_url

        logger.log("Request received for recipe steps scraping: " + recipe_url)
        
        try:
            response = requests.get(recipe_url, headers=headers)
            response.raise_for_status()  
        except requests.RequestException as e:
            return {'error': 'Failed to fetch recipe data: {}'.format(str(e))}, 500
        
        soup = BeautifulSoup(response.content, 'html.parser')

        recipe_name = postprocess_text(extract_recipe_name(soup, recipe_url))
        recipe_steps = postprocess_list(extract_recipe_steps(soup))
        recipe_state.ingredients = postprocess_list(extract_ingredients(soup))
        if recipe_state.ingredients:
            recipe_state.ingredients, recipe_state.original_unit_type, recipe_state.ingredients_pre_conversion = extract_units(recipe_state.ingredients)
            recipe_state.servings = get_serving_size(soup)
        
        save_recipe_state(recipe_state)
        
        # With error handling
        if recipe_name and recipe_steps and recipe_state.ingredients and recipe_state.servings:
            response = {
                'recipe_url': recipe_url, 
                'recipe_name': recipe_name, 
                'recipe_steps': recipe_steps, 
                'ingredients': recipe_state.ingredients, 
                'servings': recipe_state.servings, 
                'original_unit_type': recipe_state.original_unit_type
            }
            logger.log("Response succeeded for " + recipe_url + "\nResponse: " + str(response), {"endpoint": "scrapeRecipeSteps", "result": "success"})
            return response, 200
        else:
            response = {"error": "Oops! We encountered a hiccup while trying to extract the recipe from this website. It seems its structure is quite unique and our system is having trouble with it. We're continuously working on improvements though! Thank you for your patience and support. ^^"}
            logger.log("Response failed for " + recipe_url + "\nResponse: " + str(response), {"endpoint": "scrapeRecipeSteps", "result": "fail"})
            return response

@api.route('/health-check')
class HealthCheck(Resource):
    @api.doc(description="Health check endpoint")
    def head(self):
        return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)