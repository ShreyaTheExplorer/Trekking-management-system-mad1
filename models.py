from datetime import datetime, date, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db  # db = SQLAlchemy() defined in extensions.py


# ---------------------------------------------------------------------------
# USER  (Admin / Staff / Trekker — common auth fields live here)
# ---------------------------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Nullable now: a Google-only trekker account has no local password.
    # Local accounts (admin/staff always, trekkers optionally) must set this.
    password_hash = db.Column(db.String(255), nullable=True)

    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))

    role = db.Column(db.String(10), nullable=False, default="trekker")
    # allowed values: 'admin', 'staff', 'trekker'

    # --- Google OAuth (trekkers only — see auth_provider in_("local","google") below) ---
    auth_provider = db.Column(db.String(10), nullable=False, default="local")
    # allowed values: 'local', 'google'
    google_id = db.Column(db.String(255), unique=True, nullable=True)  # Google's "sub" claim
    profile_pic_url = db.Column(db.String(255), nullable=True)

    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # relationships
    staff_profile = db.relationship(
        "StaffProfile", back_populates="user", uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="StaffProfile.user_id",
    )
    bookings = db.relationship(
        "Booking", back_populates="user", cascade="all, delete-orphan"
    )
    treks_created = db.relationship(
        "Trek", back_populates="created_by_admin",
        foreign_keys="Trek.created_by"
    )

    __table_args__ = (
        db.CheckConstraint("role IN ('admin','staff','trekker')", name="ck_user_role"),
        db.CheckConstraint("auth_provider IN ('local','google')", name="ck_user_auth_provider"),
        # Only trekkers are allowed to use Google sign-in; admin/staff are always local.
        db.CheckConstraint(
            "auth_provider = 'local' OR role = 'trekker'",
            name="ck_google_only_for_trekkers"
        ),
    )

    # --- password helpers ---
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if not self.password_hash:
            # Google-only account — there is no local password to check.
            return False
        return check_password_hash(self.password_hash, raw_password)

    # --- convenience flags ---
    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_staff(self):
        return self.role == "staff"

    @property
    def is_trekker(self):
        return self.role == "trekker"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# ---------------------------------------------------------------------------
# STAFF PROFILE  (extra fields only relevant to staff, 1:1 with User)
# ---------------------------------------------------------------------------
class StaffProfile(db.Model):
    __tablename__ = "staff_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    bio = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    certification = db.Column(db.String(200))

    approval_status = db.Column(db.String(10), nullable=False, default="pending")
    # allowed values: 'pending', 'approved', 'rejected'

    # Issued by the system the moment admin approves — NULL until then.
    # Staff must supply this value (in addition to username+password) at login.
    staff_id = db.Column(db.String(20), unique=True, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", back_populates="staff_profile", foreign_keys=[user_id])
    treks_assigned = db.relationship("Trek", back_populates="assigned_staff")

    __table_args__ = (
        db.CheckConstraint(
            "approval_status IN ('pending','approved','rejected')",
            name="ck_staff_approval_status"
        ),
    )

    @property
    def can_access_dashboard(self):
        return self.approval_status == "approved" and not self.user.is_blacklisted

    def __repr__(self):
        return f"<StaffProfile user_id={self.user_id} status={self.approval_status}>"


# ---------------------------------------------------------------------------
# TREK
# ---------------------------------------------------------------------------
class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)   # Easy / Moderate / Hard
    duration_days = db.Column(db.Integer, nullable=False)

    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    month = db.Column(db.String(15))     # e.g. 'October' — used for filter UX
    season = db.Column(db.String(15))    # e.g. 'Winter' — used for filter UX

    price = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255))  # path/url to hero image

    status = db.Column(db.String(15), nullable=False, default="Pending")
    # allowed values: Pending, Approved, Open, Closed, Completed

    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("staff_profiles.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # relationships
    assigned_staff = db.relationship("StaffProfile", back_populates="treks_assigned")
    created_by_admin = db.relationship(
        "User", back_populates="treks_created", foreign_keys=[created_by]
    )
    bookings = db.relationship("Booking", back_populates="trek", cascade="all, delete-orphan")
    images = db.relationship("TrekImage", back_populates="trek", cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint("difficulty IN ('Easy','Moderate','Hard')", name="ck_trek_difficulty"),
        db.CheckConstraint(
            "status IN ('Pending','Approved','Open','Closed','Completed')",
            name="ck_trek_status"
        ),
        db.CheckConstraint("available_slots >= 0", name="ck_trek_slots_nonnegative"),
        db.CheckConstraint("available_slots <= total_slots", name="ck_trek_slots_within_total"),
    )

    @property
    def is_bookable(self):
        return self.status == "Open" and self.available_slots > 0

    def __repr__(self):
        return f"<Trek {self.name} [{self.status}] slots={self.available_slots}/{self.total_slots}>"


# ---------------------------------------------------------------------------
# TREK IMAGE  (optional gallery, keeps Trek table lean)
# ---------------------------------------------------------------------------
class TrekImage(db.Model):
    __tablename__ = "trek_images"

    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(150))

    trek = db.relationship("Trek", back_populates="images")


# ---------------------------------------------------------------------------
# BOOKING
# ---------------------------------------------------------------------------
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)

    booking_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    num_people = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(10), nullable=False, default="Booked")
    # allowed values: Booked, Cancelled, Completed

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="bookings")
    trek = db.relationship("Trek", back_populates="bookings")

    __table_args__ = (
        db.CheckConstraint("status IN ('Booked','Cancelled','Completed')", name="ck_booking_status"),
        db.CheckConstraint("num_people > 0", name="ck_booking_num_people_positive"),
    )

    def __repr__(self):
        return f"<Booking user={self.user_id} trek={self.trek_id} status={self.status}>"


# ---------------------------------------------------------------------------
# Helper: booking creation with overbooking prevention
# (call this from your route instead of inserting a Booking directly)
# ---------------------------------------------------------------------------
def create_booking(user, trek, num_people=1):
    """
    Atomically validates and creates a booking, decrementing available_slots.
    Raises ValueError with a user-facing message on any rule violation.
    """
    if user.is_blacklisted:
        raise ValueError("Your account has been blacklisted and cannot book treks.")
    if trek.status != "Open":
        raise ValueError("This trek is not open for booking.")
    if trek.available_slots < num_people:
        raise ValueError("Not enough slots available for this trek.")

    trek.available_slots -= num_people
    booking = Booking(user_id=user.id, trek_id=trek.id, num_people=num_people)
    db.session.add(booking)
    db.session.add(trek)
    db.session.commit()
    return booking


def cancel_booking(booking):
    """Restores slots if the trek hasn't already started/completed."""
    if booking.status != "Booked":
        raise ValueError("Only active bookings can be cancelled.")
    booking.status = "Cancelled"
    if booking.trek.status in ("Open", "Approved"):
        booking.trek.available_slots += booking.num_people
    db.session.commit()


# ---------------------------------------------------------------------------
# Helper: approve a staff registration → generates the unique staff_id
# ---------------------------------------------------------------------------
def approve_staff(staff_profile, admin_user):
    """
    Admin-only action. Generates a unique staff_id (only happens here,
    never at registration) and flips the profile to 'approved'.
    """
    if admin_user.role != "admin":
        raise ValueError("Only an admin can approve staff.")
    if staff_profile.approval_status == "approved" and staff_profile.staff_id:
        return staff_profile  # already approved, idempotent

    staff_profile.approval_status = "approved"
    staff_profile.approved_at = datetime.now(timezone.utc)
    staff_profile.approved_by = admin_user.id
    db.session.flush()  # ensures staff_profile.id is populated

    # Deterministic, unique by construction: e.g. "STF-00007"
    staff_profile.staff_id = f"STF-{staff_profile.id:05d}"

    db.session.commit()
    return staff_profile


def reject_staff(staff_profile):
    staff_profile.approval_status = "rejected"
    staff_profile.staff_id = None
    db.session.commit()
    return staff_profile


# ---------------------------------------------------------------------------
# Helper: staff login — checks username/password AND the issued staff_id
# ---------------------------------------------------------------------------
def authenticate_staff(username, password, staff_id_input):
    """
    Returns the User on success, or raises ValueError with a message
    suitable for displaying back to the staff member.
    """
    user = User.query.filter_by(username=username, role="staff").first()
    if not user or not user.check_password(password):
        raise ValueError("Invalid username or password.")

    profile = user.staff_profile
    if not profile or profile.approval_status != "approved":
        raise ValueError("Your registration is still pending admin approval.")

    if user.is_blacklisted:
        raise ValueError("Your account has been blacklisted.")

    if not profile.staff_id or profile.staff_id.strip() != staff_id_input.strip():
        raise ValueError("Staff ID does not match our records.")

    return user


# ---------------------------------------------------------------------------
# Helper: Google sign-in — find-or-create a trekker account
# ---------------------------------------------------------------------------
def get_or_create_google_user(google_id, email, full_name, profile_pic_url=None):
    """
    Call this after verifying the Google ID token server-side (Authlib/
    Flask-Dance). Links to an existing local account with the same email
    if one exists; otherwise creates a new Google-auth trekker account.
    """
    user = User.query.filter_by(google_id=google_id).first()
    if user:
        return user

    user = User.query.filter_by(email=email).first()
    if user:
        # Existing local account with the same (verified) email — link it.
        user.google_id = google_id
        user.auth_provider = "google" if not user.password_hash else user.auth_provider
        if profile_pic_url:
            user.profile_pic_url = profile_pic_url
        db.session.commit()
        return user

    # Brand-new Google-only trekker account.
    base_username = email.split("@")[0]
    username = base_username
    suffix = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{suffix}"
        suffix += 1

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role="trekker",
        auth_provider="google",
        google_id=google_id,
        profile_pic_url=profile_pic_url,
        password_hash=None,
    )
    db.session.add(user)
    db.session.commit()
    return user


# ---------------------------------------------------------------------------
# One-time admin seed — call once at startup (idempotent)
# ---------------------------------------------------------------------------
def seed_admin(username="admin", email="admin@trek.com", password="Admin@123"):
    existing = User.query.filter_by(role="admin").first()
    if existing:
        return existing
    admin = User(
        username=username,
        email=email,
        full_name="System Administrator",
        role="admin",
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    return admin