# Acceptance Criteria
1. A public `/api/login` endpoint is created on the backend
2. The endpoint authenticates the user's credentials against the hashed password
3. The endpoint prevents login for any user whose status is not 'approved'
4. Upon successful login, the system generates and returns a JWT access token
5. The JWT payload contains the user's ID and role
