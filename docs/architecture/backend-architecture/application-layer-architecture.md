# Application Layer Architecture

## FastAPI Application Structure

**Core Application (`main.py`)**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pocketflow import FlowManager

app = FastAPI(title="Theo Theological AI Assistant")
