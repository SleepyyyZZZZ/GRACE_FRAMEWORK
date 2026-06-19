---
name: security-review
description: Security review checklist for FastAPI backends and mobile app APIs. Covers OWASP Top 10, secrets management, input validation, SQL injection, authentication, and pre-deployment checklist.
---

# Security Review

Ensures all code follows security best practices. Critical for APIs exposed to mobile apps.

## When to Activate

- Implementing authentication or authorization
- Handling user input or file uploads
- Creating new API endpoints
- Working with secrets or credentials
- Storing or transmitting sensitive data

## Security Checklist

### 1. Secrets Management

```python
# NEVER do this
API_KEY = "sk-proj-xxxxx"
DB_PASSWORD = "password123"

# ALWAYS do this
import os
API_KEY = os.environ["API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

if not API_KEY:
    raise RuntimeError("API_KEY not configured")
```

Verification:
- [ ] No hardcoded API keys, tokens, or passwords
- [ ] All secrets in environment variables
- [ ] `.env` in .gitignore
- [ ] No secrets in git history

### 2. Input Validation (FastAPI + Pydantic)

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)

@app.post("/users")
async def create_user(request: CreateUserRequest):
    # Input already validated by Pydantic
    return await user_service.create(request)
```

Verification:
- [ ] All user inputs validated with Pydantic models
- [ ] File uploads restricted (size, type, extension)
- [ ] No direct use of user input in queries
- [ ] Error messages don't leak sensitive info

### 3. SQL Injection Prevention

```python
# NEVER concatenate SQL
query = f"SELECT * FROM users WHERE email = '{user_email}'"  # DANGEROUS

# ALWAYS use parameterized queries
from sqlalchemy import select
stmt = select(User).where(User.email == user_email)  # Safe
result = await session.execute(stmt)

# Or with raw SQL
await session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": user_email})
```

### 4. Authentication & Authorization

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user = await get_user(payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user
```

### 5. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    ...

@app.get("/api/search")
@limiter.limit("10/minute")
async def search(request: Request, q: str):
    ...
```

### 6. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # NOT "*" in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 7. Error Handling (Don't Leak Info)

```python
# WRONG: Exposing internal details
@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse({"detail": str(exc), "traceback": traceback.format_exc()})

# CORRECT: Generic error messages
@app.exception_handler(Exception)
async def handler(request, exc):
    logger.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

### 8. PostgreSQL Row Level Security

```sql
ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_data_policy ON user_data
  FOR ALL
  USING (user_id = current_setting('app.current_user_id')::bigint);

-- Always index RLS columns
CREATE INDEX user_data_user_id_idx ON user_data (user_id);
```

## Pre-Deployment Checklist

- [ ] **Secrets**: No hardcoded secrets, all in env vars
- [ ] **Validation**: All inputs validated with Pydantic
- [ ] **SQL**: All queries parameterized (SQLAlchemy)
- [ ] **Auth**: JWT tokens properly validated
- [ ] **RBAC**: Role checks before sensitive operations
- [ ] **Rate Limiting**: Enabled on all endpoints
- [ ] **HTTPS**: Enforced in production
- [ ] **CORS**: Properly restricted (not `*`)
- [ ] **Errors**: No sensitive data in error responses
- [ ] **Logging**: No passwords/tokens in logs
- [ ] **Dependencies**: `pip-audit` clean
- [ ] **RLS**: Enabled on multi-tenant tables
- [ ] **File uploads**: Validated (size, type)
