from flask import Blueprint, request, jsonify, make_response
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
            username = data.get("username").lower()
            password = data.get("password")
            
            if not username or not password:
                return make_response(jsonify({"error": "Username and password are required"}), 400)
            
            if not is_valid_username(username):
                return make_response(jsonify({"error": "Invalid username format"}), 400)
            
            sudo_password = os.getenv("SUDO_PASSWORD")
            if not sudo_password:
                return make_response(jsonify({"error": "Sudo password not found"}), 500)
            
            try:
                # Create the shared directory if it doesn't exist
                shared_dir = "/home/shared"
                subprocess.run(["sudo", "-S", "mkdir", "-p", shared_dir], input=sudo_password + '\n', text=True, check=True)
                
                # Set the group ownership and permissions for the shared directory
                common_group = "sharedgroup"
                subprocess.run(["sudo", "-S", "chown", f":{common_group}", shared_dir], input=sudo_password + '\n', text=True, check=True)
                subprocess.run(["sudo", "-S", "chmod", "2775", shared_dir], input=sudo_password + '\n', text=True, check=True)
                
                # Add the user with a command line utility and set the home directory to the shared directory
                result = subprocess.run(["sudo", "-S", "useradd", "-m", "-d", shared_dir, username], input=sudo_password + '\n', text=True, capture_output=True)
                if result.returncode != 0:
                    if "already exists" in result.stderr:
                        return make_response(jsonify({"error": "User already exists"}), 400)
                    else:
                        return make_response(jsonify({"error": f"Failed to create user: {result.stderr}"}), 500)
            
                # Set the password for the user
                subprocess.run(f"echo '{username}:{password}' | sudo -S chpasswd", input=sudo_password + '\n', shell=True, text=True, check=True)
            
                # Add the user to the sudo group
                subprocess.run(["sudo", "-S", "usermod", "-aG", "sudo", username], input=sudo_password + '\n', text=True, check=True)
                
                # Add the user to the common group
                subprocess.run(["sudo", "-S", "usermod", "-aG", common_group, username], input=sudo_password + '\n', text=True, check=True)
                
                # Set the default shell to /bin/bash
                subprocess.run(["sudo", "-S", "chsh", "-s", "/bin/bash", username], input=sudo_password + '\n', text=True, check=True)
            
                # Copy default shell configuration files to the shared directory
                subprocess.run(["sudo", "-S", "cp", "/etc/skel/.bashrc", f"{shared_dir}/.bashrc"], input=sudo_password + '\n', text=True, check=True)
                subprocess.run(["sudo", "-S", "cp", "/etc/skel/.profile", f"{shared_dir}/.profile"], input=sudo_password + '\n', text=True, check=True)
                subprocess.run(["sudo", "-S", "chown", f"{username}:{common_group}", f"{shared_dir}/.bashrc"], input=sudo_password + '\n', text=True, check=True)
                subprocess.run(["sudo", "-S", "chown", f"{username}:{common_group}", f"{shared_dir}/.profile"], input=sudo_password + '\n', text=True, check=True)
                
                # Call the awsuser.sh script to create the AWS IAM user
                script_path = os.path.join(os.path.dirname(__file__), '../../awsuser.sh')
                subprocess.run(["/bin/bash", script_path, username, password], check=True)
            
                return make_response(jsonify({"message": "User created successfully"}), 201)
            except subprocess.CalledProcessError as e:
                return make_response(jsonify({"error": f"Failed to create user: {str(e)}"}), 500)

    class DeleteUser(Resource):
        def delete(self):
            data = request.get_json()
            
            # Extract and validate username
            username = data.get("username").lower()
            
            if not username:
                return make_response(jsonify({"error": "Username is required"}), 400)
            
            if not is_valid_username(username):
                return make_response(jsonify({"error": "Invalid username format"}), 400)
            
            sudo_password = os.getenv("SUDO_PASSWORD")
            if not sudo_password:
                return make_response(jsonify({"error": "Sudo password not found"}), 500)
            
            try:
                # Forcefully terminate all processes for the user
                subprocess.run(["sudo", "-S", "pkill", "-u", username], input=sudo_password + '\n', text=True, check=True)
                
                # Delete the user with a command line utility
                subprocess.run(["sudo", "-S", "userdel", "-r", username], input=sudo_password + '\n', text=True, check=True)

                return make_response(jsonify({"message": "User deleted successfully"}), 200)
            except subprocess.CalledProcessError as e:
                return make_response(jsonify({"error": f"Failed to delete user: {str(e)}"}), 500)

# Register the endpoints
api.add_resource(UserAPI.CreateUser, '/create-user')
api.add_resource(UserAPI.DeleteUser, '/delete-user')