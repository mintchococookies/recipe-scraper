from flask_restx import fields

def create_models(api):
    # Define models for the input payloads
    recipe_url_model = api.model('RecipeURL', {
        'recipe_url': fields.String(required=True, description='URL of the recipe')
    })

    unit_type_model = api.model('UnitType', {
        'unit_type': fields.String(required=True, description='Either "si" or "metric" ')
    })

    serving_size_model = api.model('ServingSize', {
        'serving_size': fields.String(required=True, description='Numeric value')
    })

    return recipe_url_model, unit_type_model, serving_size_model 