# Trekking-management-system-mad1
Python Flask based application for treks booking for trekkers and management by authorities.

## 1. Problem Statement
Managing outdoor trekking operations, guide allocations, and trekker bookings manually or via fragmented tools leads to several operational challenges:
- **Overbooking and Under-allocation**: Real-time slot management is difficult when multiple trekkers attempt to book simultaneously, causing either overbooking or wasted capacity.
- **Unverified/Uncoordinated Staff**: Coordinating guide assignments without structured approval processes can lead to unqualified personnel guiding high-altitude treks.
- **Roster & Blacklist Gaps**: A lack of centralized tracking makes it hard to manage active participant rosters, handle cancellations (with auto-returned slots), and enforce safety rules (such as immediately locking out blacklisted/misbehaving users).
- **Poor User Experience**: Trekkers lack personalized recommendations based on past locations or difficulty preferences, making it harder to find suitable treks.

The Trekking Management System is a centralized platform designed to solve these issues, enabling seamless administration, secure booking control, and real-time guide workflows.

---

## 2. Approach
The application is structured as a modular, MVC-pattern Python Flask web application. Key design decisions include:
- **Modular Architecture (Flask Blueprints)**: Segmented code into role-based controllers (`admin`, `staff`, `user`, and `auth`) to keep code clean, readable, and highly maintainable.
- **Robust Relational Schemas**: Leveraged SQLAlchemy ORM with SQLite, utilizing database constraints (CheckConstraints, Foreign Keys) to enforce slot limitations (`available_slots <= total_slots`) and role definitions natively at the storage layer.
- **Role-Based Authorization Decorators**: Created custom decorators (`admin_required`, `staff_required`, `trekker_required`)wrapping Flask-Login's state validation to prevent cross-role unauthorized access.
- **Transaction-Safe Operations**: Wrapped booking creation and cancellation in dedicated transaction helper methodsinto atomically check availability, update available slots, and commit the state.

---

## 3. Frameworks and Libraries
The project utilizes the following tools and libraries:
- **Flask (v3.1.3)**: A lightweight, WSGI-compliant micro web framework providing routing, sessions, and request handling.
- **SQLAlchemy (v2.0.51) & Flask-SQLAlchemy (v3.1.1)**: ORM library mapping database tables to Python classes and facilitating safe SQL execution.
- **WTForms (v3.2.2) & Flask-WTF (v1.3.0)**: Handles secure form generation, fields rendering, client/server-side validation, and CSRF token protection.
- **Flask-Login (v0.6.3)**: Manages authenticated user session states, logins, logouts, and user loading from the database.
- **Authlib (v1.7.2)**: Integrates Authlib OAuth client logic to enable secure, standard Google OAuth 2.0 Sign-In.
- **Werkzeug (v3.1.8)**: Flask’s underlying WSGI utility, utilized specifically for secure cryptographic password hashing (`generate_password_hash` and `check_password_hash`).

---


## 5. API Resource Endpoints

### Root / Routing Entry
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/` | Redirects to role-specific dashboard based on session role | Public / Logged In |

### Auth Blueprint (`/auth` prefix)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET`, `POST` | `/auth/register` | User/Staff registration form & processing | Public |
| `GET`, `POST` | `/auth/login` | Tabbed login form (Trekker, Staff, Admin) | Public |
| `GET` | `/auth/logout` | Ends active session & logs out | Logged In |
| `GET`, `POST` | `/auth/staff/check-status` | Check if staff application is approved/pending | Public |
| `GET` | `/auth/google/login` | Initiates external Google OAuth flow | Public |
| `GET` | `/auth/google/callback` | Google OAuth callback handler | Public |

### Admin Blueprint (`/admin` prefix)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/admin/dashboard` | Main admin panel with stats counters & activity logs | Admin |
| `GET` | `/admin/treks` | List all treks | Admin |
| `GET`, `POST` | `/admin/treks/new` | Create a new trek (includes date validation) | Admin |
| `GET`, `POST` | `/admin/treks/<trek_id>/edit` | Edit a trek (includes slot validation) | Admin |
| `POST` | `/admin/treks/<trek_id>/delete` | Delete a trek | Admin |
| `GET`, `POST` | `/admin/treks/<trek_id>/assign` | Assign/Unassign an approved guide to a trek | Admin |
| `GET` | `/admin/staff/pending` | List pending staff registrations | Admin |
| `POST` | `/admin/staff/<profile_id>/approve` | Approve guide (generates sequential Staff ID) | Admin |
| `POST` | `/admin/staff/<profile_id>/reject` | Reject pending guide application | Admin |
| `GET` | `/admin/staff` | Search and manage all staff members | Admin |
| `POST` | `/admin/staff/<user_id>/blacklist` | Toggle blacklist status of a guide | Admin |
| `GET` | `/admin/users` | Search and view all registered trekkers | Admin |
| `POST` | `/admin/users/<user_id>/blacklist` | Toggle blacklist status of a trekker | Admin |

### Staff Blueprint (`/staff` prefix)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/staff/dashboard` | List assigned treks and booking statistics | Approved Staff |
| `GET`, `POST` | `/staff/treks/<trek_id>/update` | Edit available slots and trek state | Approved Staff |
| `GET` | `/staff/treks/<trek_id>/participants` | View trek's passenger manifest & status | Approved Staff |
| `POST` | `/staff/treks/<trek_id>/mark-started`| Closes bookings & sets status to Closed | Approved Staff |
| `POST` | `/staff/treks/<trek_id>/mark-completed`| Sets trek to Completed & cascades to bookings | Approved Staff |

### User / Trekker Blueprint (`/` prefix)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/treks` | Filter/search open treks; view suggestions | Trekker |
| `GET` | `/treks/<trek_id>` | Show trek descriptions, price, status, and slots | Trekker |
| `POST` | `/treks/<trek_id>/book` | Confirm 1-slot booking for the selected trek | Trekker |
| `GET` | `/bookings` | View user's active & completed booking history | Trekker |
| `POST` | `/bookings/<booking_id>/cancel` | Cancel active booking and release slot | Trekker |
| `GET`, `POST` | `/profile` | View and edit profile details | Trekker |
| `GET` | `/dashboard` | Redirects to `/treks` | Trekker |

Thank you!
