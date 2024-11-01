from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
import subprocess
import re

user_api = Blueprint('user_api', __name__, url_prefix='/api')
api = Api(user_api)

# Helper function to sanitize and validate user inputs
def is_valid_username(username):
    return re.match("^[a-zA-Z0-9_.-]+$", username) is not None

class UserAPI(Resource):
    class CreateUser(Resource):
        def post(self):
            data = request.get_json()
            
            # Extract and validate username and password
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                return jsonify({"error": "Username and password are required"}), 400
            
            if not is_valid_username(username):
                return jsonify({"error": "Invalid username format"}), 400
            
            try:
                # Add the user with a command line utility
                subprocess.run(["sudo", "useradd", "-m", username], check=True)

                # Set the password for the user
                subprocess.run(f"echo '{username}:{password}' | sudo chpasswd", shell=True, check=True)

                return jsonify({"message": "User created successfully"}), 201
            except subprocess.CalledProcessError as e:
                return jsonify({"error": f"Failed to create user: {str(e)}"}), 500

# Register the endpoint
api.add_resource(UserAPI.CreateUser, '/create-user')