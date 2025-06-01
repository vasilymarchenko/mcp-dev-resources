# Performance Optimization

## Overview
This document provides comprehensive guidance on performance optimization techniques for modern applications. It covers profiling, optimization strategies, and best practices for building high-performance systems.

## Performance Fundamentals

### Key Metrics
- **Response Time**: Time to complete a single operation
- **Throughput**: Number of operations per unit time
- **Latency**: Delay before operation begins
- **Resource Utilization**: CPU, memory, I/O usage
- **Scalability**: Performance under increasing load

### Performance Goals
- **Sub-second response times** for user-facing operations
- **High throughput** for batch processing
- **Efficient resource utilization** (< 80% under normal load)
- **Graceful degradation** under stress
- **Predictable performance** across different loads

## Profiling & Measurement

### Python Profiling
```python
import cProfile
import pstats
from functools import wraps
import time

def profile_function(func):
    """Decorator to profile function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        profiler.disable()
        
        # Print stats
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        print(f"Function {func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

# Usage
@profile_function
def slow_function():
    # Your code here
    time.sleep(1)
    return "done"
```

### Memory Profiling
```python
import tracemalloc
from memory_profiler import profile

# Track memory usage
def track_memory():
    tracemalloc.start()
    
    # Your code here
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    
    tracemalloc.stop()

# Line-by-line memory profiling
@profile
def memory_intensive_function():
    # Each line's memory usage will be displayed
    big_list = [i for i in range(1000000)]
    big_dict = {i: i**2 for i in range(100000)}
    return len(big_list) + len(big_dict)
```

### Database Query Profiling
```python
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Log slow queries
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log queries taking > 100ms
        logger.warning(f"Slow query: {total:.3f}s - {statement[:100]}...")
```

## Algorithm & Data Structure Optimization

### Time Complexity Optimization
```python
# O(n²) - Inefficient
def find_duplicates_slow(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates

# O(n) - Efficient
def find_duplicates_fast(arr):
    seen = set()
    duplicates = set()
    for item in arr:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)
```

### Efficient Data Structures
```python
from collections import defaultdict, deque, Counter
import bisect

# Use appropriate data structures
class OptimizedDataStructures:
    def __init__(self):
        # For fast lookups
        self.lookup_set = set()
        
        # For counting
        self.counter = Counter()
        
        # For grouping
        self.groups = defaultdict(list)
        
        # For queue operations
        self.queue = deque()
        
        # For sorted operations
        self.sorted_list = []
    
    def add_item(self, item, category):
        # O(1) operations
        self.lookup_set.add(item)
        self.counter[item] += 1
        self.groups[category].append(item)
        
        # O(log n) for maintaining sorted order
        bisect.insort(self.sorted_list, item)
    
    def find_in_sorted(self, target):
        # O(log n) binary search
        index = bisect.bisect_left(self.sorted_list, target)
        if index < len(self.sorted_list) and self.sorted_list[index] == target:
            return index
        return -1
```

## Database Optimization

### Query Optimization
```python
# Inefficient - N+1 Query Problem
def get_users_with_orders_slow():
    users = User.query.all()
    for user in users:
        orders = Order.query.filter_by(user_id=user.id).all()  # N queries
        user.orders = orders
    return users

# Efficient - Use joins or eager loading
def get_users_with_orders_fast():
    return User.query.options(joinedload(User.orders)).all()

# Use pagination for large datasets
def get_paginated_users(page=1, per_page=50):
    return User.query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

# Use database functions for aggregations
def get_user_statistics():
    return db.session.query(
        func.count(User.id).label('total_users'),
        func.avg(User.age).label('avg_age'),
        func.max(User.created_at).label('latest_signup')
    ).first()
```

### Index Optimization
```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Composite indexes for multi-column queries
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Partial indexes for specific conditions
CREATE INDEX idx_active_users ON users(id) WHERE status = 'active';
```

### Connection Pooling
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Optimized database connection
engine = create_engine(
    'postgresql://user:password@localhost/db',
    poolclass=QueuePool,
    pool_size=20,          # Number of connections to maintain
    max_overflow=30,       # Additional connections when needed
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Validate connections before use
)
```

## Caching Strategies

### In-Memory Caching
```python
from functools import lru_cache
import time

# Function-level caching
@lru_cache(maxsize=128)
def expensive_calculation(n):
    # Simulate expensive operation
    time.sleep(1)
    return n * n

# Class-based caching
class CacheManager:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())
    
    def invalidate(self, key):
        if key in self.cache:
            del self.cache[key]

# Usage
cache = CacheManager(ttl=1800)  # 30 minutes

def get_user_profile(user_id):
    profile = cache.get(f"user_profile_{user_id}")
    if profile is None:
        profile = fetch_user_profile_from_db(user_id)
        cache.set(f"user_profile_{user_id}", profile)
    return profile
```

### Redis Caching
```python
import redis
import json
import pickle

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host, 
            port=port, 
            db=db,
            decode_responses=True
        )
    
    def get_json(self, key):
        value = self.redis_client.get(key)
        return json.loads(value) if value else None
    
    def set_json(self, key, value, ttl=3600):
        self.redis_client.setex(key, ttl, json.dumps(value))
    
    def get_object(self, key):
        value = self.redis_client.get(key)
        return pickle.loads(value) if value else None
    
    def set_object(self, key, value, ttl=3600):
        self.redis_client.setex(key, ttl, pickle.dumps(value))
    
    def invalidate_pattern(self, pattern):
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

# Usage
cache = RedisCache()

def get_popular_posts():
    posts = cache.get_json("popular_posts")
    if posts is None:
        posts = fetch_popular_posts_from_db()
        cache.set_json("popular_posts", posts, ttl=1800)
    return posts
```

## Asynchronous Programming

### Async/Await Patterns
```python
import asyncio
import aiohttp
import time

# Synchronous - Sequential execution
def fetch_urls_sync(urls):
    results = []
    for url in urls:
        response = requests.get(url)
        results.append(response.json())
    return results

# Asynchronous - Concurrent execution
async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.json()

async def fetch_urls_async(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# Performance comparison
def compare_performance():
    urls = ['http://api.example.com/data'] * 10
    
    # Synchronous timing
    start = time.time()
    sync_results = fetch_urls_sync(urls)
    sync_time = time.time() - start
    
    # Asynchronous timing
    start = time.time()
    async_results = asyncio.run(fetch_urls_async(urls))
    async_time = time.time() - start
    
    print(f"Sync time: {sync_time:.2f}s")
    print(f"Async time: {async_time:.2f}s")
    print(f"Speedup: {sync_time / async_time:.2f}x")
```

### Background Task Processing
```python
import celery
from celery import Celery

# Celery configuration
app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def process_large_dataset(dataset_id):
    """Process large dataset in background"""
    # Heavy computation here
    time.sleep(10)  # Simulate processing
    return f"Processed dataset {dataset_id}"

# Usage in web application
def trigger_background_processing(dataset_id):
    # Start background task
    task = process_large_dataset.delay(dataset_id)
    return {"task_id": task.id, "status": "processing"}

def check_task_status(task_id):
    task = process_large_dataset.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

## Memory Optimization

### Memory-Efficient Patterns
```python
import sys
from typing import Iterator, Generator

# Memory-efficient data processing
def process_large_file_inefficient(filename):
    """Loads entire file into memory"""
    with open(filename, 'r') as f:
        lines = f.readlines()  # All lines in memory
    
    processed = []
    for line in lines:
        processed.append(process_line(line))
    return processed

def process_large_file_efficient(filename) -> Generator[str, None, None]:
    """Processes file line by line"""
    with open(filename, 'r') as f:
        for line in f:  # One line at a time
            yield process_line(line.strip())

# Memory usage comparison
def memory_usage_demo():
    # Inefficient - all in memory
    big_list = [i ** 2 for i in range(1000000)]
    print(f"List memory: {sys.getsizeof(big_list)} bytes")
    
    # Efficient - generator
    big_generator = (i ** 2 for i in range(1000000))
    print(f"Generator memory: {sys.getsizeof(big_generator)} bytes")

# Use __slots__ for memory-efficient classes
class MemoryEfficientClass:
    __slots__ = ['x', 'y', 'z']  # Reduces memory overhead
    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class RegularClass:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

# Memory comparison
import pympler.asizeof as asizeof

efficient_obj = MemoryEfficientClass(1, 2, 3)
regular_obj = RegularClass(1, 2, 3)

print(f"Efficient class: {asizeof.asizeof(efficient_obj)} bytes")
print(f"Regular class: {asizeof.asizeof(regular_obj)} bytes")
```

## CPU Optimization

### Multiprocessing for CPU-bound Tasks
```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time

def cpu_bound_task(n):
    """Simulate CPU-intensive work"""
    result = 0
    for i in range(n):
        result += i ** 2
    return result

def compare_execution_methods():
    tasks = [1000000] * 8
    
    # Sequential execution
    start = time.time()
    sequential_results = [cpu_bound_task(n) for n in tasks]
    sequential_time = time.time() - start
    
    # Multiprocessing
    start = time.time()
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        parallel_results = list(executor.map(cpu_bound_task, tasks))
    parallel_time = time.time() - start
    
    print(f"Sequential time: {sequential_time:.2f}s")
    print(f"Parallel time: {parallel_time:.2f}s")
    print(f"Speedup: {sequential_time / parallel_time:.2f}x")

# Optimized numerical operations
import numpy as np

def optimize_numerical_operations():
    # Inefficient - Python loops
    start = time.time()
    python_result = sum(i ** 2 for i in range(1000000))
    python_time = time.time() - start
    
    # Efficient - NumPy vectorization
    start = time.time()
    arr = np.arange(1000000)
    numpy_result = np.sum(arr ** 2)
    numpy_time = time.time() - start
    
    print(f"Python time: {python_time:.4f}s")
    print(f"NumPy time: {numpy_time:.4f}s")
    print(f"Speedup: {python_time / numpy_time:.2f}x")
```

## Network & I/O Optimization

### Connection Pooling & Keep-Alive
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OptimizedHTTPClient:
    def __init__(self):
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Connection pooling
        adapter = HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Keep-alive
        self.session.headers.update({'Connection': 'keep-alive'})
    
    def get(self, url, **kwargs):
        return self.session.get(url, **kwargs)
    
    def close(self):
        self.session.close()

# Usage
client = OptimizedHTTPClient()
responses = []
for url in urls:
    response = client.get(url)
    responses.append(response.json())
client.close()
```

## Frontend Performance

### Lazy Loading & Code Splitting
```python
# Server-side optimization for web apps
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/data')
def get_data():
    # Pagination for large datasets
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Only fetch requested fields
    fields = request.args.get('fields', '').split(',')
    
    # Use efficient queries
    query = optimize_query_for_fields(fields)
    paginated_data = query.paginate(page, per_page, False)
    
    return jsonify({
        'data': [item.to_dict(fields) for item in paginated_data.items],
        'pagination': {
            'page': page,
            'pages': paginated_data.pages,
            'total': paginated_data.total
        }
    })

# Response compression
from flask_compress import Compress

Compress(app)

# Caching headers
@app.after_request
def add_cache_headers(response):
    if request.endpoint == 'static':
        # Cache static files for 1 year
        response.cache_control.max_age = 31536000
    elif request.endpoint in ['get_data']:
        # Cache API responses for 5 minutes
        response.cache_control.max_age = 300
    return response
```

## Monitoring & Optimization

### Performance Monitoring
```python
import time
from functools import wraps
import logging

# Performance monitoring decorator
def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            status = 'success'
        except Exception as e:
            status = 'error'
            raise
        finally:
            end_time = time.time()
            end_memory = get_memory_usage()
            
            # Log performance metrics
            logging.info(f"PERF: {func.__name__} - "
                        f"time={end_time - start_time:.3f}s, "
                        f"memory_delta={end_memory - start_memory}MB, "
                        f"status={status}")
        
        return result
    return wrapper

def get_memory_usage():
    """Get current memory usage in MB"""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

# Application metrics
class PerformanceMetrics:
    def __init__(self):
        self.request_times = []
        self.error_count = 0
        self.success_count = 0
    
    def record_request(self, duration, success=True):
        self.request_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_stats(self):
        if not self.request_times:
            return {}
        
        sorted_times = sorted(self.request_times)
        count = len(sorted_times)
        
        return {
            'count': count,
            'avg_time': sum(sorted_times) / count,
            'p50': sorted_times[count // 2],
            'p90': sorted_times[int(count * 0.9)],
            'p99': sorted_times[int(count * 0.99)],
            'error_rate': self.error_count / (self.success_count + self.error_count)
        }

metrics = PerformanceMetrics()

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    success = 200 <= response.status_code < 400
    metrics.record_request(duration, success)
    return response
```

## Performance Testing

### Load Testing with Locust
```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.login()
    
    def login(self):
        response = self.client.post("/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
    
    @task(3)
    def view_homepage(self):
        self.client.get("/")
    
    @task(2)
    def view_profile(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/profile", headers=headers)
    
    @task(1)
    def create_post(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.post("/posts", json={
            "title": "Test Post",
            "content": "This is a test post"
        }, headers=headers)

# Run with: locust -f locustfile.py --host=http://localhost:5000
```

## Performance Checklist

### Code Level
- [ ] Use appropriate algorithms and data structures
- [ ] Implement caching strategies
- [ ] Optimize database queries
- [ ] Use async programming for I/O operations
- [ ] Profile and eliminate bottlenecks
- [ ] Minimize memory allocations
- [ ] Use generators for large datasets

### Database Level
- [ ] Create appropriate indexes
- [ ] Optimize query performance
- [ ] Use connection pooling
- [ ] Implement pagination
- [ ] Use database-level aggregations
- [ ] Monitor slow queries

### System Level
- [ ] Configure caching (Redis/Memcached)
- [ ] Use CDN for static assets
- [ ] Implement load balancing
- [ ] Optimize server configuration
- [ ] Monitor resource usage
- [ ] Set up performance alerts

### Application Level
- [ ] Implement response compression
- [ ] Use appropriate cache headers
- [ ] Optimize API response sizes
- [ ] Implement rate limiting
- [ ] Use background job processing
- [ ] Monitor application metrics

Remember: Measure first, optimize second. Always profile your application to identify real bottlenecks before optimization.
