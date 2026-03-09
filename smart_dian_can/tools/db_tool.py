from typing import List, Dict, Any, Optional
import mysql.connector
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DataBaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", "3306"))
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "root")
        self.database = os.getenv("MYSQL_DATABASE", "menu")

    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4"
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                logger.info(f"已成功建立数据库连接,数据库: {self.database}")
                return True
            else:
                logger.error(f"数据库连接关闭,数据库: {self.database}")
                return False
        except mysql.connector.Error as e:
            logger.error(f"数据库连接错误,异常原因 {e}")
            return False

    def dis_connect(self):
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info(f"已成功关闭数据库连接,数据库: {self.database}")
                self.connection = None
        except mysql.connector.Error as e:
            logger.error(f"关闭数据库连接错误,异常原因 {e}")
            raise

    def __enter__(self):
        if self.connect():
            return self
        else:
            raise Exception("无法建立数据库连接")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dis_connect()

    def commit(self):
        """提交事务"""
        if self.connection and self.connection.is_connected():
            self.connection.commit()
            logger.info("数据库事务提交成功")

    def rollback(self):
        """回滚事务"""
        if self.connection and self.connection.is_connected():
            self.connection.rollback()
            logger.warning("数据库事务回滚")


# ===================== 菜品相关操作（原有功能优化） =====================
def get_all_menu_items() -> str:
    """获取所有菜单项（格式化字符串）"""
    try:
        with DataBaseConnection() as db:
            query_sql = """
                        SELECT id, dish_name, price, category, spice_level, is_vegetarian
                        FROM menu_items \
                        WHERE is_available = 1 \
                        ORDER BY category, dish_name \
                        """
            db.cursor.execute(query_sql)
            menu_items = db.cursor.fetchall()

            if not menu_items:
                return "📭 当前暂无可用菜品"

            # 构建表头
            header = f"{'ID':<4} {'菜品名称':<12} {'价格':<8} {'分类':<6} {'辣度':<6} {'素食'}"
            menu_strings = [header, "-" * 45]

            spice_map = {0: "不辣", 1: "微辣", 2: "中辣", 3: "重辣"}
            for item in menu_items:
                spice_text = spice_map.get(item["spice_level"], "未知")
                veg_text = "✅" if item["is_vegetarian"] else "❌"
                menu_line = (
                    f"{item['id']:<4} {item['dish_name']:<12} ¥{item['price']:<7.2f} "
                    f"{item['category']:<6} {spice_text:<6} {veg_text}"
                )
                menu_strings.append(menu_line)

            return "\n".join(menu_strings)
    except Exception as e:
        logger.error(f"查询菜品失败: {e}")
        return f"❌ 查询菜品失败: {str(e)[:50]}..."


def get_menu_items_list() -> List[dict]:
    """获取所有菜单项（字典列表）"""
    try:
        with DataBaseConnection() as db:
            query_sql = """
                        SELECT id, \
                               dish_name, \
                               price, \
                               description, \
                               category, \
                               spice_level, \
                               flavor,
                               main_ingredients, \
                               cooking_method, \
                               is_vegetarian, \
                               allergens, \
                               is_available
                        FROM menu_items \
                        WHERE is_available = 1 \
                        ORDER BY category, dish_name \
                        """
            db.cursor.execute(query_sql)
            items = db.cursor.fetchall()

            spice_map = {0: "不辣", 1: "微辣", 2: "中辣", 3: "重辣"}
            processed = []
            for item in items:
                processed.append({
                    "id": item['id'],
                    "dish_name": item['dish_name'],
                    "price": float(item['price']),
                    "formatted_price": f"¥{item['price']:.2f}",
                    "description": item['description'] or "暂无描述",
                    "category": item['category'],
                    "spice_text": spice_map.get(item['spice_level'], "未知"),
                    "vegetarian_text": "是" if item['is_vegetarian'] else "否",
                    "allergens": item['allergens'] or "无"
                })
            return processed
    except Exception as e:
        logger.error(f"查询菜品列表失败: {e}")
        return []


def get_menu_item_by_id(item_id: int) -> Optional[dict]:
    """通过ID获取菜品详情"""
    try:
        with DataBaseConnection() as db:
            sql = """
                  SELECT * \
                  FROM menu_items \
                  WHERE id = %s \
                    AND is_available = 1 \
                  """
            db.cursor.execute(sql, (item_id,))
            item = db.cursor.fetchone()

            if not item:
                logger.warning(f"菜品ID{item_id}不存在或已下架")
                return None

            spice_map = {0: "不辣", 1: "微辣", 2: "中辣", 3: "重辣"}
            return {
                "id": item['id'],
                "dish_name": item['dish_name'],
                "price": float(item['price']),
                "description": item['description'] or "暂无描述",
                "category": item['category'],
                "spice_text": spice_map.get(item['spice_level'], "未知"),
                "main_ingredients": item['main_ingredients'] or "未知食材",
                "vegetarian_text": "是" if item['is_vegetarian'] else "否",
                "allergens": item['allergens'] or "无过敏原"
            }
    except Exception as e:
        logger.error(f"查询菜品ID{item_id}失败: {e}")
        return None


# ===================== 新增：购物车操作 =====================
def add_to_cart(user_id: str, item_id: int, quantity: int = 1) -> bool:
    """添加菜品到购物车"""
    try:
        with DataBaseConnection() as db:
            # 1. 检查菜品是否存在
            item = get_menu_item_by_id(item_id)
            if not item:
                logger.error(f"添加购物车失败：菜品ID{item_id}不存在")
                return False

            # 2. 检查购物车中是否已有该菜品
            db.cursor.execute(
                "SELECT quantity FROM cart WHERE user_id = %s AND item_id = %s",
                (user_id, item_id)
            )
            existing = db.cursor.fetchone()

            if existing:
                # 更新数量
                new_quantity = existing['quantity'] + quantity
                db.cursor.execute(
                    "UPDATE cart SET quantity = %s WHERE user_id = %s AND item_id = %s",
                    (new_quantity, user_id, item_id)
                )
            else:
                # 新增购物车项
                db.cursor.execute(
                    """
                    INSERT INTO cart (user_id, item_id, quantity, add_time)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, item_id, quantity, datetime.now())
                )

            db.commit()
            logger.info(f"用户{user_id}添加菜品{item_id}×{quantity}到购物车成功")
            return True
    except Exception as e:
        logger.error(f"添加购物车失败: {e}")
        return False


def get_cart(user_id: str) -> List[dict]:
    """获取用户购物车"""
    try:
        with DataBaseConnection() as db:
            db.cursor.execute(
                """
                SELECT c.id,
                       c.item_id,
                       c.quantity,
                       m.dish_name,
                       m.price,
                       m.category,
                       m.spice_level
                FROM cart c
                         JOIN menu_items m ON c.item_id = m.id
                WHERE c.user_id = %s
                  AND m.is_available = 1
                """,
                (user_id,)
            )
            cart_items = db.cursor.fetchall()

            spice_map = {0: "不辣", 1: "微辣", 2: "中辣", 3: "重辣"}
            processed = []
            total_price = 0.0

            for item in cart_items:
                price = float(item['price'])
                subtotal = price * item['quantity']
                total_price += subtotal

                processed.append({
                    "cart_id": item['id'],
                    "item_id": item['item_id'],
                    "dish_name": item['dish_name'],
                    "quantity": item['quantity'],
                    "unit_price": f"¥{price:.2f}",
                    "subtotal": f"¥{subtotal:.2f}",
                    "category": item['category'],
                    "spice_text": spice_map.get(item['spice_level'], "未知")
                })

            # 添加总计信息
            processed.append({
                "total_count": sum([item['quantity'] for item in cart_items]),
                "total_price": f"¥{total_price:.2f}"
            })

            return processed
    except Exception as e:
        logger.error(f"获取购物车失败: {e}")
        return []


# ===================== 新增：订单操作 =====================
def create_order(user_id: str, cart_ids: List[int], address: str) -> Optional[str]:
    """创建订单（从购物车结算）"""
    try:
        with DataBaseConnection() as db:
            # 1. 验证购物车项
            cart_ids_str = ",".join(map(str, cart_ids))
            db.cursor.execute(
                f"""
                SELECT c.item_id, c.quantity, m.price, m.dish_name
                FROM cart c
                JOIN menu_items m ON c.item_id = m.id
                WHERE c.id IN ({cart_ids_str}) AND c.user_id = %s
                """,
                (user_id,)
            )
            items = db.cursor.fetchall()

            if not items:
                logger.error(f"用户{user_id}创建订单失败：购物车项不存在")
                return None

            # 2. 计算总价
            total_price = sum(float(item['price']) * item['quantity'] for item in items)

            # 3. 创建订单
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id[-4:]}"
            db.cursor.execute(
                """
                INSERT INTO orders (order_id, user_id, total_price, address,
                                    create_time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (order_id, user_id, total_price, address, datetime.now(), "待支付")
            )

            # 4. 创建订单项
            for item in items:
                db.cursor.execute(
                    """
                    INSERT INTO order_items (order_id, item_id, quantity, unit_price,
                                             dish_name)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (order_id, item['item_id'], item['quantity'],
                     item['price'], item['dish_name'])
                )

            # 5. 删除购物车项
            db.cursor.execute(
                f"DELETE FROM cart WHERE id IN ({cart_ids_str}) AND user_id = %s",
                (user_id,)
            )

            db.commit()
            logger.info(f"用户{user_id}创建订单{order_id}成功，总价{total_price:.2f}")
            return order_id
    except Exception as e:
        logger.error(f"创建订单失败: {e}")
        return None


# ===================== 格式化打印工具 =====================
def print_separator(title: str, length: int = 60):
    """打印分隔符标题"""
    print(f"\n{'=' * length}")
    print(f"📌 {title}")
    print(f"{'=' * length}")


def print_menu_table():
    """格式化打印菜品列表"""
    print_separator("菜品列表")
    menu_str = get_all_menu_items()
    print(menu_str)


def print_cart_detail(user_id: str):
    """格式化打印购物车"""
    print_separator(f"用户{user_id}的购物车")
    cart_items = get_cart(user_id)

    if not cart_items:
        print("🛒 购物车为空")
        return

    # 打印购物车项（排除总计行）
    total_info = cart_items.pop()
    header = f"{'ID':<6} {'菜品名称':<12} {'数量':<6} {'单价':<8} {'小计':<8} {'分类':<6}"
    print(header)
    print("-" * 50)

    for item in cart_items:
        print(
            f"{item['item_id']:<6} {item['dish_name']:<12} {item['quantity']:<6} "
            f"{item['unit_price']:<8} {item['subtotal']:<8} {item['category']:<6}"
        )

    # 打印总计
    print("-" * 50)
    print(f"📊 总计: {total_info['total_count']}件商品 | 总价: {total_info['total_price']}")


def print_order_success(order_id: str, user_id: str):
    """打印订单创建成功信息"""
    print_separator(f"订单创建成功")
    print(f"✅ 订单编号: {order_id}")
    print(f"👤 下单用户: {user_id}")
    print(f"🕒 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💡 请及时完成支付，感谢您的点餐！")


# ===================== 测试主函数 =====================
if __name__ == '__main__':
    # 1. 测试数据库连接
    print_separator("测试数据库连接", 80)
    db_test = DataBaseConnection()
    if db_test.connect():
        print("✅ 数据库连接成功")
        db_test.dis_connect()
    else:
        print("❌ 数据库连接失败")

    # 2. 打印菜品列表
    print_menu_table()

    # 3. 测试购物车操作
    USER_ID = "test001"
    add_to_cart(USER_ID, 1, 2)  # 添加2份宫保鸡丁
    add_to_cart(USER_ID, 2, 1)  # 添加1份麻婆豆腐
    print_cart_detail(USER_ID)

    # 4. 测试创建订单（需先确保cart表有数据）
    # 假设购物车项ID为1和2
    order_id = create_order(USER_ID, [1, 2], "深圳市南山区科技园")
    if order_id:
        print_order_success(order_id, USER_ID)

    # 5. 打印创建订单后的购物车（应该为空）
    print_cart_detail(USER_ID)