"""
blueprints/admin/routes.py
"""

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user

from . import bp
from .forms import TrekForm, AssignStaffForm
from extensions import db
from models import User, StaffProfile, Trek, Booking, approve_staff, reject_staff
from utils import admin_required


# ── DASHBOARD ──────────────────────────────────────────────────────────────

@bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {
        "total_treks":     Trek.query.count(),
        "open_treks":      Trek.query.filter_by(status="Open").count(),
        "total_trekkers":  User.query.filter_by(role="trekker").count(),
        "total_staff":     User.query.filter_by(role="staff").count(),
        "pending_staff":   StaffProfile.query.filter_by(approval_status="pending").count(),
        "total_bookings":  Booking.query.count(),
        "active_bookings": Booking.query.filter_by(status="Booked").count(),
    }
    recent_treks    = Trek.query.order_by(Trek.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_treks=recent_treks,
        recent_bookings=recent_bookings,
    )


# ── TREK CRUD ───────────────────────────────────────────────────────────────

@bp.route("/treks")
@admin_required
def list_treks():
    treks = Trek.query.order_by(Trek.created_at.desc()).all()
    return render_template("admin/treks.html", treks=treks)


@bp.route("/treks/new", methods=["GET", "POST"])
@admin_required
def new_trek():
    form = TrekForm()
    if form.validate_on_submit():
        trek = Trek(
            name=form.name.data,
            location=form.location.data,
            difficulty=form.difficulty.data,
            duration_days=form.duration_days.data,
            total_slots=form.total_slots.data,
            available_slots=form.total_slots.data,   # always full on creation
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            month=form.month.data or form.start_date.data.strftime("%B"),
            season=form.season.data or "",
            price=form.price.data or 0.0,
            description=form.description.data,
            cover_image=form.cover_image.data or "",
            status=form.status.data,
            created_by=current_user.id,
        )
        db.session.add(trek)
        db.session.commit()
        flash(f"Trek '{trek.name}' created successfully.", "success")
        return redirect(url_for("admin.list_treks"))
    return render_template("admin/trek_form.html", form=form, trek=None)


@bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = TrekForm(obj=trek)
    if form.validate_on_submit():
        trek.name          = form.name.data
        trek.location      = form.location.data
        trek.difficulty    = form.difficulty.data
        trek.duration_days = form.duration_days.data
        trek.total_slots   = form.total_slots.data
        # Allow admin to manually correct available_slots if needed.
        if form.available_slots.data is not None:
            trek.available_slots = form.available_slots.data
        trek.start_date    = form.start_date.data
        trek.end_date      = form.end_date.data
        trek.month         = form.month.data or form.start_date.data.strftime("%B")
        trek.season        = form.season.data or trek.season or ""
        trek.price         = form.price.data or 0.0
        trek.description   = form.description.data
        trek.cover_image   = form.cover_image.data or ""
        trek.status        = form.status.data
        db.session.commit()
        flash(f"Trek '{trek.name}' updated.", "success")
        return redirect(url_for("admin.list_treks"))
    return render_template("admin/trek_form.html", form=form, trek=trek)


@bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    name = trek.name
    db.session.delete(trek)
    db.session.commit()
    flash(f"Trek '{name}' deleted.", "info")
    return redirect(url_for("admin.list_treks"))


# ── ASSIGN STAFF TO TREK ───────────────────────────────────────────────────

@bp.route("/treks/<int:trek_id>/assign", methods=["GET", "POST"])
@admin_required
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    eligible = (
        StaffProfile.query
        .join(User, StaffProfile.user_id == User.id)
        .filter(
            StaffProfile.approval_status == "approved",
            User.is_blacklisted == False,
        )
        .all()
    )

    form = AssignStaffForm()
    # 0 = unassign option
    form.staff_profile_id.choices = (
        [(0, "-- Unassign --")]
        + [(p.id, f"{p.user.full_name}  ({p.staff_id})") for p in eligible]
    )

    if form.validate_on_submit():
        chosen = form.staff_profile_id.data
        trek.assigned_staff_id = chosen if chosen != 0 else None
        db.session.commit()
        msg = (
            f"Staff assigned to '{trek.name}'."
            if trek.assigned_staff_id
            else f"Staff unassigned from '{trek.name}'."
        )
        flash(msg, "success")
        return redirect(url_for("admin.list_treks"))

    # Pre-select the current assignment on GET.
    if trek.assigned_staff_id:
        form.staff_profile_id.data = trek.assigned_staff_id
    return render_template("admin/assign_staff.html", form=form, trek=trek, eligible=eligible)


# ── STAFF APPROVAL ─────────────────────────────────────────────────────────

@bp.route("/staff/pending")
@admin_required
def pending_staff():
    pending = StaffProfile.query.filter_by(approval_status="pending").all()
    return render_template("admin/staff_pending.html", pending=pending)


@bp.route("/staff/<int:profile_id>/approve", methods=["POST"])
@admin_required
def approve_staff_member(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    approve_staff(profile, current_user)
    flash(
        f"Approved {profile.user.full_name}. "
        f"Their Staff ID is: {profile.staff_id}  — share this with them.",
        "success",
    )
    return redirect(url_for("admin.pending_staff"))


@bp.route("/staff/<int:profile_id>/reject", methods=["POST"])
@admin_required
def reject_staff_member(profile_id):
    profile = StaffProfile.query.get_or_404(profile_id)
    name = profile.user.full_name
    reject_staff(profile)
    flash(f"Registration for {name} rejected.", "warning")
    return redirect(url_for("admin.pending_staff"))


# ── STAFF LIST + BLACKLIST ─────────────────────────────────────────────────

@bp.route("/staff")
@admin_required
def list_staff():
    q    = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = User.query.filter_by(role="staff")
    if q:
        query = query.filter(
            (User.username.ilike(f"%{q}%")) | (User.full_name.ilike(f"%{q}%"))
        )
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/staff.html", pagination=pagination, q=q)


@bp.route("/staff/<int:user_id>/blacklist", methods=["POST"])
@admin_required
def blacklist_staff(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != "staff":
        abort(403)
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    action = "blacklisted" if user.is_blacklisted else "reinstated"
    flash(f"Staff member {user.username} has been {action}.", "info")
    return redirect(url_for("admin.list_staff"))


# ── USER (TREKKER) LIST + BLACKLIST ────────────────────────────────────────

@bp.route("/users")
@admin_required
def list_users():
    q    = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = User.query.filter_by(role="trekker")
    if q:
        query = query.filter(
            (User.username.ilike(f"%{q}%")) | (User.full_name.ilike(f"%{q}%"))
        )
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/users.html", pagination=pagination, q=q)


@bp.route("/users/<int:user_id>/blacklist", methods=["POST"])
@admin_required
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != "trekker":
        abort(403)
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    action = "blacklisted" if user.is_blacklisted else "reinstated"
    flash(f"User {user.username} has been {action}.", "info")
    return redirect(url_for("admin.list_users"))