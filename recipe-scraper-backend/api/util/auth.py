from flask import Flask, request
from flask_restx import Api, Resource, fields
from flask_compress import Compress
import jwt
import datetime
import os
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from .metrics import track_latency

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('RECIPE_SCRAPER_SESSION_KEY')

# Initialize Flask-Compress with some basic configuration
Compress(app)
app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']
app.config['COMPRESS_LEVEL'] = 6  # Compression level (1-9, 9 being highest compression)

authorizations = {
    'basicAuth': {
        'type': 'basic'
    }
}

api = Api(app, authorizations=authorizations)

# Login model for Swagger UI docs
login_model = api.model('Login', {
    'username': fields.String(required=True, description='The username'),
    'password': fields.String(required=True, description='The password')
})

def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # Token expiration time
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

def verify_credentials(username, password):
    expected_username = os.getenv('RECIPE_SCRAPER_USERNAME')
    expected_password = os.getenv('RECIPE_SCRAPER_PASSWORD')
    if username == expected_username and password == expected_password:
        return True
    return False

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', None)
        # logging.info(f"Received Authorization header: {token}")
        if not token:
            return {'message': 'Missing authorization token'}, 401

        try:
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            current_user = data['username']
        except jwt.DecodeError:
            return {'message': 'Invalid token'}, 401

        return f(current_user, *args, **kwargs)

    return decorated

@api.route('/login')
class UserLogin(Resource):
    @api.expect(login_model)
    @track_latency('login')
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'message': 'Missing username or password'}, 401

        if not verify_credentials(username, password):
            return {'message': 'Invalid credentials'}, 401

        token = generate_token(username)

        return {'token': token}
