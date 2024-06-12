import pytest
from api.app import app
from bs4 import BeautifulSoup
from api.app import extract_recipe_steps_manual, extract_recipe_steps_labelled, extract_ingredients, extract_recipe_name, get_serving_size, postprocess_list, postprocess_text, standardize_units, extract_units, calculate_servings, convert_units
from api.auth import verify_credentials

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test extract_recipe_steps_labelled function
def test_extract_recipe_steps_labelled():
    soup = BeautifulSoup("<html><body><div><li id='instruction1'>Boil the water</li><li class='direction'>Peel the potato</li><p class='step'>Serve hot</p></div></body></html>", 'html.parser')
    result = extract_recipe_steps_labelled(soup)
    assert result == ["Boil the water", "Peel the potato", "Serve hot"]

# Test extract_recipe_steps_manual function
def test_extract_recipe_steps_manual():
    soup = BeautifulSoup("<html><body><h1>Directions</h1><ol><li>Step 1</li><li>Step 2</li></ol></body></html>", 'html.parser')
    result = extract_recipe_steps_manual(soup)
    assert result == ["Step 1", "Step 2"]

# Test extract_ingredients function
def test_extract_ingredients():
    # Case where ingredients are found with id/class labels
    soup_with_labelled_ingredients = BeautifulSoup("<html><body><li id='ingredient1'>Ingredient 1</li><p class='ingredient'>Ingredient 2</p></body></html>", 'html.parser')
    result_labelled = extract_ingredients(soup_with_labelled_ingredients)
    assert result_labelled == ["Ingredient 1 ", "Ingredient 2"]
    
    # Case where ingredients are found within lists but not labelled
    soup_with_list_ingredients = BeautifulSoup("<html><body><ol class='ingredient'><li>Ingredient 3</li><li>Ingredient 4</li></ol></body></html>", 'html.parser')
    result_list = extract_ingredients(soup_with_list_ingredients)
    assert result_list == ["Ingredient 3", "Ingredient 4"]

    # Case where ingredients are manually searched
    soup_with_manual_ingredients = BeautifulSoup("<html><body><h1>Ingredients</h1><ul><li>Ingredient 5</li><li>Ingredient 6</li></ul></body></html>", 'html.parser')
    result_manual = extract_ingredients(soup_with_manual_ingredients)
    assert result_manual == ["Ingredient 5", "Ingredient 6"]

# Test extract_recipe_name function
def test_extract_recipe_name():
    # Case where recipe name is found in the URL
    soup = BeautifulSoup("<html></html>", 'html.parser')
    url_with_recipe_name = "https://example.com/recipe-name"
    result_url_name = extract_recipe_name(soup, url_with_recipe_name)
    assert result_url_name == "Recipe Name"

    # Case where recipe name is found in the title/headings with IDs/classes
    soup_with_labelled_title = BeautifulSoup("<html><body><h1 id='title'>Recipe Title</h1><h2 class='heading'>Heading Title</h2></body></html>", 'html.parser')
    result_labelled_title = extract_recipe_name(soup_with_labelled_title, "https://example.com/recipe-url")
    assert result_labelled_title == "Recipe Title"

# Test get_serving_size function
def test_get_serving_size():
    # Case where serving size is found within the same element as the keyword
    soup_with_serving_in_element = BeautifulSoup("<html><body><p>Serves: 4</p></body></html>", 'html.parser')
    result_in_element = get_serving_size(soup_with_serving_in_element)
    assert result_in_element == '4'

    # Case where serving size is found in the next elements within the same parent
    soup_with_serving_in_next_elements = BeautifulSoup("<html><body><div><p>Servings: </p><span>4</span></div></body></html>", 'html.parser')
    result_in_next_elements = get_serving_size(soup_with_serving_in_next_elements)
    assert result_in_next_elements == '4'

# Test postprocess_list function
def test_postprocess_list():
    # Case where list is not empty
    input_list = ['▢ Item 1', '▢ Item 2', '▢ Item 3']
    result_list = postprocess_list(input_list)
    assert result_list == ['Item 1', 'Item 2', 'Item 3']

    # Case where list is empty
    empty_list = []
    result_empty = postprocess_list(empty_list)
    assert result_empty == None

# Test postprocess_text function
def test_postprocess_text():
    # Case where text has leading/trailing whitespace
    input_text = "   Some Text   "
    result_text = postprocess_text(input_text)
    assert result_text == "Some Text"

    # Case where text has no leading/trailing whitespace
    no_whitespace_text = "Some Text"
    result_no_whitespace = postprocess_text(no_whitespace_text)
    assert result_no_whitespace == "Some Text"

# Test standardize_units function
def test_standardize_units():
    # Case where units are successfully standardized
    input_ingredients = [["Sugar", "g"], ["Butter", "lb"], ["Water", "ml"], ["Salt", "teaspoon"]]
    result_standardized = standardize_units(input_ingredients)
    expected_result = [["Sugar", "grams"], ["Butter", "lb"], ["Water", "ml"], ["Salt", "tsp"]]
    assert result_standardized == expected_result

    # Case where units are already standardized
    standardized_ingredients = [["Flour", "grams"], ["Oil", "ml"], ["Vinegar", "tbsp"]]
    result_already_standardized = standardize_units(standardized_ingredients)
    assert result_already_standardized == standardized_ingredients

    # Case where unit is not found in mapping
    ingredients_with_unknown_unit = [["Honey", "cups"]]
    result_unknown_unit = standardize_units(ingredients_with_unknown_unit)
    assert result_unknown_unit == ingredients_with_unknown_unit

# Test extract_units function
def test_extract_units():
    input = [
    "5pounds potatoes(I use half Yukon Gold, half Russet potatoes)",
    "2large cloves garlic, minced",
    "fine sea salt",
    "6 tablespoonsbutter",
    "1 cupwhole milk",
    "4ounces cream cheese, room temperature",
    "toppings: chopped fresh chives or green onions, freshly-cracked black pepper"
  ]
    ingredients, original_unit_type, ingredients_pre_conversion = extract_units(input)
    assert ingredients == [
        ["5", "lb", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
        ["2", None, "large cloves garlic, minced"],
        [None, None, "fine sea salt"],
        ["6", "tbsp", "butter"],
        ["1", "cup", "whole milk"],
        ["4", "oz", "cream cheese, room temperature"],
        [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
    ]
    assert original_unit_type == 'metric'
    assert ingredients_pre_conversion == ingredients

# Test calculate_servings function
def test_calculate_servings():
    servings = 4
    requested_serving_size = 8

    input_ingredients = [
        ["5", "lb", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
        ["2", None, "large cloves garlic, minced"],
        [None, None, "fine sea salt"],
        ["6", "tbsp", "butter"],
        ["1", "cup", "whole milk"],
        ["4", "oz", "cream cheese, room temperature"],
        [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
    ]
    expected_result = [
        ["10", "lb", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
        ["4", None, "large cloves garlic, minced"],
        [None, None, "fine sea salt"],
        ["12", "tbsp", "butter"],
        ["2", "cup", "whole milk"],
        ["8", "oz", "cream cheese, room temperature"],
        [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
    ]
    result_calculated = calculate_servings(input_ingredients, servings, requested_serving_size)
    assert result_calculated == expected_result

# Test convert_units function
def test_convert_units():
    input_data = [
        ["5", "lb", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
        ["2", None, "large cloves garlic, minced"],
        [None, None, "fine sea salt"],
        ["6", "tbsp", "butter"],
        ["1", "cup", "whole milk"],
        ["4", "oz", "cream cheese, room temperature"],
        [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
    ]

    output_data = [
        [2267.96, "g", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
        ["2", None, "large cloves garlic, minced"],
        [None, None, "fine sea salt"],
        ["6", "tbsp", "butter"],
        [236.59, "ml", "whole milk"],
        [113.4, "g", "cream cheese, room temperature"],
        [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
    ]
    
    # Test converting to the same unit type with the same serving size
    result_same_unit = convert_units(input_data, "metric", 4, 4, "metric", input_data)
    assert result_same_unit == input_data
    
    # Test converting to a different unit type
    result_diff_unit = convert_units(input_data, "si", 4, 4, "metric", input_data)
    assert result_diff_unit == output_data
    
    # Test converting with a requested serving size different from the original serving size
    result_req_serving_size = convert_units(output_data, "si", 4, 4, "metric", input_data)
    assert result_req_serving_size == input_data

# Helper function
def replace_non_breaking_spaces(data):
    if isinstance(data, str):
        return data.replace('\xa0', ' ')
    elif isinstance(data, list):
        return [replace_non_breaking_spaces(item) for item in data]
    elif isinstance(data, dict):
        return {key: replace_non_breaking_spaces(value) for key, value in data.items()}
    return data

### TEST AUTH APIs
global token
token = None

def test_verify_credentials():
    assert verify_credentials('user', 'pw') == True
    assert verify_credentials('invalid_user', 'invalid_pw') == False

def test_user_login(client):
    global token
    login_data = {
        "username": "user",
        "password": "pw"
    }

    response = client.post('/login', json=login_data)
    token = response.json['token']

    assert response.status_code == 200
    assert response.json is not None
    assert 'token' in response.json

# TEST APIs
def test_scrape_recipe_steps(client):
    global token
    input_data = {
        "recipe_url": "https://www.gimmesomeoven.com/best-mashed-potatoes-recipe/"
    }
    response = client.post('/scrape-recipe-steps',          
                           headers={"Authorization": f"{token}"},
                           json=input_data)
    expected_response = {
        "recipe_url": "https://www.gimmesomeoven.com/best-mashed-potatoes-recipe/",
        "recipe_name": "Best Mashed Potatoes Recipe",
        "recipe_steps": [
            "Cut the potatoes.Feel free to peel your potatoes or leave the skins on.  Then cut them into evenly-sized chunks, about an inch or so thick, and transfer them to alarge stockpotfull of cold water.",
            "Boil the potatoes.Once all of your potatoes are cut, be sure that there is enough cold water in the pan so that the water line sits about 1 inch above the potatoes.  Stir the garlic and 1 tablespoon sea salt into the water.  Then turn the heat to high and cook until the water comes to a boil.  Reduce heat to medium-high (or whatever temperature is needed to maintain the boil) and continue cooking for about 10-12 minutes, or until a knife inserted in the middle of a potato goes in easily with almost no resistance.  Carefully drain out all of the water.",
            "Prepare your melted butter mixture.Meanwhile, as the potatoes are boiling, heat the butter, milk and an additional 2 teaspoons of sea salt together either in a small saucepan or in the microwave until the butter isjustmelted.  (You want to avoid boiling the milk.)  Set aside until ready to use.",
            "Pan-dry the potatoes.After draining the water, immediately return the potatoes to the hot stockpot, place it back on the hot burner, and turn the heat down to low.  Using two oven mitts, carefully hold the handles on the stockpot and shake it gently on the burner for about 1 minute to help cook off some of the remaining steam within the potatoes.  Remove the stockpot entirely from the heat and set it on a flat, heatproof surface.",
            "Mash the potatoes.Using your preferred kind of potato masher (I recommendthis onein general, orthis onefor extra-smooth), mash the potatoes to your desired consistency.",
            "Stir everything together.Then pour half of the melted butter mixture over the potatoes, and fold it in with a wooden spoon or spatula until potatoes have soaked up the liquid.  Repeat with the remaining butter, and then again with the cream cheese, folding in each addition in untiljustcombined to avoid over-mixing.  (Feel free to add in more warm milk to reach your desired consistency, if needed.)",
            "Taste and season.One final time, taste the potatoes and season with extra salt if needed.",
            "Serve warm.Then serve warm, garnished withgravyor any extra toppings that you might like, and enjoy!"
        ],
        "ingredients": [
            ["5", "lb", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
            ["2", None, "large cloves garlic, minced"],
            [None, None, "fine sea salt"],
            ["6", "tbsp", "butter"],
            ["1", "cup", "whole milk"],
            ["4", "oz", "cream cheese, room temperature"],
            [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
        ],
        "servings": "10",
        "original_unit_type": "metric"
    }

    actual_response = replace_non_breaking_spaces(response.json)

    assert response.status_code == 200
    assert actual_response == expected_response

def test_convert_recipe_units(client):
    global token
    input_data = {
        "unit_type": "si"
    }
    response = client.post('/convert-recipe-units',          
                           headers={"Authorization": f"{token}"},
                           json=input_data)
    
    expected_response = [
        [2267.96, "g", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
        ["2", None, "large cloves garlic, minced"],
        [None, None, "fine sea salt"],
        ["6", "tbsp", "butter"],
        [236.59, "ml", "whole milk"],
        [113.4, "g", "cream cheese, room temperature"],
        [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
    ]
    
    actual_response = replace_non_breaking_spaces(response.json)

    assert response.status_code == 200
    assert actual_response == expected_response

def test_multiply_serving_size(client):
    global token
    input_data = {
        "serving_size": "20"
    }
    response = client.post('/calculate-serving-ingredients',          
                           headers={"Authorization": f"{token}"},
                           json=input_data)
    
    expected_response = [
        ["4535.92", "g", "potatoes(I use half Yukon Gold, half Russet potatoes)"],
        ["4", None, "large cloves garlic, minced"],
        [None, None, "fine sea salt"],
        ["12", "tbsp", "butter"],
        ["473.18", "ml", "whole milk"],
        ["226.8", "g", "cream cheese, room temperature"],
        [None, None, "toppings : chopped fresh chives or green onions, freshly-cracked black pepper"]
    ]
    
    actual_response = replace_non_breaking_spaces(response.json)

    assert response.status_code == 200
    assert actual_response == expected_response