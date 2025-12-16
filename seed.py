from faker import Faker
from app import create_app
from models import db, User, DoctorProfile, Medicine, Pharmacy, PharmacyStock, Review, VIPConsult, VIPConsultAssignment, Availability
import random
from datetime import datetime, time

# Use English locale for English data, but with Tunisian context
fake = Faker('en')

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
        specialties = ['Cardiology', 'Dermatology', 'Neurology', 'Pediatrics', 'Orthopedics', 'General Medicine', 'Internal Medicine', 'Gynecology', 'Ophthalmology', 'Dentistry']
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

        # Add common medicines for easier testing
        common_medicines = [
            ("Aspirin", "Pain reliever and fever reducer."),
            ("Ibuprofen", "Anti-inflammatory drug."),
            ("Paracetamol", "Pain reliever and fever reducer."),
            ("Amoxicillin", "Antibiotic for bacterial infections."),
            ("Omeprazole", "Reduces stomach acid."),
            ("Metformin", "Diabetes medication."),
            ("Lisinopril", "Blood pressure medication."),
            ("Simvastatin", "Cholesterol-lowering drug."),
            ("Levothyroxine", "Thyroid hormone replacement."),
            ("Albuterol", "Bronchodilator for asthma."),
        ]
        for name, desc in common_medicines:
            if not Medicine.query.filter_by(name=name).first():
                medicine = Medicine(name=name, description=desc)
                medicines.append(medicine)
                db.session.add(medicine)
        db.session.commit()

        # Seed pharmacies with real Tunisian data
        real_pharmacies_data = [
            {"name": "Pharmacie Centrale", "address": "Avenue Habib Bourguiba, Tunis, Tunisia", "lat": 36.8065, "lng": 10.1815},
            {"name": "Pharmacie Ibn Khaldoun", "address": "Rue Ibn Khaldoun, Tunis, Tunisia", "lat": 36.7992, "lng": 10.1704},
            {"name": "Pharmacie El Medina", "address": "Souk El Medina, Tunis, Tunisia", "lat": 36.7988, "lng": 10.1658},
            {"name": "Pharmacie Carthage", "address": "Byrsa Hill, Carthage, Tunisia", "lat": 36.8525, "lng": 10.3236},
            {"name": "Pharmacie Sfax", "address": "Avenue de la République, Sfax, Tunisia", "lat": 34.7406, "lng": 10.7603},
            {"name": "Pharmacie Sousse", "address": "Boulevard du 14 Janvier, Sousse, Tunisia", "lat": 35.8256, "lng": 10.6369},
            {"name": "Pharmacie Monastir", "address": "Avenue Farhat Hached, Monastir, Tunisia", "lat": 35.7780, "lng": 10.8262},
            {"name": "Pharmacie Bizerte", "address": "Rue de la Kasbah, Bizerte, Tunisia", "lat": 37.2744, "lng": 9.8739},
            {"name": "Pharmacie Nabeul", "address": "Avenue Hedi Chaker, Nabeul, Tunisia", "lat": 36.4561, "lng": 10.7376},
            {"name": "Pharmacie Hammamet", "address": "Rue de la Médina, Hammamet, Tunisia", "lat": 36.4000, "lng": 10.6167},
            {"name": "Pharmacie Gabès", "address": "Avenue de la République, Gabès, Tunisia", "lat": 33.8815, "lng": 10.0982},
            {"name": "Pharmacie Kairouan", "address": "Rue de la Grande Mosquée, Kairouan, Tunisia", "lat": 35.6781, "lng": 10.0963},
            {"name": "Pharmacie Tozeur", "address": "Avenue Abou El Kacem Chebbi, Tozeur, Tunisia", "lat": 33.9197, "lng": 8.1335},
            {"name": "Pharmacie Gafsa", "address": "Rue Ali Belhouane, Gafsa, Tunisia", "lat": 34.4250, "lng": 8.7842},
            {"name": "Pharmacie Ariana", "address": "Avenue de la République, Ariana, Tunisia", "lat": 36.8625, "lng": 10.1956},
            {"name": "Pharmacie Ben Arous", "address": "Rue de la Révolution, Ben Arous, Tunisia", "lat": 36.7531, "lng": 10.2189},
            {"name": "Pharmacie Manouba", "address": "Rue de l'Indépendance, Manouba, Tunisia", "lat": 36.8100, "lng": 10.1000},
            {"name": "Pharmacie Zaghouan", "address": "Rue de la Kasbah, Zaghouan, Tunisia", "lat": 36.4029, "lng": 10.1429},
            {"name": "Pharmacie Beja", "address": "Rue de la République, Beja, Tunisia", "lat": 36.7256, "lng": 9.1817},
            {"name": "Pharmacie Mahdia", "address": "Rue du 7 Novembre, Mahdia, Tunisia", "lat": 35.5047, "lng": 11.0622}
        ]
        
        pharmacies = []
        pharmacy_users = [u for u in users if u.role == 'pharmacy']
        for i, user in enumerate(pharmacy_users):
            data = real_pharmacies_data[i % len(real_pharmacies_data)]
            pharmacy = Pharmacy(
                name=data["name"],
                address=data["address"],
                lat=data["lat"],
                lng=data["lng"],
                user_id=user.id
            )
            pharmacies.append(pharmacy)
            db.session.add(pharmacy)
        # Add more pharmacies without users if needed
        for i in range(max(0, 20 - len(pharmacy_users))):
            data = real_pharmacies_data[(len(pharmacy_users) + i) % len(real_pharmacies_data)]
            pharmacy = Pharmacy(
                name=data["name"],
                address=data["address"],
                lat=data["lat"],
                lng=data["lng"]
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

        # Ensure every medicine has at least one pharmacy stock
        for medicine in medicines:
            if not PharmacyStock.query.filter_by(medicine_id=medicine.id).first():
                pharmacy = random.choice(pharmacies)
                stock = PharmacyStock(
                    pharmacy_id=pharmacy.id,
                    medicine_id=medicine.id,
                    quantity=random.randint(1, 50)
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

        print("Database seeded with English data from Tunisia!")

if __name__ == '__main__':
    seed_database()