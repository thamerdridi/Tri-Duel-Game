# HTTPS & Certificate Validation – Auth Service

All authentication endpoints are exposed exclusively via HTTPS
when accessed through the API Gateway.

## Security Guarantees
- TLS encryption protects credentials in transit
- JWT tokens are never transmitted over plain HTTP
- Gateway enforces HTTPS redirection

## Certificate Validation
- Client must verify gateway certificate chain
- Self-signed certificates are allowed in development
- Production requires CA-signed certificates

## Impact
- Prevents MITM attacks
- Protects login credentials
- Ensures token confidentiality
