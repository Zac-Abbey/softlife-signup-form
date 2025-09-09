# Main application file for the Signup Form project
# This Flask app renders HTML templates for the user interface and handles form submissions, admin dashboard, and CSV export.
import csv
from flask import Response
from flask import session
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Database setup: configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formdata.db'
db = SQLAlchemy(app)

# Database model for storing user form data
class UserForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    sex = db.Column(db.String(20), nullable=False)
    birthday = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Route for displaying the signup form
@app.route("/", methods=["GET"])
def index():
    # Get success or error messages from query parameters
    message = request.args.get("message")
    error = request.args.get("error")
    # Render the form template with messages
    return render_template("form.html", message=message, error=error)

# Route for handling form submission
@app.route("/submit", methods=["POST"])
def submit():
    # Get form data from POST request
    full_name = request.form["full_name"]
    phone_number = request.form["phone_number"]
    email = request.form["email"]
    sex = request.form["sex"]
    birthday = request.form["birthday"]

    # Check for duplicate email in the database
    if UserForm.query.filter_by(email=email).first():
        # Redirect back to form with error message
        return redirect(url_for("index", error="❌ Error: This email already exists in the database!"))

    # Create new user entry and save to database
    user = UserForm(full_name=full_name, phone_number=phone_number, email=email, sex=sex, birthday=birthday)
    db.session.add(user)
    db.session.commit()

    # Redirect back to form with success message
    return redirect(url_for("index", message="✅ Your Information has been submitted successfully!"))

# Secret key for admin session management
app.secret_key = "Masterkey123"  # Add a secret key for session management

# Admin login route
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    # Handles GET (show login form) and POST (process login) requests
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Hardcoded credentials for demonstration; replace with secure method in production
        if username == "admin" and password == "Masterkey123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "Invalid username or password."
    # Render login form and pass error message if present
    return render_template("admin_login.html", error=error)

# Protect the admin dashboard
@app.route("/admin")
def admin():
    # Only allow access if admin is logged in
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    message = request.args.get("message")
    error = request.args.get("error")
    users = UserForm.query.all()
    # Render admin template with all users and messages
    return render_template("admin.html", users=users, message=message, error=error)

# Admin logout route
@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

# Route for deleting a user
@app.route("/delete/<int:user_id>", methods=["POST"])
def delete(user_id):
    user = UserForm.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for("admin", message="User deleted successfully."))
    else:
        return redirect(url_for("admin", error="User not found."))

# Route for exporting user data to CSV
@app.route("/export")
def export():
    users = UserForm.query.all()

    # Function to generate CSV data in memory
    def generate():
        data = [["Full Name", "Phone Number", "Email", "Sex", "Birthday"]]
        for u in users:
            data.append([u.full_name, u.phone_number, u.email, u.sex, u.birthday])
        output=[]
        writer=csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        for row in data:
            writer.writerow(row)
        return "\n".join([",".join(row) for row in data])
    
    # Send CSV file as response
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=form_data.csv"},
    )

# Run the Flask app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)