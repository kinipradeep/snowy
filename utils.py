from functools import wraps
from flask import session, redirect, url_for, flash
from models import User
import secrets
import string

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Verify user still exists
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_active or not user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def generate_token(length=32):
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_current_user():
    """Get current logged in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def get_current_organization():
    """Get current active organization for user"""
    user = get_current_user()
    if user:
        return user.get_current_organization()
    return None

def organization_required(f):
    """Decorator to require user to be in an organization"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = get_current_user()
        if not user or not user.is_active:
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        organization = get_current_organization()
        if not organization:
            flash('Please select an organization to continue.', 'warning')
            return redirect(url_for('organizations.organizations'))
        
        return f(*args, **kwargs)
    return decorated_function

def format_phone(phone):
    """Format phone number for display"""
    if not phone:
        return ''
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone

def truncate_text(text, length=50):
    """Truncate text to specified length"""
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length-3] + '...'
