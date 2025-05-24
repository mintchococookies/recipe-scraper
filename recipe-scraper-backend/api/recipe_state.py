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

# Retrieve and store the recipe state in the session
def get_recipe_state(session):
    if 'recipe_state' not in session:
        session['recipe_state'] = RecipeState().to_dict()
    
    recipe_state = RecipeState()
    recipe_state.from_dict(session['recipe_state'])
    session.modified = True
    
    return recipe_state

def save_recipe_state(session, recipe_state):
    session['recipe_state'] = recipe_state.to_dict()