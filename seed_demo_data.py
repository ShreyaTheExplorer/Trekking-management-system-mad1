"""
seed_demo_data.py — Seeds the database with realistic sample treks, staff, trekkers, and bookings.
Safe to run multiple times (checks for existing data).
"""

from datetime import date, datetime
from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, seed_admin, approve_staff

def seed_data():
    app = create_app()
    with app.app_context():
        print("Starting database seeding...")
        
        # 1. Ensure DB tables exist
        db.create_all()
        
        # 2. Seed Admin
        admin = seed_admin()
        print(f"Admin verified: {admin.username}")
        
        # 3. Seed Staff Members
        staff_data = [
            {"username": "staff1", "email": "staff1@trek.com", "full_name": "Rajesh Kumar", "bio": "Himalayan guide with 10 years experience. Certified in wilderness first aid.", "exp": 10, "cert": "Basic Mountaineering Course (BMC)"},
            {"username": "staff2", "email": "staff2@trek.com", "full_name": "Priya Sharma", "bio": "Specializes in Western Ghats and botanical trails. Nature enthusiast.", "exp": 6, "cert": "Advance Mountaineering Course (AMC)"},
            {"username": "staff3", "email": "staff3@trek.com", "full_name": "Amit Patel", "bio": "High altitude rescuer and expert trek coordinator.", "exp": 8, "cert": "NOLS Wilderness First Responder"}
        ]
        
        seeded_staff = []
        for s in staff_data:
            user = User.query.filter_by(username=s["username"]).first()
            if not user:
                user = User(
                    username=s["username"],
                    email=s["email"],
                    full_name=s["full_name"],
                    role="staff"
                )
                user.set_password("Staff@123")
                db.session.add(user)
                db.session.flush()
                
                profile = StaffProfile(
                    user_id=user.id,
                    bio=s["bio"],
                    experience_years=s["exp"],
                    certification=s["cert"],
                    approval_status="pending"
                )
                db.session.add(profile)
                db.session.commit()
                
                # Approve staff programmatically to generate Staff ID
                approve_staff(profile, admin)
                print(f"Seeded and approved staff: {user.username} -> ID: {profile.staff_id}")
            else:
                profile = user.staff_profile
                print(f"Staff exists: {user.username} (ID: {profile.staff_id})")
            seeded_staff.append(profile)
            
        # 4. Seed Trekkers
        trekker_data = [
            {"username": "trekker1", "email": "john@trek.com", "full_name": "John Doe", "phone": "+91 9876543210"},
            {"username": "trekker2", "email": "sarah@trek.com", "full_name": "Sarah Connor", "phone": "+91 9876543211"},
            {"username": "trekker3", "email": "emily@trek.com", "full_name": "Emily Watson", "phone": "+91 9876543212"}
        ]
        
        seeded_trekkers = []
        for t in trekker_data:
            user = User.query.filter_by(username=t["username"]).first()
            if not user:
                user = User(
                    username=t["username"],
                    email=t["email"],
                    full_name=t["full_name"],
                    phone=t["phone"],
                    role="trekker"
                )
                user.set_password("Trekker@123")
                db.session.add(user)
                db.session.commit()
                print(f"Seeded trekker: {user.username}")
            else:
                print(f"Trekker exists: {user.username}")
            seeded_trekkers.append(user)

        # 5. Seed Treks
        treks_data = [
            {
                "name": "Kedarkantha Winter Trek",
                "location": "Uttarakhand, Himalayas",
                "difficulty": "Easy",
                "duration_days": 6,
                "total_slots": 15,
                "start_date": date(2026, 12, 10),
                "end_date": date(2026, 12, 15),
                "month": "December",
                "season": "Winter",
                "price": 8500.0,
                "description": "Kedarkantha Trek is one of the best winter treks in India. It is known for its beautiful pine forests, snow-covered trails, and panoramic view of the majestic Himalayan peaks from the summit.",
                "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?q=80&w=600",
                "status": "Open",
                "staff_index": 0
            },
            {
                "name": "Valley of Flowers Monsoon Trek",
                "location": "Uttarakhand, Himalayas",
                "difficulty": "Moderate",
                "duration_days": 6,
                "total_slots": 12,
                "start_date": date(2026, 7, 15),
                "end_date": date(2026, 7, 20),
                "month": "July",
                "season": "Monsoon",
                "price": 9500.0,
                "description": "Valley of Flowers is a UNESCO World Heritage Site located in Nanda Devi Biosphere Reserve. During monsoon, the valley blooms with hundreds of species of wild alpine flowers, turning it into a colourful paradise.",
                "cover_image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=600",
                "status": "Open",
                "staff_index": 1
            },
            {
                "name": "Har Ki Dun Autumn Trek",
                "location": "Uttarakhand, Himalayas",
                "difficulty": "Moderate",
                "duration_days": 7,
                "total_slots": 10,
                "start_date": date(2026, 10, 5),
                "end_date": date(2026, 10, 11),
                "month": "October",
                "season": "Autumn",
                "price": 10500.0,
                "description": "Har Ki Dun is a cradle-shaped valley in the Garhwal Himalayas. It is surrounded by snow-capped peaks and dense forests of pine and oak. Excellent trail for spotting rich wildlife and ancient wooden culture villages.",
                "cover_image": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?q=80&w=600",
                "status": "Open",
                "staff_index": 2
            },
            {
                "name": "Roopkund Mystery Lake Trek",
                "location": "Uttarakhand, Himalayas",
                "difficulty": "Hard",
                "duration_days": 8,
                "total_slots": 8,
                "start_date": date(2027, 5, 20),
                "end_date": date(2027, 5, 27),
                "month": "May",
                "season": "Spring",
                "price": 13500.0,
                "description": "Roopkund is a high-altitude glacial lake famous for the hundreds of human skeletons found at its edge. The trail winds through dense forests, magnificent alpine meadows (Bugyals), and steep snow slopes.",
                "cover_image": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=600",
                "status": "Open",
                "staff_index": 0
            },
            {
                "name": "Sandakphu Ridge Trek",
                "location": "West Bengal, Himalayas",
                "difficulty": "Moderate",
                "duration_days": 6,
                "total_slots": 15,
                "start_date": date(2026, 1, 15),
                "end_date": date(2026, 1, 20),
                "month": "January",
                "season": "Winter",
                "price": 11000.0,
                "description": "Sandakphu is the highest peak in West Bengal, offering unparalleled views of the Sleeping Buddha range (Kanchenjunga) and Everest. The trail goes along the Indo-Nepal border through Singalila National Park.",
                "cover_image": "https://images.unsplash.com/photo-1521336575822-6da63fb45455?q=80&w=600",
                "status": "Completed",
                "staff_index": 1
            },
            {
                "name": "Kudremukh Peak Monsoon Trail",
                "location": "Karnataka, Western Ghats",
                "difficulty": "Moderate",
                "duration_days": 2,
                "total_slots": 20,
                "start_date": date(2026, 9, 12),
                "end_date": date(2026, 9, 13),
                "month": "September",
                "season": "Monsoon",
                "price": 3200.0,
                "description": "Kudremukh is a horse-face shaped peak in Chikmagalur. It is a spectacular green ridge walk through Shola grasslands and dense forest patches. The monsoon mist and rain make the landscape look incredibly lush.",
                "cover_image": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=600",
                "status": "Open",
                "staff_index": 2
            },
            {
                "name": "Chembra Peak Heart Lake Trail",
                "location": "Kerala, Western Ghats",
                "difficulty": "Easy",
                "duration_days": 1,
                "total_slots": 25,
                "start_date": date(2027, 2, 10),
                "end_date": date(2027, 2, 10),
                "month": "February",
                "season": "Spring",
                "price": 1500.0,
                "description": "Chembra Peak is the tallest peak in Wayanad. The highlight of this day hike is the heart-shaped lake (Hriday Saras) situated on the way to the peak, which never dries up. Offers spectacular views of Wayanad hills.",
                "cover_image": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?q=80&w=600",
                "status": "Open",
                "staff_index": 0
            },
            {
                "name": "Hampta Pass Summer Crossing",
                "location": "Himachal Pradesh, Himalayas",
                "difficulty": "Hard",
                "duration_days": 5,
                "total_slots": 10,
                "start_date": date(2026, 6, 18),
                "end_date": date(2026, 6, 22),
                "month": "June",
                "season": "Summer",
                "price": 9000.0,
                "description": "Hampta Pass is a dramatic trek from the lush green valleys of Kullu to the stark, dry desert landscapes of Lahaul & Spiti. Highlights include crossing fast-flowing streams and camping near Chandratal Lake.",
                "cover_image": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?q=80&w=600",
                "status": "Open",
                "staff_index": 1
            }
        ]

        seeded_treks = []
        for t in treks_data:
            trek = Trek.query.filter_by(name=t["name"]).first()
            if not trek:
                trek = Trek(
                    name=t["name"],
                    location=t["location"],
                    difficulty=t["difficulty"],
                    duration_days=t["duration_days"],
                    total_slots=t["total_slots"],
                    available_slots=t["total_slots"],
                    start_date=t["start_date"],
                    end_date=t["end_date"],
                    month=t["month"],
                    season=t["season"],
                    price=t["price"],
                    description=t["description"],
                    cover_image=t["cover_image"],
                    status=t["status"],
                    assigned_staff_id=seeded_staff[t["staff_index"]].id,
                    created_by=admin.id
                )
                db.session.add(trek)
                db.session.commit()
                print(f"Seeded trek: {trek.name} (assigned to {seeded_staff[t['staff_index']].user.full_name})")
            else:
                print(f"Trek exists: {trek.name}")
            seeded_treks.append(trek)

        # 6. Seed Bookings
        # Only seed bookings if booking table is empty
        if Booking.query.count() == 0:
            print("Seeding sample bookings...")
            
            # Booking 1: John books Kedarkantha (Open) -> status: Booked
            # decrement available_slots
            t1 = seeded_treks[0]  # Kedarkantha
            u1 = seeded_trekkers[0] # John
            b1 = Booking(user_id=u1.id, trek_id=t1.id, num_people=1, status="Booked")
            t1.available_slots -= 1
            db.session.add(b1)
            db.session.add(t1)
            
            # Booking 2: Sarah books Valley of Flowers (Open) -> status: Booked
            t2 = seeded_treks[1]  # Valley of Flowers
            u2 = seeded_trekkers[1] # Sarah
            b2 = Booking(user_id=u2.id, trek_id=t2.id, num_people=1, status="Booked")
            t2.available_slots -= 1
            db.session.add(b2)
            db.session.add(t2)

            # Booking 3: Emily books Har Ki Dun (Open) -> status: Booked
            t3 = seeded_treks[2]  # Har Ki Dun
            u3 = seeded_trekkers[2] # Emily
            b3 = Booking(user_id=u3.id, trek_id=t3.id, num_people=1, status="Booked")
            t3.available_slots -= 1
            db.session.add(b3)
            db.session.add(t3)

            # Booking 4: John has Completed booking for Sandakphu (Completed)
            t5 = seeded_treks[4]  # Sandakphu (Completed)
            b4 = Booking(user_id=u1.id, trek_id=t5.id, num_people=1, status="Completed")
            # Completed trek, slots don't need decrementing for active counts
            db.session.add(b4)

            # Booking 5: Sarah has Cancelled booking for Kedarkantha
            b5 = Booking(user_id=u2.id, trek_id=t1.id, num_people=1, status="Cancelled")
            db.session.add(b5)

            db.session.commit()
            print("Successfully seeded all sample bookings!")
        else:
            print("Bookings already exist in the database, skipping bookings seed.")

        print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
