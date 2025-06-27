#!/usr/bin/env python3
"""
简单的被测试服务器
提供各种 API 端点用于 JMeter 测试
"""
import random
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# 创建 FastAPI 应用
app = FastAPI(title="JMeter Test Server", description="A simple test server for JMeter load testing", version="1.0.0")

# 模拟数据
users_db = {}
orders_db = {}
user_counter = 1
order_counter = 1


# 数据模型
class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class Order(BaseModel):
    user_id: int
    product: str
    quantity: int
    price: float


class LoginRequest(BaseModel):
    username: str
    password: str


# 根路径
@app.get("/")
async def root():
    """根路径 - 健康检查"""
    return {"message": "JMeter Test Server is running!", "timestamp": datetime.now().isoformat(), "status": "healthy"}


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}


# 用户管理 API
@app.post("/api/users")
async def create_user(user: User):
    """创建用户"""
    global user_counter

    # 模拟处理时间
    time.sleep(random.uniform(0.1, 0.3))

    user_id = user_counter
    users_db[user_id] = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "created_at": datetime.now().isoformat(),
    }
    user_counter += 1

    return {"success": True, "message": "User created successfully", "user": users_db[user_id]}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """获取用户信息"""
    # 模拟处理时间
    time.sleep(random.uniform(0.05, 0.15))

    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "user": users_db[user_id]}


@app.get("/api/users")
async def list_users(limit: int = 10, offset: int = 0):
    """获取用户列表"""
    # 模拟处理时间
    time.sleep(random.uniform(0.1, 0.2))

    all_users = list(users_db.values())
    total = len(all_users)
    users = all_users[offset : offset + limit]

    return {
        "success": True,
        "total": total,
        "users": users,
        "pagination": {"limit": limit, "offset": offset, "has_more": offset + limit < total},
    }


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user: User):
    """更新用户信息"""
    # 模拟处理时间
    time.sleep(random.uniform(0.1, 0.25))

    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    users_db[user_id].update(
        {"name": user.name, "email": user.email, "age": user.age, "updated_at": datetime.now().isoformat()}
    )

    return {"success": True, "message": "User updated successfully", "user": users_db[user_id]}


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """删除用户"""
    # 模拟处理时间
    time.sleep(random.uniform(0.05, 0.1))

    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    deleted_user = users_db.pop(user_id)

    return {"success": True, "message": "User deleted successfully", "deleted_user": deleted_user}


# 订单管理 API
@app.post("/api/orders")
async def create_order(order: Order):
    """创建订单"""
    global order_counter

    # 模拟处理时间
    time.sleep(random.uniform(0.2, 0.5))

    # 检查用户是否存在
    if order.user_id not in users_db:
        raise HTTPException(status_code=400, detail="User not found")

    order_id = order_counter
    orders_db[order_id] = {
        "id": order_id,
        "user_id": order.user_id,
        "product": order.product,
        "quantity": order.quantity,
        "price": order.price,
        "total": order.quantity * order.price,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    order_counter += 1

    return {"success": True, "message": "Order created successfully", "order": orders_db[order_id]}


@app.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    """获取订单信息"""
    # 模拟处理时间
    time.sleep(random.uniform(0.05, 0.15))

    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"success": True, "order": orders_db[order_id]}


@app.get("/api/orders")
async def list_orders(user_id: Optional[int] = None, limit: int = 10, offset: int = 0):
    """获取订单列表"""
    # 模拟处理时间
    time.sleep(random.uniform(0.1, 0.3))

    all_orders = list(orders_db.values())

    # 按用户过滤
    if user_id:
        all_orders = [order for order in all_orders if order["user_id"] == user_id]

    total = len(all_orders)
    orders = all_orders[offset : offset + limit]

    return {
        "success": True,
        "total": total,
        "orders": orders,
        "pagination": {"limit": limit, "offset": offset, "has_more": offset + limit < total},
    }


# 认证 API
@app.post("/api/login")
async def login(login_data: LoginRequest):
    """用户登录"""
    # 模拟处理时间
    time.sleep(random.uniform(0.2, 0.4))

    # 简单的用户名密码验证
    valid_users = {"admin": "admin123", "user1": "password1", "user2": "password2", "test": "test123"}

    if login_data.username not in valid_users:
        raise HTTPException(status_code=401, detail="Invalid username")

    if valid_users[login_data.username] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    # 生成模拟token
    token = f"token_{login_data.username}_{int(time.time())}"

    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {"username": login_data.username, "login_time": datetime.now().isoformat()},
    }


# 模拟慢接口
@app.get("/api/slow")
async def slow_endpoint():
    """模拟慢接口"""
    # 随机延迟 1-3 秒
    delay = random.uniform(1.0, 3.0)
    time.sleep(delay)

    return {
        "success": True,
        "message": f"Slow endpoint completed after {delay:.2f}s",
        "timestamp": datetime.now().isoformat(),
        "delay": delay,
    }


# 模拟错误接口
@app.get("/api/error")
async def error_endpoint():
    """模拟错误接口"""
    # 随机返回不同的错误
    error_type = random.choice([400, 401, 403, 404, 500, 503])

    error_messages = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }

    raise HTTPException(status_code=error_type, detail=error_messages[error_type])


# 模拟文件上传
@app.post("/api/upload")
async def upload_file(request: Request):
    """模拟文件上传"""
    # 模拟处理时间
    time.sleep(random.uniform(0.5, 1.0))

    # 获取请求体大小
    content_length = request.headers.get("content-length", "0")

    return {
        "success": True,
        "message": "File uploaded successfully",
        "file_size": content_length,
        "upload_time": datetime.now().isoformat(),
    }


# 统计端点
@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    return {
        "success": True,
        "stats": {
            "total_users": len(users_db),
            "total_orders": len(orders_db),
            "server_uptime": datetime.now().isoformat(),
            "users": list(users_db.values())[:5],  # 最近5个用户
            "orders": list(orders_db.values())[:5],  # 最近5个订单
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("🎯 Starting JMeter Test Server...")
    print("📍 Server URL: http://localhost:3000")
    print("📖 API Documentation: http://localhost:3000/docs")
    print("🔍 Health Check: http://localhost:3000/health")
    print("⏹️  Press Ctrl+C to stop server")
    print("")
    print("📋 Available Endpoints:")
    print("  GET  /                     - Root endpoint")
    print("  GET  /health               - Health check")
    print("  GET  /api/stats            - Statistics")
    print("  POST /api/users            - Create user")
    print("  GET  /api/users            - List users")
    print("  GET  /api/users/{id}       - Get user")
    print("  PUT  /api/users/{id}       - Update user")
    print("  DELETE /api/users/{id}     - Delete user")
    print("  POST /api/orders           - Create order")
    print("  GET  /api/orders           - List orders")
    print("  GET  /api/orders/{id}      - Get order")
    print("  POST /api/login            - User login")
    print("  GET  /api/slow             - Slow endpoint (1-3s)")
    print("  GET  /api/error            - Random error endpoint")
    print("  POST /api/upload           - File upload simulation")

    uvicorn.run(app, host="0.0.0.0", port=3000, reload=False)
