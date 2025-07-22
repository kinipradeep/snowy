from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from models import Organization, User, UserRole, OrganizationInvitation, Contact, Group, Template
from forms import FormValidator
from utils import login_required, get_current_user
import logging

organizations_bp = Blueprint('organizations', __name__)

class OrganizationForm(FormValidator):
    """Organization form validator"""
    
    def validate(self):
        self.name = self.validate_length('name', min_length=1, max_length=100)
        self.description = self.data.get('description', '').strip()
        return self.is_valid()

class InvitationForm(FormValidator):
    """Invitation form validator"""
    
    def validate(self):
        self.email = self.validate_email('email')
        self.role = self.validate_required('role', 'Role is required')
        
        # Validate role is valid
        valid_roles = ['member', 'admin']
        if self.role not in valid_roles:
            self.errors['role'] = 'Invalid role selected'
        
        return self.is_valid()

@organizations_bp.route('/')
@login_required
def organizations():
    """List user's organizations"""
    user = get_current_user()
    user_roles = UserRole.query.filter_by(user_id=user.id).all()
    
    return render_template('organizations/organizations.html', 
                         user_roles=user_roles, 
                         user=user)

@organizations_bp.route('/switch/<int:org_id>')
@login_required
def switch_organization(org_id):
    """Switch to a different organization"""
    user = get_current_user()
    
    # Check if user has access to this organization
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role:
        flash('You do not have access to that organization.', 'danger')
        return redirect(url_for('organizations.organizations'))
    
    # Deactivate current active organization
    UserRole.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
    
    # Activate new organization
    user_role.is_active = True
    db.session.commit()
    
    flash(f'Switched to {user_role.organization.name}', 'success')
    return redirect(url_for('index'))

@organizations_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_organization():
    """Create new organization"""
    if request.method == 'POST':
        form = OrganizationForm()
        if form.validate():
            user = get_current_user()
            
            try:
                # Create organization
                organization = Organization(
                    name=form.name,
                    description=form.description,
                    owner_id=user.id
                )
                db.session.add(organization)
                db.session.flush()
                
                # Add user as owner
                user_role = UserRole(
                    user_id=user.id,
                    organization_id=organization.id,
                    role='owner'
                )
                db.session.add(user_role)
                db.session.commit()
                
                flash('Organization created successfully!', 'success')
                return redirect(url_for('organizations.organizations'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Organization creation error: {e}")
                flash('An error occurred while creating the organization.', 'danger')
        
        return render_template('organizations/organization_form.html', errors=form.errors)
    
    return render_template('organizations/organization_form.html', errors={})

@organizations_bp.route('/<int:org_id>')
@login_required
def organization_detail(org_id):
    """Organization details and settings"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role:
        flash('You do not have access to that organization.', 'danger')
        return redirect(url_for('organizations.organizations'))
    
    organization = user_role.organization
    
    # Get organization statistics
    total_contacts = Contact.query.filter_by(organization_id=org_id).count()
    total_groups = Group.query.filter_by(organization_id=org_id).count()
    total_templates = Template.query.filter_by(organization_id=org_id).count()
    
    # Get members
    members = UserRole.query.filter_by(organization_id=org_id).all()
    
    # Get pending invitations
    pending_invitations = OrganizationInvitation.query.filter_by(
        organization_id=org_id, 
        status='pending'
    ).all()
    
    return render_template('organizations/organization_detail.html',
                         organization=organization,
                         user_role=user_role,
                         total_contacts=total_contacts,
                         total_groups=total_groups,
                         total_templates=total_templates,
                         members=members,
                         pending_invitations=pending_invitations)

@organizations_bp.route('/<int:org_id>/invite', methods=['GET', 'POST'])
@login_required
def invite_user(org_id):
    """Invite user to organization"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        flash('You do not have permission to invite users.', 'danger')
        return redirect(url_for('organizations.organization_detail', org_id=org_id))
    
    if request.method == 'POST':
        form = InvitationForm()
        if form.validate():
            # Check if user is already a member
            existing_user = User.query.filter_by(email=form.email).first()
            if existing_user:
                existing_role = UserRole.query.filter_by(
                    user_id=existing_user.id, 
                    organization_id=org_id
                ).first()
                if existing_role:
                    form.errors['email'] = 'User is already a member of this organization'
                    return render_template('organizations/invite_form.html', 
                                         errors=form.errors, org_id=org_id)
            
            # Check if there's already a pending invitation
            existing_invitation = OrganizationInvitation.query.filter_by(
                email=form.email,
                organization_id=org_id,
                status='pending'
            ).first()
            
            if existing_invitation:
                form.errors['email'] = 'An invitation is already pending for this email'
                return render_template('organizations/invite_form.html', 
                                     errors=form.errors, org_id=org_id)
            
            try:
                # Create invitation
                invitation = OrganizationInvitation(
                    organization_id=org_id,
                    email=form.email,
                    role=form.role,
                    invited_by_id=user.id,
                    invitee_id=existing_user.id if existing_user else None
                )
                invitation.generate_token()
                
                db.session.add(invitation)
                db.session.commit()
                
                # In a real application, you would send an email here
                logging.info(f"Invitation created for {form.email} to join organization {org_id}")
                flash(f'Invitation sent to {form.email}!', 'success')
                return redirect(url_for('organizations.organization_detail', org_id=org_id))
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Invitation error: {e}")
                flash('An error occurred while sending the invitation.', 'danger')
        
        return render_template('organizations/invite_form.html', errors=form.errors, org_id=org_id)
    
    return render_template('organizations/invite_form.html', errors={}, org_id=org_id)

@organizations_bp.route('/invite/<token>')
def accept_invitation(token):
    """Accept organization invitation"""
    invitation = OrganizationInvitation.query.filter_by(token=token).first()
    
    if not invitation:
        flash('Invalid invitation link.', 'danger')
        return redirect(url_for('index'))
    
    if invitation.status != 'pending':
        flash('This invitation has already been processed.', 'warning')
        return redirect(url_for('index'))
    
    if invitation.is_expired():
        invitation.status = 'expired'
        db.session.commit()
        flash('This invitation has expired.', 'warning')
        return redirect(url_for('index'))
    
    # Check if user is logged in
    if 'user_id' not in session:
        session['invitation_token'] = token
        flash('Please log in or register to accept the invitation.', 'info')
        return redirect(url_for('auth.login'))
    
    user = get_current_user()
    
    # Check if user email matches invitation
    if user.email != invitation.email:
        flash('This invitation is for a different email address.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Create user role
        user_role = UserRole(
            user_id=user.id,
            organization_id=invitation.organization_id,
            role=invitation.role
        )
        db.session.add(user_role)
        
        # Update invitation status
        invitation.status = 'accepted'
        invitation.invitee_id = user.id
        
        db.session.commit()
        
        flash(f'Successfully joined {invitation.organization.name}!', 'success')
        return redirect(url_for('organizations.switch_organization', 
                              org_id=invitation.organization_id))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Accept invitation error: {e}")
        flash('An error occurred while accepting the invitation.', 'danger')
        return redirect(url_for('index'))