"""
app.py — application factory.

Run locally with:
    python app.py
or, for the CLI seed command:
    flask --app app seed-db
"""

import click
from flask import Flask, redirect, url_for
from flask_login import current_user

from config import Config
from extensions import db, login_manager


from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)          # makes csrf_token() available in every template
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from extensions import oauth
    oauth.init_app(app)
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )


    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # All four blueprints, as specified.
    from blueprints.auth import bp as auth_bp
    from blueprints.admin import bp as admin_bp
    from blueprints.staff import bp as staff_bp
    from blueprints.user import bp as user_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    @app.cli.command("seed-db")
    def seed_db():
        """flask --app app seed-db -> creates tables + the admin user."""
        from models import seed_admin
        db.create_all()
        admin = seed_admin()
        click.echo(f"Database ready. Admin user: {admin.username}")

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        if current_user.is_staff:
            return redirect(url_for("staff.dashboard"))
        if current_user.is_trekker:
            return redirect(url_for("user.dashboard"))
        return (
            f"Logged in as {current_user.full_name} ({current_user.role}). "
            "Dashboard for this role arrives in a later phase."
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)