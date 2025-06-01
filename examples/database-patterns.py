"""
Database Access Patterns and ORM Examples

This module demonstrates common database access patterns, repository pattern implementation,
connection pooling strategies, and migration approaches for Python applications.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
import asyncpg
from databases import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy Models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("User", back_populates="posts")

# Data Transfer Objects
@dataclass
class UserDTO:
    id: Optional[int]
    username: str
    email: str
    created_at: Optional[datetime] = None

@dataclass
class PostDTO:
    id: Optional[int]
    title: str
    content: str
    author_id: int
    created_at: Optional[datetime] = None

# Generic Repository Pattern
T = TypeVar('T')

class Repository(ABC, Generic[T]):
    """Abstract base repository for common database operations"""
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Retrieve entity by ID"""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Retrieve all entities with pagination"""
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity"""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID"""
        pass

# SQLAlchemy Repository Implementation
class SQLAlchemyUserRepository(Repository[User]):
    """SQLAlchemy implementation of User repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, entity_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == entity_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.query(User).filter(User.username == username).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        return self.session.query(User).offset(offset).limit(limit).all()
    
    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def update(self, user: User) -> User:
        self.session.merge(user)
        self.session.commit()
        return user
    
    def delete(self, entity_id: int) -> bool:
        user = self.get_by_id(entity_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False

class SQLAlchemyPostRepository(Repository[Post]):
    """SQLAlchemy implementation of Post repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, entity_id: int) -> Optional[Post]:
        return self.session.query(Post).filter(Post.id == entity_id).first()
    
    def get_by_author(self, author_id: int) -> List[Post]:
        return self.session.query(Post).filter(Post.author_id == author_id).all()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Post]:
        return self.session.query(Post).offset(offset).limit(limit).all()
    
    def create(self, post: Post) -> Post:
        self.session.add(post)
        self.session.commit()
        self.session.refresh(post)
        return post
    
    def update(self, post: Post) -> Post:
        self.session.merge(post)
        self.session.commit()
        return post
    
    def delete(self, entity_id: int) -> bool:
        post = self.get_by_id(entity_id)
        if post:
            self.session.delete(post)
            self.session.commit()
            return True
        return False

# Connection Pool Configuration
class DatabaseConnection:
    """Database connection manager with pooling"""
    
    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections every hour
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Drop all tables"""
        Base.metadata.drop_all(self.engine)

# Unit of Work Pattern
class UnitOfWork:
    """Unit of Work pattern for managing transactions"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
        self._session = None
        self._user_repo = None
        self._post_repo = None
    
    def __enter__(self):
        self._session = self.db_connection.SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._session.rollback()
        else:
            self._session.commit()
        self._session.close()
    
    @property
    def users(self) -> SQLAlchemyUserRepository:
        if self._user_repo is None:
            self._user_repo = SQLAlchemyUserRepository(self._session)
        return self._user_repo
    
    @property
    def posts(self) -> SQLAlchemyPostRepository:
        if self._post_repo is None:
            self._post_repo = SQLAlchemyPostRepository(self._session)
        return self._post_repo

# Async Database Pattern
class AsyncDatabaseService:
    """Async database service using asyncpg"""
    
    def __init__(self, database_url: str):
        self.database = Database(database_url)
    
    async def connect(self):
        await self.database.connect()
    
    async def disconnect(self):
        await self.database.disconnect()
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM users WHERE id = :user_id"
        return await self.database.fetch_one(query, {"user_id": user_id})
    
    async def create_user(self, username: str, email: str) -> int:
        query = """
        INSERT INTO users (username, email, created_at)
        VALUES (:username, :email, :created_at)
        RETURNING id
        """
        result = await self.database.fetch_one(query, {
            "username": username,
            "email": email,
            "created_at": datetime.utcnow()
        })
        return result["id"]
    
    async def get_posts_by_author(self, author_id: int) -> List[Dict[str, Any]]:
        query = """
        SELECT p.*, u.username as author_name
        FROM posts p
        JOIN users u ON p.author_id = u.id
        WHERE p.author_id = :author_id
        ORDER BY p.created_at DESC
        """
        return await self.database.fetch_all(query, {"author_id": author_id})

# Migration Strategies
class DatabaseMigration:
    """Database migration utilities"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def create_migration_table(self):
        """Create migration tracking table"""
        with self.db_connection.get_session() as session:
            session.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY,
                    version VARCHAR(50) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def apply_migration(self, version: str, sql_script: str):
        """Apply a database migration"""
        with self.db_connection.get_session() as session:
            # Check if migration already applied
            result = session.execute(
                "SELECT COUNT(*) FROM migrations WHERE version = :version",
                {"version": version}
            ).scalar()
            
            if result > 0:
                logger.info(f"Migration {version} already applied")
                return
            
            # Apply migration
            session.execute(sql_script)
            session.execute(
                "INSERT INTO migrations (version) VALUES (:version)",
                {"version": version}
            )
            logger.info(f"Applied migration {version}")

# Service Layer Example
class UserService:
    """Business logic layer for user operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def create_user_with_posts(self, user_data: UserDTO, posts_data: List[PostDTO]) -> UserDTO:
        """Create user with initial posts in a transaction"""
        with UnitOfWork(self.db_connection) as uow:
            # Create user
            user = User(username=user_data.username, email=user_data.email)
            created_user = uow.users.create(user)
            
            # Create posts
            for post_data in posts_data:
                post = Post(
                    title=post_data.title,
                    content=post_data.content,
                    author_id=created_user.id
                )
                uow.posts.create(post)
            
            return UserDTO(
                id=created_user.id,
                username=created_user.username,
                email=created_user.email,
                created_at=created_user.created_at
            )
    
    def get_user_with_posts(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user with all their posts"""
        with self.db_connection.get_session() as session:
            user_repo = SQLAlchemyUserRepository(session)
            post_repo = SQLAlchemyPostRepository(session)
            
            user = user_repo.get_by_id(user_id)
            if not user:
                return None
            
            posts = post_repo.get_by_author(user_id)
            
            return {
                "user": UserDTO(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    created_at=user.created_at
                ),
                "posts": [
                    PostDTO(
                        id=post.id,
                        title=post.title,
                        content=post.content,
                        author_id=post.author_id,
                        created_at=post.created_at
                    ) for post in posts
                ]
            }

# Example Usage
async def example_usage():
    """Example of how to use the database patterns"""
    
    # Synchronous SQLAlchemy example
    db_url = "sqlite:///example.db"
    db_connection = DatabaseConnection(db_url)
    db_connection.create_tables()
    
    # Create user service
    user_service = UserService(db_connection)
    
    # Create user with posts
    user_data = UserDTO(id=None, username="john_doe", email="john@example.com")
    posts_data = [
        PostDTO(id=None, title="First Post", content="Hello World!", author_id=0),
        PostDTO(id=None, title="Second Post", content="Database patterns", author_id=0)
    ]
    
    created_user = user_service.create_user_with_posts(user_data, posts_data)
    print(f"Created user: {created_user}")
    
    # Retrieve user with posts
    user_with_posts = user_service.get_user_with_posts(created_user.id)
    print(f"User with posts: {user_with_posts}")
    
    # Async database example
    async_db = AsyncDatabaseService("postgresql://user:pass@localhost/db")
    await async_db.connect()
    
    try:
        # Create user asynchronously
        user_id = await async_db.create_user("jane_doe", "jane@example.com")
        user = await async_db.get_user_by_id(user_id)
        print(f"Async created user: {user}")
    finally:
        await async_db.disconnect()

if __name__ == "__main__":
    asyncio.run(example_usage())
