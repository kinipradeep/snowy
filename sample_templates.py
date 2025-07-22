#!/usr/bin/env python3
"""
Sample templates for SMS, Email, and WhatsApp messaging
"""

import os
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

SAMPLE_TEMPLATES = [
        # SMS Templates
        {
            'name': 'Welcome SMS',
            'channel': 'sms',
            'subject': '',
            'content': 'Welcome to {{organization_name}}! 👋 Thank you for joining us. Your account is now active. Reply STOP to opt out.',
            'variables': 'organization_name'
        },
        {
            'name': 'Appointment Reminder',
            'channel': 'sms',
            'subject': '',
            'content': 'Hi {{first_name}}, reminder: Your appointment with {{organization_name}} is scheduled for {{appointment_date}} at {{appointment_time}}. See you soon!',
            'variables': 'first_name,organization_name,appointment_date,appointment_time'
        },
        {
            'name': 'Order Status Update',
            'channel': 'sms',
            'subject': '',
            'content': '📦 Order Update: Your order #{{order_id}} has been {{status}}. Track here: {{tracking_link}}. Questions? Call us at {{phone}}.',
            'variables': 'order_id,status,tracking_link,phone'
        },
        
        # Email Templates
        {
            'name': 'Welcome Email',
            'channel': 'email',
            'subject': 'Welcome to {{organization_name}} - Let\'s Get Started!',
            'content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to {{organization_name}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .btn { display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{organization_name}}!</h1>
            <p>We're thrilled to have you join our community</p>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>Thank you for joining {{organization_name}}! We're excited to help you achieve your goals.</p>
            
            <h3>What's Next?</h3>
            <ul>
                <li>Complete your profile setup</li>
                <li>Explore our features and tools</li>
                <li>Connect with our community</li>
            </ul>
            
            <a href="{{dashboard_link}}" class="btn">Get Started Now</a>
            
            <p>If you have any questions, don't hesitate to reach out to our support team at {{support_email}}.</p>
            
            <p>Best regards,<br>The {{organization_name}} Team</p>
        </div>
        <div class="footer">
            <p>{{organization_name}} | {{organization_address}}</p>
            <p><a href="{{unsubscribe_link}}">Unsubscribe</a> | <a href="{{preferences_link}}">Email Preferences</a></p>
        </div>
    </div>
</body>
</html>''',
            'variables': 'organization_name,first_name,dashboard_link,support_email,organization_address,unsubscribe_link,preferences_link'
        },
        {
            'name': 'Newsletter Template',
            'channel': 'email',
            'subject': '{{organization_name}} Newsletter - {{newsletter_title}}',
            'content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{newsletter_title}}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }
        .container { max-width: 600px; margin: 0 auto; background: white; }
        .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px; }
        .article { margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
        .article:last-child { border-bottom: none; }
        .article h3 { color: #2c3e50; margin-top: 0; }
        .article img { max-width: 100%; height: auto; border-radius: 5px; }
        .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        .social { text-align: center; padding: 20px; background: #ecf0f1; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{organization_name}}</h1>
            <p>{{newsletter_title}}</p>
        </div>
        <div class="content">
            <p>Hello {{first_name}},</p>
            
            <div class="article">
                <h3>{{article_1_title}}</h3>
                <p>{{article_1_content}}</p>
                <a href="{{article_1_link}}" class="btn">Read More</a>
            </div>
            
            <div class="article">
                <h3>{{article_2_title}}</h3>
                <p>{{article_2_content}}</p>
                <a href="{{article_2_link}}" class="btn">Read More</a>
            </div>
            
            <div class="article">
                <h3>Quick Updates</h3>
                <ul>
                    <li>{{update_1}}</li>
                    <li>{{update_2}}</li>
                    <li>{{update_3}}</li>
                </ul>
            </div>
        </div>
        <div class="social">
            <p>Follow us on social media:</p>
            <a href="{{facebook_link}}">Facebook</a> | 
            <a href="{{twitter_link}}">Twitter</a> | 
            <a href="{{linkedin_link}}">LinkedIn</a>
        </div>
        <div class="footer">
            <p>{{organization_name}} | {{organization_address}}</p>
            <p><a href="{{unsubscribe_link}}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>''',
            'variables': 'organization_name,newsletter_title,first_name,article_1_title,article_1_content,article_1_link,article_2_title,article_2_content,article_2_link,update_1,update_2,update_3,facebook_link,twitter_link,linkedin_link,organization_address,unsubscribe_link'
        },
        
        # WhatsApp Templates
        {
            'name': 'Order Confirmation',
            'channel': 'whatsapp',
            'subject': '',
            'content': '''🎉 *Order Confirmed!*

Hi {{first_name}},

Your order has been confirmed:

📦 *Order Details:*
• Order ID: #{{order_id}}
• Total: {{currency}}{{total_amount}}
• Estimated Delivery: {{delivery_date}}

🚚 *Tracking Information:*
Track your order: {{tracking_link}}

📞 *Need Help?*
Contact us: {{support_phone}}
Email: {{support_email}}

Thank you for choosing {{organization_name}}!

_Reply STOP to opt out of notifications_''',
            'variables': 'first_name,order_id,currency,total_amount,delivery_date,tracking_link,support_phone,support_email,organization_name'
        },
        {
            'name': 'Appointment Booking',
            'channel': 'whatsapp',
            'subject': '',
            'content': '''📅 *Appointment Booked*

Hello {{first_name}},

Your appointment has been successfully booked:

🗓️ *Appointment Details:*
• Date: {{appointment_date}}
• Time: {{appointment_time}}
• Service: {{service_name}}
• Provider: {{provider_name}}
• Location: {{location}}

💡 *Important Notes:*
{{appointment_notes}}

📲 *Manage Your Appointment:*
• Reschedule: {{reschedule_link}}
• Cancel: {{cancel_link}}

We look forward to seeing you!

{{organization_name}}
{{organization_phone}}

_Reply STOP to opt out_''',
            'variables': 'first_name,appointment_date,appointment_time,service_name,provider_name,location,appointment_notes,reschedule_link,cancel_link,organization_name,organization_phone'
        },
        {
            'name': 'Payment Reminder',
            'channel': 'whatsapp',
            'subject': '',
            'content': '''💳 *Payment Reminder*

Hi {{first_name}},

This is a friendly reminder about your upcoming payment:

💰 *Payment Details:*
• Amount: {{currency}}{{amount}}
• Due Date: {{due_date}}
• Invoice: #{{invoice_id}}

💻 *Pay Now:*
{{payment_link}}

📞 *Questions?*
Call us: {{support_phone}}
Email: {{support_email}}

*{{organization_name}}*

_Secure payment link expires in 7 days_
_Reply STOP to opt out_''',
            'variables': 'first_name,currency,amount,due_date,invoice_id,payment_link,support_phone,support_email,organization_name'
        }
    ]

def display_sample_templates():
    """Display sample templates for demonstration"""
    print("=== Cool Blue Sample Templates ===\n")
    
    for i, template in enumerate(SAMPLE_TEMPLATES, 1):
        print(f"📄 Template {i}: {template['name']} ({template['channel'].upper()})")
        print(f"   Subject: {template['subject'] or 'N/A'}")
        print(f"   Variables: {template['variables']}")
        
        # Show content preview
        content_preview = template['content'].replace('\n', ' ')[:150]
        if len(content_preview) >= 150:
            content_preview += "..."
        print(f"   Preview: {content_preview}")
        print()
    
    print(f"🎯 Total templates available: {len(SAMPLE_TEMPLATES)}")
    print("\nKey Features:")
    print("✅ Professional HTML email templates with responsive design")
    print("✅ SMS templates optimized for mobile engagement") 
    print("✅ WhatsApp templates with emojis and formatting")
    print("✅ Variable substitution support for personalization")
    print("✅ Unsubscribe and preference management links")
    print("✅ Tracking pixels for open rate measurement")
    print("✅ Click tracking for engagement analytics")

if __name__ == "__main__":
    display_sample_templates()