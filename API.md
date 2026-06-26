# 咖啡店订单与库存管理 API 文档

## 基础信息
- 服务地址: `http://localhost:5000`
- 统一响应格式:
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```
- `code=0` 表示成功, `code=1` 表示失败

---

## 一、菜单管理模块

### 1.1 获取菜单列表
```
GET /api/menu
```
**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "拿铁咖啡",
      "category": "经典咖啡",
      "bean_id": 1,
      "bean_name": "意式拼配豆",
      "bean_grams_medium": 18,
      "bean_grams_large": 25,
      "price_medium": 28,
      "price_large": 34,
      "is_active": true
    }
  ]
}
```

### 1.2 获取单个菜单项
```
GET /api/menu/<item_id>
```

### 1.3 新增菜单项
```
POST /api/menu
Content-Type: application/json
```
**请求体:**
```json
{
  "name": "卡布奇诺",
  "category": "经典咖啡",
  "bean_id": 1,
  "bean_grams_medium": 18,
  "bean_grams_large": 25,
  "price_medium": 26,
  "price_large": 32,
  "is_active": true
}
```

### 1.4 更新菜单项
```
PUT /api/menu/<item_id>
Content-Type: application/json
```
**请求体:** (支持部分字段更新)
```json
{
  "price_medium": 28,
  "is_active": false
}
```

### 1.5 删除菜单项
```
DELETE /api/menu/<item_id>
```

---

## 二、下单模块

### 2.1 创建订单 (自动扣库存)
```
POST /api/orders
Content-Type: application/json
```
**请求体:**
```json
{
  "customer_name": "张先生",
  "items": [
    {
      "menu_item_id": 2,
      "cup_size": "medium",
      "sugar_level": "50%",
      "quantity": 2
    },
    {
      "menu_item_id": 1,
      "cup_size": "large",
      "sugar_level": "0%",
      "quantity": 1
    }
  ]
}
```

**字段说明:**
- `cup_size`: `medium` (中杯) 或 `large` (大杯)
- `sugar_level`: `0%`, `30%`, `50%`, `70%`, `100%`

**响应示例 (库存预警):**
```json
{
  "code": 0,
  "message": "订单创建成功，注意部分豆子库存低于阈值",
  "data": {
    "id": 1,
    "order_no": "ORD20250626103025A1B2",
    "status": "pending_payment",
    "status_text": "待支付",
    "total_amount": 84,
    "customer_name": "张先生",
    "items": [...],
    "low_stock_warnings": [
      {
        "bean_id": 1,
        "bean_name": "意式拼配豆",
        "current_stock": 550,
        "after_deduction": 482,
        "threshold": 500
      }
    ]
  }
}
```

**200ml 拿铁示例:**
- 中杯拿铁用豆 18g × 数量 = 自动扣减对应克数
- 库存不足会直接返回错误，订单不创建

---

## 三、订单状态推进模块

### 3.1 获取订单列表
```
GET /api/orders
GET /api/orders?status=making
```
**状态列表:**
- `pending_payment` - 待支付
- `paid` - 已支付
- `making` - 制作中
- `completed` - 完成
- `picked_up` - 已取单

### 3.2 获取订单详情
```
GET /api/orders/<order_id>
```

### 3.3 推进到下一状态 (推荐使用)
```
POST /api/orders/<order_id>/next-status
```
**自动按顺序流转:** 待支付 → 已支付 → 制作中 → 完成 → 已取单

### 3.4 指定状态更新 (需按顺序)
```
PUT /api/orders/<order_id>/status
Content-Type: application/json
```
**请求体:**
```json
{
  "status": "making"
}
```
**注意:** 不能跳状态，必须按顺序流转。例如不能从「待支付」直接跳到「制作中」。

---

## 四、库存查询和低库存预警模块

### 4.1 获取全部库存
```
GET /api/inventory
GET /api/inventory?only_low=true
```

### 4.2 获取低库存预警列表
```
GET /api/inventory/low-stock
```
**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "count": 1,
  "data": [
    {
      "id": 2,
      "bean_name": "埃塞俄比亚耶加雪菲",
      "stock_grams": 350,
      "threshold_grams": 400,
      "is_low_stock": true
    }
  ]
}
```

### 4.3 获取单个库存项
```
GET /api/inventory/<inventory_id>
```

### 4.4 补货
```
POST /api/inventory/<inventory_id>/restock
Content-Type: application/json
```
**请求体:**
```json
{
  "add_grams": 1000
}
```

### 4.5 新增库存项
```
POST /api/inventory
Content-Type: application/json
```
```json
{
  "bean_name": "巴西喜拉多",
  "stock_grams": 1000,
  "threshold_grams": 400
}
```

### 4.6 更新库存项
```
PUT /api/inventory/<inventory_id>
```
```json
{
  "threshold_grams": 600
}
```

---

## 五、元数据接口

### 5.1 获取枚举值
```
GET /api/meta
```
**响应:**
```json
{
  "code": 0,
  "data": {
    "order_statuses": [
      {"key": "pending_payment", "text": "待支付"},
      {"key": "paid", "text": "已支付"},
      ...
    ],
    "cup_sizes": [
      {"key": "medium", "text": "中杯"},
      {"key": "large", "text": "大杯"}
    ],
    "sugar_levels": ["0%", "30%", "50%", "70%", "100%"]
  }
}
```

---

## 测试示例 (curl)

```bash
# 查看菜单
curl http://localhost:5000/api/menu

# 下订单 (2杯中杯拿铁 + 1杯大杯美式)
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "李女士",
    "items": [
      {"menu_item_id": 2, "cup_size": "medium", "sugar_level": "50%", "quantity": 2},
      {"menu_item_id": 1, "cup_size": "large", "sugar_level": "0%", "quantity": 1}
    ]
  }'

# 推进订单状态 (待支付 → 已支付)
curl -X POST http://localhost:5000/api/orders/1/next-status

# 查看低库存预警
curl http://localhost:5000/api/inventory/low-stock

# 补货
curl -X POST http://localhost:5000/api/inventory/1/restock \
  -H "Content-Type: application/json" \
  -d '{"add_grams": 1000}'
```

---

## 默认初始化数据

启动时会自动创建以下测试数据:

**豆子库存:**
1. 意式拼配豆 - 2000g (阈值 500g)
2. 埃塞俄比亚耶加雪菲 - 800g (阈值 400g)
3. 哥伦比亚慧兰 - 600g (阈值 400g)

**菜单:**
| 名称 | 中杯价格 | 大杯价格 | 中杯用豆 | 大杯用豆 |
|------|---------|---------|---------|---------|
| 美式咖啡 | 22元 | 28元 | 18g | 25g |
| 拿铁咖啡 | 28元 | 34元 | 18g | 25g |
| 手冲耶加雪菲 | 38元 | 48元 | 15g | 20g |
| 手冲哥伦比亚 | 36元 | 46元 | 15g | 20g |
