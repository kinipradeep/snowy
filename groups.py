from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Group, Contact
from forms import GroupForm
from utils import login_required, get_current_user
import logging

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/')
@login_required
def groups():
    """List all groups for current user"""
    user = get_current_user()
    groups = Group.query.filter_by(user_id=user.id).order_by(Group.name).all()
    
    # Add contact count for each group
    for group in groups:
        group.contact_count = Contact.query.filter_by(group_id=group.id).count()
    
    return render_template('groups/groups.html', groups=groups)

@groups_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_group():
    """Create new group"""
    user = get_current_user()
    
    if request.method == 'POST':
        form = GroupForm()
        if form.validate():
            # Check if group name already exists for this user
            existing_group = Group.query.filter_by(name=form.name, user_id=user.id).first()
            if existing_group:
                form.errors['name'] = 'A group with this name already exists'
                return render_template('groups/group_form.html', errors=form.errors, form_data=request.form)
            
            group = Group(
                name=form.name,
                description=form.description or None,
                user_id=user.id
            )
            
            try:
                db.session.add(group)
                db.session.commit()
                flash(f'Group "{group.name}" has been created successfully!', 'success')
                return redirect(url_for('groups.groups'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Group creation error: {e}")
                flash('An error occurred while creating the group. Please try again.', 'danger')
        
        return render_template('groups/group_form.html', errors=form.errors, form_data=request.form)
    
    return render_template('groups/group_form.html')

@groups_bp.route('/<int:group_id>')
@login_required
def group_detail(group_id):
    """View group details"""
    user = get_current_user()
    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    
    # Get contacts in this group
    contacts = Contact.query.filter_by(group_id=group.id).order_by(Contact.first_name, Contact.last_name).all()
    
    return render_template('groups/group_detail.html', group=group, contacts=contacts)

@groups_bp.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit existing group"""
    user = get_current_user()
    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        form = GroupForm()
        if form.validate():
            # Check if group name already exists for this user (excluding current group)
            existing_group = Group.query.filter_by(name=form.name, user_id=user.id).filter(Group.id != group.id).first()
            if existing_group:
                form.errors['name'] = 'A group with this name already exists'
                return render_template('groups/group_form.html', group=group, errors=form.errors, form_data=request.form)
            
            group.name = form.name
            group.description = form.description or None
            
            try:
                db.session.commit()
                flash(f'Group "{group.name}" has been updated successfully!', 'success')
                return redirect(url_for('groups.group_detail', group_id=group.id))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Group update error: {e}")
                flash('An error occurred while updating the group. Please try again.', 'danger')
        
        return render_template('groups/group_form.html', group=group, errors=form.errors, form_data=request.form)
    
    return render_template('groups/group_form.html', group=group)

@groups_bp.route('/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    """Delete group"""
    user = get_current_user()
    group = Group.query.filter_by(id=group_id, user_id=user.id).first_or_404()
    
    # Check if group has contacts
    contact_count = Contact.query.filter_by(group_id=group.id).count()
    if contact_count > 0:
        flash(f'Cannot delete group "{group.name}" because it contains {contact_count} contacts. Please move or delete the contacts first.', 'danger')
        return redirect(url_for('groups.group_detail', group_id=group.id))
    
    try:
        db.session.delete(group)
        db.session.commit()
        flash(f'Group "{group.name}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Group deletion error: {e}")
        flash('An error occurred while deleting the group. Please try again.', 'danger')
    
    return redirect(url_for('groups.groups'))
