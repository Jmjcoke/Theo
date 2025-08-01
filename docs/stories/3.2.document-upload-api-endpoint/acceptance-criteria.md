# Acceptance Criteria
1. A protected `/api/admin/upload` endpoint is created that requires 'admin' role authentication.
2. The endpoint accepts a file upload and associated metadata.
3. Upon receiving a file, the endpoint creates a new record in the `documents` table with a status of `queued`.
4. A new background job is dispatched to the Celery/Redis queue.
5. The endpoint immediately returns a success response with the ID of the new document record.
