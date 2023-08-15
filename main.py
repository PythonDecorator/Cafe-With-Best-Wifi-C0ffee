from flask import Flask, render_template, request, url_for, redirect, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, URLField, SelectField
from wtforms.validators import Length, DataRequired, URL
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from flask import abort
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.app_context().push()

Bootstrap(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(f"{basedir}\\instance", 'cafe_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ADMIN ONLY DECORATOR
def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return func(*args, **kwargs)

    return decorated_function


# DATABASE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def to_dict(self) -> dict:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Cafe(db.Model):
    __tablename__ = "cafes"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default="datetime.utcnow")
    name = db.Column(db.String(50), nullable=False)
    has_wifi = db.Column(db.String, nullable=False)
    wifi_strength = db.Column(db.String, nullable=True)
    coffee_price = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String, nullable=False)
    seats = db.Column(db.String(10), nullable=False)
    has_sockets = db.Column(db.String(10), nullable=False)
    map_url = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)
    website = db.Column(db.String, nullable=True)

    def to_dict(self) -> dict:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# db.create_all()


# FORM
class AddCafeForm(FlaskForm):
    name = StringField('Name', [DataRequired(), Length(min=3, max=50)])
    location = StringField('Name', [DataRequired(), Length(min=3, max=20)])
    wifi_strength = SelectField('Wifi Strength',
                                choices=[('Poor', 'Poor'), ('Good', 'Good'), ('Excellent', 'Excellent'),
                                         ('None', 'None')])
    coffee_price = StringField('Coffee Price', [DataRequired(), Length(min=1, max=5)])
    seats = StringField('Numbers Of Seats', [DataRequired(), Length(min=3, max=50)])
    img_url = URLField("Image URL", validators=[DataRequired(), URL()])
    map_url = URLField('Map Url', [DataRequired(), URL()])
    website = URLField('Website', [DataRequired(), URL()])
    submit = SubmitField("Add Cafe")


class LoginForm(FlaskForm):
    username = StringField('User Name', [DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password', [DataRequired(), Length(min=8, max=50)])
    submit = SubmitField("Login")


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("That user name does not exist, please try again.")
            return redirect(url_for('login'))
        elif user.password != password:
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('cafe'))
    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/cafes")
def cafe():
    all_cafe_data = db.session.query(Cafe).all()
    return render_template("cafe_view.html", all_cafe_data=all_cafe_data, logged_in=current_user.is_authenticated,
                           current_user=current_user)


@app.route("/add", methods=["GET", "POST"])
@login_required
@admin_only
def add_cafe():
    add_cafe_form = AddCafeForm()
    if request.method == "POST" and add_cafe_form.validate_on_submit():
        wifi_strength = request.form.get('wifi_strength')
        has_wifi = "Yes"
        if wifi_strength == "None":
            has_wifi = "No"

        new_cafe = Cafe(
            date=datetime.now().date(),
            name=request.form.get("name"),
            has_wifi=has_wifi,
            wifi_strength=wifi_strength,
            coffee_price=request.form.get('coffee_price'),
            location=request.form.get('location'),
            seats=request.form.get('seats'),
            has_sockets=request.form['gridRadios'],
            img_url=request.form.get('img_url'),
            map_url=request.form.get('map_url'),
            website=request.form.get('website'),
        )

        db.session.add(new_cafe)
        db.session.commit()
        flash("New Cafe have been added successfully")
        return redirect(url_for("cafe"))
    return render_template("add_cafe.html", form=add_cafe_form)


@app.route("/delete/<int:cafe_id>")
@login_required
@admin_only
def delete(cafe_id):
    post_to_delete = Cafe.query.get(int(cafe_id))
    db.session.delete(post_to_delete)
    db.session.commit()
    flash(f"Cafe with id {cafe_id}, have been deleted.")
    return redirect(url_for('cafe'))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
