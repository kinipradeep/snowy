"""
REST API Blueprint - Essential API endpoints for Contact Manager
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify
from sqlalchemy import and_, or_
from models import (
    db, User, Contact, Group, Template, Organization, 
    UserRole, ApiKey, MessageLog
)
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
        
        # Update usage stats
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
    raw_key = f"cm_{secrets.token_urlsafe(32)}"
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
        'generated_at': datetime.utcnow().isoformat()
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