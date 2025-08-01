# Acceptance Criteria
1. Middleware is implemented in FastAPI that validates the JWT from the Authorization header
2. A protected test endpoint is created that is only accessible with a valid 'user' or 'admin' token
3. A protected admin endpoint is created that is only accessible with a valid 'admin' token
4. The middleware returns a 401 Unauthorized or 403 Forbidden error appropriately
