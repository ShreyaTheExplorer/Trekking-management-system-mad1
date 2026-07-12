"""
utils.py — shared decorators used across blueprints.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required


def admin_required(view_func):
    """Blocks any non-admin from reaching the route."""
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped


def staff_required(view_func):
    """
    Blocks non-staff users (403) and staff who haven't been approved yet or
    who are blacklisted (flash + redirect to login so they see the reason).
    """
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_staff:
            abort(403)
        profile = current_user.staff_profile
        if not profile or not profile.can_access_dashboard:
            flash(
                "Your account is pending admin approval or has been blacklisted. "
                "Use the 'Check approval status' page to see your current status.",
                "warning",
            )
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped





def trekker_required(view_func):
    """
    Only registered, non-blacklisted trekkers can access.
    Admin / staff are blocked (they should not make bookings).
    """
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_trekker:
            abort(403)
        if current_user.is_blacklisted:
            flash("Your account has been blacklisted.", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped