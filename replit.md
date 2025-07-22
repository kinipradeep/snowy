# Contact Manager Application

## Overview

This is a comprehensive multi-tenant Flask-based contact management system built with PostgreSQL. The application features organization-based collaboration where teams can share contact databases, with role-based permissions, user authentication, and advanced contact/template management capabilities. Users automatically get their own organization when registering and can create additional organizations or join existing ones through email invitations.

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
- **Database**: PostgreSQL with connection pooling and environment-based configuration
- **ORM**: SQLAlchemy with declarative base model
- **Schema**: Multi-tenant system with organization-based data isolation
- **Relationships**: Complex many-to-many relationships between users and organizations with role-based permissions
- **Data Scope**: All contacts, groups, and templates are scoped to organizations rather than individual users

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
1. **User Model**: Authentication and user profile data with admin flags
2. **Organization Model**: Multi-tenant organization structure with ownership
3. **UserRole Model**: Role-based permissions (owner, admin, member, viewer) linking users to organizations
4. **Contact Model**: Contact information scoped to organizations with group relationships
5. **Group Model**: Contact organization and categorization within organizations
6. **Template Model**: Message templates for various channels scoped to organizations
7. **OrganizationInvitation Model**: Email-based team invitation system with token authentication
8. **PasswordResetToken Model**: Secure password reset functionality

### Utility Functions (`utils.py`)
- Authentication decorators (`@login_required`, `@admin_required`)
- Session management helpers
- Security token generation
- User context helpers

## Data Flow

1. **Authentication Flow**: Session-based authentication with secure password hashing and automatic organization creation for new users
2. **Organization Management**: Multi-tenant architecture with role-based permissions and team collaboration
3. **Contact Management**: Organization-scoped CRUD operations with group relationships and team sharing
4. **Template System**: Multi-channel template creation with content validation scoped to organizations
5. **Invitation System**: Email-based team invitations with token authentication and role assignment
6. **Admin Functions**: Role-based access control for user management within organizations

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

## Recent Changes

**January 2025**: 
- Implemented comprehensive multi-tenant architecture with organizations and role-based permissions
- Added team collaboration features with email invitations
- Converted from user-based to organization-based data scoping
- Fixed database relationship conflicts and recreated schema with correct structure
- Added GitHub sync preparation with .gitignore and comprehensive README.md

The application follows Flask best practices with proper separation of concerns, secure authentication, and a scalable multi-tenant architecture suitable for team-based contact management scenarios.