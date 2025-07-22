from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import db
from models import Contact, Group, Organization, User
from forms import ContactForm
from utils import login_required, get_current_user, get_current_organization
import logging
import csv
import io
from werkzeug.utils import secure_filename

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/')
@login_required
def contacts():
    """List all contacts for current organization"""
    organization = get_current_organization()
    if not organization:
        return redirect(url_for('organizations.organizations'))
    
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    group_filter = request.args.get('group', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Contact.query.filter_by(organization_id=organization.id)
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                Contact.first_name.ilike(f'%{search}%'),
                Contact.last_name.ilike(f'%{search}%'),
                Contact.email.ilike(f'%{search}%'),
                Contact.company.ilike(f'%{search}%')
            )
        )
    
    # Apply group filter
    if group_filter:
        query = query.filter_by(group_id=group_filter)
    
    # Order and paginate
    contacts = query.order_by(Contact.first_name, Contact.last_name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get groups for filter dropdown
    groups = Group.query.filter_by(organization_id=organization.id).order_by(Group.name).all()
    
    return render_template('contacts/contacts.html', 
                         contacts=contacts, 
                         groups=groups,
                         search=search,
                         group_filter=group_filter)

@contacts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_contact():
    """Create new contact"""
    user = get_current_user()
    organization = get_current_organization()
    
    if not organization:
        return redirect(url_for('organizations.organizations'))
    
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
                organization_id=organization.id,
                created_by_id=user.id
            )
            
            # Set group if provided
            group_id = request.form.get('group_id', type=int)
            if group_id:
                group = Group.query.filter_by(id=group_id, organization_id=organization.id).first()
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
        
        groups = Group.query.filter_by(organization_id=organization.id).order_by(Group.name).all()
        return render_template('contacts/contact_form.html', 
                             errors=form.errors, 
                             groups=groups,
                             form_data=request.form)
    
    groups = Group.query.filter_by(organization_id=organization.id).order_by(Group.name).all()
    return render_template('contacts/contact_form.html', groups=groups, errors={})

@contacts_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_contacts():
    """Import contacts from CSV"""
    user = get_current_user()
    organization = get_current_organization()
    
    if not organization:
        return redirect(url_for('organizations.organizations'))
    
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith('.csv'):
            try:
                # Read CSV content
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                imported_count = 0
                skipped_count = 0
                errors = []
                
                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
                    try:
                        # Skip empty rows
                        if not any(row.values()):
                            continue
                        
                        # Required fields
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        
                        if not first_name or not last_name:
                            errors.append(f"Row {row_num}: First name and last name are required")
                            skipped_count += 1
                            continue
                        
                        # Check for duplicate email
                        email = row.get('email', '').strip() or None
                        if email:
                            existing = Contact.query.filter_by(email=email, organization_id=organization.id).first()
                            if existing:
                                errors.append(f"Row {row_num}: Email {email} already exists")
                                skipped_count += 1
                                continue
                        
                        # Find group by name if specified
                        group_id = None
                        group_name = row.get('group', '').strip()
                        if group_name:
                            group = Group.query.filter_by(name=group_name, organization_id=organization.id).first()
                            if group:
                                group_id = group.id
                        
                        # Create contact
                        contact = Contact(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone=row.get('phone', '').strip() or None,
                            mobile=row.get('mobile', '').strip() or None,
                            company=row.get('company', '').strip() or None,
                            job_title=row.get('job_title', '').strip() or None,
                            address=row.get('address', '').strip() or None,
                            city=row.get('city', '').strip() or None,
                            state=row.get('state', '').strip() or None,
                            postal_code=row.get('postal_code', '').strip() or None,
                            country=row.get('country', '').strip() or None,
                            notes=row.get('notes', '').strip() or None,
                            organization_id=organization.id,
                            created_by_id=user.id,
                            group_id=group_id
                        )
                        
                        db.session.add(contact)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        skipped_count += 1
                
                try:
                    db.session.commit()
                    
                    # Show results
                    if imported_count > 0:
                        flash(f'Successfully imported {imported_count} contacts', 'success')
                    if skipped_count > 0:
                        flash(f'Skipped {skipped_count} rows due to errors', 'warning')
                    if errors:
                        flash('Import errors: ' + '; '.join(errors[:5]) + ('...' if len(errors) > 5 else ''), 'danger')
                    
                    return redirect(url_for('contacts.contacts'))
                    
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"CSV import error: {e}")
                    flash('An error occurred while saving contacts. Please try again.', 'danger')
                    
            except Exception as e:
                logging.error(f"CSV processing error: {e}")
                flash(f'Error processing CSV file: {str(e)}', 'danger')
        else:
            flash('Please upload a CSV file', 'danger')
    
    return render_template('contacts/import.html')

@contacts_bp.route('/<int:contact_id>')
@login_required
def contact_detail(contact_id):
    """View contact details"""
    organization = get_current_organization()
    contact = Contact.query.filter_by(id=contact_id, organization_id=organization.id).first_or_404()
    return render_template('contacts/contact_detail.html', contact=contact)

@contacts_bp.route('/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    """Edit existing contact"""
    user = get_current_user()
    organization = get_current_organization()
    contact = Contact.query.filter_by(id=contact_id, organization_id=organization.id).first_or_404()
    
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
                group = Group.query.filter_by(id=group_id, organization_id=organization.id).first()
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
        
        groups = Group.query.filter_by(organization_id=organization.id).order_by(Group.name).all()
        return render_template('contacts/contact_form.html', 
                             contact=contact, 
                             errors=form.errors, 
                             groups=groups,
                             form_data=request.form)
    
    groups = Group.query.filter_by(organization_id=organization.id).order_by(Group.name).all()
    return render_template('contacts/contact_form.html', contact=contact, groups=groups, errors={})

@contacts_bp.route('/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    """Delete contact"""
    organization = get_current_organization()
    contact = Contact.query.filter_by(id=contact_id, organization_id=organization.id).first_or_404()
    
    try:
        db.session.delete(contact)
        db.session.commit()
        flash(f'Contact {contact.full_name} has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Contact deletion error: {e}")
        flash('An error occurred while deleting the contact. Please try again.', 'danger')
    
    return redirect(url_for('contacts.contacts'))