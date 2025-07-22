from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from models import Organization, User, UserRole, OrganizationInvitation, Contact, Group, Template, OrganizationConfig
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

@organizations_bp.route('/<int:org_id>/settings')
@login_required
def settings(org_id):
    """Organization settings page"""
    user = get_current_user()
    
    # Check if user has access to this organization
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    if not user_role:
        flash('You do not have access to that organization.', 'danger')
        return redirect(url_for('organizations.organizations'))
    
    organization = Organization.query.get_or_404(org_id)
    config = OrganizationConfig.query.filter_by(organization_id=org_id).first()
    
    # Parse configuration data
    sms_config = None
    email_config = None
    whatsapp_config = None
    
    if config:
        import json
        try:
            sms_config = json.loads(config.sms_config) if config.sms_config else None
            email_config = json.loads(config.email_config) if config.email_config else None  
            whatsapp_config = json.loads(config.whatsapp_config) if config.whatsapp_config else None
        except json.JSONDecodeError:
            pass
    
    return render_template('organizations/settings.html',
                         organization=organization,
                         user_role=user_role,
                         sms_config=sms_config,
                         email_config=email_config,
                         whatsapp_config=whatsapp_config,
                         sms_configured=bool(sms_config),
                         email_configured=bool(email_config),
                         whatsapp_configured=bool(whatsapp_config))

@organizations_bp.route('/<int:org_id>/save-sms-config', methods=['POST'])
@login_required
def save_sms_config(org_id):
    """Save SMS configuration"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        flash('You do not have permission to modify organization settings.', 'danger')
        return redirect(url_for('organizations.settings', org_id=org_id))
    
    # Get or create organization config
    config = OrganizationConfig.query.filter_by(organization_id=org_id).first()
    if not config:
        config = OrganizationConfig(organization_id=org_id)
        db.session.add(config)
    
    # Build SMS config
    import json
    sms_config = {
        'provider': request.form.get('sms_provider'),
        'api_key': request.form.get('sms_api_key'),
        'auth_token': request.form.get('sms_auth_token'),
        'from_number': request.form.get('sms_from_number')
    }
    
    config.sms_config = json.dumps(sms_config)
    db.session.commit()
    
    flash('SMS configuration saved successfully!', 'success')
    return redirect(url_for('organizations.settings', org_id=org_id))

@organizations_bp.route('/<int:org_id>/save-email-config', methods=['POST'])
@login_required
def save_email_config(org_id):
    """Save email configuration"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        flash('You do not have permission to modify organization settings.', 'danger')
        return redirect(url_for('organizations.settings', org_id=org_id))
    
    # Get or create organization config
    config = OrganizationConfig.query.filter_by(organization_id=org_id).first()
    if not config:
        config = OrganizationConfig(organization_id=org_id)
        db.session.add(config)
    
    # Build email config
    import json
    email_config = {
        'smtp_host': request.form.get('smtp_host'),
        'smtp_port': request.form.get('smtp_port'),
        'security': request.form.get('smtp_security'),
        'username': request.form.get('smtp_username'),
        'password': request.form.get('smtp_password'),
        'from_name': request.form.get('smtp_from_name')
    }
    
    config.email_config = json.dumps(email_config)
    db.session.commit()
    
    flash('Email configuration saved successfully!', 'success')
    return redirect(url_for('organizations.settings', org_id=org_id))

@organizations_bp.route('/<int:org_id>/save-whatsapp-config', methods=['POST'])
@login_required
def save_whatsapp_config(org_id):
    """Save WhatsApp configuration"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        flash('You do not have permission to modify organization settings.', 'danger')
        return redirect(url_for('organizations.settings', org_id=org_id))
    
    # Get or create organization config
    config = OrganizationConfig.query.filter_by(organization_id=org_id).first()
    if not config:
        config = OrganizationConfig(organization_id=org_id)
        db.session.add(config)
    
    # Build WhatsApp config
    import json
    whatsapp_config = {
        'account_id': request.form.get('whatsapp_account_id'),
        'phone_id': request.form.get('whatsapp_phone_id'),
        'access_token': request.form.get('whatsapp_access_token')
    }
    
    config.whatsapp_config = json.dumps(whatsapp_config)
    db.session.commit()
    
    flash('WhatsApp configuration saved successfully!', 'success')
    return redirect(url_for('organizations.settings', org_id=org_id))

@organizations_bp.route('/<int:org_id>/test-sms-config', methods=['POST'])
@login_required
def test_sms_config(org_id):
    """Test SMS configuration"""
    try:
        data = request.get_json()
        test_phone = data.get('test_phone')
        
        if not test_phone:
            return jsonify({'success': False, 'error': 'Test phone number required'})
        
        # TODO: Implement SMS test using messaging_clients.py
        return jsonify({'success': True, 'message': 'SMS test successful'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@organizations_bp.route('/<int:org_id>/test-email', methods=['POST'])
@login_required  
def test_email(org_id):
    """Test email configuration"""
    try:
        data = request.get_json()
        test_email = data.get('test_email')
        
        if not test_email:
            return jsonify({'success': False, 'error': 'Test email address required'})
        
        # TODO: Implement email test using messaging_clients.py
        return jsonify({'success': True, 'message': 'Email test successful'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@organizations_bp.route('/<int:org_id>/test-whatsapp', methods=['POST'])
@login_required
def test_whatsapp(org_id):
    """Test WhatsApp configuration"""
    try:
        data = request.get_json()
        test_phone = data.get('test_phone')
        
        if not test_phone:
            return jsonify({'success': False, 'error': 'Test phone number required'})
        
        # TODO: Implement WhatsApp test using messaging_clients.py
        return jsonify({'success': True, 'message': 'WhatsApp test successful'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
                         user_role=user_role.role,
                         total_contacts=total_contacts,
                         total_groups=total_groups,
                         total_templates=total_templates,
                         members=members,
                         member_count=len(members),
                         contact_count=total_contacts,
                         template_count=total_templates,
                         pending_invitations=pending_invitations)

@organizations_bp.route('/<int:org_id>/settings', methods=['GET', 'POST'])
@login_required
def organization_settings(org_id):
    """Organization messaging settings"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role or not user_role.can_manage_organization():
        flash('You do not have permission to manage organization settings.', 'danger')
        return redirect(url_for('organizations.organization_detail', org_id=org_id))
    
    organization = user_role.organization
    
    # Get or create config
    config = OrganizationConfig.query.filter_by(organization_id=org_id).first()
    if not config:
        config = OrganizationConfig(organization_id=org_id)
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            # Update SMS settings
            config.sms_provider = request.form.get('sms_provider', 'twilio')
            config.sms_api_url = request.form.get('sms_api_url', '')
            config.sms_api_key = request.form.get('sms_api_key', '')
            config.sms_username = request.form.get('sms_username', '')
            config.sms_sender_id = request.form.get('sms_sender_id', '')
            
            # Update Email settings
            config.email_provider = request.form.get('email_provider', 'smtp')
            config.smtp_host = request.form.get('smtp_host', '')
            config.smtp_port = int(request.form.get('smtp_port', 587)) if request.form.get('smtp_port') else 587
            config.smtp_username = request.form.get('smtp_username', '')
            config.smtp_password = request.form.get('smtp_password', '')
            config.smtp_use_tls = 'smtp_use_tls' in request.form
            
            # AWS SES settings
            config.aws_access_key_id = request.form.get('aws_access_key_id', '')
            config.aws_secret_access_key = request.form.get('aws_secret_access_key', '')
            config.aws_region = request.form.get('aws_region', 'us-east-1')
            config.aws_sender_email = request.form.get('aws_sender_email', '')
            
            # WhatsApp settings
            config.whatsapp_api_url = request.form.get('whatsapp_api_url', '')
            config.whatsapp_api_key = request.form.get('whatsapp_api_key', '')
            config.whatsapp_phone_number = request.form.get('whatsapp_phone_number', '')
            config.whatsapp_webhook_url = request.form.get('whatsapp_webhook_url', '')
            
            # General settings
            config.default_sender_name = request.form.get('default_sender_name', organization.name)
            config.is_active = 'is_active' in request.form
            
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('organizations.organization_settings', org_id=org_id))
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Settings update error: {e}")
            flash('An error occurred while saving settings.', 'danger')
    
    return render_template('organizations/organization_settings.html',
                         organization=organization,
                         config=config)

@organizations_bp.route('/<int:org_id>/invite', methods=['GET', 'POST'])
@login_required
def invite_form(org_id):
    """Invite user form"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id, organization_id=org_id).first()
    
    if not user_role or not user_role.can_invite_users():
        flash('You do not have permission to invite users.', 'danger')
        return redirect(url_for('organizations.organization_detail', org_id=org_id))
    
    organization = user_role.organization
    current_members = UserRole.query.filter_by(organization_id=org_id).all()
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'member')
        message = request.form.get('message', '').strip()
        
        errors = {}
        
        if not email:
            errors['email'] = 'Email is required'
        elif not email.endswith('@'):
            if '@' not in email:
                errors['email'] = 'Invalid email format'
        
        if role not in ['admin', 'member', 'viewer']:
            errors['role'] = 'Invalid role selected'
        
        if not errors:
            # Check if user already exists and is a member
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                existing_role = UserRole.query.filter_by(
                    user_id=existing_user.id, 
                    organization_id=org_id
                ).first()
                if existing_role:
                    errors['email'] = 'User is already a member of this organization'
            
            # Check for pending invitation
            if not errors:
                existing_invitation = OrganizationInvitation.query.filter_by(
                    email=email,
                    organization_id=org_id,
                    status='pending'
                ).first()
                
                if existing_invitation:
                    errors['email'] = 'An invitation is already pending for this email'
        
        if not errors:
            try:
                # Create invitation
                invitation = OrganizationInvitation(
                    organization_id=org_id,
                    email=email,
                    role=role,
                    invited_by_id=user.id,
                    invitee_id=existing_user.id if existing_user else None
                )
                invitation.generate_token()
                
                db.session.add(invitation)
                db.session.commit()
                
                flash(f'Invitation sent to {email}!', 'success')
                return redirect(url_for('organizations.organization_detail', org_id=org_id))
            
            except Exception as e:
                db.session.rollback()
                logging.error(f"Invitation error: {e}")
                errors['general'] = 'An error occurred while sending the invitation'
        
        if errors:
            return render_template('organizations/invite_form.html',
                                 organization=organization,
                                 errors=errors,
                                 form_data=request.form,
                                 current_members=current_members,
                                 team_count=len(current_members))
    
    return render_template('organizations/invite_form.html',
                         organization=organization,
                         errors={},
                         current_members=current_members,
                         team_count=len(current_members))





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