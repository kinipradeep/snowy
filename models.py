from datetime import datetime, timedelta
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

class Organization(db.Model):
    """Organization model for multi-tenant support"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('UserRole', backref='organization', lazy=True, cascade='all, delete-orphan')
    contacts = db.relationship('Contact', backref='organization', lazy=True, cascade='all, delete-orphan')
    groups = db.relationship('Group', backref='organization', lazy=True, cascade='all, delete-orphan')
    templates = db.relationship('Template', backref='organization', lazy=True, cascade='all, delete-orphan')
    invitations = db.relationship('OrganizationInvitation', backref='organization', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Organization {self.name}>'

class User(db.Model):
    """User model for authentication and user management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owned_organizations = db.relationship('Organization', backref='owner', lazy=True)
    organization_roles = db.relationship('UserRole', backref='user', lazy=True, cascade='all, delete-orphan')
    received_invitations = db.relationship('OrganizationInvitation', foreign_keys='OrganizationInvitation.invitee_id', backref='invitee', lazy=True, cascade='all, delete-orphan')
    sent_invitations = db.relationship('OrganizationInvitation', foreign_keys='OrganizationInvitation.invited_by_id', backref='inviter', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_current_organization(self):
        """Get user's current active organization"""
        active_role = UserRole.query.filter_by(user_id=self.id, is_active=True).first()
        return active_role.organization if active_role else None
    
    def get_organization_role(self, organization_id):
        """Get user's role in a specific organization"""
        role = UserRole.query.filter_by(user_id=self.id, organization_id=organization_id).first()
        return role.role if role else None
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserRole(db.Model):
    """User roles within organizations"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # owner, admin, member, viewer
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'organization_id'),)
    
    def __repr__(self):
        return f'<UserRole {self.user.username} - {self.organization.name} - {self.role}>'

class OrganizationInvitation(db.Model):
    """Organization invitations for new members"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    token = db.Column(db.String(100), nullable=False, unique=True)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Set when user exists
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, expired
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    
    def generate_token(self):
        """Generate unique invitation token"""
        self.token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        self.expires_at = datetime.utcnow() + timedelta(days=7)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<OrganizationInvitation {self.email} -> {self.organization.name}>'

class Group(db.Model):
    """Group model for organizing contacts"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contacts = db.relationship('Contact', backref='group', lazy=True)
    created_by = db.relationship('User', backref='created_groups')
    
    def __repr__(self):
        return f'<Group {self.name}>'

class Contact(db.Model):
    """Contact model for storing contact information"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    prefix = db.Column(db.String(10))  # Mr., Ms., Dr., etc.
    suffix = db.Column(db.String(10))  # Jr., Sr., PhD, etc.
    
    # Contact Information
    email = db.Column(db.String(120))
    email_secondary = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    fax = db.Column(db.String(20))
    website = db.Column(db.String(200))
    
    # Professional Information
    company = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    
    # Address Information
    address = db.Column(db.Text)
    address_line_2 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(50))
    
    # Personal Information
    birthday = db.Column(db.Date)
    gender = db.Column(db.String(20))
    marital_status = db.Column(db.String(20))
    
    # Social Media & Communication
    linkedin = db.Column(db.String(200))
    twitter = db.Column(db.String(200))
    facebook = db.Column(db.String(200))
    instagram = db.Column(db.String(200))
    skype = db.Column(db.String(100))
    whatsapp = db.Column(db.String(20))
    telegram = db.Column(db.String(100))
    
    # Additional Information
    lead_source = db.Column(db.String(100))  # How did you find this contact
    lead_status = db.Column(db.String(50))   # Lead, Prospect, Customer, etc.
    priority = db.Column(db.String(20), default='normal')  # high, normal, low
    tags = db.Column(db.Text)  # JSON array of tags
    notes = db.Column(db.Text)
    
    # Custom fields (JSON storage for flexibility)
    custom_fields = db.Column(db.Text)  # JSON object for custom fields
    
    # Foreign keys
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    
    # Relationships
    created_by = db.relationship('User', backref='created_contacts')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Contact {self.full_name}>'

class Template(db.Model):
    """Template model for message templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template_type = db.Column(db.String(20), nullable=False)  # email, sms, whatsapp, rcs
    subject = db.Column(db.String(200))  # For email templates
    content = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text)  # JSON string of available variables
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='created_templates')
    
    def __repr__(self):
        return f'<Template {self.name}>'

class PasswordResetToken(db.Model):
    """Model for password reset tokens"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='reset_tokens')
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token}>'
