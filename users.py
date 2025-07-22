from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from models import User
from forms import RegisterForm
from utils import admin_required, get_current_user
import logging

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@admin_required
def users():
    """List all users (admin only)"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = User.query
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term))
        )
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'admin':
        query = query.filter_by(is_admin=True)
    
    users = query.order_by(User.username).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('users/users.html', 
                         users=users, 
                         search=search,
                         status_filter=status_filter)

@users_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    """Create new user (admin only)"""
    if request.method == 'POST':
        form = RegisterForm()
        if form.validate():
            # Check if username already exists
            if User.query.filter_by(username=form.username).first():
                form.errors['username'] = 'Username already exists'
                return render_template('users/user_form.html', errors=form.errors, form_data=request.form)
            
            # Check if email already exists
            if User.query.filter_by(email=form.email).first():
                form.errors['email'] = 'Email already registered'
                return render_template('users/user_form.html', errors=form.errors, form_data=request.form)
            
            # Create new user
            user = User(
                username=form.username,
                email=form.email,
                first_name=form.first_name,
                last_name=form.last_name,
                is_admin=request.form.get('is_admin') == 'on',
                is_active=request.form.get('is_active', 'on') == 'on'
            )
            user.set_password(form.password)
            
            try:
                db.session.add(user)
                db.session.commit()
                flash(f'User "{user.username}" has been created successfully!', 'success')
                return redirect(url_for('users.users'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"User creation error: {e}")
                flash('An error occurred while creating the user. Please try again.', 'danger')
        
        return render_template('users/user_form.html', errors=form.errors, form_data=request.form)
    
    return render_template('users/user_form.html')

@users_bp.route('/<int:user_id>')
@admin_required
def user_detail(user_id):
    """View user details (admin only)"""
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    contact_count = len(user.contacts)
    group_count = len(user.groups)
    template_count = len(user.templates)
    
    return render_template('users/user_detail.html', 
                         user=user,
                         contact_count=contact_count,
                         group_count=group_count,
                         template_count=template_count)

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit existing user (admin only)"""
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    
    if request.method == 'POST':
        # Basic validation
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        errors = {}
        
        if not username:
            errors['username'] = 'Username is required'
        elif username != user.username and User.query.filter_by(username=username).first():
            errors['username'] = 'Username already exists'
        
        if not email:
            errors['email'] = 'Email is required'
        elif email != user.email and User.query.filter_by(email=email).first():
            errors['email'] = 'Email already registered'
        
        if not first_name:
            errors['first_name'] = 'First name is required'
        
        if not last_name:
            errors['last_name'] = 'Last name is required'
        
        if not errors:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            
            # Only allow admin status changes if current user is admin and not editing themselves
            if current_user.is_admin and user.id != current_user.id:
                user.is_admin = request.form.get('is_admin') == 'on'
                user.is_active = request.form.get('is_active', 'on') == 'on'
            
            # Handle password change
            new_password = request.form.get('password', '').strip()
            if new_password:
                if len(new_password) < 6:
                    errors['password'] = 'Password must be at least 6 characters long'
                else:
                    confirm_password = request.form.get('confirm_password', '').strip()
                    if new_password != confirm_password:
                        errors['confirm_password'] = 'Passwords do not match'
                    else:
                        user.set_password(new_password)
            
            if not errors:
                try:
                    db.session.commit()
                    flash(f'User "{user.username}" has been updated successfully!', 'success')
                    return redirect(url_for('users.user_detail', user_id=user.id))
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"User update error: {e}")
                    flash('An error occurred while updating the user. Please try again.', 'danger')
        
        return render_template('users/user_form.html', 
                             user=user, 
                             errors=errors, 
                             form_data=request.form,
                             current_user=current_user)
    
    return render_template('users/user_form.html', user=user, current_user=current_user)

@users_bp.route('/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('users.user_detail', user_id=user.id))
    
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User "{user.username}" has been {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"User status toggle error: {e}")
        flash('An error occurred while updating the user status. Please try again.', 'danger')
    
    return redirect(url_for('users.user_detail', user_id=user.id))

@users_bp.route('/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin_status(user_id):
    """Toggle user admin status (admin only)"""
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    
    # Prevent admin from removing their own admin status
    if user.id == current_user.id:
        flash('You cannot modify your own admin status.', 'danger')
        return redirect(url_for('users.user_detail', user_id=user.id))
    
    user.is_admin = not user.is_admin
    
    try:
        db.session.commit()
        status = 'granted' if user.is_admin else 'removed'
        flash(f'Admin privileges have been {status} for user "{user.username}"!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"User admin toggle error: {e}")
        flash('An error occurred while updating admin status. Please try again.', 'danger')
    
    return redirect(url_for('users.user_detail', user_id=user.id))

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users.user_detail', user_id=user.id))
    
    # Check if user has data that would be deleted
    contact_count = len(user.contacts)
    group_count = len(user.groups)
    template_count = len(user.templates)
    
    if contact_count > 0 or group_count > 0 or template_count > 0:
        flash(f'Cannot delete user "{user.username}" because they have associated data. Deactivate the user instead.', 'danger')
        return redirect(url_for('users.user_detail', user_id=user.id))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{user.username}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"User deletion error: {e}")
        flash('An error occurred while deleting the user. Please try again.', 'danger')
    
    return redirect(url_for('users.users'))
