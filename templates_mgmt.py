from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from models import Template, Organization, User
from forms import TemplateForm
from utils import login_required, get_current_user, get_current_organization
import logging
import json

templates_bp = Blueprint('templates', __name__)

@templates_bp.route('/')
@login_required
def templates():
    """List all templates for current organization"""
    organization = get_current_organization()
    if not organization:
        return redirect(url_for('organizations.organizations'))
    
    # Get filter and search parameters
    template_type = request.args.get('type', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Template.query.filter_by(organization_id=organization.id)
    
    # Apply type filter
    if template_type:
        query = query.filter_by(template_type=template_type)
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                Template.name.ilike(f'%{search}%'),
                Template.content.ilike(f'%{search}%'),
                Template.subject.ilike(f'%{search}%')
            )
        )
    
    # Order and paginate
    templates = query.order_by(Template.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('templates/templates.html', 
                         templates=templates, 
                         template_type=template_type, 
                         search=search)

@templates_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_template():
    """Create new template"""
    user = get_current_user()
    organization = get_current_organization()
    
    if not organization:
        return redirect(url_for('organizations.organizations'))
    
    if request.method == 'POST':
        form = TemplateForm()
        if form.validate():
            # Check if template name already exists for this organization
            existing_template = Template.query.filter_by(name=form.name, organization_id=organization.id).first()
            if existing_template:
                form.errors['name'] = 'A template with this name already exists'
                return render_template('templates/template_form.html', errors=form.errors, form_data=request.form)
            
            # Prepare variables list
            variables_text = request.form.get('variables', '').strip()
            variables = []
            if variables_text:
                # Parse variables (one per line)
                variables = [var.strip() for var in variables_text.split('\n') if var.strip()]
            
            template = Template(
                name=form.name,
                template_type=form.template_type,
                subject=form.subject or None,
                content=form.content,
                variables=json.dumps(variables) if variables else None,
                organization_id=organization.id,
                created_by_id=user.id
            )
            
            try:
                db.session.add(template)
                db.session.commit()
                flash(f'Template "{template.name}" has been created successfully!', 'success')
                return redirect(url_for('templates.templates'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Template creation error: {e}")
                flash('An error occurred while creating the template. Please try again.', 'danger')
        
        return render_template('templates/template_form.html', errors=form.errors, form_data=request.form)
    
    return render_template('templates/template_form.html', errors={})

@templates_bp.route('/<int:template_id>')
@login_required
def template_detail(template_id):
    """View template details"""
    organization = get_current_organization()
    template = Template.query.filter_by(id=template_id, organization_id=organization.id).first_or_404()
    
    # Parse variables
    variables = []
    if template.variables:
        try:
            variables = json.loads(template.variables)
        except json.JSONDecodeError:
            variables = []
    
    return render_template('templates/template_detail.html', template=template, variables=variables)

@templates_bp.route('/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    """Edit existing template"""
    organization = get_current_organization()
    template = Template.query.filter_by(id=template_id, organization_id=organization.id).first_or_404()
    
    if request.method == 'POST':
        form = TemplateForm()
        if form.validate():
            # Check if template name already exists for this organization (excluding current template)
            existing_template = Template.query.filter_by(
                name=form.name, 
                organization_id=organization.id
            ).filter(Template.id != template.id).first()
            if existing_template:
                form.errors['name'] = 'A template with this name already exists'
                return render_template('templates/template_form.html', template=template, errors=form.errors, form_data=request.form)
            
            template.name = form.name
            template.template_type = form.template_type
            template.subject = form.subject or None
            template.content = form.content
            
            # Update variables
            variables_text = request.form.get('variables', '').strip()
            variables = []
            if variables_text:
                variables = [var.strip() for var in variables_text.split('\n') if var.strip()]
            template.variables = json.dumps(variables) if variables else None
            
            try:
                db.session.commit()
                flash(f'Template "{template.name}" has been updated successfully!', 'success')
                return redirect(url_for('templates.template_detail', template_id=template.id))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Template update error: {e}")
                flash('An error occurred while updating the template. Please try again.', 'danger')
        
        # Parse variables for form display
        variables_text = ''
        if template.variables:
            try:
                variables = json.loads(template.variables)
                variables_text = '\n'.join(variables)
            except json.JSONDecodeError:
                variables_text = ''
        
        return render_template('templates/template_form.html', 
                             template=template, 
                             variables_text=variables_text,
                             errors=form.errors, 
                             form_data=request.form)
    
    # Parse variables for form display
    variables_text = ''
    if template.variables:
        try:
            variables = json.loads(template.variables)
            variables_text = '\n'.join(variables)
        except json.JSONDecodeError:
            variables_text = ''
    
    return render_template('templates/template_form.html', 
                         template=template, 
                         variables_text=variables_text, 
                         errors={})

@templates_bp.route('/<int:template_id>/duplicate', methods=['POST'])
@login_required
def duplicate_template(template_id):
    """Create a copy of existing template"""
    user = get_current_user()
    organization = get_current_organization()
    template = Template.query.filter_by(id=template_id, organization_id=organization.id).first_or_404()
    
    # Generate unique name for duplicate
    base_name = f"{template.name} (Copy)"
    duplicate_name = base_name
    counter = 1
    
    while Template.query.filter_by(name=duplicate_name, organization_id=organization.id).first():
        duplicate_name = f"{base_name} {counter}"
        counter += 1
    
    duplicate_template = Template(
        name=duplicate_name,
        template_type=template.template_type,
        subject=template.subject,
        content=template.content,
        variables=template.variables,
        organization_id=organization.id,
        created_by_id=user.id
    )
    
    try:
        db.session.add(duplicate_template)
        db.session.commit()
        flash(f'Template "{duplicate_template.name}" has been created as a copy!', 'success')
        return redirect(url_for('templates.template_detail', template_id=duplicate_template.id))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Template duplication error: {e}")
        flash('An error occurred while duplicating the template. Please try again.', 'danger')
        return redirect(url_for('templates.template_detail', template_id=template.id))

@templates_bp.route('/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete template"""
    organization = get_current_organization()
    template = Template.query.filter_by(id=template_id, organization_id=organization.id).first_or_404()
    
    try:
        db.session.delete(template)
        db.session.commit()
        flash(f'Template "{template.name}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Template deletion error: {e}")
        flash('An error occurred while deleting the template. Please try again.', 'danger')
    
    return redirect(url_for('templates.templates'))