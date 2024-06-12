from flask import Flask, request
from flask_restx import Api, Resource, fields
import jwt
import datetime
import os
from functools import wraps

app = Flask(__name__)
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key') # for production
app.config['SECRET_KEY'] = 'your_secret_key'  # for testing/dev
authorizations = {
    'basicAuth': {
        'type': 'basic'
    }
}
api = Api(app, authorizations=authorizations)

# Define a model for the login request body (for Swagger UI clarity)
login_model = api.model('Login', {
    'username': fields.String(required=True, description='The username'),
    'password': fields.String(required=True, description='The password')
})

def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # Token expiration time
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_credentials(username, password):
    # Replace with actual authentication mechanism (don't store passwords in plain text)
    if username == 'user' and password == 'pw':
        return True
    return False

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', None)
        print(f"Received Authorization header: {token}")
        if not token:
            return {'message': 'Missing authorization token'}, 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['username']
        except jwt.DecodeError:
            return {'message': 'Invalid token'}, 401

        return f(current_user, *args, **kwargs)

    return decorated

@api.route('/login')
class UserLogin(Resource):
    @api.expect(login_model)  # Optional for Swagger UI clarity
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
