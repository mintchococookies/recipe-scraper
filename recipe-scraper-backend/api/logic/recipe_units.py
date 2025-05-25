import re
import logging
from copy import deepcopy
from constants import *
from logic.recipe_servings import calculate_servings

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
            if len(modified_unit) > 1:
                # If unit is 'g' and next letter is vowel, treat whole as name, for example "garlic" vs "gchicken"
                if modified_unit[1] == 'g' and modified_unit[2][:1].lower() in 'aeiour':
                    name = unit + " " + name
                    unit = None
                else:
                    unit = modified_unit[1]
                    name = modified_unit[2] + " " + name
            else:
                unit = modified_unit[0]

        else:
            # the unit may be stuck directly to the ingredient name without any spacing, so filter whether the name contains any common units
            logging.info("DEBUG: Unit is NoneType:", name)
            for u in sorted(common_units, key=len, reverse=True):
                if u in name.lower():
                    pattern = re.compile(r'\b' + re.escape(u) + r'\b', re.IGNORECASE)
                    match = pattern.search(name)
                    if match:
                        unit = match.group(0)
                        name = pattern.sub('', name, count=1).strip()
                        if not unit:
                            modified_unit = re.split(r'^({})'.format('|'.join(common_units)), unit)
                            unit = modified_unit[1] if len(modified_unit) > 1 else modified_unit[0]
                            name = modified_unit[2] + " " + name if len(modified_unit) > 1 else name
                        break
        
        if unit and unit.lower() not in common_units:
            name = unit + " " + name
            unit = None

        # remove any extra quantity or unit in brackets, for example "1 cup (50ml) of water" because that won't get converted
        name = re.sub(r'[\(\[]\s*\d+\s*[a-zA-Z]*\s*[\)\]]', '', name).strip()
        
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