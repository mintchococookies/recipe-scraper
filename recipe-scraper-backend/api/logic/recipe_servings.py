import re
from constants import *
from .recipe_context import RecipeContext

# FUNCTION TO GET THE SERVING SIZE OF THE RECIPE ON THE WEBSITE
def get_serving_size(context: RecipeContext) -> str:
    """Extract serving size using the provided context."""
    servings = None
    elements = context.soup.find_all(['p', 'span', 'em', 'div'])
    target_elements = [element for element in elements 
                      if any(keyword.lower() in element.text.lower() 
                            for keyword in ['serves', 'servings', 'yield', 'serving'])]

    for element in target_elements:
        numbers = re.findall(r'\d+', element.get_text())
        if numbers:
            text = element.get_text()
            # Check if serving number is in same element as serving keywords
            match = re.search(r'(?:Yields:|Serves:|Servings:|Yield:|Serving:)\s*(.+)', text, re.IGNORECASE)
            if match:
                text = match.group(1)
                text = text.split(',')  # Split in case it includes prep time etc
                # If text is too long, split by spaces
                if len(text[0]) > 12:
                    text[0] = text[0].split(' ', 1)
                    servings = text[0][0]
                    break
                else:
                    servings = text[0]
                    break
            # Check next element in DOM
            else:
                current_element = element.find_next()
                while current_element:
                    numbers = re.findall(r'\d+', current_element.get_text())
                    if numbers and len(current_element.get_text()) < 10:
                        servings = list(filter(str.isdigit, current_element.get_text()))[0]
                        break
                    current_element = current_element.find_next()
                if servings is not None:
                    break
                # Check elements within same parent
                else:
                    current_element = element.parent
                    while current_element:
                        numbers = re.findall(r'\d+', current_element.get_text())
                        if numbers and len(current_element.get_text()) < 10:
                            servings = list(filter(str.isdigit, current_element.get_text()))[0]
                            break
                        current_element = current_element.find_next()
                    if servings is not None:
                        break

    match = re.search(r'\d+', servings) if servings else None
    return str(match.group()) if match else None

def calculate_servings(ingredients: list, servings: float, requested_serving_size: float) -> list:
    """Calculate ingredient quantities based on serving size adjustment."""
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
            # Convert decimals to fractions
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