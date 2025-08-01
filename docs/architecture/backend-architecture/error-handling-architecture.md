# Error Handling Architecture

## Node-Level Error Handling

**Graceful Error Recovery**:
```python
class RobustNode(AsyncNode):
    """Node with comprehensive error handling"""
    
    async def exec(self, data):
        try:
            return await self.process_data(data)
        except ValidationError as e:
            # Recoverable validation errors
            return {"error": "validation_failed", "details": str(e)}
        except ExternalServiceError as e:
            # Retry external service calls
            return await self.retry_with_backoff(data, max_retries=3)
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in {self.__class__.__name__}: {e}")
            return {"error": "processing_failed", "recoverable": False}
```

## API-Level Error Handling

**Consistent Error Responses**:
```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Invalid input data",
            "details": exc.errors()
        }
    )

@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "error": "authentication_failed", 
            "message": "Invalid credentials"
        }
    )
```
