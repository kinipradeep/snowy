# Cool Blue - Multi-Tenant Communication Platform

A sophisticated multi-tenant Flask-based communication management system built with PostgreSQL, featuring organization-based collaboration, role-based permissions, and comprehensive multi-channel messaging capabilities.

## 🚀 Features

### Core Functionality
- **Multi-Tenant Architecture** - Organization-based data isolation with team collaboration
- **Role-Based Permissions** - Owner, Admin, Member, Viewer roles with granular access control
- **Contact Management** - Comprehensive contact profiles with 35+ customizable fields
- **Group Organization** - Contact categorization and bulk operations
- **Template System** - Multi-channel message templates (SMS, Email, WhatsApp)
- **CSV Import** - Bulk contact upload with field mapping

### Messaging Capabilities
- **SMS Integration** - Twilio, TextLocal, MSG91, Clickatell, Custom HTTP APIs
- **Email Services** - Custom SMTP servers, Amazon SES with full authentication
- **WhatsApp Business API** - Template messages and direct messaging
- **Multi-Provider Fallback** - Automatic failover for reliable delivery
- **Test Functions** - Real-time configuration testing for all providers

### Team Collaboration
- **Email Invitations** - Token-based team invites with role assignment
- **Organization Settings** - Centralized messaging provider configuration
- **User Management** - Admin controls for team member management
- **Secure Authentication** - Session-based auth with password reset

## 🏗️ Architecture

### Backend Stack
- **Framework**: Flask with Blueprint architecture
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Session-based with werkzeug password hashing
- **Messaging**: Multi-provider API clients with unified interface

### Frontend Stack
- **UI Framework**: Bootstrap 5 with professional dark theme
- **Icons**: Feather Icons for consistent interface
- **JavaScript**: Vanilla JS for interactive functionality
- **Responsive Design**: Mobile-first approach

### Database Schema
```
Organizations (Multi-tenant containers)
├── Users (Role-based team members)
├── Contacts (35+ fields, group relationships)
├── Groups (Contact categorization)
├── Templates (Multi-channel messaging)
├── OrganizationConfig (Messaging provider settings)
└── Invitations (Team invite system)
```

## 🔧 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Environment variables for database and session management

### Setup
1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd contact-manager
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/database"
   export SESSION_SECRET="your-secret-key"
   ```

4. **Database Setup**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Run Application**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

## 📱 Usage

### Getting Started
1. **Register Account** - Create your user account and automatic organization
2. **Configure Messaging** - Set up SMS, Email, WhatsApp providers in organization settings
3. **Import Contacts** - Upload CSV files or manually add contact information
4. **Create Templates** - Design message templates for different channels
5. **Send Messages** - Use templates to communicate with contact groups

### Role Permissions
- **Owner**: Full access, can delete organization and manage all settings
- **Admin**: Manage users, configure messaging, full contact/template access
- **Member**: Create/update contacts and templates, send messages (no delete)
- **Viewer**: Read-only access to contacts and templates

### Messaging Providers

#### SMS Providers
- **Twilio** - Global SMS delivery with premium reliability
- **TextLocal** - UK-focused SMS service with competitive rates
- **MSG91** - India-focused SMS with global reach
- **Clickatell** - Enterprise SMS with worldwide coverage
- **Custom HTTP** - Integrate any REST API SMS provider

#### Email Providers
- **Custom SMTP** - Use any SMTP server (Gmail, Outlook, custom)
- **Amazon SES** - Scalable email service with high deliverability

#### WhatsApp
- **WhatsApp Business API** - Official business messaging with templates

## 🔌 API Integration

### SMS Configuration
```python
# Example: Twilio setup
config.sms_provider = 'twilio'
config.sms_api_key = 'your-auth-token'
config.sms_username = 'account-sid'
config.sms_sender_id = '+1234567890'
```

### Email Configuration
```python
# Example: SMTP setup
config.email_provider = 'smtp'
config.smtp_host = 'smtp.gmail.com'
config.smtp_port = 587
config.smtp_username = 'your-email@gmail.com'
config.smtp_password = 'app-password'
config.smtp_use_tls = True
```

### WhatsApp Configuration
```python
# Example: WhatsApp Business API
config.whatsapp_api_url = 'https://graph.facebook.com/v17.0/phone-id/messages'
config.whatsapp_api_key = 'your-access-token'
config.whatsapp_phone_number = 'your-business-number'
```

## 🛠️ Development

### Project Structure
```
contact-manager/
├── app.py                 # Flask app initialization
├── main.py               # Application entry point
├── models.py             # Database models
├── messaging.py          # Messaging service coordination
├── messaging_clients.py  # API client implementations
├── auth.py              # Authentication routes
├── contacts.py          # Contact management
├── groups.py            # Contact groups
├── templates_mgmt.py    # Template management
├── organizations.py     # Organization & team management
├── users.py             # User administration
├── utils.py             # Helper functions
├── static/              # CSS, JavaScript, assets
└── templates/           # Jinja2 HTML templates
```

### Key Components
- **Multi-Tenant Data Isolation** - All data scoped to organizations
- **Role-Based Access Control** - Granular permissions system
- **Unified Messaging Client** - Single interface for all providers
- **Automatic Fallback** - Provider failover for reliability
- **Comprehensive Error Handling** - Detailed logging and user feedback

## 🔐 Security Features

- **Session-based Authentication** - Secure login without JWT complexity
- **Password Hashing** - Werkzeug secure password storage
- **CSRF Protection** - Form-based security tokens
- **SQL Injection Prevention** - SQLAlchemy ORM parameterized queries
- **Access Control** - Role-based data access restrictions

## 📊 Monitoring & Testing

### Built-in Testing
- **Provider Test Functions** - Real-time configuration validation
- **Message Delivery Testing** - Send test messages to verify setup
- **Error Reporting** - Comprehensive failure diagnostics

### Logging
- **Application Logs** - Detailed operation tracking
- **Message Delivery Logs** - Success/failure tracking
- **Security Logs** - Authentication and access monitoring

## 🚢 Deployment

### Production Considerations
- **Environment Variables** - Secure configuration management
- **Database Connection Pooling** - Optimized for high concurrency
- **Reverse Proxy Support** - ProxyFix middleware included
- **Session Management** - Permanent sessions for user convenience

### Scaling
- **Multi-Tenant Design** - Horizontal scaling ready
- **Database Optimization** - Indexed queries and efficient relationships
- **Provider Load Balancing** - Multiple messaging providers for redundancy

## 📈 Roadmap

- [ ] **Analytics Dashboard** - Message delivery statistics and insights
- [ ] **Webhook Integration** - Real-time delivery status updates
- [ ] **Advanced Templates** - Rich text and HTML email templates
- [ ] **Contact Segmentation** - Advanced filtering and targeting
- [ ] **API Endpoints** - RESTful API for external integrations
- [ ] **Mobile App** - React Native companion application

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Review documentation in the `replit.md` file
- Check the built-in test functions for configuration validation

---

**Built with ❤️ using Flask, PostgreSQL, and modern web technologies**