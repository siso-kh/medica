from faker import Faker
from app import create_app
from models import db, User, DoctorProfile, Medicine, Pharmacy, PharmacyStock, Review, VIPConsult, VIPConsultAssignment, Availability
import random
from datetime import datetime, time

fake = Faker()

def seed_database():
    app = create_app()
    with app.app_context():
        # Clear existing data (optional, remove if you want to keep existing data)
        db.session.query(VIPConsultAssignment).delete()
        db.session.query(VIPConsult).delete()
        db.session.query(Review).delete()
        db.session.query(PharmacyStock).delete()
        db.session.query(Pharmacy).delete()
        db.session.query(Medicine).delete()
        db.session.query(Availability).delete()
        db.session.query(DoctorProfile).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Seed users (patients, doctors, admins, pharmacies)
        users = []
        roles = ['patient', 'doctor', 'admin', 'pharmacy']
        for _ in range(70):  # Adjust number as needed
            role = random.choice(roles)
            user = User(
                name=fake.name(),
                email=fake.unique.email(),
                role=role,
                is_vip=random.choice([True, False]),
                balance=round(random.uniform(0, 1000), 2)
            )
            user.set_password('password123')  # Default password for all
            users.append(user)
            db.session.add(user)
        db.session.commit()

        # Seed doctor profiles for doctor users
        specialties = ['Cardiology', 'Dermatology', 'Neurology', 'Pediatrics', 'Orthopedics', 'General Medicine']
        doctors = []
        for user in users:
            if user.role == 'doctor':
                doctor = DoctorProfile(
                    user_id=user.id,
                    specialty=random.choice(specialties),
                    address=fake.address(),
                    phone=fake.phone_number(),
                    bio=fake.text(max_nb_chars=200),
                    average_rating=round(random.uniform(1, 5), 1)
                )
                doctors.append(doctor)
                db.session.add(doctor)
        db.session.commit()

        # Seed random availability for each doctor
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for doctor in doctors:
            num_slots = random.randint(3, 7)  # Random number of availability slots per doctor
            for _ in range(num_slots):
                day = random.choice(days)
                start_hour = random.randint(8, 16)  # Start between 8 AM and 4 PM
                duration = random.randint(1, 4)  # Duration 1-4 hours
                end_hour = start_hour + duration
                if end_hour > 18:  # Cap at 6 PM
                    end_hour = 18
                start_time = time(start_hour, 0)
                end_time = time(end_hour, 0)
                availability = Availability(
                    doctor_id=doctor.id,
                    day=day,
                    start_time=start_time,
                    end_time=end_time
                )
                db.session.add(availability)
        db.session.commit()

        # Seed medicines
        medicines = []
        for _ in range(60):  # Adjust number as needed
            medicine = Medicine(
                name=fake.unique.word().capitalize() + ' ' + random.choice(['Tablet', 'Syrup', 'Injection', 'Cream']),
                description=fake.text(max_nb_chars=100)
            )
            medicines.append(medicine)
            db.session.add(medicine)
        db.session.commit()

        # Seed pharmacies (link to pharmacy users)
        pharmacies = []
        pharmacy_users = [u for u in users if u.role == 'pharmacy']
        for i, user in enumerate(pharmacy_users):
            pharmacy = Pharmacy(
                name=fake.company() + ' Pharmacy',
                address=fake.address(),
                lat=round(random.uniform(32.0, 38.0), 6),  # Random lat around Tunisia
                lng=round(random.uniform(7.0, 12.0), 6),   # Random lng around Tunisia
                user_id=user.id
            )
            pharmacies.append(pharmacy)
            db.session.add(pharmacy)
        # Add more pharmacies without users if needed
        for _ in range(max(0, 20 - len(pharmacy_users))):
            pharmacy = Pharmacy(
                name=fake.company() + ' Pharmacy',
                address=fake.address(),
                lat=round(random.uniform(32.0, 38.0), 6),
                lng=round(random.uniform(7.0, 12.0), 6)
            )
            pharmacies.append(pharmacy)
            db.session.add(pharmacy)
        db.session.commit()

        # Seed pharmacy stocks
        for pharmacy in pharmacies:
            for medicine in random.sample(medicines, random.randint(5, 15)):  # Random subset
                stock = PharmacyStock(
                    pharmacy_id=pharmacy.id,
                    medicine_id=medicine.id,
                    quantity=random.randint(0, 100)
                )
                db.session.add(stock)
        db.session.commit()

        # Seed reviews
        patients = [u for u in users if u.role == 'patient']
        for doctor in doctors:
            for _ in range(random.randint(0, 10)):  # Random reviews per doctor
                if patients:
                    patient = random.choice(patients)
                    review = Review(
                        doctor_id=doctor.id,
                        patient_id=patient.id,
                        rating=random.randint(1, 5),
                        comment=fake.text(max_nb_chars=150)
                    )
                    db.session.add(review)
        db.session.commit()

        # Update doctor average ratings
        for doctor in doctors:
            doctor.update_average_rating()

        # Seed VIP consults
        vip_users = [u for u in users if u.is_vip]
        for _ in range(10):  # Adjust number as needed
            if vip_users and doctors:
                patient = random.choice(vip_users)
                consult = VIPConsult(
                    patient_id=patient.id,
                    description=fake.text(max_nb_chars=200),
                    specialty=random.choice(specialties),
                    status=random.choice(['pending', 'accepted', 'completed', 'cancelled'])
                )
                db.session.add(consult)
                db.session.flush()  # To get consult.id

                # Assign to random doctors
                assigned_doctors = random.sample(doctors, min(5, len(doctors)))
                for doc in assigned_doctors:
                    assignment = VIPConsultAssignment(
                        consult_id=consult.id,
                        doctor_id=doc.id,
                        status=random.choice(['pending', 'accepted', 'declined'])
                    )
                    db.session.add(assignment)
        db.session.commit()

        print("Database seeded with random data!")

if __name__ == '__main__':
    seed_database()