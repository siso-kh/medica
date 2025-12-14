from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import random
import math
from functools import wraps
from models import (
    db, User, DoctorProfile, Review, Availability, 
    Medicine, Pharmacy, PharmacyStock, VIPConsult, VIPConsultAssignment
)
from config import Config

bp = Blueprint('routes', __name__)


def vip_required(f):
    """Decorator to require VIP status"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_vip:
            flash('VIP membership required. Please upgrade your plan.', 'warning')
            return redirect(url_for('routes.upgrade'))
        return f(*args, **kwargs)
    return decorated_function


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on Earth (in km)
    using the Haversine formula
    """
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'patient')
        
        # Validation
        if not name or not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login instead.', 'warning')
            return redirect(url_for('routes.login'))
        
        # Create user
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()  # Commit user first to get ID
        
        # If doctor, create doctor profile
        if role == 'doctor':
            specialty = request.form.get('specialty', 'General')
            doctor_profile = DoctorProfile(
                user_id=user.id,  # Now user.id exists
                specialty=specialty,
                address=request.form.get('address', ''),
                phone=request.form.get('phone', ''),
                bio=request.form.get('bio', '')
            )
            db.session.add(doctor_profile)
            db.session.commit()
        
        # If pharmacy, create pharmacy entry
        if role == 'pharmacy':
            pharmacy_name = request.form.get('pharmacy_name', '')
            address = request.form.get('address', '')
            lat = request.form.get('lat', type=float)
            lng = request.form.get('lng', type=float)
            
            if not pharmacy_name or not address or lat is None or lng is None:
                flash('Please provide pharmacy details.', 'danger')
                return render_template('register.html')
            
            pharmacy = Pharmacy(
                name=pharmacy_name,
                address=address,
                lat=lat,
                lng=lng,
                user_id=user.id
            )
            db.session.add(pharmacy)
            db.session.commit()
    
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('routes.login'))
    
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember') == 'on')
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('routes.index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.index'))


@bp.route('/doctors')
def doctors():
    """Doctor directory page"""
    return render_template('doctors.html')


@bp.route('/api/doctors')
def api_doctors():
    """API endpoint for doctor filtering"""
    specialty_filter = request.args.get('specialty', '')
    min_rating = request.args.get('min_rating', type=float)
    
    # Query doctors with their profiles
    query = DoctorProfile.query.join(User)
    
    if specialty_filter:
        query = query.filter(DoctorProfile.specialty.ilike(f'%{specialty_filter}%'))
    
    if min_rating is not None:
        query = query.filter(DoctorProfile.average_rating >= min_rating)
    
    doctors = query.all()
    
    # Format response
    doctors_data = []
    for doctor in doctors:
        doctors_data.append({
            'id': doctor.id,
            'name': doctor.user.name,
            'specialty': doctor.specialty,
            'average_rating': round(doctor.average_rating, 1),
            'bio': doctor.bio[:100] + '...' if doctor.bio and len(doctor.bio) > 100 else doctor.bio or '',
            'address': doctor.address or ''
        })
    
    return jsonify(doctors_data)


@bp.route('/api/specialties')
def api_specialties():
    """Get list of all specialties"""
    specialties = db.session.query(DoctorProfile.specialty).distinct().all()
    return jsonify([s[0] for s in specialties])


@bp.route('/doctor/<int:doctor_id>')
def doctor_profile(doctor_id):
    """Individual doctor profile page"""
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    reviews = Review.query.filter_by(doctor_id=doctor_id).order_by(Review.created_at.desc()).all()
    
    # Check if current user has already reviewed this doctor
    can_review = False
    if current_user.is_authenticated and current_user.role == 'patient':
        existing_review = Review.query.filter_by(
            doctor_id=doctor_id,
            patient_id=current_user.id
        ).first()
        can_review = existing_review is None
    
    return render_template('profile.html', doctor=doctor, reviews=reviews, can_review=can_review)


@bp.route('/doctor/<int:doctor_id>/review', methods=['POST'])
@login_required
def submit_review(doctor_id):
    """Submit a review for a doctor"""
    if current_user.role != 'patient':
        flash('Only patients can submit reviews.', 'danger')
        return redirect(url_for('routes.doctor_profile', doctor_id=doctor_id))
    
    # Check if already reviewed
    existing_review = Review.query.filter_by(
        doctor_id=doctor_id,
        patient_id=current_user.id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this doctor.', 'warning')
        return redirect(url_for('routes.doctor_profile', doctor_id=doctor_id))
    
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')
    
    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5).', 'danger')
        return redirect(url_for('routes.doctor_profile', doctor_id=doctor_id))
    
    # Create review
    review = Review(
        doctor_id=doctor_id,
        patient_id=current_user.id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(review)
    db.session.commit()
    
    # Update doctor's average rating
    doctor = DoctorProfile.query.get(doctor_id)
    doctor.update_average_rating()
    
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('routes.doctor_profile', doctor_id=doctor_id))


@bp.route('/medicines')
def medicines():
    """Medicine finder page"""
    return render_template('medicines.html')


@bp.route('/api/search-medicines', methods=['POST'])
def search_medicines():
    """Search for medicines and return nearby pharmacies"""
    data = request.get_json()
    medicine_name = data.get('medicine_name', '').strip()
    user_lat = data.get('lat')
    user_lng = data.get('lng')
    
    if not medicine_name:
        return jsonify({'error': 'Please enter a medicine name.'}), 400
    
    # Find medicine
    medicine = Medicine.query.filter(Medicine.name.ilike(f'%{medicine_name}%')).first()
    
    if not medicine:
        return jsonify({
            'error': f'Medicine "{medicine_name}" not found in our database. Please try another name.'
        }), 404
    
    # Find pharmacies with stock
    stocks = PharmacyStock.query.filter_by(
        medicine_id=medicine.id
    ).filter(PharmacyStock.quantity > 0).all()
    
    if not stocks:
        return jsonify({
            'error': f'Medicine "{medicine_name}" is not currently in stock at any nearby pharmacy.'
        }), 404
    
    results = []
    
    for stock in stocks:
        pharmacy = stock.pharmacy
        
        # Calculate distance only if user location provided
        distance = None
        if user_lat is not None and user_lng is not None:
            try:
                distance = haversine_distance(
                    float(user_lat), float(user_lng),
                    pharmacy.lat, pharmacy.lng
                )
            except (ValueError, TypeError):
                distance = None  # Fallback if invalid coords
    
        results.append({
            'pharmacy_id': pharmacy.id,
            'pharmacy_name': pharmacy.name,
            'address': pharmacy.address,
            'quantity': stock.quantity,
            'distance': round(distance, 2) if distance is not None else None,
            'lat': pharmacy.lat,
            'lng': pharmacy.lng
        })
    
    # Sort by distance if location provided, else by default location
    if user_lat is not None and user_lng is not None:
        results.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
    else:
        # Default location (e.g., Paris) if no user location
        default_lat, default_lng = 48.8566, 2.3522
        for result in results:
            if result['distance'] is None:
                result['distance'] = round(haversine_distance(
                    default_lat, default_lng,
                    result['lat'], result['lng']
                ), 2)
        results.sort(key=lambda x: x['distance'])
    
    # Limit to top 10 results for faster loading
    results = results[:10]
    
    return jsonify({
        'medicine': {
            'id': medicine.id,
            'name': medicine.name,
            'description': medicine.description
        },
        'pharmacies': results
    })


@bp.route('/vip-consult', methods=['GET', 'POST'])
@vip_required
def vip_consult():
    """VIP consultation request form"""
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        specialty = request.form.get('specialty', '').strip()
        
        if not description or not specialty:
            flash('Please fill in all required fields.', 'danger')
            return render_template('vip_consult.html')
        
        # Handle file upload
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                import time
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                file.save(file_path)
                file_path = f"uploads/{filename}"
        
        # Create VIP consult
        vip_consult = VIPConsult(
            patient_id=current_user.id,
            description=description,
            specialty=specialty,
            file_path=file_path,
            status='pending'
        )
        
        db.session.add(vip_consult)
        db.session.flush()  # Get the ID
        
        # Find 5 random doctors with rating > 3 and matching specialty
        matching_doctors = DoctorProfile.query.filter(
            DoctorProfile.average_rating > 3.0,
            DoctorProfile.specialty.ilike(f'%{specialty}%')
        ).all()
        
        # If not enough matching specialty, include all doctors with rating > 3
        if len(matching_doctors) < 5:
            all_qualified = DoctorProfile.query.filter(
                DoctorProfile.average_rating > 3.0
            ).all()
            matching_doctors = all_qualified
        
        # Select up to 5 random doctors
        selected_doctors = random.sample(matching_doctors, min(5, len(matching_doctors)))
        
        # Create assignments
        for doctor in selected_doctors:
            assignment = VIPConsultAssignment(
                consult_id=vip_consult.id,
                doctor_id=doctor.id,
                status='pending'
            )
            db.session.add(assignment)
        
        db.session.commit()
        
        flash('VIP consultation request submitted! Doctors will be notified.', 'success')
        return redirect(url_for('routes.vip_consult'))
    
    # Get specialties for dropdown
    specialties = db.session.query(DoctorProfile.specialty).distinct().all()
    specialty_list = [s[0] for s in specialties]
    
    return render_template('vip_consult.html', specialties=specialty_list)


@bp.route('/upgrade')
def upgrade():
    """Upgrade to VIP page"""
    return render_template('upgrade.html')


def admin_required(f):
    """Decorator to require admin status"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('routes.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/admin')
def admin_dashboard():
    """Admin dashboard overview"""
    users = User.query.all()
    doctors = DoctorProfile.query.all()
    medicines = Medicine.query.all()
    pharmacies = Pharmacy.query.all()
    reviews = Review.query.all()
    vip_consults = VIPConsult.query.all()
    
    stats = {
        'total_users': len(users),
        'total_doctors': len(doctors),
        'total_medicines': len(medicines),
        'total_pharmacies': len(pharmacies),
        'total_reviews': len(reviews),
        'total_vip_consults': len(vip_consults),
        'vip_pending': len([v for v in vip_consults if v.status == 'pending'])
    }
    
    return render_template('admin.html', 
                         users=users, 
                         doctors=doctors, 
                         medicines=medicines, 
                         pharmacies=pharmacies, 
                         reviews=reviews,
                         vip_consults=vip_consults,
                         stats=stats,
                         active_tab='overview')


@bp.route('/admin/users')
def admin_users():
    """Manage users"""
    users = User.query.all()
    return render_template('admin.html', users=users, active_tab='users')


@bp.route('/admin/doctors')
def admin_doctors():
    """Manage doctors"""
    doctors = DoctorProfile.query.all()
    return render_template('admin.html', doctors=doctors, active_tab='doctors')


@bp.route('/admin/medicines')
def admin_medicines():
    """Manage medicines"""
    medicines = Medicine.query.all()
    return render_template('admin.html', medicines=medicines, active_tab='medicines')


@bp.route('/admin/pharmacies')
def admin_pharmacies():
    """Manage pharmacies"""
    pharmacies = Pharmacy.query.all()
    return render_template('admin.html', pharmacies=pharmacies, active_tab='pharmacies')


@bp.route('/admin/reviews')
def admin_reviews():
    """Manage reviews"""
    reviews = Review.query.all()
    return render_template('admin.html', reviews=reviews, active_tab='reviews')


@bp.route('/admin/vip-consults')
def admin_vip_consults():
    """Manage VIP consults"""
    vip_consults = VIPConsult.query.all()
    return render_template('admin.html', vip_consults=vip_consults, active_tab='vip_consults')


@bp.route('/admin/user/<int:user_id>/make-admin', methods=['POST'])
def make_admin(user_id):
    """Make a user admin"""
    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    flash(f'{user.name} is now an admin.', 'success')
    return redirect(url_for('routes.admin_users'))


@bp.route('/my-availability', methods=['GET', 'POST'])
@login_required
def my_availability():
    """Doctor availability management"""
    if current_user.role != 'doctor':
        flash('Access denied. Doctor account required.', 'danger')
        return redirect(url_for('routes.index'))
    
    doctor = current_user.doctor_profile
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        day = request.form.get('day')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        if not day or not start_time_str or not end_time_str:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('routes.my_availability'))
        
        try:
            from datetime import datetime
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            if start_time >= end_time:
                flash('Start time must be before end time.', 'danger')
                return redirect(url_for('routes.my_availability'))
            
            # Check for overlapping availability on the same day
            existing = Availability.query.filter_by(doctor_id=doctor.id, day=day).all()
            for avail in existing:
                if (start_time < avail.end_time and end_time > avail.start_time):
                    flash('Time slot overlaps with existing availability.', 'warning')
                    return redirect(url_for('routes.my_availability'))
            
            availability = Availability(
                doctor_id=doctor.id,
                day=day,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(availability)
            db.session.commit()
            flash('Availability added successfully!', 'success')
        except ValueError:
            flash('Invalid time format.', 'danger')
        
        return redirect(url_for('routes.my_availability'))
    
    availabilities = doctor.availabilities.order_by(Availability.day, Availability.start_time).all()
    return render_template('availability.html', availabilities=availabilities)


@bp.route('/my-pharmacy', methods=['GET', 'POST'])
@login_required
def my_pharmacy():
    """Pharmacy stock management"""
    if current_user.role != 'pharmacy':
        flash('Access denied. Pharmacy account required.', 'danger')
        return redirect(url_for('routes.index'))
    
    pharmacy = Pharmacy.query.filter_by(user_id=current_user.id).first()
    if not pharmacy:
        flash('Pharmacy profile not found.', 'danger')
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        medicine_name = request.form.get('medicine_name', '').strip()
        quantity = request.form.get('quantity', type=int)
        
        if not medicine_name or quantity is None or quantity < 0:
            flash('Please provide valid medicine name and quantity.', 'danger')
            return redirect(url_for('routes.my_pharmacy'))
        
        # Find or create medicine
        medicine = Medicine.query.filter_by(name=medicine_name).first()
        if not medicine:
            medicine = Medicine(name=medicine_name, description='Added by pharmacy')
            db.session.add(medicine)
            db.session.flush()
        
        # Update or create stock
        stock = PharmacyStock.query.filter_by(pharmacy_id=pharmacy.id, medicine_id=medicine.id).first()
        if stock:
            stock.quantity = quantity
        else:
            stock = PharmacyStock(pharmacy_id=pharmacy.id, medicine_id=medicine.id, quantity=quantity)
            db.session.add(stock)
        
        db.session.commit()
        flash('Stock updated successfully!', 'success')
        return redirect(url_for('routes.my_pharmacy'))
    
    # Get current stock
    stocks = PharmacyStock.query.filter_by(pharmacy_id=pharmacy.id).all()
    return render_template('pharmacy.html', pharmacy=pharmacy, stocks=stocks)


@bp.route('/pharmacy/<int:pharmacy_id>')
def pharmacy_profile(pharmacy_id):
    """Individual pharmacy profile page"""
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)
    stocks = PharmacyStock.query.filter_by(pharmacy_id=pharmacy_id).all()
    
    return render_template('pharmacy_profile.html', pharmacy=pharmacy, stocks=stocks)


@bp.route('/my-profile')
@login_required
def my_profile():
    """Redirect to user's profile based on role"""
    if current_user.role == 'doctor':
        if current_user.doctor_profile:
            return redirect(url_for('routes.doctor_profile', doctor_id=current_user.doctor_profile.id))
        else:
            # Create default doctor profile if missing
            doctor_profile = DoctorProfile(
                user_id=current_user.id,
                specialty='General Medicine',
                address='Default Address',
                phone='',
                bio='Please update your profile information.'
            )
            db.session.add(doctor_profile)
            db.session.commit()
            flash('Doctor profile created. Please update your information.', 'info')
            return redirect(url_for('routes.doctor_profile', doctor_id=doctor_profile.id))
    elif current_user.role == 'pharmacy':
        pharmacy = Pharmacy.query.filter_by(user_id=current_user.id).first()
        if pharmacy:
            return redirect(url_for('routes.pharmacy_profile', pharmacy_id=pharmacy.id))
        else:
            # Create default pharmacy if missing
            pharmacy = Pharmacy(
                name=f"{current_user.name}'s Pharmacy",
                address='Default Address, Tunisia',
                lat=36.8, lng=10.2,  # Default location in Tunisia
                user_id=current_user.id
            )
            db.session.add(pharmacy)
            db.session.commit()
            flash('Pharmacy profile created. Please update your information.', 'info')
            return redirect(url_for('routes.pharmacy_profile', pharmacy_id=pharmacy.id))
    else:
        flash('No profile available for your role.', 'info')
        return redirect(url_for('routes.index'))

