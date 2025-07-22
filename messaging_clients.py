"""
Messaging API Clients - SMS, Email, WhatsApp Integration
Comprehensive client implementations for all supported messaging providers
"""

import os
import logging
import requests
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError
from models import OrganizationConfig

class SMSClientFactory:
    """Factory for creating SMS clients based on provider"""
    
    @staticmethod
    def create_client(config: OrganizationConfig):
        """Create SMS client based on configuration"""
        provider = config.sms_provider.lower()
        
        if provider == 'twilio':
            return TwilioSMSClient(config)
        elif provider == 'textlocal':
            return TextLocalSMSClient(config)
        elif provider == 'msg91':
            return MSG91SMSClient(config)
        elif provider == 'clickatell':
            return ClickatellSMSClient(config)
        elif provider == 'custom':
            return CustomSMSClient(config)
        else:
            raise ValueError(f"Unsupported SMS provider: {provider}")

class BaseSMSClient:
    """Base class for SMS clients"""
    
    def __init__(self, config: OrganizationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_sms(self, to_number: str, message: str, sender_id: str = None) -> Dict[str, Any]:
        """Send SMS message - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement send_sms method")

class TwilioSMSClient(BaseSMSClient):
    """Twilio SMS client implementation"""
    
    def send_sms(self, to_number: str, message: str, sender_id: str = None) -> Dict[str, Any]:
        try:
            # Use environment variables or config for Twilio credentials
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID') or self.config.sms_username
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN') or self.config.sms_api_key
            from_number = os.environ.get('TWILIO_PHONE_NUMBER') or self.config.sms_sender_id
            
            if not all([account_sid, auth_token, from_number]):
                return {'success': False, 'error': 'Twilio credentials not configured'}
            
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            
            message_obj = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'provider': 'twilio',
                'status': message_obj.status
            }
            
        except Exception as e:
            self.logger.error(f"Twilio SMS error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'twilio'}

class TextLocalSMSClient(BaseSMSClient):
    """TextLocal SMS client implementation"""
    
    def send_sms(self, to_number: str, message: str, sender_id: str = None) -> Dict[str, Any]:
        try:
            api_key = self.config.sms_api_key
            username = self.config.sms_username
            sender = sender_id or self.config.sms_sender_id or 'TextLocal'
            
            if not api_key:
                return {'success': False, 'error': 'TextLocal API key not configured'}
            
            # Clean phone number
            to_number = to_number.replace('+', '').replace(' ', '')
            
            data = {
                'apikey': api_key,
                'numbers': to_number,
                'message': message,
                'sender': sender
            }
            
            if username:
                data['username'] = username
            
            response = requests.post('https://api.textlocal.in/send/', data=data)
            result = response.json()
            
            if result.get('status') == 'success':
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'provider': 'textlocal',
                    'credits_used': result.get('cost')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errors', [{}])[0].get('message', 'Unknown error'),
                    'provider': 'textlocal'
                }
                
        except Exception as e:
            self.logger.error(f"TextLocal SMS error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'textlocal'}

class MSG91SMSClient(BaseSMSClient):
    """MSG91 SMS client implementation"""
    
    def send_sms(self, to_number: str, message: str, sender_id: str = None) -> Dict[str, Any]:
        try:
            api_key = self.config.sms_api_key
            sender = sender_id or self.config.sms_sender_id or 'MSG91'
            
            if not api_key:
                return {'success': False, 'error': 'MSG91 API key not configured'}
            
            # Clean phone number
            to_number = to_number.replace('+', '').replace(' ', '')
            
            headers = {'Content-Type': 'application/json'}
            
            data = {
                'sender': sender,
                'route': '4',
                'country': '91',
                'sms': [{
                    'message': message,
                    'to': [to_number]
                }]
            }
            
            url = f'https://api.msg91.com/api/v5/flow/?apikey={api_key}'
            response = requests.post(url, json=data, headers=headers)
            result = response.json()
            
            if response.status_code == 200 and result.get('type') == 'success':
                return {
                    'success': True,
                    'message_id': result.get('request_id'),
                    'provider': 'msg91'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error'),
                    'provider': 'msg91'
                }
                
        except Exception as e:
            self.logger.error(f"MSG91 SMS error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'msg91'}

class ClickatellSMSClient(BaseSMSClient):
    """Clickatell SMS client implementation"""
    
    def send_sms(self, to_number: str, message: str, sender_id: str = None) -> Dict[str, Any]:
        try:
            api_key = self.config.sms_api_key
            
            if not api_key:
                return {'success': False, 'error': 'Clickatell API key not configured'}
            
            headers = {
                'Authorization': api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'text': message,
                'to': [to_number]
            }
            
            if sender_id or self.config.sms_sender_id:
                data['from'] = sender_id or self.config.sms_sender_id
            
            response = requests.post(
                'https://platform.clickatell.com/messages',
                json=data,
                headers=headers
            )
            
            if response.status_code == 202:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('apiMessageId'),
                    'provider': 'clickatell'
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'provider': 'clickatell'
                }
                
        except Exception as e:
            self.logger.error(f"Clickatell SMS error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'clickatell'}

class CustomSMSClient(BaseSMSClient):
    """Custom HTTP API SMS client implementation"""
    
    def send_sms(self, to_number: str, message: str, sender_id: str = None) -> Dict[str, Any]:
        try:
            api_url = self.config.sms_api_url
            api_key = self.config.sms_api_key
            
            if not all([api_url, api_key]):
                return {'success': False, 'error': 'Custom SMS API URL or key not configured'}
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'to': to_number,
                'message': message,
                'from': sender_id or self.config.sms_sender_id
            }
            
            response = requests.post(api_url, json=data, headers=headers)
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('id') or result.get('messageId') or result.get('message_id'),
                    'provider': 'custom'
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'provider': 'custom'
                }
                
        except Exception as e:
            self.logger.error(f"Custom SMS error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'custom'}

class EmailClientFactory:
    """Factory for creating email clients based on provider"""
    
    @staticmethod
    def create_client(config: OrganizationConfig):
        """Create email client based on configuration"""
        provider = config.email_provider.lower()
        
        if provider == 'smtp':
            return SMTPEmailClient(config)
        elif provider == 'aws_ses':
            return AWSSESEmailClient(config)
        else:
            raise ValueError(f"Unsupported email provider: {provider}")

class BaseEmailClient:
    """Base class for email clients"""
    
    def __init__(self, config: OrganizationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, to_email: str, subject: str, content: str, 
                   from_email: str = None, from_name: str = None) -> Dict[str, Any]:
        """Send email - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement send_email method")

class SMTPEmailClient(BaseEmailClient):
    """SMTP email client implementation"""
    
    def send_email(self, to_email: str, subject: str, content: str, 
                   from_email: str = None, from_name: str = None) -> Dict[str, Any]:
        try:
            smtp_host = self.config.smtp_host
            smtp_port = self.config.smtp_port or 587
            smtp_username = self.config.smtp_username
            smtp_password = self.config.smtp_password
            use_tls = self.config.smtp_use_tls
            
            if not all([smtp_host, smtp_username, smtp_password]):
                return {'success': False, 'error': 'SMTP configuration incomplete'}
            
            from_email = from_email or smtp_username
            from_name = from_name or self.config.default_sender_name
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(content, 'html' if '<' in content else 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_host, smtp_port)
            if use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return {
                'success': True,
                'provider': 'smtp',
                'from_email': from_email,
                'to_email': to_email
            }
            
        except Exception as e:
            self.logger.error(f"SMTP email error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'smtp'}

class AWSSESEmailClient(BaseEmailClient):
    """Amazon SES email client implementation"""
    
    def send_email(self, to_email: str, subject: str, content: str, 
                   from_email: str = None, from_name: str = None) -> Dict[str, Any]:
        try:
            access_key = self.config.aws_access_key_id
            secret_key = self.config.aws_secret_access_key
            region = self.config.aws_region or 'us-east-1'
            
            if not all([access_key, secret_key]):
                return {'success': False, 'error': 'AWS SES credentials not configured'}
            
            from_email = from_email or self.config.aws_sender_email
            from_name = from_name or self.config.default_sender_name
            
            if not from_email:
                return {'success': False, 'error': 'Sender email not configured'}
            
            # Create SES client
            client = boto3.client(
                'ses',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Determine content type
            body_key = 'Html' if '<' in content else 'Text'
            
            response = client.send_email(
                Destination={
                    'ToAddresses': [to_email]
                },
                Message={
                    'Body': {
                        body_key: {
                            'Charset': 'UTF-8',
                            'Data': content
                        }
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': subject
                    }
                },
                Source=f"{from_name} <{from_email}>" if from_name else from_email
            )
            
            return {
                'success': True,
                'message_id': response['MessageId'],
                'provider': 'aws_ses',
                'from_email': from_email,
                'to_email': to_email
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"AWS SES error {error_code}: {error_message}")
            return {'success': False, 'error': f'{error_code}: {error_message}', 'provider': 'aws_ses'}
        except Exception as e:
            self.logger.error(f"AWS SES error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'aws_ses'}

class WhatsAppClient:
    """WhatsApp Business API client implementation"""
    
    def __init__(self, config: OrganizationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, to_number: str, message: str, message_type: str = 'text') -> Dict[str, Any]:
        """Send WhatsApp message"""
        try:
            api_url = self.config.whatsapp_api_url
            api_key = self.config.whatsapp_api_key
            
            if not all([api_url, api_key]):
                return {'success': False, 'error': 'WhatsApp API configuration incomplete'}
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Clean phone number (remove + and spaces)
            to_number = to_number.replace('+', '').replace(' ', '')
            
            data = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'type': message_type,
                'text': {
                    'body': message
                }
            }
            
            response = requests.post(api_url, json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'provider': 'whatsapp',
                    'to_number': to_number
                }
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get('error', {}).get('message', response.text)
                
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {error_message}',
                    'provider': 'whatsapp'
                }
                
        except Exception as e:
            self.logger.error(f"WhatsApp error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'whatsapp'}
    
    def send_template_message(self, to_number: str, template_name: str, 
                            template_variables: List[str] = None) -> Dict[str, Any]:
        """Send WhatsApp template message"""
        try:
            api_url = self.config.whatsapp_api_url
            api_key = self.config.whatsapp_api_key
            
            if not all([api_url, api_key]):
                return {'success': False, 'error': 'WhatsApp API configuration incomplete'}
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Clean phone number
            to_number = to_number.replace('+', '').replace(' ', '')
            
            data = {
                'messaging_product': 'whatsapp',
                'to': to_number,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {
                        'code': 'en'
                    }
                }
            }
            
            # Add template variables if provided
            if template_variables:
                data['template']['components'] = [{
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': var} for var in template_variables]
                }]
            
            response = requests.post(api_url, json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'provider': 'whatsapp_template',
                    'template': template_name,
                    'to_number': to_number
                }
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get('error', {}).get('message', response.text)
                
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {error_message}',
                    'provider': 'whatsapp_template'
                }
                
        except Exception as e:
            self.logger.error(f"WhatsApp template error: {e}")
            return {'success': False, 'error': str(e), 'provider': 'whatsapp_template'}

class UnifiedMessagingClient:
    """Unified client that handles all messaging providers with fallback"""
    
    def __init__(self, config: OrganizationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_sms(self, to_number: str, message: str, sender_id: str = None) -> Dict[str, Any]:
        """Send SMS with configured provider and Twilio fallback"""
        try:
            # Try configured SMS provider first
            sms_client = SMSClientFactory.create_client(self.config)
            result = sms_client.send_sms(to_number, message, sender_id)
            
            if result['success']:
                return result
            
            # Fallback to Twilio if available and different from primary
            if self.config.sms_provider.lower() != 'twilio':
                if os.environ.get('TWILIO_ACCOUNT_SID'):
                    self.logger.info(f"Primary SMS provider failed, trying Twilio fallback")
                    fallback_config = OrganizationConfig(sms_provider='twilio')
                    twilio_client = TwilioSMSClient(fallback_config)
                    fallback_result = twilio_client.send_sms(to_number, message, sender_id)
                    
                    if fallback_result['success']:
                        fallback_result['fallback'] = True
                        return fallback_result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Unified SMS error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_email(self, to_email: str, subject: str, content: str, 
                   from_email: str = None, from_name: str = None) -> Dict[str, Any]:
        """Send email with configured provider and fallback"""
        try:
            # Try configured email provider first
            email_client = EmailClientFactory.create_client(self.config)
            result = email_client.send_email(to_email, subject, content, from_email, from_name)
            
            if result['success']:
                return result
            
            # Fallback logic can be added here if needed
            return result
            
        except Exception as e:
            self.logger.error(f"Unified email error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_whatsapp(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message"""
        try:
            whatsapp_client = WhatsAppClient(self.config)
            return whatsapp_client.send_message(to_number, message)
            
        except Exception as e:
            self.logger.error(f"WhatsApp error: {e}")
            return {'success': False, 'error': str(e)}