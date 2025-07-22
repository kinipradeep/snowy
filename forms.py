from flask import request
import re

class FormValidator:
    """Base form validator class"""
    
    def __init__(self, data=None):
        self.data = data or request.form
        self.errors = {}
    
    def validate_required(self, field, message=None):
        """Validate required field"""
        value = self.data.get(field, '').strip()
        if not value:
            self.errors[field] = message or f"{field.replace('_', ' ').title()} is required"
        return value
    
    def validate_email(self, field, required=True):
        """Validate email format"""
        value = self.data.get(field, '').strip()
        if required and not value:
            self.errors[field] = "Email is required"
            return value
        
        if value and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            self.errors[field] = "Invalid email format"
        
        return value
    
    def validate_length(self, field, min_length=None, max_length=None, required=True):
        """Validate field length"""
        value = self.data.get(field, '').strip()
        
        if required and not value:
            self.errors[field] = f"{field.replace('_', ' ').title()} is required"
            return value
        
        if value:
            if min_length and len(value) < min_length:
                self.errors[field] = f"Must be at least {min_length} characters long"
            elif max_length and len(value) > max_length:
                self.errors[field] = f"Must be no more than {max_length} characters long"
        
        return value
    
    def validate_phone(self, field, required=False):
        """Validate phone number format"""
        value = self.data.get(field, '').strip()
        
        if required and not value:
            self.errors[field] = f"{field.replace('_', ' ').title()} is required"
            return value
        
        if value and not re.match(r'^[\d\s\-\+\(\)\.]+$', value):
            self.errors[field] = "Invalid phone number format"
        
        return value
    
    def is_valid(self):
        """Check if form is valid"""
        return len(self.errors) == 0

class LoginForm(FormValidator):
    """Login form validator"""
    
    def validate(self):
        self.username = self.validate_required('username', 'Username is required')
        self.password = self.validate_required('password', 'Password is required')
        return self.is_valid()

class RegisterForm(FormValidator):
    """Registration form validator"""
    
    def validate(self):
        self.username = self.validate_length('username', min_length=3, max_length=80)
        self.email = self.validate_email('email')
        self.first_name = self.validate_length('first_name', min_length=1, max_length=50)
        self.last_name = self.validate_length('last_name', min_length=1, max_length=50)
        self.password = self.validate_length('password', min_length=6)
        self.confirm_password = self.validate_required('confirm_password', 'Please confirm your password')
        
        # Check password confirmation
        if self.password and self.confirm_password and self.password != self.confirm_password:
            self.errors['confirm_password'] = 'Passwords do not match'
        
        return self.is_valid()

class ContactForm(FormValidator):
    """Contact form validator"""
    
    def validate(self):
        self.first_name = self.validate_length('first_name', min_length=1, max_length=50)
        self.last_name = self.validate_length('last_name', min_length=1, max_length=50)
        self.email = self.validate_email('email', required=False)
        self.phone = self.validate_phone('phone', required=False)
        self.mobile = self.validate_phone('mobile', required=False)
        self.company = self.validate_length('company', max_length=100, required=False)
        self.job_title = self.validate_length('job_title', max_length=100, required=False)
        self.city = self.validate_length('city', max_length=50, required=False)
        self.state = self.validate_length('state', max_length=50, required=False)
        self.postal_code = self.validate_length('postal_code', max_length=20, required=False)
        self.country = self.validate_length('country', max_length=50, required=False)
        
        # At least one contact method should be provided
        if not any([self.email, self.phone, self.mobile]):
            self.errors['contact_method'] = 'Please provide at least one contact method (email, phone, or mobile)'
        
        return self.is_valid()

class GroupForm(FormValidator):
    """Group form validator"""
    
    def validate(self):
        self.name = self.validate_length('name', min_length=1, max_length=100)
        self.description = self.data.get('description', '').strip()
        return self.is_valid()

class TemplateForm(FormValidator):
    """Template form validator"""
    
    def validate(self):
        self.name = self.validate_length('name', min_length=1, max_length=100)
        self.template_type = self.validate_required('template_type', 'Template type is required')
        self.content = self.validate_required('content', 'Template content is required')
        self.subject = self.data.get('subject', '').strip()
        
        # Subject is required for email templates
        if self.template_type == 'email' and not self.subject:
            self.errors['subject'] = 'Subject is required for email templates'
        
        return self.is_valid()

class PasswordResetRequestForm(FormValidator):
    """Password reset request form validator"""
    
    def validate(self):
        self.email = self.validate_email('email')
        return self.is_valid()

class PasswordResetForm(FormValidator):
    """Password reset form validator"""
    
    def validate(self):
        self.password = self.validate_length('password', min_length=6)
        self.confirm_password = self.validate_required('confirm_password', 'Please confirm your password')
        
        # Check password confirmation
        if self.password and self.confirm_password and self.password != self.confirm_password:
            self.errors['confirm_password'] = 'Passwords do not match'
        
        return self.is_valid()
