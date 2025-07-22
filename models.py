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
    
    def can_create_contacts(self):
        """Check if user can create contacts"""
        return self.role in ['owner', 'admin', 'member']
    
    def can_update_contacts(self):
        """Check if user can update contacts"""
        return self.role in ['owner', 'admin', 'member']
    
    def can_delete_contacts(self):
        """Check if user can delete contacts"""
        return self.role in ['owner', 'admin']
    
    def can_create_templates(self):
        """Check if user can create templates"""
        return self.role in ['owner', 'admin', 'member']
    
    def can_send_messages(self):
        """Check if user can send messages"""
        return self.role in ['owner', 'admin', 'member']
    
    def can_manage_organization(self):
        """Check if user can manage organization settings"""
        return self.role in ['owner', 'admin']
    
    def can_invite_users(self):
        """Check if user can invite users"""
        return self.role in ['owner', 'admin']
    
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

class OrganizationConfig(db.Model):
    """Organization-level configuration for messaging providers"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False, unique=True)
    
    # SMS Configuration
    sms_provider = db.Column(db.String(50), default='twilio')  # twilio, textlocal, msg91, clickatell, custom
    sms_api_url = db.Column(db.String(255))  # For custom SMS providers
    sms_api_key = db.Column(db.String(255))
    sms_username = db.Column(db.String(100))  # For TextLocal, etc.
    sms_sender_id = db.Column(db.String(50))
    
    # Email Configuration
    email_provider = db.Column(db.String(50), default='smtp')  # smtp, aws_ses
    smtp_host = db.Column(db.String(255))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(255))
    smtp_password = db.Column(db.String(255))
    smtp_use_tls = db.Column(db.Boolean, default=True)
    
    # AWS SES Configuration
    aws_access_key_id = db.Column(db.String(255))
    aws_secret_access_key = db.Column(db.String(255))
    aws_region = db.Column(db.String(50), default='us-east-1')
    aws_sender_email = db.Column(db.String(255))
    
    # WhatsApp Configuration
    whatsapp_api_url = db.Column(db.String(255))
    whatsapp_api_key = db.Column(db.String(255))
    whatsapp_phone_number = db.Column(db.String(50))
    whatsapp_webhook_url = db.Column(db.String(255))
    
    # General Settings
    default_sender_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    organization = db.relationship('Organization', backref=db.backref('config', uselist=False))
    
    def __repr__(self):
        return f'<OrganizationConfig {self.organization.name}>'

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
    
    @property
    def type(self):
        """Alias for template_type to maintain compatibility"""
        return self.template_type
    
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

class ApiKey(db.Model):
    """API Key model for external integrations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=False)  # SHA-256 hash of the key
    permissions = db.Column(db.JSON, default=['read'])  # ['read', 'write', 'message', 'admin']
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    
    # Relationships
    organization = db.relationship('Organization', backref='api_keys')
    created_by = db.relationship('User', backref='created_api_keys')
    
    def __repr__(self):
        return f'<ApiKey {self.name}>'

# Message Tracking Models
class MessageCampaign(db.Model):
    """Campaign tracking for message sends"""
    __tablename__ = 'message_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sending, completed, cancelled
    
    # Scheduling
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Target audience
    target_group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    recipient_count = db.Column(db.Integer, default=0)
    
    # Tracking metrics
    messages_sent = db.Column(db.Integer, default=0)
    messages_delivered = db.Column(db.Integer, default=0)
    messages_failed = db.Column(db.Integer, default=0)
    messages_opened = db.Column(db.Integer, default=0)
    messages_clicked = db.Column(db.Integer, default=0)
    messages_bounced = db.Column(db.Integer, default=0)
    unsubscribes = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = db.relationship('Template', backref='campaigns')
    organization = db.relationship('Organization', backref='message_campaigns')
    target_group = db.relationship('Group', backref='campaigns')
    
    @property
    def delivery_rate(self):
        """Calculate delivery rate percentage"""
        if self.messages_sent == 0:
            return 0
        return round((self.messages_delivered / self.messages_sent) * 100, 2)
    
    @property
    def open_rate(self):
        """Calculate open rate percentage"""
        if self.messages_delivered == 0:
            return 0
        return round((self.messages_opened / self.messages_delivered) * 100, 2)
    
    @property
    def click_rate(self):
        """Calculate click-through rate percentage"""
        if self.messages_delivered == 0:
            return 0
        return round((self.messages_clicked / self.messages_delivered) * 100, 2)

class MessageDelivery(db.Model):
    """Individual message delivery tracking"""
    __tablename__ = 'message_deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('message_campaigns.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    
    # Message details
    message_id = db.Column(db.String(100))  # External provider message ID
    channel = db.Column(db.String(20), nullable=False)  # sms, email, whatsapp
    recipient = db.Column(db.String(200), nullable=False)  # phone/email address
    
    # Status tracking
    status = db.Column(db.String(20), default='queued')  # queued, sent, delivered, failed, bounced
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    
    # Error tracking
    error_code = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = db.relationship('MessageCampaign', backref='deliveries')
    contact = db.relationship('Contact', backref='message_deliveries')

class MessageLog(db.Model):
    """Message Log model for tracking sent messages"""
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_key.id'))  # If sent via API
    
    message_type = db.Column(db.String(20), nullable=False)  # sms, email, whatsapp
    recipient = db.Column(db.String(255), nullable=False)  # phone or email
    subject = db.Column(db.String(255))  # for emails
    content = db.Column(db.Text)
    
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, delivered
    provider = db.Column(db.String(50))  # twilio, smtp, etc.
    provider_message_id = db.Column(db.String(255))
    error_message = db.Column(db.Text)
    
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_via_api = db.Column(db.Boolean, default=False)
    
    # Relationships
    contact = db.relationship('Contact', backref='message_logs')
    template = db.relationship('Template', backref='message_logs')
    organization = db.relationship('Organization', backref='message_logs')
    api_key = db.relationship('ApiKey', backref='message_logs')
    
    def __repr__(self):
        return f'<MessageLog {self.message_type} to {self.recipient}>'
