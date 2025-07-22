# Contact Manager Application

## Overview

This is a Flask-based contact management system that allows users to organize contacts, create message templates, and manage user accounts. The application features a modern web interface with authentication, group-based contact organization, and template management for various communication channels.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5 with dark theme
- **Icons**: Feather Icons
- **JavaScript**: Vanilla JavaScript for interactivity
- **CSS**: Custom CSS for enhanced styling

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy extension
- **Authentication**: Session-based authentication with werkzeug password hashing
- **Application Structure**: Blueprint-based modular architecture
- **Form Validation**: Custom form validation classes

### Database Architecture
- **ORM**: SQLAlchemy with declarative base model
- **Schema**: Multi-user system with user isolation
- **Relationships**: One-to-many relationships between users and their data

## Key Components

### Core Modules
1. **Authentication System** (`auth.py`)
   - User login/logout
   - User registration
   - Password reset functionality
   - Session management

2. **Contact Management** (`contacts.py`)
   - CRUD operations for contacts
   - Search and filtering capabilities
   - Group-based organization
   - Pagination support

3. **Group Management** (`groups.py`)
   - Contact group creation and management
   - Group-based contact filtering
   - Contact counting per group

4. **Template Management** (`templates_mgmt.py`)
   - Multi-channel message templates (Email, SMS, WhatsApp, RCS)
   - Template duplication
   - Type-based filtering

5. **User Administration** (`users.py`)
   - Admin-only user management
   - User activation/deactivation
   - Role-based access control

### Data Models
1. **User Model**: Authentication and user profile data
2. **Contact Model**: Contact information with group relationships
3. **Group Model**: Contact organization and categorization
4. **Template Model**: Message templates for various channels
5. **PasswordResetToken Model**: Secure password reset functionality

### Utility Functions (`utils.py`)
- Authentication decorators (`@login_required`, `@admin_required`)
- Session management helpers
- Security token generation
- User context helpers

## Data Flow

1. **Authentication Flow**: Session-based authentication with secure password hashing
2. **Contact Management**: User-scoped CRUD operations with group relationships
3. **Template System**: Multi-channel template creation with content validation
4. **Admin Functions**: Role-based access control for user management

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Werkzeug**: Password hashing and utilities
- **Standard Library**: logging, os, datetime, secrets

### Frontend Dependencies
- **Bootstrap 5**: UI framework (CDN)
- **Feather Icons**: Icon library (CDN)
- **Custom CSS/JS**: Application-specific styling and behavior

### Database
- **SQLAlchemy**: Database abstraction layer
- **Environment-based configuration**: Database URL from environment variables
- **Connection pooling**: Configured for production use

## Deployment Strategy

### Environment Configuration
- **Database URL**: Environment variable `DATABASE_URL`
- **Session Secret**: Environment variable `SESSION_SECRET`
- **Debug Mode**: Configurable for development/production

### Production Considerations
- **Proxy Support**: ProxyFix middleware for reverse proxy deployments
- **Database Connection Pooling**: Configured with pool recycling and pre-ping
- **Session Management**: Permanent sessions with secure configuration
- **Error Handling**: Custom error pages for 404 and 500 errors

### File Structure
- **Templates**: Organized by feature (auth, contacts, groups, templates, users)
- **Static Assets**: CSS and JavaScript files for frontend functionality
- **Modular Design**: Blueprint-based architecture for maintainability

The application follows Flask best practices with proper separation of concerns, secure authentication, and a scalable architecture suitable for multi-user contact management scenarios.