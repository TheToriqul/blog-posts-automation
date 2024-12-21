# Security Policy

## Supported Versions

The following versions of Blog Post Automation are currently being supported with security updates:

| Version | Supported          |
|---------|-------------------|
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:               |

## Security Considerations

### API Tokens
- Never commit API tokens to the repository
- Store all sensitive credentials in environment variables or secure secret management systems
- Rotate API tokens periodically
- Use the minimum required permissions for API tokens

### Data Security
- No user credentials are stored in the application
- Post tracking data is stored locally and contains no sensitive information
- Published content follows platform-specific security guidelines

### Dependencies
- All dependencies are regularly updated
- Automated security scanning is implemented through GitHub Actions
- Known vulnerabilities are patched as soon as possible

## Reporting a Vulnerability

We take security vulnerabilities seriously. Please follow these steps to report a security issue:

1. **Do Not** create a public GitHub issue for security vulnerabilities

2. **Contact Information**
   - Email: toriqul.int@gmail.com
   - Subject line should start with: [SECURITY]
   - Alternative contact: Message via LinkedIn [@TheToriqul](https://www.linkedin.com/in/thetoriqul/)

3. **Include in Your Report**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

4. **Response Timeline**:
   - Initial response: Within 48 hours
   - Update on assessment: Within 5 business days
   - Fix implementation: Based on severity
     - Critical: Within 7 days
     - High: Within 14 days
     - Medium: Within 30 days
     - Low: Next release cycle

## Vulnerability Disclosure Process

1. **Receipt**: You will receive acknowledgment within 48 hours

2. **Assessment**: Our team will assess the vulnerability

3. **Communication**: We will maintain communication about:
   - Verification status
   - Fix development
   - Release timeline

4. **Resolution**:
   - Security patch release
   - Public disclosure (if applicable)
   - Credit to reporter (if desired)

## Best Practices for Users

1. **API Security**:
   - Use separate API tokens for development and production
   - Implement rate limiting in your deployment
   - Monitor API usage regularly

2. **Environment Setup**:
   - Use `.env` files for local development
   - Implement proper secret management in production
   - Keep Python and all dependencies updated

3. **Content Security**:
   - Validate all markdown content before publishing
   - Sanitize HTML output
   - Follow platform-specific content guidelines

4. **Deployment Security**:
   - Use HTTPS for all API communications
   - Implement proper access controls
   - Regular security audits of deployment environment

## Security Updates

Security updates are delivered through:
1. GitHub Security Advisories
2. Release Notes
3. Direct email notification for critical issues

## Responsible Disclosure

We follow responsible disclosure principles:
1. Prompt acknowledgment of reports
2. Regular updates on progress
3. Credit to security researchers (with permission)
4. Public disclosure after patch release

## Tools and Automation

We use the following security tools:
- GitHub's Dependabot for dependency scanning
- CodeQL for code analysis
- Regular automated security testing
- Automated vulnerability scanning

## Contributing to Security

We welcome security improvements:
1. Security-related pull requests
2. Documentation improvements
3. Security tool integration
4. Test case additions

## Contact

Security team contact information:
- Primary: toriqul.int@gmail.com
- Phone: +65 8936 7705, +8801765 939006
- GitHub: [@TheToriqul](https://github.com/TheToriqul)

Thank you for helping keep Blog Post Automation and its users safe!
