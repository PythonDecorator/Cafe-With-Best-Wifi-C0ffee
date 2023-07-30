from flask import Flask,  render_template
from flask_bootstrap import Bootstrap
import os


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.app_context().push()

Bootstrap(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cafes")
def cafe():
    return render_template("cafe.html")


if __name__ == "__main__":
    app.run()
