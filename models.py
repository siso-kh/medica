from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model with authentication and role support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')  # 'patient', 'doctor', 'admin', 'pharmacy'
    is_vip = db.Column(db.Boolean, default=False, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    doctor_profile = db.relationship('DoctorProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', foreign_keys='Review.patient_id', backref='patient', lazy='dynamic')
    vip_consults = db.relationship('VIPConsult', backref='patient', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def pharmacy(self):
        """Get pharmacy for pharmacy users"""
        if self.role == 'pharmacy':
            return Pharmacy.query.filter_by(user_id=self.id).first()
        return None
    
    def __repr__(self):
        return f'<User {self.email}>'


class DoctorProfile(db.Model):
    """Doctor profile with specialty and ratings"""
    __tablename__ = 'doctor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    average_rating = db.Column(db.Float, default=0.0, nullable=False)
    
    # Relationships
    reviews = db.relationship('Review', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    availabilities = db.relationship('Availability', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    vip_assignments = db.relationship('VIPConsultAssignment', backref='doctor', lazy='dynamic')
    
    def update_average_rating(self):
        """Recalculate and update average rating from reviews"""
        reviews = self.reviews.all()
        if reviews:
            self.average_rating = sum(review.rating for review in reviews) / len(reviews)
        else:
            self.average_rating = 0.0
        db.session.commit()
    
    def __repr__(self):
        return f'<DoctorProfile {self.user.name if self.user else None}>'


class Review(db.Model):
    """Patient reviews for doctors"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.rating} stars by Patient {self.patient_id}>'


class Availability(db.Model):
    """Doctor availability schedule"""
    __tablename__ = 'availabilities'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False)
    day = db.Column(db.String(20), nullable=False)  # e.g., 'Monday', 'Tuesday'
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    def __repr__(self):
        return f'<Availability {self.day} {self.start_time}-{self.end_time}>'


class Medicine(db.Model):
    """Medicine catalog"""
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Relationships
    pharmacy_stocks = db.relationship('PharmacyStock', backref='medicine', lazy='dynamic')
    
    def __repr__(self):
        return f'<Medicine {self.name}>'


class Pharmacy(db.Model):
    """Pharmacy locations"""
    __tablename__ = 'pharmacies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False, index=True)  # Added index for faster distance queries
    lng = db.Column(db.Float, nullable=False, index=True)  # Added index for faster distance queries
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=True)  # Link to pharmacy user
    
    # Relationships
    stocks = db.relationship('PharmacyStock', backref='pharmacy', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pharmacy {self.name}>'


class PharmacyStock(db.Model):
    """Stock levels for medicines in pharmacies"""
    __tablename__ = 'pharmacy_stocks'
    
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id', ondelete='CASCADE'), primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='CASCADE'), primary_key=True, index=True)  # Added index for faster medicine filtering
    quantity = db.Column(db.Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f'<PharmacyStock Pharmacy {self.pharmacy_id} Medicine {self.medicine_id} Qty {self.quantity}>'


class VIPConsult(db.Model):
    """VIP consultation requests"""
    __tablename__ = 'vip_consults'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(500))  # Path to uploaded file
    status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'accepted', 'completed', 'cancelled'
    discord_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('VIPConsultAssignment', backref='consult', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<VIPConsult {self.id} by Patient {self.patient_id}>'


class VIPConsultAssignment(db.Model):
    """Assignments of VIP consults to doctors"""
    __tablename__ = 'vip_consult_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    consult_id = db.Column(db.Integer, db.ForeignKey('vip_consults.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'accepted', 'declined'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VIPConsultAssignment Consult {self.consult_id} Doctor {self.doctor_id} Status {self.status}>'

