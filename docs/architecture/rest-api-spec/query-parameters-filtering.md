# Query Parameters & Filtering

## Standard Query Parameters

**Pagination**:
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 20, max: 100) - Items per page

**Sorting**:  
- `sortBy` (string) - Field to sort by
- `sortOrder` (string: "asc"|"desc", default: "desc") - Sort direction

**Filtering**:
- `status` (string) - Filter by status
- `type` (string) - Filter by type/category  
- `search` (string) - Text search across relevant fields
- `dateFrom` (ISO date) - Filter from date
- `dateTo` (ISO date) - Filter to date

## Example Query String
```http
GET /api/documents?page=2&limit=50&sortBy=createdAt&sortOrder=desc&status=completed&search=genesis&dateFrom=2025-01-01T00:00:00Z
```
