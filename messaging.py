"""
Enterprise Messaging System - SMS, Email, WhatsApp Integration
Supports custom SMTP settings and AWS SES for email delivery
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException

from flask import current_app
from models import Contact, Template, Organization


class MessagingService:
    """Enterprise messaging service supporting multiple channels"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, 
                    template_id: int, 
                    contact_ids: List[int], 
                    custom_variables: Dict[str, Any] = None,
                    organization_id: int = None) -> Dict[str, Any]:
        """
        Send message using template to multiple contacts
        
        Args:
            template_id: ID of the message template
            contact_ids: List of contact IDs to send to
            custom_variables: Additional variables for template personalization
            organization_id: Organization ID for scoping
            
        Returns:
            Dict with success status and delivery results
        """
        try:
            # Get template and validate
            template = Template.query.filter_by(
                id=template_id,
                organization_id=organization_id
            ).first()
            
            if not template:
                return {'success': False, 'error': 'Template not found'}
            
            # Get contacts
            contacts = Contact.query.filter(
                Contact.id.in_(contact_ids),
                Contact.organization_id == organization_id
            ).all()
            
            if not contacts:
                return {'success': False, 'error': 'No valid contacts found'}
            
            results = {
                'success': True,
                'sent': 0,
                'failed': 0,
                'details': []
            }
            
            for contact in contacts:
                try:
                    # Personalize template content
                    personalized_content = self._personalize_template(
                        template, contact, custom_variables
                    )
                    
                    # Send based on channel type
                    if template.channel == 'email':
                        result = self._send_email(contact, template, personalized_content)
                    elif template.channel == 'sms':
                        result = self._send_sms(contact, template, personalized_content)
                    elif template.channel == 'whatsapp':
                        result = self._send_whatsapp(contact, template, personalized_content)
                    else:
                        result = {'success': False, 'error': f'Unsupported channel: {template.channel}'}
                    
                    if result['success']:
                        results['sent'] += 1
                    else:
                        results['failed'] += 1
                    
                    results['details'].append({
                        'contact_id': contact.id,
                        'contact_name': f"{contact.first_name} {contact.last_name}",
                        'channel': template.channel,
                        'success': result['success'],
                        'message': result.get('message', ''),
                        'error': result.get('error', '')
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error sending to contact {contact.id}: {str(e)}")
                    results['failed'] += 1
                    results['details'].append({
                        'contact_id': contact.id,
                        'contact_name': f"{contact.first_name} {contact.last_name}",
                        'channel': template.channel,
                        'success': False,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in send_message: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _personalize_template(self, template: Template, contact: Contact, 
                             custom_variables: Dict[str, Any] = None) -> Dict[str, str]:
        """Personalize template content with contact data and custom variables"""
        
        # Build variable dictionary
        variables = {
            'first_name': contact.first_name or '',
            'last_name': contact.last_name or '',
            'full_name': f"{contact.first_name or ''} {contact.last_name or ''}".strip(),
            'email': contact.email or '',
            'phone': contact.phone or '',
            'mobile': contact.mobile or '',
            'company': contact.company or '',
            'job_title': contact.job_title or '',
            'department': contact.department or '',
            'industry': contact.industry or '',
            'website': contact.website or '',
            'address': contact.address or '',
            'city': contact.city or '',
            'state': contact.state or '',
            'country': contact.country or '',
            'postal_code': contact.postal_code or ''
        }
        
        # Add custom variables if provided
        if custom_variables:
            variables.update(custom_variables)
        
        # Personalize subject and content
        subject = template.subject or ''
        content = template.content or ''
        
        try:
            # Replace variables in format {variable_name}
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                subject = subject.replace(placeholder, str(value))
                content = content.replace(placeholder, str(value))
            
            return {
                'subject': subject,
                'content': content
            }
        except Exception as e:
            self.logger.error(f"Error personalizing template: {str(e)}")
            return {
                'subject': template.subject or '',
                'content': template.content or ''
            }
    
    def _send_email(self, contact: Contact, template: Template, 
                   personalized_content: Dict[str, str]) -> Dict[str, Any]:
        """Send email using configured SMTP settings or AWS SES"""
        
        if not contact.email:
            return {'success': False, 'error': 'Contact has no email address'}
        
        try:
            # Try AWS SES first if configured
            if self._is_aws_ses_configured():
                return self._send_email_aws_ses(contact, template, personalized_content)
            
            # Fall back to custom SMTP
            elif self._is_custom_smtp_configured():
                return self._send_email_smtp(contact, template, personalized_content)
            
            else:
                return {'success': False, 'error': 'No email service configured'}
                
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_email_aws_ses(self, contact: Contact, template: Template,
                           personalized_content: Dict[str, str]) -> Dict[str, Any]:
        """Send email using AWS SES"""
        try:
            # Initialize SES client
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
            
            # Prepare email
            from_email = os.environ.get('AWS_SES_FROM_EMAIL', 'noreply@contacthub.com')
            subject = personalized_content['subject']
            content = personalized_content['content']
            
            # Send email
            response = ses_client.send_email(
                Source=from_email,
                Destination={
                    'ToAddresses': [contact.email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html' if template.content_type == 'html' else 'Text': {
                            'Data': content,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            message_id = response.get('MessageId')
            self.logger.info(f"Email sent via AWS SES to {contact.email}, MessageId: {message_id}")
            
            return {
                'success': True,
                'message': f'Email sent successfully via AWS SES',
                'message_id': message_id
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"AWS SES error {error_code}: {error_message}")
            return {'success': False, 'error': f'AWS SES error: {error_message}'}
            
        except NoCredentialsError:
            return {'success': False, 'error': 'AWS credentials not configured'}
            
        except Exception as e:
            self.logger.error(f"Unexpected error with AWS SES: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_email_smtp(self, contact: Contact, template: Template,
                        personalized_content: Dict[str, str]) -> Dict[str, Any]:
        """Send email using custom SMTP settings"""
        try:
            # Get SMTP configuration
            smtp_host = os.environ.get('SMTP_HOST')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_username = os.environ.get('SMTP_USERNAME')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            smtp_use_tls = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
            from_email = os.environ.get('SMTP_FROM_EMAIL', smtp_username)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = contact.email
            msg['Subject'] = personalized_content['subject']
            
            # Add body
            body = personalized_content['content']
            if template.content_type == 'html':
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls() if smtp_use_tls else None
            server.login(smtp_username, smtp_password)
            
            text = msg.as_string()
            server.sendmail(from_email, contact.email, text)
            server.quit()
            
            self.logger.info(f"Email sent via SMTP to {contact.email}")
            
            return {
                'success': True,
                'message': 'Email sent successfully via SMTP'
            }
            
        except Exception as e:
            self.logger.error(f"SMTP error: {str(e)}")
            return {'success': False, 'error': f'SMTP error: {str(e)}'}
    
    def _send_sms(self, contact: Contact, template: Template,
                 personalized_content: Dict[str, str]) -> Dict[str, Any]:
        """Send SMS using Twilio"""
        
        phone_number = contact.phone or contact.mobile
        if not phone_number:
            return {'success': False, 'error': 'Contact has no phone number'}
        
        try:
            # Initialize Twilio client
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            from_number = os.environ.get('TWILIO_PHONE_NUMBER')
            
            if not all([account_sid, auth_token, from_number]):
                return {'success': False, 'error': 'Twilio credentials not configured'}
            
            client = TwilioClient(account_sid, auth_token)
            
            # Send SMS
            message = client.messages.create(
                body=personalized_content['content'],
                from_=from_number,
                to=phone_number
            )
            
            self.logger.info(f"SMS sent to {phone_number}, SID: {message.sid}")
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'message_sid': message.sid
            }
            
        except TwilioException as e:
            self.logger.error(f"Twilio error: {str(e)}")
            return {'success': False, 'error': f'Twilio error: {str(e)}'}
            
        except Exception as e:
            self.logger.error(f"SMS error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_whatsapp(self, contact: Contact, template: Template,
                      personalized_content: Dict[str, str]) -> Dict[str, Any]:
        """Send WhatsApp message using Twilio WhatsApp API"""
        
        phone_number = contact.phone or contact.mobile
        if not phone_number:
            return {'success': False, 'error': 'Contact has no phone number'}
        
        try:
            # Initialize Twilio client
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            from_whatsapp = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Twilio Sandbox
            
            if not all([account_sid, auth_token]):
                return {'success': False, 'error': 'Twilio credentials not configured'}
            
            client = TwilioClient(account_sid, auth_token)
            
            # Format WhatsApp number
            to_whatsapp = f"whatsapp:{phone_number}"
            
            # Send WhatsApp message
            message = client.messages.create(
                body=personalized_content['content'],
                from_=from_whatsapp,
                to=to_whatsapp
            )
            
            self.logger.info(f"WhatsApp sent to {phone_number}, SID: {message.sid}")
            
            return {
                'success': True,
                'message': 'WhatsApp message sent successfully',
                'message_sid': message.sid
            }
            
        except TwilioException as e:
            self.logger.error(f"Twilio WhatsApp error: {str(e)}")
            return {'success': False, 'error': f'Twilio WhatsApp error: {str(e)}'}
            
        except Exception as e:
            self.logger.error(f"WhatsApp error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _is_aws_ses_configured(self) -> bool:
        """Check if AWS SES is properly configured"""
        return all([
            os.environ.get('AWS_ACCESS_KEY_ID'),
            os.environ.get('AWS_SECRET_ACCESS_KEY'),
            os.environ.get('AWS_SES_FROM_EMAIL')
        ])
    
    def _is_custom_smtp_configured(self) -> bool:
        """Check if custom SMTP is properly configured"""
        return all([
            os.environ.get('SMTP_HOST'),
            os.environ.get('SMTP_USERNAME'),
            os.environ.get('SMTP_PASSWORD')
        ])
    
    def test_email_configuration(self, test_email: str) -> Dict[str, Any]:
        """Test email configuration by sending a test message"""
        try:
            # Create test contact
            test_contact = type('TestContact', (), {
                'email': test_email,
                'first_name': 'Test',
                'last_name': 'User'
            })()
            
            # Create test template
            test_template = type('TestTemplate', (), {
                'subject': 'ContactHub Email Configuration Test',
                'content': 'Hello {first_name}! This is a test email to verify your email configuration is working correctly.',
                'content_type': 'plain',
                'channel': 'email'
            })()
            
            # Test AWS SES first
            if self._is_aws_ses_configured():
                result = self._send_email_aws_ses(test_contact, test_template, {
                    'subject': test_template.subject.replace('{first_name}', 'Test'),
                    'content': test_template.content.replace('{first_name}', 'Test')
                })
                if result['success']:
                    result['service'] = 'AWS SES'
                    return result
            
            # Test SMTP if SES failed or not configured
            if self._is_custom_smtp_configured():
                result = self._send_email_smtp(test_contact, test_template, {
                    'subject': test_template.subject.replace('{first_name}', 'Test'),
                    'content': test_template.content.replace('{first_name}', 'Test')
                })
                if result['success']:
                    result['service'] = 'Custom SMTP'
                    return result
            
            return {'success': False, 'error': 'No email service configured'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_available_variables(self) -> List[Dict[str, str]]:
        """Get list of available variables for template personalization"""
        return [
            {'name': 'first_name', 'description': 'Contact first name'},
            {'name': 'last_name', 'description': 'Contact last name'},
            {'name': 'full_name', 'description': 'Contact full name'},
            {'name': 'email', 'description': 'Contact email address'},
            {'name': 'phone', 'description': 'Contact phone number'},
            {'name': 'mobile', 'description': 'Contact mobile number'},
            {'name': 'company', 'description': 'Contact company'},
            {'name': 'job_title', 'description': 'Contact job title'},
            {'name': 'department', 'description': 'Contact department'},
            {'name': 'industry', 'description': 'Contact industry'},
            {'name': 'website', 'description': 'Contact website'},
            {'name': 'address', 'description': 'Contact address'},
            {'name': 'city', 'description': 'Contact city'},
            {'name': 'state', 'description': 'Contact state'},
            {'name': 'country', 'description': 'Contact country'},
            {'name': 'postal_code', 'description': 'Contact postal code'}
        ]