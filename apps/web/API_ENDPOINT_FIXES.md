# API Endpoint Fixes for Theo Frontend Services

## Current vs Actual Backend Endpoints

### Authentication Endpoints ✅ CORRECT
- Current: `/api/login` → Backend: `/api/login` ✅
- Current: `/api/register` → Backend: `/api/register` ✅

### Document Endpoints - NEEDS UPDATES
- Current: `/documents/upload` → Backend: `/api/admin/upload` ❌
- Current: `/documents` → Backend: `/api/admin/documents` ❌  
- Current: `/documents/{id}` → Backend: `/api/admin/documents/{id}` ❌

### Chat Endpoints ✅ CORRECT
- Current: `/api/chat` → Backend: `/api/chat` ✅

### Admin Endpoints ✅ CORRECT  
- Current: `/api/admin/dashboard/metrics` → Backend: `/api/admin/dashboard/metrics` ✅
- Current: `/api/admin/users` → Backend: `/api/admin/users` ✅

### SSE Endpoints ✅ CORRECT
- Current: `/api/jobs/{jobId}/events` → Backend: `/api/jobs/{job_id}/events` ✅

### Export Endpoints - NEEDS UPDATES
- Current: `/api/export` → Backend: `/api/export/pdf` ❌

## Required Changes in api.ts

1. Update document upload endpoint path
2. Update document management endpoint paths  
3. Update export endpoint path
4. Ensure proper authentication headers for admin endpoints