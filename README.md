# Contact Manager Application

A comprehensive multi-tenant contact management system built with Flask and PostgreSQL, featuring organization-based collaboration, user authentication, and team management.

## Features

### Core Functionality
- **Multi-tenant Architecture**: Organizations with role-based permissions (owner, admin, member, viewer)
- **Contact Management**: Full CRUD operations with group organization
- **Team Collaboration**: Invite team members via email to share contact databases
- **Template System**: Multi-channel message templates (Email, SMS, WhatsApp, RCS)
- **User Management**: Admin controls for user activation/deactivation

### Authentication & Security
- Session-based authentication with secure password hashing
- Role-based access control within organizations
- Password reset functionality with secure tokens
- User isolation and data security

### User Interface
- Modern Bootstrap 5 dark theme interface
- Responsive design with Feather Icons
- Intuitive navigation and dashboard
- Real-time form validation

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, Jinja2 templates, Vanilla JavaScript
- **Authentication**: Werkzeug password hashing
- **Deployment**: Gunicorn WSGI server

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `SESSION_SECRET`: Secret key for session management
4. Run the application:
   ```bash
   python main.py
   ```

## Database Schema

The application uses a multi-tenant architecture where:
- Users can belong to multiple organizations
- Each organization has its own contact database
- Role-based permissions control access within organizations
- All data (contacts, groups, templates) is scoped to organizations

## Project Structure

```
├── app.py              # Flask application setup
├── main.py             # Application entry point
├── models.py           # Database models
├── auth.py             # Authentication routes
├── contacts.py         # Contact management
├── groups.py           # Group management
├── templates_mgmt.py   # Template management
├── users.py            # User administration
├── organizations.py    # Organization management
├── utils.py            # Utility functions
├── forms.py            # Form validation classes
├── templates/          # Jinja2 templates
└── static/             # CSS and JavaScript assets
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For support or questions, please create an issue in the GitHub repository.