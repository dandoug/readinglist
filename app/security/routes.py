from flask import current_app as app, render_template_string, request, render_template, redirect, url_for, \
    jsonify
from flask_login import login_required
from flask_security import auth_required, roles_required, hash_password

from .. import db, user_datastore


@app.route("/admin")
@auth_required()
def admin():
    return render_template_string("Hello {{ current_user.email }}")


@app.errorhandler(403)
def access_forbidden(e):
    return jsonify({'error': 'You do not have permission to access this resource'}), 403


@app.route('/registerx', methods=['GET', 'POST'])
@login_required  # Ensure only logged-in users can access
@roles_required('admin')  # Restrict to users with the 'admin' role
def custom_register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Here you can set the default role for the new user, e.g., 'user':
        user = user_datastore.create_user(
            email=email,
            password=hash_password(password))
        db.session.commit()
        return redirect(url_for(app.config.get('APPLICATION_ROOT', '/')))  # Redirect to home after registering

    # Render the registration form if GET method
    return render_template(app.config.get('SECURITY_REGISTER_USER_TEMPLATE'))
