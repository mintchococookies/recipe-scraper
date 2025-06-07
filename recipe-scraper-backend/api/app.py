import re
import requests
import logging
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bs4 import BeautifulSoup
from copy import deepcopy
from flask import Flask, request, session
from flask_cors import CORS
from flask_restx import Api, Resource
from urllib.parse import urlparse

# Local imports
from util import *
from constants import *
from recipe_state import *
from logic import *

CORS(app, 
     origins=["https://recipescraper.mintchococookies.com", "http://localhost:8080", "http://localhost:8000"],
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

# Create a session with connection pooling and retry strategy
http_session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
http_session.mount("http://", adapter)
http_session.mount("https://", adapter)

# ============= APIs =============
@api.route('/convert-recipe-units')
class ConvertUnits(Resource):
    @api.doc(description="Convert between SI and metric units")
    @api.doc(security='basicAuth')
    @api.doc(params={'Authorization': {'in': 'header', 'description': 'Bearer <JWT token>', 'type': 'string'}})
    @api.expect(unit_type_model)
    @token_required
    @track_latency('convert-recipe-units')
    def post(self, current_user):
        recipe_state = get_recipe_state(session)
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
            save_recipe_state(session, recipe_state)
        
            datadog_logger.log("ConvertUnits succeeded for " + recipe_state.recipe_url + "\nResponse: " + str(result), {"endpoint": "convertUnits", "result": "success"})
            return result
        else:
            datadog_logger.log("ConvertUnits failed for " + recipe_state.recipe_url + "\nResponse: None", {"endpoint": "convertUnits", "result": "fail"})
            return None

@api.route('/calculate-serving-ingredients')
class MultiplyServingSize(Resource):
    @api.doc(description="Calculate the amount of ingredients based on the serving size wanted")
    @api.expect(serving_size_model)
    @api.doc(security='basicAuth')
    @api.doc(params={'Authorization': {'in': 'header', 'description': 'Bearer <JWT token>', 'type': 'string'}})
    @token_required
    @track_latency('calculate-serving-ingredients')
    def post(self, current_user):
        recipe_state = get_recipe_state(session)
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
    
        save_recipe_state(session, recipe_state)
        response = recipe_state.ingredients
        if response:
            datadog_logger.log("MultiplyServingSize succeeded for " + recipe_state.recipe_url + "\nResponse: " + str(response), {"endpoint": "multiplyServingSize", "result": "success"})
        else:
            datadog_logger.log("MultiplyServingSize failed for " + recipe_state.recipe_url + "\nResponse: None", {"endpoint": "multiplyServingSize", "result": "fail"})
        return response

def extract_recipe_data_parallel(soup, recipe_url):
    """Extract recipe data in parallel using ThreadPoolExecutor"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_name = executor.submit(extract_recipe_name, soup, recipe_url)
        future_steps = executor.submit(extract_recipe_steps, soup)
        future_ingredients = executor.submit(extract_ingredients, soup)
        future_servings = executor.submit(get_serving_size, soup)
        
        # Get results as they complete
        recipe_name = postprocess_text(future_name.result())
        recipe_steps = postprocess_list(future_steps.result())
        ingredients = postprocess_list(future_ingredients.result())
        servings = future_servings.result()
        
        return recipe_name, recipe_steps, ingredients, servings

@api.route('/scrape-recipe-steps')
class ScrapeRecipeSteps(Resource):
    @api.doc(description="Recipe steps scraping")
    @api.expect(recipe_url_model)
    @api.doc(security='basicAuth')
    @api.doc(params={'Authorization': {'in': 'header', 'description': 'Bearer <JWT token>', 'type': 'string'}})
    @token_required
    @track_latency('scrape-recipe-steps')
    def post(self, current_user):
        recipe_state = RecipeState()
        data = request.get_json()
        recipe_url = data.get('recipe_url')
        recipe_state.recipe_url = recipe_url
        
        try:
            response = http_session.get(recipe_url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            return {'error': 'Failed to fetch recipe data: {}'.format(str(e))}, 400
        
        soup = BeautifulSoup(response.content, 'lxml')  # Using lxml parser for better performance

        # Extract all recipe data in parallel
        recipe_name, recipe_steps, recipe_state.ingredients, recipe_state.servings = extract_recipe_data_parallel(soup, recipe_url)
        
        if recipe_state.ingredients:
            recipe_state.ingredients, recipe_state.original_unit_type, recipe_state.ingredients_pre_conversion = extract_units(recipe_state.ingredients)
        
        save_recipe_state(session, recipe_state)
        
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
            datadog_logger.log("ScrapeRecipeSteps succeeded for " + recipe_url + "\nResponse: " + str(response), {"endpoint": "scrapeRecipeSteps", "result": "success"})
            return response, 200
        else:
            response = {"error": "Oops! We encountered a hiccup while trying to extract the recipe from this website. It seems its structure is quite unique and our system is having trouble with it. We're continuously working on improvements though! Thank you for your patience and support. ^^"}
            details = f"{recipe_url} | {recipe_name} | {recipe_steps} | {recipe_state.ingredients} | {recipe_state.servings} | {recipe_state.original_unit_type}"
            datadog_logger.log("ScrapeRecipeSteps failed for " + recipe_url + "\nDetails: " + details, {"endpoint": "scrapeRecipeSteps", "result": "fail"})
            return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)