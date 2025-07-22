from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from models import Contact, Group, User
from forms import ContactForm
from utils import login_required, get_current_user
import logging

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/')
@login_required
def contacts():
    """List all contacts for current user"""
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    group_id = request.args.get('group', type=int)
    
    query = Contact.query.filter_by(user_id=user.id)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Contact.first_name.ilike(search_term)) |
            (Contact.last_name.ilike(search_term)) |
            (Contact.email.ilike(search_term)) |
            (Contact.company.ilike(search_term))
        )
    
    # Apply group filter
    if group_id:
        query = query.filter_by(group_id=group_id)
    
    contacts = query.order_by(Contact.first_name, Contact.last_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get groups for filter dropdown
    groups = Group.query.filter_by(user_id=user.id).order_by(Group.name).all()
    
    return render_template('contacts/contacts.html', 
                         contacts=contacts, 
                         groups=groups, 
                         search=search,
                         selected_group=group_id)

@contacts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_contact():
    """Create new contact"""
    user = get_current_user()
    
    if request.method == 'POST':
        form = ContactForm()
        if form.validate():
            contact = Contact(
                first_name=form.first_name,
                last_name=form.last_name,
                email=form.email or None,
                phone=form.phone or None,
                mobile=form.mobile or None,
                company=form.company or None,
                job_title=form.job_title or None,
                address=request.form.get('address', '').strip() or None,
                city=form.city or None,
                state=form.state or None,
                postal_code=form.postal_code or None,
                country=form.country or None,
                notes=request.form.get('notes', '').strip() or None,
                user_id=user.id
            )
            
            # Set group if provided
            group_id = request.form.get('group_id', type=int)
            if group_id:
                group = Group.query.filter_by(id=group_id, user_id=user.id).first()
                if group:
                    contact.group_id = group_id
            
            try:
                db.session.add(contact)
                db.session.commit()
                flash(f'Contact {contact.full_name} has been created successfully!', 'success')
                return redirect(url_for('contacts.contacts'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Contact creation error: {e}")
                flash('An error occurred while creating the contact. Please try again.', 'danger')
        
        groups = Group.query.filter_by(user_id=user.id).order_by(Group.name).all()
        return render_template('contacts/contact_form.html', 
                             errors=form.errors, 
                             groups=groups,
                             form_data=request.form)
    
    groups = Group.query.filter_by(user.id).order_by(Group.name).all()
    return render_template('contacts/contact_form.html', groups=groups)

@contacts_bp.route('/<int:contact_id>')
@login_required
def contact_detail(contact_id):
    """View contact details"""
    user = get_current_user()
    contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first_or_404()
    return render_template('contacts/contact_detail.html', contact=contact)

@contacts_bp.route('/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    """Edit existing contact"""
    user = get_current_user()
    contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        form = ContactForm()
        if form.validate():
            contact.first_name = form.first_name
            contact.last_name = form.last_name
            contact.email = form.email or None
            contact.phone = form.phone or None
            contact.mobile = form.mobile or None
            contact.company = form.company or None
            contact.job_title = form.job_title or None
            contact.address = request.form.get('address', '').strip() or None
            contact.city = form.city or None
            contact.state = form.state or None
            contact.postal_code = form.postal_code or None
            contact.country = form.country or None
            contact.notes = request.form.get('notes', '').strip() or None
            
            # Update group if provided
            group_id = request.form.get('group_id', type=int)
            if group_id:
                group = Group.query.filter_by(id=group_id, user_id=user.id).first()
                contact.group_id = group_id if group else None
            else:
                contact.group_id = None
            
            try:
                db.session.commit()
                flash(f'Contact {contact.full_name} has been updated successfully!', 'success')
                return redirect(url_for('contacts.contact_detail', contact_id=contact.id))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Contact update error: {e}")
                flash('An error occurred while updating the contact. Please try again.', 'danger')
        
        groups = Group.query.filter_by(user_id=user.id).order_by(Group.name).all()
        return render_template('contacts/contact_form.html', 
                             contact=contact, 
                             errors=form.errors, 
                             groups=groups,
                             form_data=request.form)
    
    groups = Group.query.filter_by(user_id=user.id).order_by(Group.name).all()
    return render_template('contacts/contact_form.html', contact=contact, groups=groups)

@contacts_bp.route('/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    """Delete contact"""
    user = get_current_user()
    contact = Contact.query.filter_by(id=contact_id, user_id=user.id).first_or_404()
    
    try:
        db.session.delete(contact)
        db.session.commit()
        flash(f'Contact {contact.full_name} has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Contact deletion error: {e}")
        flash('An error occurred while deleting the contact. Please try again.', 'danger')
    
    return redirect(url_for('contacts.contacts'))
