"""
test_flows.py — Automated test script to verify core requirements using Flask Test Client.
"""

import unittest
from datetime import date
from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, create_booking, cancel_booking, seed_admin, approve_staff

class TrekkingManagementTestCase(unittest.TestCase):

    def setUp(self):
        # Configure app to use a testing-specific SQLite database
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for easier testing of POST requests
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Seed admin
        self.admin = seed_admin()
        
        # Seed staff
        self.staff_user = User(username="staff_test", email="staff_test@trek.com", full_name="Test Staff", role="staff")
        self.staff_user.set_password("Staff@123")
        db.session.add(self.staff_user)
        db.session.flush()
        
        self.staff_profile = StaffProfile(user_id=self.staff_user.id, bio="Test Bio", experience_years=5, certification="BMC")
        db.session.add(self.staff_profile)
        db.session.commit()
        approve_staff(self.staff_profile, self.admin)
        
        # Seed trekkers
        self.trekker1 = User(username="trekker_test1", email="trekker_test1@trek.com", full_name="Test Trekker One", role="trekker")
        self.trekker1.set_password("Trekker@123")
        
        self.trekker2 = User(username="trekker_test2", email="trekker_test2@trek.com", full_name="Test Trekker Two", role="trekker")
        self.trekker2.set_password("Trekker@123")
        
        db.session.add(self.trekker1)
        db.session.add(self.trekker2)
        db.session.commit()

        # Seed treks
        self.trek_easy = Trek(
            name="Easy Valley Trek", location="Himalayas", difficulty="Easy", duration_days=3,
            total_slots=5, available_slots=5, start_date=date(2026, 8, 10), end_date=date(2026, 8, 13),
            month="August", season="Summer", price=3000.0, description="Easy walk",
            status="Open", assigned_staff_id=self.staff_profile.id, created_by=self.admin.id
        )
        
        self.trek_moderate = Trek(
            name="Moderate Peak Trek", location="Western Ghats", difficulty="Moderate", duration_days=2,
            total_slots=10, available_slots=10, start_date=date(2026, 9, 15), end_date=date(2026, 9, 17),
            month="September", season="Monsoon", price=2000.0, description="Moderate climb",
            status="Open", assigned_staff_id=self.staff_profile.id, created_by=self.admin.id
        )

        self.trek_hard = Trek(
            name="Hard Pass Trek", location="Himalayas", difficulty="Hard", duration_days=10,
            total_slots=3, available_slots=3, start_date=date(2026, 10, 1), end_date=date(2026, 10, 11),
            month="October", season="Autumn", price=15000.0, description="Hard pass crossing",
            status="Open", assigned_staff_id=self.staff_profile.id, created_by=self.admin.id
        )

        db.session.add(self.trek_easy)
        db.session.add(self.trek_moderate)
        db.session.add(self.trek_hard)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_and_browsing_filters(self):
        # 1. Login as trekker
        response = self.client.post("/auth/login", data={
            "role": "trekker",
            "trekker_username": "trekker_test1",
            "trekker_password": "Trekker@123"
        }, follow_redirects=True)
        self.assertIn(b"Welcome back, Test Trekker One!", response.data)
        
        # 2. Browse treks with no filters (should show all 3)
        response = self.client.get("/treks")
        self.assertIn(b"Easy Valley Trek", response.data)
        self.assertIn(b"Moderate Peak Trek", response.data)
        self.assertIn(b"Hard Pass Trek", response.data)
        self.assertIn(b"Popular treks overall", response.data)  # Suggestions fallback since no past bookings

        # 3. Browse with difficulty filter "Hard"
        response = self.client.get("/treks?difficulty=Hard")
        self.assertIn(b"1 trail(s) found", response.data)
        self.assertIn(b"Hard Pass Trek", response.data)

        # 4. Browse with location filter "Western Ghats"
        response = self.client.get("/treks?location=Western Ghats")
        self.assertIn(b"1 trail(s) found", response.data)
        self.assertIn(b"Moderate Peak Trek", response.data)


    def test_suggestions_based_on_past_bookings(self):
        # Login
        self.client.post("/auth/login", data={
            "role": "trekker",
            "trekker_username": "trekker_test1",
            "trekker_password": "Trekker@123"
        }, follow_redirects=True)

        # Book the Easy Valley Trek
        create_booking(self.trekker1, self.trek_easy, num_people=1)

        # Now when we browse treks, the suggestion section should look for location 'Himalayas' or difficulty 'Easy'
        response = self.client.get("/treks")
        self.assertIn(b"Based on your recent booking: Easy Valley Trek", response.data)
        # It should suggest 'Hard Pass Trek' because it is in Himalayas (same location)
        # Even though Easy Valley Trek matches, it is excluded since it is already booked/the most recent one.
        self.assertIn(b"Hard Pass Trek", response.data)

    def test_booking_decrement_and_overbooking_prevention(self):
        # 1. Login
        self.client.post("/auth/login", data={
            "role": "trekker",
            "trekker_username": "trekker_test1",
            "trekker_password": "Trekker@123"
        }, follow_redirects=True)

        # 2. Book Hard Pass Trek (total_slots=3, available_slots=3)
        self.assertEqual(self.trek_hard.available_slots, 3)
        response = self.client.post(f"/treks/{self.trek_hard.id}/book", follow_redirects=True)
        self.assertIn(b"Successfully booked &#39;Hard Pass Trek&#39;!", response.data)
        self.assertEqual(self.trek_hard.available_slots, 2)

        # 3. Book down to 0 slots
        create_booking(self.trekker2, self.trek_hard, num_people=2)
        self.assertEqual(self.trek_hard.available_slots, 0)

        # 4. Try to book another slot (should fail)
        response = self.client.post(f"/treks/{self.trek_hard.id}/book", follow_redirects=True)
        self.assertIn(b"Not enough slots available for this trek.", response.data)
        self.assertEqual(self.trek_hard.available_slots, 0)

    def test_cancel_booking_restores_slots(self):
        # 1. Login
        self.client.post("/auth/login", data={
            "role": "trekker",
            "trekker_username": "trekker_test1",
            "trekker_password": "Trekker@123"
        }, follow_redirects=True)

        # 2. Create booking
        booking = create_booking(self.trekker1, self.trek_hard, num_people=1)
        self.assertEqual(self.trek_hard.available_slots, 2)

        # 3. Cancel booking via route
        response = self.client.post(f"/bookings/{booking.id}/cancel", follow_redirects=True)
        self.assertIn(b"Booking cancelled successfully.", response.data)
        self.assertEqual(self.trek_hard.available_slots, 3)

    def test_blacklisted_user_or_staff_locked_out(self):
        # 1. Blacklist trekker
        self.trekker1.is_blacklisted = True
        db.session.commit()

        # 2. Try to log in
        response = self.client.post("/auth/login", data={
            "role": "trekker",
            "trekker_username": "trekker_test1",
            "trekker_password": "Trekker@123"
        }, follow_redirects=True)
        self.assertIn(b"This account has been blacklisted.", response.data)

        # 3. Blacklist staff
        self.staff_user.is_blacklisted = True
        db.session.commit()

        # 4. Try staff login
        response = self.client.post("/auth/login", data={
            "role": "staff",
            "staff_username": "staff_test",
            "staff_password": "Staff@123",
            "staff_id": "STF-00001"
        }, follow_redirects=True)
        self.assertIn(b"Your account has been blacklisted.", response.data)

if __name__ == "__main__":
    unittest.main()
