"""
blueprints/auth/routes.py
"""

from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from . import bp
from .forms import RegisterForm, LoginForm, CheckStatusForm
from extensions import db
from models import User, StaffProfile, authenticate_staff


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("That username is already taken.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash("That email is already registered.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # populate user.id before creating a StaffProfile FK

        if form.role.data == "staff":
            profile = StaffProfile(
                user_id=user.id,
                bio=form.bio.data,
                experience_years=form.experience_years.data or 0,
                certification=form.certification.data,
            )
            db.session.add(profile)

        db.session.commit()

        if form.role.data == "staff":
            flash(
                "Registered! Your account needs admin approval before you can "
                "log in. Use 'Check approval status' any time — once approved "
                "it will show you the Staff ID you need to log in.",
                "info",
            )
        else:
            flash("Registered successfully! You can log in now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        role = form.role.data

        if role == "admin":
            user = User.query.filter_by(username=form.admin_username.data, role="admin").first()
            if not user or not user.check_password(form.admin_password.data):
                flash("Invalid admin username or password.", "danger")
                return render_template("auth/login.html", form=form)
            if user.is_blacklisted:
                flash("This account has been blacklisted.", "danger")
                return render_template("auth/login.html", form=form)
            login_user(user)
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for("admin.dashboard"))

        if role == "staff":
            if not (form.staff_username.data and form.staff_password.data and form.staff_id.data):
                flash("Username, password, and Staff ID are all required.", "danger")
                return render_template("auth/login.html", form=form)
            try:
                user = authenticate_staff(
                    form.staff_username.data, form.staff_password.data, form.staff_id.data
                )
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("auth/login.html", form=form)
            login_user(user)
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for("index"))  # staff.dashboard arrives in Phase 6

        # role == "trekker"
        user = User.query.filter_by(username=form.trekker_username.data, role="trekker").first()
        if not user or not user.check_password(form.trekker_password.data):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html", form=form)
        if user.is_blacklisted:
            flash("This account has been blacklisted.", "danger")
            return render_template("auth/login.html", form=form)
        login_user(user)
        flash(f"Welcome back, {user.full_name}!", "success")
        return redirect(url_for("index"))  # user.browse_treks arrives in Phase 7

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/staff/check-status", methods=["GET", "POST"])
def check_status():
    form = CheckStatusForm()
    result = None
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.identifier.data) | (User.email == form.identifier.data)
        ).first()

        if not user or user.role != "staff" or not user.staff_profile:
            result = {"found": False}
        else:
            profile = user.staff_profile
            result = {
                "found": True,
                "status": profile.approval_status,
                "staff_id": profile.staff_id,
            }

    return render_template("auth/check_status.html", form=form, result=result)