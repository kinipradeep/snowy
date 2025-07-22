# Contributing to Contact Manager

Thank you for your interest in contributing to the Contact Manager project! We welcome contributions from the community to help make this multi-tenant communication platform even better.

## 🚀 Getting Started

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/contact-manager.git
   cd contact-manager
   ```

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-flask pytest-cov  # For testing
   ```

4. **Configure Environment**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/contact_manager_dev"
   export SESSION_SECRET="your-development-secret-key"
   export FLASK_ENV="development"
   ```

5. **Initialize Database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

6. **Run Development Server**
   ```bash
   python main.py
   ```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings for all classes and functions
- Keep functions focused and under 50 lines when possible

### Project Structure
- **Models** (`models.py`): Database schema and relationships
- **Routes** (`*.py` blueprint files): HTTP endpoints and business logic
- **Templates** (`templates/`): Jinja2 HTML templates organized by feature
- **Static Assets** (`static/`): CSS, JavaScript, and other assets
- **Messaging** (`messaging.py`, `messaging_clients.py`): Communication providers

### Database Changes
- Always create migrations for schema changes
- Test migrations on sample data before submitting
- Document any breaking changes in PR description

### Multi-Tenant Considerations
- All data operations must respect organization boundaries
- Test role-based permissions thoroughly
- Ensure proper data isolation between organizations

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_contacts.py

# Run tests with verbose output
python -m pytest -v
```

### Test Structure
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows

### Required Tests
When contributing new features, please include:
- Unit tests for all new functions
- Integration tests for API endpoints
- Role-based permission tests
- Multi-tenant isolation tests

## 📝 Pull Request Process

### Before Submitting
1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write Tests**
   - Add tests for new functionality
   - Ensure existing tests pass
   - Aim for >80% code coverage

3. **Test Messaging Providers**
   - Test with at least one SMS provider
   - Test email functionality
   - Verify error handling

4. **Update Documentation**
   - Update relevant docstrings
   - Add configuration examples
   - Update README if needed

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New functionality includes tests
- [ ] Documentation updated where necessary
- [ ] Multi-tenant isolation maintained
- [ ] Role-based permissions respected
- [ ] No sensitive data in commits

### PR Template
Please include in your PR description:
- **What**: Brief description of changes
- **Why**: Reasoning for the changes
- **How**: Implementation approach
- **Testing**: How you tested the changes
- **Breaking Changes**: Any API or database changes

## 🔧 Areas for Contribution

### High Priority
- **Analytics Dashboard** - Message delivery statistics
- **Webhook Integration** - Real-time status updates
- **Advanced Template Editor** - Rich text and HTML templates
- **Contact Segmentation** - Advanced filtering capabilities
- **API Documentation** - OpenAPI/Swagger documentation

### Medium Priority
- **Mobile Responsive** - Enhanced mobile experience
- **Bulk Operations** - Mass contact operations
- **Export Functionality** - Contact and message export
- **Audit Logs** - User action tracking
- **Performance Optimization** - Query optimization

### Provider Integration
- **New SMS Providers** - Additional SMS gateways
- **Email Templates** - Pre-built email templates
- **WhatsApp Templates** - Business message templates
- **Social Media Integration** - LinkedIn, Twitter messaging

## 🐛 Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable
- Role and organization context

## 💡 Feature Requests

For new features, please provide:
- Use case description
- User type affected (Owner, Admin, Member, Viewer)
- Messaging channel relevance
- Implementation suggestions
- Alternative solutions considered

## 🔐 Security Considerations

### Reporting Security Issues
- **DO NOT** open public issues for security vulnerabilities
- Email security concerns to: security@example.com
- Include detailed description and reproduction steps

### Security Guidelines
- Validate all user inputs
- Use parameterized database queries
- Implement proper authentication checks
- Respect role-based permissions
- Encrypt sensitive configuration data

## 📞 Communication

### Getting Help
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Code Review**: Comments on pull requests

### Community Guidelines
- Be respectful and constructive
- Help others learn and grow
- Focus on the code, not the person
- Celebrate contributions of all sizes

## 🎯 Development Priorities

### Current Focus Areas
1. **Messaging Reliability** - Error handling and retry mechanisms
2. **User Experience** - Interface improvements and accessibility
3. **Performance** - Database optimization and caching
4. **Documentation** - API documentation and user guides
5. **Testing** - Increased test coverage and automated testing

### Future Roadmap
- **Mobile Application** - React Native companion app
- **Advanced Analytics** - Delivery insights and performance metrics
- **Integration Platform** - Third-party service connections
- **AI Features** - Smart contact segmentation and message optimization

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Contact Manager! Your efforts help make communication management better for everyone. 🚀