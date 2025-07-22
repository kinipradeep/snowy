"""
REST API Blueprint - Bulk Operations & API User Management
Comprehensive API for external integrations and bulk contact/messaging operations
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import and_, or_
from models import (
    db, User, Contact, Group, Template, Organization, OrganizationConfig, 
    UserRole, ApiKey, MessageLog
)
from messaging_clients import UnifiedMessagingClient
from utils import get_current_user, login_required

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API Authentication Decorator
def api_key_required(f):
    """Require valid API key for endpoint access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Hash the provided key to match stored hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        api_key_obj = ApiKey.query.filter_by(key_hash=key_hash, is_active=True).first()
        
        if not api_key_obj:
            return jsonify({'error': 'Invalid API key'}), 401
        
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            return jsonify({'error': 'API key expired'}), 401
        
        # Update last used timestamp
        api_key_obj.last_used_at = datetime.utcnow()
        api_key_obj.usage_count += 1
        db.session.commit()
        
        # Add API key context to request
        request.api_key = api_key_obj
        request.api_organization = api_key_obj.organization
        
        return f(*args, **kwargs)
    return decorated_function

def check_api_permission(permission):
    """Check if API key has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if permission not in request.api_key.permissions:
                return jsonify({'error': f'Permission {permission} required'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# API Key Management Routes
@api_bp.route('/keys', methods=['GET'])
@login_required
def list_api_keys():
    """List all API keys for current organization"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        return jsonify({'error': 'Admin access required'}), 403
    
    api_keys = ApiKey.query.filter_by(organization_id=user_role.organization_id).all()
    
    return jsonify({
        'api_keys': [{
            'id': key.id,
            'name': key.name,
            'permissions': key.permissions,
            'is_active': key.is_active,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat() if key.expires_at else None,
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
            'usage_count': key.usage_count
        } for key in api_keys]
    })

@api_bp.route('/keys', methods=['POST'])
@login_required
def create_api_key():
    """Create new API key for current organization"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'API key name required'}), 400
    
    # Generate API key
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    # Set expiration
    expires_days = data.get('expires_days', 90)
    expires_at = datetime.utcnow() + timedelta(days=expires_days) if expires_days else None
    
    # Create API key record
    api_key = ApiKey(
        name=data['name'],
        key_hash=key_hash,
        permissions=data.get('permissions', ['read']),
        organization_id=user_role.organization_id,
        created_by_id=user.id,
        expires_at=expires_at
    )
    
    db.session.add(api_key)
    db.session.commit()
    
    return jsonify({
        'message': 'API key created successfully',
        'api_key': raw_key,
        'key_id': api_key.id,
        'expires_at': expires_at.isoformat() if expires_at else None
    })

@api_bp.route('/keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """Delete API key"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        return jsonify({'error': 'Admin access required'}), 403
    
    api_key = ApiKey.query.filter_by(
        id=key_id, 
        organization_id=user_role.organization_id
    ).first()
    
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404
    
    db.session.delete(api_key)
    db.session.commit()
    
    return jsonify({'message': 'API key deleted successfully'})

# Contact Management API Routes
@api_bp.route('/contacts', methods=['GET'])
@api_key_required
@check_api_permission('read')
def get_contacts():
    """Get contacts with filtering and pagination"""
    organization = request.api_organization
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 1000)
    
    # Build query
    query = Contact.query.filter_by(organization_id=organization.id)
    
    # Apply filters
    search = request.args.get('search')
    if search:
        query = query.filter(or_(
            Contact.first_name.ilike(f'%{search}%'),
            Contact.last_name.ilike(f'%{search}%'),
            Contact.email.ilike(f'%{search}%'),
            Contact.company.ilike(f'%{search}%')
        ))
    
    group_id = request.args.get('group_id', type=int)
    if group_id:
        query = query.filter_by(group_id=group_id)
    
    # Get paginated results
    contacts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'contacts': [{
            'id': c.id,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'email': c.email,
            'phone': c.phone,
            'mobile': c.mobile,
            'company': c.company,
            'job_title': c.job_title,
            'created_at': c.created_at.isoformat(),
            'group_id': c.group_id
        } for c in contacts.items],
        'pagination': {
            'page': contacts.page,
            'per_page': contacts.per_page,
            'total': contacts.total,
            'pages': contacts.pages,
            'has_next': contacts.has_next,
            'has_prev': contacts.has_prev
        }
    })

@api_bp.route('/contacts/bulk', methods=['POST'])
@api_key_required
@check_api_permission('write')
def create_contacts_bulk():
    """Create up to 1000 contacts in bulk"""
    organization = request.api_organization
    data = request.get_json()
    
    if not data or not data.get('contacts'):
        return jsonify({'error': 'Contacts data required'}), 400
    
    contacts_data = data['contacts']
    if len(contacts_data) > 1000:
        return jsonify({'error': 'Maximum 1000 contacts per request'}), 400
    
    created_contacts = []
    errors = []
    
    for i, contact_data in enumerate(contacts_data):
        try:
            # Validate required fields
            if not contact_data.get('email'):
                errors.append(f'Contact {i}: Email is required')
                continue
            
            # Check for existing contact
            existing = Contact.query.filter_by(
                email=contact_data['email'], 
                organization_id=organization.id
            ).first()
            
            if existing:
                errors.append(f'Contact {i}: Email already exists')
                continue
            
            # Create contact
            contact = Contact(
                first_name=contact_data.get('first_name', ''),
                last_name=contact_data.get('last_name', ''),
                email=contact_data['email'],
                phone=contact_data.get('phone'),
                mobile=contact_data.get('mobile'),
                company=contact_data.get('company'),
                job_title=contact_data.get('job_title'),
                department=contact_data.get('department'),
                website=contact_data.get('website'),
                address=contact_data.get('address'),
                city=contact_data.get('city'),
                state=contact_data.get('state'),
                country=contact_data.get('country'),
                postal_code=contact_data.get('postal_code'),
                organization_id=organization.id,
                group_id=contact_data.get('group_id')
            )
            
            db.session.add(contact)
            created_contacts.append(contact)
            
        except Exception as e:
            errors.append(f'Contact {i}: {str(e)}')
    
    try:
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully created {len(created_contacts)} contacts',
            'created_count': len(created_contacts),
            'error_count': len(errors),
            'errors': errors,
            'created_contacts': [{
                'id': c.id,
                'email': c.email,
                'first_name': c.first_name,
                'last_name': c.last_name
            } for c in created_contacts]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

# Messaging API Routes
@api_bp.route('/messages/send', methods=['POST'])
@api_key_required
@check_api_permission('message')
def send_bulk_messages():
    """Send bulk messages using templates"""
    organization = request.api_organization
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    template_id = data.get('template_id')
    contact_ids = data.get('contact_ids', [])
    custom_variables = data.get('custom_variables', {})
    
    if not template_id:
        return jsonify({'error': 'Template ID required'}), 400
    
    if not contact_ids:
        return jsonify({'error': 'Contact IDs required'}), 400
    
    # Get template
    template = Template.query.filter_by(
        id=template_id, 
        organization_id=organization.id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Get contacts
    contacts = Contact.query.filter(
        Contact.id.in_(contact_ids),
        Contact.organization_id == organization.id
    ).all()
    
    if not contacts:
        return jsonify({'error': 'No valid contacts found'}), 400
    
    # Send messages using messaging client
    messaging_client = UnifiedMessagingClient(organization.id)
    results = []
    
    for contact in contacts:
        try:
            # Prepare recipient based on message type
            if template.type == 'sms':
                recipient = contact.mobile or contact.phone
            elif template.type == 'email':
                recipient = contact.email
            elif template.type == 'whatsapp':
                recipient = contact.mobile or contact.phone
            else:
                results.append({
                    'contact_id': contact.id,
                    'success': False,
                    'error': f'Unsupported message type: {template.type}'
                })
                continue
            
            if not recipient:
                results.append({
                    'contact_id': contact.id,
                    'success': False,
                    'error': f'No {template.type} recipient found'
                })
                continue
            
            # Send message
            result = messaging_client.send_message(
                message_type=template.type,
                recipient=recipient,
                subject=template.subject if template.type == 'email' else None,
                content=template.content,
                variables={
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'full_name': f'{contact.first_name} {contact.last_name}'.strip(),
                    'email': contact.email,
                    'phone': contact.phone,
                    'mobile': contact.mobile,
                    'company': contact.company,
                    **custom_variables
                }
            )
            
            # Log message
            message_log = MessageLog(
                contact_id=contact.id,
                template_id=template.id,
                organization_id=organization.id,
                api_key_id=request.api_key.id,
                message_type=template.type,
                recipient=recipient,
                subject=template.subject if template.type == 'email' else None,
                content=template.content,
                status='sent' if result['success'] else 'failed',
                provider=result.get('provider'),
                provider_message_id=result.get('message_id'),
                error_message=result.get('error'),
                sent_at=datetime.utcnow() if result['success'] else None,
                sent_via_api=True
            )
            
            db.session.add(message_log)
            results.append({
                'contact_id': contact.id,
                'success': result['success'],
                'message_id': result.get('message_id'),
                'error': result.get('error')
            })
            
        except Exception as e:
            results.append({
                'contact_id': contact.id,
                'success': False,
                'error': str(e)
            })
    
    db.session.commit()
    
    success_count = sum(1 for r in results if r['success'])
    error_count = len(results) - success_count
    
    return jsonify({
        'message': f'Processed {len(results)} messages',
        'success_count': success_count,
        'error_count': error_count,
        'results': results
    })

# Analytics API Routes
@api_bp.route('/analytics/summary', methods=['GET'])
@api_key_required
@check_api_permission('read')
def get_analytics_summary():
    """Get organization analytics summary"""
    organization = request.api_organization
    
    # Basic counts
    total_contacts = Contact.query.filter_by(organization_id=organization.id).count()
    total_groups = Group.query.filter_by(organization_id=organization.id).count()
    total_templates = Template.query.filter_by(organization_id=organization.id).count()
    
    # Message stats (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    messages_sent = MessageLog.query.filter(
        MessageLog.organization_id == organization.id,
        MessageLog.sent_at >= thirty_days_ago
    ).count()
    
    # Message type breakdown
    message_types = db.session.query(
        MessageLog.message_type,
        db.func.count(MessageLog.id)
    ).filter(
        MessageLog.organization_id == organization.id,
        MessageLog.sent_at >= thirty_days_ago
    ).group_by(MessageLog.message_type).all()
    
    return jsonify({
        'organization': {
            'id': organization.id,
            'name': organization.name
        },
        'summary': {
            'total_contacts': total_contacts,
            'total_groups': total_groups,
            'total_templates': total_templates,
            'messages_sent_30_days': messages_sent
        },
        'message_breakdown': {
            message_type: count for message_type, count in message_types
        },
        'generated_at': datetime.utcnow().isoformat()
    })
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    name = data.get('name')
    permissions = data.get('permissions', ['read'])
    expires_days = data.get('expires_days', 90)
    
    if not name:
        return jsonify({'error': 'Name required'}), 400
    
    # Generate API key
    api_key_value = f"cm_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=expires_days) if expires_days else None
    
    # Create API key record
    api_key_obj = ApiKey(
        name=name,
        key_hash=key_hash,
        permissions=permissions,
        organization_id=user_role.organization_id,
        created_by_user_id=user.id,
        expires_at=expires_at,
        is_active=True
    )
    
    db.session.add(api_key_obj)
    db.session.commit()
    
    return jsonify({
        'message': 'API key created successfully',
        'api_key': api_key_value,  # Only shown once
        'key_info': {
            'id': api_key_obj.id,
            'name': api_key_obj.name,
            'permissions': api_key_obj.permissions,
            'expires_at': expires_at.isoformat() if expires_at else None
        }
    }), 201

@api_bp.route('/keys/<int:key_id>', methods=['PUT'])
@login_required
def update_api_key(key_id):
    """Update API key permissions or status"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        return jsonify({'error': 'Admin access required'}), 403
    
    api_key_obj = ApiKey.query.filter_by(
        id=key_id, 
        organization_id=user_role.organization_id
    ).first()
    
    if not api_key_obj:
        return jsonify({'error': 'API key not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    # Update fields
    if 'name' in data:
        api_key_obj.name = data['name']
    if 'permissions' in data:
        api_key_obj.permissions = data['permissions']
    if 'is_active' in data:
        api_key_obj.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({'message': 'API key updated successfully'})

@api_bp.route('/keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """Delete API key"""
    user = get_current_user()
    user_role = UserRole.query.filter_by(user_id=user.id).first()
    
    if not user_role or user_role.role not in ['owner', 'admin']:
        return jsonify({'error': 'Admin access required'}), 403
    
    api_key_obj = ApiKey.query.filter_by(
        id=key_id, 
        organization_id=user_role.organization_id
    ).first()
    
    if not api_key_obj:
        return jsonify({'error': 'API key not found'}), 404
    
    db.session.delete(api_key_obj)
    db.session.commit()
    
    return jsonify({'message': 'API key deleted successfully'})

# Bulk Contact Operations
@api_bp.route('/contacts', methods=['GET'])
@api_key_required
@check_api_permission('read')
def get_contacts():
    """Get contacts with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 1000)
    group_id = request.args.get('group_id', type=int)
    search = request.args.get('search', '')
    
    query = Contact.query.filter_by(organization_id=request.api_organization.id)
    
    if group_id:
        query = query.filter(Contact.groups.any(Group.id == group_id))
    
    if search:
        search_filter = or_(
            Contact.first_name.ilike(f'%{search}%'),
            Contact.last_name.ilike(f'%{search}%'),
            Contact.email.ilike(f'%{search}%'),
            Contact.phone.ilike(f'%{search}%'),
            Contact.company.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    contacts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'contacts': [{
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email,
            'phone': contact.phone,
            'company': contact.company,
            'title': contact.title,
            'groups': [{'id': g.id, 'name': g.name} for g in contact.groups],
            'created_at': contact.created_at.isoformat(),
            'updated_at': contact.updated_at.isoformat()
        } for contact in contacts.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': contacts.total,
            'pages': contacts.pages,
            'has_next': contacts.has_next,
            'has_prev': contacts.has_prev
        }
    })

@api_bp.route('/contacts', methods=['POST'])
@api_key_required
@check_api_permission('write')
def create_contact():
    """Create single contact"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    required_fields = ['first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    contact = Contact(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data.get('email'),
        phone=data.get('phone'),
        company=data.get('company'),
        title=data.get('title'),
        organization_id=request.api_organization.id,
        created_by_user_id=request.api_key.created_by_user_id
    )
    
    # Add to groups if specified
    group_ids = data.get('group_ids', [])
    if group_ids:
        groups = Group.query.filter(
            Group.id.in_(group_ids),
            Group.organization_id == request.api_organization.id
        ).all()
        contact.groups.extend(groups)
    
    db.session.add(contact)
    db.session.commit()
    
    return jsonify({
        'message': 'Contact created successfully',
        'contact': {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': contact.email,
            'phone': contact.phone
        }
    }), 201

@api_bp.route('/contacts/bulk', methods=['POST'])
@api_key_required
@check_api_permission('write')
def create_contacts_bulk():
    """Create multiple contacts in bulk"""
    data = request.get_json()
    if not data or 'contacts' not in data:
        return jsonify({'error': 'contacts array required'}), 400
    
    contacts_data = data['contacts']
    if not isinstance(contacts_data, list) or len(contacts_data) > 1000:
        return jsonify({'error': 'contacts must be array with max 1000 items'}), 400
    
    created_contacts = []
    errors = []
    
    for i, contact_data in enumerate(contacts_data):
        try:
            required_fields = ['first_name', 'last_name']
            for field in required_fields:
                if not contact_data.get(field):
                    raise ValueError(f'{field} is required')
            
            contact = Contact(
                first_name=contact_data['first_name'],
                last_name=contact_data['last_name'],
                email=contact_data.get('email'),
                phone=contact_data.get('phone'),
                company=contact_data.get('company'),
                title=contact_data.get('title'),
                organization_id=request.api_organization.id,
                created_by_user_id=request.api_key.created_by_user_id
            )
            
            # Add to groups if specified
            group_ids = contact_data.get('group_ids', [])
            if group_ids:
                groups = Group.query.filter(
                    Group.id.in_(group_ids),
                    Group.organization_id == request.api_organization.id
                ).all()
                contact.groups.extend(groups)
            
            db.session.add(contact)
            created_contacts.append(contact)
            
        except Exception as e:
            errors.append(f'Contact {i}: {str(e)}')
    
    if created_contacts:
        db.session.commit()
    
    return jsonify({
        'message': f'Created {len(created_contacts)} contacts',
        'created_count': len(created_contacts),
        'error_count': len(errors),
        'errors': errors,
        'created_contacts': [{
            'id': c.id,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'email': c.email
        } for c in created_contacts]
    }), 201

# Bulk Messaging Operations
@api_bp.route('/messages/send', methods=['POST'])
@api_key_required
@check_api_permission('message')
def send_message():
    """Send message to contacts using template"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    template_id = data.get('template_id')
    contact_ids = data.get('contact_ids', [])
    custom_variables = data.get('custom_variables', {})
    
    if not template_id:
        return jsonify({'error': 'template_id required'}), 400
    
    if not contact_ids or not isinstance(contact_ids, list):
        return jsonify({'error': 'contact_ids array required'}), 400
    
    # Get template
    template = Template.query.filter_by(
        id=template_id,
        organization_id=request.api_organization.id
    ).first()
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Get contacts
    contacts = Contact.query.filter(
        Contact.id.in_(contact_ids),
        Contact.organization_id == request.api_organization.id
    ).all()
    
    if not contacts:
        return jsonify({'error': 'No valid contacts found'}), 400
    
    # Get organization config for messaging
    org_config = OrganizationConfig.query.filter_by(
        organization_id=request.api_organization.id
    ).first()
    
    if not org_config:
        return jsonify({'error': 'Organization messaging not configured'}), 400
    
    # Send messages
    messaging_client = UnifiedMessagingClient(org_config)
    results = []
    
    for contact in contacts:
        # Personalize content
        personalized_content = template.content
        for var, value in custom_variables.items():
            personalized_content = personalized_content.replace(f'{{{var}}}', str(value))
        
        # Replace contact variables
        personalized_content = personalized_content.replace('{first_name}', contact.first_name or '')
        personalized_content = personalized_content.replace('{last_name}', contact.last_name or '')
        personalized_content = personalized_content.replace('{company}', contact.company or '')
        
        # Send based on template type
        if template.template_type == 'sms':
            result = messaging_client.send_sms(contact.phone, personalized_content)
        elif template.template_type == 'email':
            subject = template.subject or 'Message from {}'.format(org_config.default_sender_name)
            result = messaging_client.send_email(contact.email, subject, personalized_content)
        elif template.template_type == 'whatsapp':
            result = messaging_client.send_whatsapp(contact.phone, personalized_content)
        else:
            result = {'success': False, 'error': f'Unsupported template type: {template.template_type}'}
        
        # Log message attempt
        message_log = MessageLog(
            contact_id=contact.id,
            template_id=template.id,
            organization_id=request.api_organization.id,
            message_type=template.template_type,
            status='sent' if result['success'] else 'failed',
            error_message=result.get('error') if not result['success'] else None,
            sent_via_api=True,
            api_key_id=request.api_key.id
        )
        db.session.add(message_log)
        
        results.append({
            'contact_id': contact.id,
            'contact_name': f"{contact.first_name} {contact.last_name}",
            'success': result['success'],
            'message_id': result.get('message_id'),
            'error': result.get('error')
        })
    
    db.session.commit()
    
    successful_sends = len([r for r in results if r['success']])
    
    return jsonify({
        'message': f'Sent {successful_sends}/{len(results)} messages',
        'total_contacts': len(results),
        'successful_sends': successful_sends,
        'failed_sends': len(results) - successful_sends,
        'results': results
    })

# Analytics and Reporting
@api_bp.route('/analytics/summary', methods=['GET'])
@api_key_required
@check_api_permission('read')
def get_analytics_summary():
    """Get organization analytics summary"""
    org_id = request.api_organization.id
    
    # Contact statistics
    total_contacts = Contact.query.filter_by(organization_id=org_id).count()
    total_groups = Group.query.filter_by(organization_id=org_id).count()
    total_templates = Template.query.filter_by(organization_id=org_id).count()
    
    # Message statistics (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_messages = MessageLog.query.filter(
        MessageLog.organization_id == org_id,
        MessageLog.created_at >= thirty_days_ago
    ).all()
    
    message_stats = {
        'total_sent': len([m for m in recent_messages if m.status == 'sent']),
        'total_failed': len([m for m in recent_messages if m.status == 'failed']),
        'sms_sent': len([m for m in recent_messages if m.message_type == 'sms' and m.status == 'sent']),
        'email_sent': len([m for m in recent_messages if m.message_type == 'email' and m.status == 'sent']),
        'whatsapp_sent': len([m for m in recent_messages if m.message_type == 'whatsapp' and m.status == 'sent'])
    }
    
    return jsonify({
        'organization': {
            'name': request.api_organization.name,
            'total_contacts': total_contacts,
            'total_groups': total_groups,
            'total_templates': total_templates
        },
        'messaging_stats_30_days': message_stats,
        'api_usage': {
            'key_name': request.api_key.name,
            'total_requests': request.api_key.usage_count,
            'last_used': request.api_key.last_used_at.isoformat() if request.api_key.last_used_at else None
        }
    })

# Health Check
@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Error Handlers
@api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500