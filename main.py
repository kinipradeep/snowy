from flask import render_template, redirect, url_for, session, request
from app import app, db
from models import User, Contact, Group, Template, Organization, UserRole
from utils import login_required, get_current_user, get_current_organization
import logging

@app.route('/')
def index():
    """Home page - dashboard for logged in users, landing for others"""
    if 'user_id' not in session:
        return render_template('index.html', logged_in=False)
    
    user = get_current_user()
    if not user:
        session.clear()
        return render_template('index.html', logged_in=False)
    
    # Check if user has any organizations
    organization = get_current_organization()
    if not organization:
        # Redirect to organization selection if no active organization
        return redirect(url_for('organizations.organizations'))
    
    # Dashboard data for logged in users within current organization
    total_contacts = Contact.query.filter_by(organization_id=organization.id).count()
    total_groups = Group.query.filter_by(organization_id=organization.id).count()
    total_templates = Template.query.filter_by(organization_id=organization.id).count()
    recent_contacts = Contact.query.filter_by(organization_id=organization.id).order_by(Contact.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         logged_in=True, 
                         user=user,
                         organization=organization,
                         total_contacts=total_contacts,
                         total_groups=total_groups,
                         total_templates=total_templates,
                         recent_contacts=recent_contacts)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for authenticated users"""
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
