from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# 1. 创建 FastAPI 实例
appsasdasd = FastAPI(
    title="FoodAgent API",
    description="一个简单的 FoodAgent 后端服务",
    version="0.1.0"
)


# 2. 定义一个数据模型 (用于接收 POST 请求的数据)
class FoodItem(BaseModel):
    name: str
    price: float
    is_available: bool = True
    description: Optional[str] = None


# 3. 定义路由

# 根路径 (GET 请求)
@app.get("/")
async def read_root():
    return {"message": "欢迎使用 FoodAgent API!", "status": "running"}


# 获取特定食物信息 (GET 请求，带路径参数)
@app.get("/food/{food_id}")
async def get_food(food_id: int, q: Optional[str] = None):
    # 这里只是模拟数据，实际项目中通常从数据库查询
    fake_db = {
        1: {"name": "汉堡", "price": 25.0},
        2: {"name": "披萨", "price": 60.0},
        3: {"name": "沙拉", "price": 15.0}
    }

    item = fake_db.get(food_id)
    if not item:
        return {"error": "食物未找到"}

    response = item.copy()
    if q:
        response["query"] = q

    return response


# 添加新食物 (POST 请求，带 JSON 身体)
@app.post("/food/")
async def create_food(item: FoodItem):
    # 这里模拟保存操作
    return {
        "message": "食物添加成功",
        "data": item,
        "total_price_with_tax": item.price * 1.1  # 模拟计算含税价
    }


# 4. 启动入口 (如果直接运行此文件)
if __name__ == "__main__":
    import uvicorn

    # host="0.0.0.0" 允许外部访问，port=8000 是默认端口
    uvicorn.run(app, host="0.0.0.0", port=8000)


