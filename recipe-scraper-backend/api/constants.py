# Define headers to simulate website access via browsers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
}

teaspoons_per_cup = 48
teaspoons_per_tablespoon = 3
ounces_per_pound = 16

# Define some cooking action words to help locate the recipe in some websites where the recipe isn't labelled
cooking_action_words = [
    'heat', 'preheat', 'saute', 'stir', 'simmer', 'remove', 'serve', 'garnish', 
    'pour', 'mix', 'bake', 'grill', 'boil', 'chop', 'slice', 'dice', 'cool', 
    'prepare', 'melt', 'transfer', 'refrigerate', 'reheat', 'arrange', 'whisk', 'blend', 'fry',
    'marinate', 'combine', 'drizzle', 'sprinkle', 'toss', 'fold', 'cover', 'let stand',
    'mix together', 'beat', 'brush', 'shape', 'spray', 'roll', 'cut', 'spread', 'dip',
    'top with', 'squeeze', 'shake', 'divide', 'whip', 'knead', 'grate', 'baste', 'pound', 'set', 'mash', 'stir',
    'dry', 'wait', 'cool', 'season', 'start', 'cook'
]

liquids = [
    "water", "oil", "milk", "honey"
]

solids = [
    "flour", "pepper", "salt"
]

common_units = [
    "grams", "gram", "milliliters", "milliliter", "centimeter", "centimeter", "kilograms", "kilogram", 
    "cups", "cup", "tablespoons", "tablespoon", "teaspoons", "teaspoon",
    "pounds", "pound", "ounces", "ounce", "grams", "gram", "tsp .", "tb .", "lb",
    "cloves", "clove", "can", "tin", "jar", "g", "kg", "litre", "litres", "millilitres", "millilitre"
]

quantity_separators = ['-', 'to', '–']

unit_standardization_mapping = {
    'g': 'g', 'gram': 'grams', 'g': 'grams', 'lb': 'lb', 'pound': 'lb', 'pounds': 'lb', 'kg': 'kg', 'kilogram': 'kg', 
    'kilograms': 'kg', 'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz', 'mg': 'mg', 'milligram': 'mg', 'milligrams': 'mg', 
    'l': 'l', 'liter': 'l', 'liters': 'l', 'litre': 'l', 'litres': 'l', 'ml': 'ml', 'milliliter': 'ml', 'milliliters': 'ml', 
    'millilitre': 'ml', 'millilitres': 'ml', 'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp', 
    'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp'
}

# Unit conversion constants
to_si_conversion = {
    'cups': {'ml': 236.588, 'g': 125.39},
    'cup': {'ml': 236.588, 'g': 125.39},
    'lb': {'g': 453.592},
    'oz': {'g': 28.3495}
} 

to_metric_conversion = {
    'ml': {'cups': 0.00422675, 'cup': 0.00422675},
    'l': {'cups': 4.22675, 'cup': 4.22675},
    'g': {'oz': 0.03527396, 'cup': 0.007975, 'cups': 0.007975, 'lb': 1}
}

# Fraction conversions
fraction_conversions = {
    "½": "1/2",
    "¼": "1/4",
    "¾": "3/4",
    "⅛": "1/8",
    "⅔": "2/3",
    "1/2": "0.5",
    "1/4": "0.25",
    "3/4": "0.75",
    "1/8": "0.125",
    "2/3": "0.667",
    "1/3": "0.333"
}


"""
We ❤ Recipes (and Code), but sometimes they don't see eye to eye!

The web is a wonderful (and sometimes wacky) place, and every website has its own unique way of presenting things. We've done our best to train our recipe detectives to handle all sorts of situations, but occasionally they might encounter a website that throws them a curveball.

If you ever find a recipe that doesn't seem quite right, don't be shy! Just send us a quick email at xxx@gmail.com and we'll be happy to put on our detective hats and see if we can fix it.

Thanks for your understanding, and happy cooking! ‍‍


Current Limitations:
-   All unit conversions involving cups are based on the density of water (for liquids) and flour (for solids) as a proof of concept. More accurate conversions based on specific ingredients have yet to be implemented. But its coming soon!
    It's important to consider the density of ingredients when converting units, as the conversion factor may vary depending on the type of ingredient being measured. For instance, while the metric system suggests 250 grams in 1 cup, this value can differ based on the density of the ingredient.
    In the meantime, you can find a comprehensive list of conversions for different ingredients from the web: https://www.allrecipes.com/article/cup-to-gram-conversions/
"""