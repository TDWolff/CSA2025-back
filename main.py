from flask import Flask, render_template
from init import app, port, selftitle
from api.user import *

app = Flask(__name__)

app.register_blueprint(user_api)

@app.route('/')
def home():
    title = selftitle
    return render_template('index.html', title=title)

@app.route('/landing')
def landing():
    title = selftitle
    return render_template('landing.html', title=title)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)