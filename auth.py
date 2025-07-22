from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from app import db
from models import User, PasswordResetToken, Organization, UserRole
from forms import LoginForm, RegisterForm, PasswordResetRequestForm, PasswordResetForm
from utils import generate_token
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        form = LoginForm()
        if form.validate():
            user = User.query.filter_by(username=form.username).first()
            
            if user and user.check_password(form.password):
                if not user.is_active:
                    flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                    return render_template('auth/login.html', errors=form.errors)
                
                session['user_id'] = user.id
                session['username'] = user.username
                session.permanent = True
                
                flash(f'Welcome back, {user.first_name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
        
        return render_template('auth/login.html', errors=form.errors)
    
    return render_template('auth/login.html', errors={})

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        form = RegisterForm()
        if form.validate():
            # Check if username already exists
            if User.query.filter_by(username=form.username).first():
                form.errors['username'] = 'Username already exists'
                return render_template('auth/register.html', errors=form.errors)
            
            # Check if email already exists
            if User.query.filter_by(email=form.email).first():
                form.errors['email'] = 'Email already registered'
                return render_template('auth/register.html', errors=form.errors)
            
            # Create new user
            user = User(
                username=form.username,
                email=form.email,
                first_name=form.first_name,
                last_name=form.last_name
            )
            user.set_password(form.password)
            
            try:
                db.session.add(user)
                db.session.flush()  # Flush to get the user ID
                
                # Create default organization for the user
                org_name = f"{user.full_name}'s Organization"
                organization = Organization(
                    name=org_name,
                    description=f"Default organization for {user.full_name}",
                    owner_id=user.id
                )
                db.session.add(organization)
                db.session.flush()  # Flush to get organization ID
                
                # Add user as owner of the organization
                user_role = UserRole(
                    user_id=user.id,
                    organization_id=organization.id,
                    role='owner'
                )
                db.session.add(user_role)
                
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
        
        return render_template('auth/register.html', errors=form.errors)
    
    return render_template('auth/register.html', errors={})

@auth_bp.route('/logout')
def logout():
    """User logout"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/reset-request', methods=['GET', 'POST'])
def reset_request():
    """Request password reset"""
    if request.method == 'POST':
        form = PasswordResetRequestForm()
        if form.validate():
            user = User.query.filter_by(email=form.email).first()
            
            if user:
                # Generate reset token
                token = generate_token()
                expires_at = datetime.utcnow() + timedelta(hours=1)
                
                reset_token = PasswordResetToken(
                    user_id=user.id,
                    token=token,
                    expires_at=expires_at
                )
                
                try:
                    db.session.add(reset_token)
                    db.session.commit()
                    
                    # In a real application, you would send an email here
                    # For now, we'll just log the token and show a message
                    logging.info(f"Password reset token for {user.email}: {token}")
                    flash('Password reset instructions have been sent to your email.', 'info')
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Reset token generation error: {e}")
                    flash('An error occurred. Please try again.', 'danger')
            else:
                # Don't reveal if email exists or not
                flash('If that email address exists in our system, you will receive password reset instructions.', 'info')
                return redirect(url_for('auth.login'))
        
        return render_template('auth/reset_request.html', errors=form.errors)
    
    return render_template('auth/reset_request.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    
    if not reset_token or reset_token.is_expired():
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.reset_request'))
    
    if request.method == 'POST':
        form = PasswordResetForm()
        if form.validate():
            user = reset_token.user
            user.set_password(form.password)
            reset_token.used = True
            
            try:
                db.session.commit()
                flash('Your password has been reset successfully!', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Password reset error: {e}")
                flash('An error occurred. Please try again.', 'danger')
        
        return render_template('auth/reset_password.html', errors=form.errors, token=token)
    
    return render_template('auth/reset_password.html', token=token)
