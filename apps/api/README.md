# Theo API

FastAPI backend application for the Theo AI-powered document management and chat platform.

## Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Option 1: Using the startup script
```bash
./start.sh
```

### Option 2: Direct command
```bash
source venv/bin/activate
python main.py
```

### Option 3: Using Uvicorn directly
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## API Endpoints

### Root
- **URL:** `GET /`
- **Description:** API welcome message with links
- **Response:** 
  ```json
  {
    "message": "Welcome to Theo API",
    "version": "1.0.0", 
    "docs": "/docs",
    "health": "/health"
  }
  ```

### Health Check
- **URL:** `GET /health`
- **Description:** Verify server is running correctly
- **Response:** `{"status": "ok"}`
- **Example:**
  ```bash
  curl http://localhost:8001/health
  ```

## Development

The server runs on `http://localhost:8001` by default with auto-reload enabled for development.

Access the interactive API documentation at:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Testing

### Automated Testing
Run the included test script to verify all endpoints:

```bash
source venv/bin/activate
python test_api.py
```

### Manual Testing
Test individual endpoints:

```bash
# Test root endpoint
curl http://localhost:8001/

# Test health endpoint  
curl http://localhost:8001/health

# Check API documentation
open http://localhost:8001/docs
```