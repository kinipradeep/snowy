from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Template
from forms import TemplateForm
from utils import login_required, get_current_user
import logging
import json

templates_bp = Blueprint('templates', __name__)

@templates_bp.route('/')
@login_required
def templates():
    """List all templates for current user"""
    user = get_current_user()
    template_type = request.args.get('type', '')
    
    query = Template.query.filter_by(user_id=user.id)
    
    # Filter by template type if specified
    if template_type:
        query = query.filter_by(template_type=template_type)
    
    templates = query.order_by(Template.name).all()
    
    # Get template type counts
    type_counts = {
        'email': Template.query.filter_by(user_id=user.id, template_type='email').count(),
        'sms': Template.query.filter_by(user_id=user.id, template_type='sms').count(),
        'whatsapp': Template.query.filter_by(user_id=user.id, template_type='whatsapp').count(),
        'rcs': Template.query.filter_by(user_id=user.id, template_type='rcs').count(),
    }
    
    return render_template('templates/templates.html', 
                         templates=templates, 
                         selected_type=template_type,
                         type_counts=type_counts)

@templates_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_template():
    """Create new template"""
    user = get_current_user()
    
    if request.method == 'POST':
        form = TemplateForm()
        if form.validate():
            # Check if template name already exists for this user
            existing_template = Template.query.filter_by(name=form.name, user_id=user.id).first()
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
                user_id=user.id
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
    user = get_current_user()
    template = Template.query.filter_by(id=template_id, user_id=user.id).first_or_404()
    
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
    user = get_current_user()
    template = Template.query.filter_by(id=template_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        form = TemplateForm()
        if form.validate():
            # Check if template name already exists for this user (excluding current template)
            existing_template = Template.query.filter_by(name=form.name, user_id=user.id).filter(Template.id != template.id).first()
            if existing_template:
                form.errors['name'] = 'A template with this name already exists'
                return render_template('templates/template_form.html', template=template, errors=form.errors, form_data=request.form)
            
            # Prepare variables list
            variables_text = request.form.get('variables', '').strip()
            variables = []
            if variables_text:
                variables = [var.strip() for var in variables_text.split('\n') if var.strip()]
            
            template.name = form.name
            template.template_type = form.template_type
            template.subject = form.subject or None
            template.content = form.content
            template.variables = json.dumps(variables) if variables else None
            
            try:
                db.session.commit()
                flash(f'Template "{template.name}" has been updated successfully!', 'success')
                return redirect(url_for('templates.template_detail', template_id=template.id))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Template update error: {e}")
                flash('An error occurred while updating the template. Please try again.', 'danger')
        
        return render_template('templates/template_form.html', template=template, errors=form.errors, form_data=request.form)
    
    return render_template('templates/template_form.html', template=template)

@templates_bp.route('/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete template"""
    user = get_current_user()
    template = Template.query.filter_by(id=template_id, user_id=user.id).first_or_404()
    
    try:
        db.session.delete(template)
        db.session.commit()
        flash(f'Template "{template.name}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Template deletion error: {e}")
        flash('An error occurred while deleting the template. Please try again.', 'danger')
    
    return redirect(url_for('templates.templates'))

@templates_bp.route('/<int:template_id>/duplicate', methods=['POST'])
@login_required
def duplicate_template(template_id):
    """Duplicate template"""
    user = get_current_user()
    original_template = Template.query.filter_by(id=template_id, user_id=user.id).first_or_404()
    
    # Create new template with copied data
    new_template = Template(
        name=f"{original_template.name} (Copy)",
        template_type=original_template.template_type,
        subject=original_template.subject,
        content=original_template.content,
        variables=original_template.variables,
        user_id=user.id
    )
    
    try:
        db.session.add(new_template)
        db.session.commit()
        flash(f'Template "{new_template.name}" has been created successfully!', 'success')
        return redirect(url_for('templates.edit_template', template_id=new_template.id))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Template duplication error: {e}")
        flash('An error occurred while duplicating the template. Please try again.', 'danger')
        return redirect(url_for('templates.template_detail', template_id=template_id))
