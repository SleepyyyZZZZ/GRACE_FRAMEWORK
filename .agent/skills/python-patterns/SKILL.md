---
name: python-patterns
description: |
  Pythonic idioms, PEP 8 standards, type hints, async patterns, Repository/Service Layer patterns,
  DI, custom exceptions hierarchy, and best practices for FastAPI and Python backend development.
user-invocable: true
---

# Python Development Patterns

Idiomatic Python patterns for robust, efficient backend applications.

## When to Activate

- Writing new Python code
- Reviewing Python code
- Refactoring existing Python code
- Designing FastAPI services and repositories

---

## Core Rules

### Type Annotations Everywhere

```python
from __future__ import annotations

# All function signatures must have type hints
async def get_user(user_id: int, db: AsyncSession) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### Modern Type Hints (Python 3.10+)

```python
# Use built-in types and | union
def process(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

def get_user(user_id: int) -> User | None:
    ...
```

### Immutability

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    db_url: str
    debug: bool = False

from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float
```

---

## Architecture Patterns

### Repository Pattern

```python
class OrderRepository:
    """Abstracts all database operations for orders.

    NEVER contains business logic.
    NEVER imports Service.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, order_id: UUID) -> Order | None:
        """Side effects: NONE"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, order: Order) -> Order:
        """Side effects: NONE (DB write is expected)"""
        self.db.add(order)
        await self.db.flush()
        return order

    async def find_by_user(self, user_id: UUID) -> list[Order]:
        """Side effects: NONE"""
        stmt = select(Order).where(Order.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

### Service Layer Pattern

```python
class OrderService:
    """Business logic for order domain. All public methods are Sinks."""

    def __init__(self, repo: OrderRepository, inventory: InventoryService):
        # Dependencies via DI — never create inside
        self.repo = repo
        self.inventory = inventory

    async def create(self, data: OrderCreate, user_id: int) -> Order:
        """
        Creates a validated order with inventory check.

        Args:
            data: Validated order creation data
            user_id: ID of the user creating the order

        Returns:
            Created Order instance

        Raises:
            InsufficientInventoryError: if items not available
            ValidationError: if data is invalid

        Side effects: NONE
        """
        await self.inventory.check_availability(data.items)
        order = Order(user_id=user_id, **data.model_dump())
        return await self.repo.save(order)
```

### Dependency Injection in FastAPI

```python
# Dependencies factory
def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    repo = OrderRepository(db)
    inventory = InventoryService(InventoryRepository(db))
    return OrderService(repo, inventory)

# Usage in router
@router.post("/orders", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    return await service.create(data, current_user.id)
```

---

## Error Handling

```python
# Specific exceptions, never bare except
try:
    result = await db.execute(stmt)
except IntegrityError as e:
    raise HTTPException(status_code=409, detail="Already exists") from e
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database error") from e

# Custom exception hierarchy
class AppError(Exception):
    """Base application error."""

class DomainError(AppError):
    """Business logic errors."""

class NotFoundError(DomainError):
    """Resource not found."""

class ValidationError(DomainError):
    """Input validation failed."""

class OrderError(DomainError):
    """Order-related errors."""

class InsufficientInventoryError(OrderError):
    """Not enough inventory."""
```

Custom exceptions live in `shared/exceptions.py` and inherit hierarchically.

---

## Async Patterns (FastAPI)

```python
# ALWAYS async — never block the event loop
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Parallel execution when possible
results = await asyncio.gather(
    fetch_users(db),
    fetch_orders(db),
    fetch_stats(db),
)

# NEVER do this in async context
import requests  # blocks event loop!
data = requests.get(url)  # BAD
```

---

## Context Managers

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## Comprehensions and Generators

```python
# List comprehension for simple transforms
active_users = [u for u in users if u.is_active]

# Generator for large datasets (lazy evaluation)
def read_large_file(path: str) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# Use sum() with generator (no intermediate list)
total = sum(x * x for x in range(1_000_000))
```

---

## Anti-Patterns to Avoid

```python
# BAD: Mutable default arguments
def append_to(item, items=[]):  # Shared mutable default!
    items.append(item)
    return items

# GOOD: Use None
def append_to(item, items: list | None = None):
    if items is None:
        items = []
    items.append(item)
    return items

# BAD: Bare except
try:
    risky()
except:
    pass

# BAD: from module import *
from os.path import *

# BAD: type() instead of isinstance
if type(obj) == list:  # use isinstance(obj, list)
```

---

## Tooling

```bash
# Formatting
black .
isort .

# Linting
ruff check .

# Type checking
mypy .
# or
pyright .

# Testing
pytest --cov=app --cov-report=term-missing

# Security
bandit -r .
pip-audit
```
