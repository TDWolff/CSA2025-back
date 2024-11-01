from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
import subprocess
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
            
            sudo_password = os.getenv("SUDO_PASSWORD")
            if not sudo_password:
                return jsonify({"error": "Sudo password not found"}), 500
            
            try:
                # Add the user with a command line utility
                subprocess.run(["sudo", "-S", "useradd", "-m", username], input=sudo_password + '\n', text=True, check=True)

                # Set the password for the user
                subprocess.run(f"echo '{username}:{password}' | sudo -S chpasswd", input=sudo_password + '\n', shell=True, text=True, check=True)

                return jsonify({"message": "User created successfully"}), 201
            except subprocess.CalledProcessError as e:
                return jsonify({"error": f"Failed to create user: {str(e)}"}), 500

# Register the endpoint
api.add_resource(UserAPI.CreateUser, '/create-user')