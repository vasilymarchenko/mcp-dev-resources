"""
FastAPI Endpoint Template with Validation and Error Handling

This template demonstrates a complete FastAPI endpoint implementation including:
- Pydantic models for request/response validation
- Comprehensive error handling
- Authentication and authorization
- Documentation with OpenAPI
- Logging and monitoring
- Dependency injection
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
import uuid
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class StatusEnum(str, Enum):
    """Status enumeration for items"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class ItemBase(BaseModel):
    """Base item model with common fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    status: StatusEnum = Field(StatusEnum.ACTIVE, description="Item status")
    tags: List[str] = Field(default_factory=list, description="Item tags")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        # Remove duplicates and empty tags
        return list(set(tag.strip() for tag in v if tag.strip()))

class ItemCreate(ItemBase):
    """Model for creating new items"""
    pass

class ItemUpdate(BaseModel):
    """Model for updating existing items"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[StatusEnum] = None
    tags: Optional[List[str]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip() if v else v

class ItemResponse(ItemBase):
    """Model for item responses"""
    id: str = Field(..., description="Unique item identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sample Item",
                "description": "This is a sample item",
                "status": "active",
                "tags": ["sample", "demo"],
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }

class PaginatedResponse(BaseModel):
    """Generic paginated response model"""
    items: List[ItemResponse]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")

class ErrorResponse(BaseModel):
    """Standard error response model"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")

# Custom Exceptions
class ItemNotFoundError(Exception):
    """Raised when an item is not found"""
    def __init__(self, item_id: str):
        self.item_id = item_id
        super().__init__(f"Item with id {item_id} not found")

class DuplicateItemError(Exception):
    """Raised when trying to create a duplicate item"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Item with name '{name}' already exists")

class ValidationError(Exception):
    """Raised for business logic validation errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Validate JWT token and return current user information
    In a real application, you would validate the JWT token here
    """
    token = credentials.credentials
    
    # Mock token validation - replace with actual JWT validation
    if not token or token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mock user data - replace with actual user lookup
    return {
        "user_id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"]
    }

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role for access"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Database Dependencies (Mock)
class ItemRepository:
    """Mock repository for demonstration"""
    
    def __init__(self):
        self._items: Dict[str, Dict[str, Any]] = {}
    
    async def create(self, item_data: ItemCreate) -> Dict[str, Any]:
        # Check for duplicates
        existing = [item for item in self._items.values() 
                   if item["name"].lower() == item_data.name.lower()]
        if existing:
            raise DuplicateItemError(item_data.name)
        
        item_id = str(uuid.uuid4())
        now = datetime.utcnow()
        item = {
            "id": item_id,
            "created_at": now,
            "updated_at": now,
            **item_data.dict()
        }
        self._items[item_id] = item
        return item
    
    async def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self._items.get(item_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        items = list(self._items.values())
        return items[skip:skip + limit]
    
    async def update(self, item_id: str, updates: ItemUpdate) -> Dict[str, Any]:
        item = self._items.get(item_id)
        if not item:
            raise ItemNotFoundError(item_id)
        
        update_data = updates.dict(exclude_unset=True)
        item.update(update_data)
        item["updated_at"] = datetime.utcnow()
        return item
    
    async def delete(self, item_id: str) -> bool:
        if item_id not in self._items:
            raise ItemNotFoundError(item_id)
        del self._items[item_id]
        return True
    
    async def count(self) -> int:
        return len(self._items)

# Dependency injection
item_repository = ItemRepository()

async def get_item_repository() -> ItemRepository:
    """Dependency injection for item repository"""
    return item_repository

# Middleware for request tracking
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests for tracking"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"completed in {process_time:.3f}s with status {response.status_code}"
    )
    
    return response

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting up application...")
    # Initialize resources here (database connections, etc.)
    
    yield
    
    logger.info("Shutting down application...")
    # Cleanup resources here

# FastAPI Application
app = FastAPI(
    title="Item Management API",
    description="A comprehensive REST API for managing items with authentication and validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"]
)

app.middleware("http")(add_request_id_middleware)

# Exception Handlers
@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Item with id {exc.item_id} not found"
    )

@app.exception_handler(DuplicateItemError)
async def duplicate_item_handler(request: Request, exc: DuplicateItemError):
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Item with name '{exc.name}' already exists"
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc)
    )

# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

# API Endpoints
@app.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
    description="Create a new item with the provided data",
    responses={
        201: {"description": "Item created successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"},
        409: {"description": "Item already exists"}
    },
    tags=["Items"]
)
async def create_item(
    item: ItemCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ItemRepository = Depends(get_item_repository)
) -> ItemResponse:
    """
    Create a new item.
    
    - **name**: Item name (required, 1-100 characters)
    - **description**: Item description (optional, max 500 characters)
    - **status**: Item status (active, inactive, pending)
    - **tags**: List of tags associated with the item
    """
    try:
        logger.info(f"User {current_user['user_id']} creating item: {item.name}")
        created_item = await repository.create(item)
        return ItemResponse(**created_item)
    except DuplicateItemError as e:
        logger.warning(f"Attempt to create duplicate item: {e.name}")
        raise
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Get item by ID",
    description="Retrieve a specific item by its unique identifier",
    responses={
        200: {"description": "Item retrieved successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Item not found"}
    },
    tags=["Items"]
)
async def get_item(
    item_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ItemRepository = Depends(get_item_repository)
) -> ItemResponse:
    """
    Get a specific item by ID.
    
    - **item_id**: Unique identifier of the item to retrieve
    """
    logger.info(f"User {current_user['user_id']} retrieving item: {item_id}")
    
    item = await repository.get(item_id)
    if not item:
        raise ItemNotFoundError(item_id)
    
    return ItemResponse(**item)

@app.get(
    "/items",
    response_model=PaginatedResponse,
    summary="List items",
    description="Get a paginated list of all items",
    responses={
        200: {"description": "Items retrieved successfully"},
        401: {"description": "Authentication required"}
    },
    tags=["Items"]
)
async def list_items(
    page: int = Field(1, ge=1, description="Page number"),
    size: int = Field(10, ge=1, le=100, description="Page size"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ItemRepository = Depends(get_item_repository)
) -> PaginatedResponse:
    """
    Get a paginated list of items.
    
    - **page**: Page number (starts from 1)
    - **size**: Number of items per page (1-100)
    """
    logger.info(f"User {current_user['user_id']} listing items: page {page}, size {size}")
    
    skip = (page - 1) * size
    items = await repository.get_all(skip=skip, limit=size)
    total = await repository.count()
    
    has_next = (page * size) < total
    
    return PaginatedResponse(
        items=[ItemResponse(**item) for item in items],
        total=total,
        page=page,
        size=size,
        has_next=has_next
    )

@app.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Update item",
    description="Update an existing item with new data",
    responses={
        200: {"description": "Item updated successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"},
        404: {"description": "Item not found"}
    },
    tags=["Items"]
)
async def update_item(
    item_id: str,
    updates: ItemUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ItemRepository = Depends(get_item_repository)
) -> ItemResponse:
    """
    Update an existing item.
    
    - **item_id**: Unique identifier of the item to update
    - Only provided fields will be updated
    """
    logger.info(f"User {current_user['user_id']} updating item: {item_id}")
    
    try:
        updated_item = await repository.update(item_id, updates)
        return ItemResponse(**updated_item)
    except ItemNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    description="Delete an existing item",
    responses={
        204: {"description": "Item deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        404: {"description": "Item not found"}
    },
    tags=["Items"]
)
async def delete_item(
    item_id: str,
    admin_user: Dict[str, Any] = Depends(require_admin),
    repository: ItemRepository = Depends(get_item_repository)
):
    """
    Delete an item (Admin only).
    
    - **item_id**: Unique identifier of the item to delete
    - Requires admin privileges
    """
    logger.info(f"Admin {admin_user['user_id']} deleting item: {item_id}")
    
    try:
        await repository.delete(item_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ItemNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

# Additional utility endpoints
@app.get("/items/search", response_model=List[ItemResponse], tags=["Items"])
async def search_items(
    q: str = Field(..., min_length=1, description="Search query"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ItemRepository = Depends(get_item_repository)
) -> List[ItemResponse]:
    """Search items by name or description"""
    logger.info(f"User {current_user['user_id']} searching items: '{q}'")
    
    all_items = await repository.get_all()
    matching_items = [
        item for item in all_items
        if q.lower() in item["name"].lower() or
           (item.get("description") and q.lower() in item["description"].lower())
    ]
    
    return [ItemResponse(**item) for item in matching_items]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
