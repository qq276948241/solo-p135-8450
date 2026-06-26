import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from database import db
from models import (
    Inventory, MenuItem, Order, OrderItem,
    ORDER_STATUS_FLOW, ORDER_STATUS_MAP, CUP_SIZE_MAP, SUGAR_LEVELS
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coffee_shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def generate_order_no():
    return 'ORD' + datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex[:4]).upper()


def init_test_data():
    if Inventory.query.count() == 0:
        beans = [
            Inventory(bean_name='意式拼配豆', stock_grams=2000, threshold_grams=500),
            Inventory(bean_name='埃塞俄比亚耶加雪菲', stock_grams=800, threshold_grams=400),
            Inventory(bean_name='哥伦比亚慧兰', stock_grams=600, threshold_grams=400)
        ]
        db.session.add_all(beans)
        db.session.flush()

        menu_items = [
            MenuItem(
                name='美式咖啡',
                category='经典咖啡',
                bean_id=beans[0].id,
                bean_grams_medium=18,
                bean_grams_large=25,
                price_medium=22,
                price_large=28
            ),
            MenuItem(
                name='拿铁咖啡',
                category='经典咖啡',
                bean_id=beans[0].id,
                bean_grams_medium=18,
                bean_grams_large=25,
                price_medium=28,
                price_large=34
            ),
            MenuItem(
                name='手冲耶加雪菲',
                category='精品手冲',
                bean_id=beans[1].id,
                bean_grams_medium=15,
                bean_grams_large=20,
                price_medium=38,
                price_large=48
            ),
            MenuItem(
                name='手冲哥伦比亚',
                category='精品手冲',
                bean_id=beans[2].id,
                bean_grams_medium=15,
                bean_grams_large=20,
                price_medium=36,
                price_large=46
            )
        ]
        db.session.add_all(menu_items)
        db.session.commit()
        print('测试数据初始化完成')


# ==================== 菜单管理模块 ====================

@app.route('/api/menu', methods=['GET'])
def get_menu():
    menu_items = MenuItem.query.all()
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': [item.to_dict() for item in menu_items]
    })


@app.route('/api/menu/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'code': 1, 'message': '菜单项不存在'}), 404
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': item.to_dict()
    })


@app.route('/api/menu', methods=['POST'])
def create_menu_item():
    data = request.get_json()
    required_fields = ['name', 'category', 'bean_id', 'bean_grams_medium', 'bean_grams_large',
                       'price_medium', 'price_large']
    for field in required_fields:
        if field not in data:
            return jsonify({'code': 1, 'message': f'缺少必填字段: {field}'}), 400

    bean = Inventory.query.get(data['bean_id'])
    if not bean:
        return jsonify({'code': 1, 'message': '关联的豆子库存不存在'}), 400

    if MenuItem.query.filter_by(name=data['name']).first():
        return jsonify({'code': 1, 'message': '该菜品名称已存在'}), 400

    item = MenuItem(
        name=data['name'],
        category=data['category'],
        bean_id=data['bean_id'],
        bean_grams_medium=float(data['bean_grams_medium']),
        bean_grams_large=float(data['bean_grams_large']),
        price_medium=float(data['price_medium']),
        price_large=float(data['price_large']),
        is_active=data.get('is_active', True)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({
        'code': 0,
        'message': '创建成功',
        'data': item.to_dict()
    }), 201


@app.route('/api/menu/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'code': 1, 'message': '菜单项不存在'}), 404

    data = request.get_json()
    if 'name' in data:
        existing = MenuItem.query.filter_by(name=data['name']).first()
        if existing and existing.id != item_id:
            return jsonify({'code': 1, 'message': '该菜品名称已存在'}), 400
        item.name = data['name']
    if 'category' in data:
        item.category = data['category']
    if 'bean_id' in data:
        bean = Inventory.query.get(data['bean_id'])
        if not bean:
            return jsonify({'code': 1, 'message': '关联的豆子库存不存在'}), 400
        item.bean_id = data['bean_id']
    if 'bean_grams_medium' in data:
        item.bean_grams_medium = float(data['bean_grams_medium'])
    if 'bean_grams_large' in data:
        item.bean_grams_large = float(data['bean_grams_large'])
    if 'price_medium' in data:
        item.price_medium = float(data['price_medium'])
    if 'price_large' in data:
        item.price_large = float(data['price_large'])
    if 'is_active' in data:
        item.is_active = data['is_active']

    db.session.commit()
    return jsonify({
        'code': 0,
        'message': '更新成功',
        'data': item.to_dict()
    })


@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'code': 1, 'message': '菜单项不存在'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'code': 0, 'message': '删除成功'})


# ==================== 下单模块 ====================

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if 'items' not in data or not isinstance(data['items'], list) or len(data['items']) == 0:
        return jsonify({'code': 1, 'message': '订单项不能为空'}), 400

    order_items = []
    total_amount = 0
    inventory_deductions = {}

    for idx, item_data in enumerate(data['items']):
        required = ['menu_item_id', 'cup_size', 'sugar_level', 'quantity']
        for field in required:
            if field not in item_data:
                return jsonify({'code': 1, 'message': f'第{idx+1}项缺少必填字段: {field}'}), 400

        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        if not menu_item:
            return jsonify({'code': 1, 'message': f'第{idx+1}项菜品不存在'}), 400
        if not menu_item.is_active:
            return jsonify({'code': 1, 'message': f'第{idx+1}项菜品已下架'}), 400

        cup_size = item_data['cup_size']
        if cup_size not in CUP_SIZE_MAP:
            return jsonify({'code': 1, 'message': f'第{idx+1}项杯型无效，只能是 medium 或 large'}), 400

        sugar_level = item_data['sugar_level']
        if sugar_level not in SUGAR_LEVELS:
            return jsonify({'code': 1, 'message': f'第{idx+1}项糖度无效，可选值: {", ".join(SUGAR_LEVELS)}'}), 400

        quantity = int(item_data['quantity'])
        if quantity <= 0:
            return jsonify({'code': 1, 'message': f'第{idx+1}项数量必须大于0'}), 400

        unit_price = menu_item.price_medium if cup_size == 'medium' else menu_item.price_large
        bean_grams_per = menu_item.bean_grams_medium if cup_size == 'medium' else menu_item.bean_grams_large
        subtotal = unit_price * quantity
        total_bean_grams = bean_grams_per * quantity

        total_amount += subtotal

        bean_id = menu_item.bean_id
        if bean_id not in inventory_deductions:
            inventory_deductions[bean_id] = 0
        inventory_deductions[bean_id] += total_bean_grams

        order_items.append({
            'menu_item_id': item_data['menu_item_id'],
            'cup_size': cup_size,
            'sugar_level': sugar_level,
            'quantity': quantity,
            'unit_price': unit_price,
            'subtotal': subtotal,
            'bean_grams_used': total_bean_grams,
            'menu_item': menu_item
        })

    low_stock_warnings = []
    for bean_id, grams_needed in inventory_deductions.items():
        inventory = Inventory.query.get(bean_id)
        if inventory:
            if inventory.stock_grams < grams_needed:
                return jsonify({
                    'code': 1,
                    'message': f'库存不足: {inventory.bean_name} 仅剩 {inventory.stock_grams:.0f}g，需要 {grams_needed:.0f}g'
                }), 400
            if inventory.stock_grams - grams_needed < inventory.threshold_grams:
                low_stock_warnings.append({
                    'bean_id': inventory.id,
                    'bean_name': inventory.bean_name,
                    'current_stock': inventory.stock_grams,
                    'after_deduction': inventory.stock_grams - grams_needed,
                    'threshold': inventory.threshold_grams
                })

    for bean_id, grams_needed in inventory_deductions.items():
        inventory = Inventory.query.get(bean_id)
        if inventory:
            inventory.stock_grams -= grams_needed

    order = Order(
        order_no=generate_order_no(),
        total_amount=total_amount,
        customer_name=data.get('customer_name'),
        status='pending_payment'
    )
    db.session.add(order)
    db.session.flush()

    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item_data['menu_item_id'],
            cup_size=item_data['cup_size'],
            sugar_level=item_data['sugar_level'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            subtotal=item_data['subtotal'],
            bean_grams_used=item_data['bean_grams_used']
        )
        db.session.add(order_item)

    db.session.commit()

    response_data = order.to_dict()
    if low_stock_warnings:
        response_data['low_stock_warnings'] = low_stock_warnings

    return jsonify({
        'code': 0,
        'message': '订单创建成功' + ('，注意部分豆子库存低于阈值' if low_stock_warnings else ''),
        'data': response_data
    }), 201


# ==================== 订单状态推进模块 ====================

@app.route('/api/orders', methods=['GET'])
def get_orders():
    status = request.args.get('status')
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': [order.to_dict() for order in orders]
    })


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'code': 1, 'message': '订单不存在'}), 404
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': order.to_dict()
    })


@app.route('/api/orders/<int:order_id>/next-status', methods=['POST'])
def advance_order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'code': 1, 'message': '订单不存在'}), 404

    current_idx = ORDER_STATUS_FLOW.index(order.status)
    if current_idx >= len(ORDER_STATUS_FLOW) - 1:
        return jsonify({'code': 1, 'message': '订单已完成全部流程'}), 400

    next_status = ORDER_STATUS_FLOW[current_idx + 1]
    order.status = next_status
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': f'订单状态已更新为: {ORDER_STATUS_MAP[next_status]}',
        'data': order.to_dict()
    })


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def set_order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'code': 1, 'message': '订单不存在'}), 404

    data = request.get_json()
    target_status = data.get('status')
    if not target_status or target_status not in ORDER_STATUS_FLOW:
        return jsonify({'code': 1, 'message': f'无效的状态值，可选值: {", ".join(ORDER_STATUS_FLOW)}'}), 400

    current_idx = ORDER_STATUS_FLOW.index(order.status)
    target_idx = ORDER_STATUS_FLOW.index(target_status)

    if target_idx != current_idx + 1:
        return jsonify({
            'code': 1,
            'message': f'状态必须按顺序流转: 当前({ORDER_STATUS_MAP[order.status]}) → 下一状态({ORDER_STATUS_MAP[ORDER_STATUS_FLOW[current_idx + 1]]})'
        }), 400

    order.status = target_status
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': f'订单状态已更新为: {ORDER_STATUS_MAP[target_status]}',
        'data': order.to_dict()
    })


# ==================== 库存查询和低库存预警模块 ====================

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    only_low = request.args.get('only_low', 'false').lower() == 'true'
    query = Inventory.query
    if only_low:
        query = query.filter(Inventory.stock_grams < Inventory.threshold_grams)
    inventory_list = query.all()

    return jsonify({
        'code': 0,
        'message': 'success',
        'data': [inv.to_dict() for inv in inventory_list]
    })


@app.route('/api/inventory/low-stock', methods=['GET'])
def get_low_stock():
    low_stock_items = Inventory.query.filter(
        Inventory.stock_grams < Inventory.threshold_grams
    ).all()

    return jsonify({
        'code': 0,
        'message': 'success',
        'count': len(low_stock_items),
        'data': [inv.to_dict() for inv in low_stock_items]
    })


@app.route('/api/inventory/<int:inventory_id>', methods=['GET'])
def get_inventory_item(inventory_id):
    inventory = Inventory.query.get(inventory_id)
    if not inventory:
        return jsonify({'code': 1, 'message': '库存项不存在'}), 404
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': inventory.to_dict()
    })


@app.route('/api/inventory/<int:inventory_id>/restock', methods=['POST'])
def restock_inventory(inventory_id):
    inventory = Inventory.query.get(inventory_id)
    if not inventory:
        return jsonify({'code': 1, 'message': '库存项不存在'}), 404

    data = request.get_json()
    add_grams = data.get('add_grams', 0)
    if add_grams <= 0:
        return jsonify({'code': 1, 'message': '补货克数必须大于0'}), 400

    inventory.stock_grams += float(add_grams)
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': f'补货成功，当前库存: {inventory.stock_grams:.0f}g',
        'data': inventory.to_dict()
    })


@app.route('/api/inventory', methods=['POST'])
def create_inventory():
    data = request.get_json()
    required = ['bean_name', 'stock_grams', 'threshold_grams']
    for field in required:
        if field not in data:
            return jsonify({'code': 1, 'message': f'缺少必填字段: {field}'}), 400

    if Inventory.query.filter_by(bean_name=data['bean_name']).first():
        return jsonify({'code': 1, 'message': '该豆子名称已存在'}), 400

    inventory = Inventory(
        bean_name=data['bean_name'],
        stock_grams=float(data['stock_grams']),
        threshold_grams=float(data['threshold_grams'])
    )
    db.session.add(inventory)
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '创建成功',
        'data': inventory.to_dict()
    }), 201


@app.route('/api/inventory/<int:inventory_id>', methods=['PUT'])
def update_inventory(inventory_id):
    inventory = Inventory.query.get(inventory_id)
    if not inventory:
        return jsonify({'code': 1, 'message': '库存项不存在'}), 404

    data = request.get_json()
    if 'bean_name' in data:
        existing = Inventory.query.filter_by(bean_name=data['bean_name']).first()
        if existing and existing.id != inventory_id:
            return jsonify({'code': 1, 'message': '该豆子名称已存在'}), 400
        inventory.bean_name = data['bean_name']
    if 'stock_grams' in data:
        inventory.stock_grams = float(data['stock_grams'])
    if 'threshold_grams' in data:
        inventory.threshold_grams = float(data['threshold_grams'])

    db.session.commit()
    return jsonify({
        'code': 0,
        'message': '更新成功',
        'data': inventory.to_dict()
    })


@app.route('/api/meta', methods=['GET'])
def get_meta():
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'order_statuses': [{'key': s, 'text': ORDER_STATUS_MAP[s]} for s in ORDER_STATUS_FLOW],
            'cup_sizes': [{'key': k, 'text': v} for k, v in CUP_SIZE_MAP.items()],
            'sugar_levels': SUGAR_LEVELS
        }
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_test_data()
    app.run(host='0.0.0.0', port=5000, debug=True)
