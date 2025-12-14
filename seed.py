from faker import Faker
from app import create_app
from models import db, User, DoctorProfile, Medicine, Pharmacy, PharmacyStock, Review, VIPConsult, VIPConsultAssignment
import random

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
        db.session.query(DoctorProfile).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Seed users (patients, doctors, admins)
        users = []
        roles = ['patient', 'doctor', 'admin']
        for _ in range(50):  # Adjust number as needed
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

        # Seed medicines
        medicines = []
        for _ in range(30):  # Adjust number as needed
            medicine = Medicine(
                name=fake.unique.word().capitalize() + ' ' + random.choice(['Tablet', 'Syrup', 'Injection', 'Cream']),
                description=fake.text(max_nb_chars=100)
            )
            medicines.append(medicine)
            db.session.add(medicine)
        db.session.commit()

        # Seed pharmacies
        pharmacies = []
        for _ in range(20):  # Adjust number as needed
            pharmacy = Pharmacy(
                name=fake.company() + ' Pharmacy',
                address=fake.address(),
                lat=round(random.uniform(-90, 90), 6),  # Random lat/lng
                lng=round(random.uniform(-180, 180), 6)
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