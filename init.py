from flask import Flask, render_template, request, redirect, url_for, flash
from flask_cors import CORS

app = Flask(__name__)

# Set up cors for allowing to all requests
cors = CORS(app, supports_credentials=True, origins=["*"])
port = 8763
selftitle = "CSA_2025"

