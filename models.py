from datetime import datetime
from database import db

ORDER_STATUS_FLOW = [
    'pending_payment',
    'paid',
    'making',
    'completed',
    'picked_up'
]

ORDER_STATUS_MAP = {
    'pending_payment': '待支付',
    'paid': '已支付',
    'making': '制作中',
    'completed': '完成',
    'picked_up': '已取单'
}

CUP_SIZE_MAP = {
    'medium': '中杯',
    'large': '大杯'
}

SUGAR_LEVELS = ['0%', '30%', '50%', '70%', '100%']


class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    bean_name = db.Column(db.String(100), nullable=False, unique=True)
    stock_grams = db.Column(db.Float, nullable=False, default=0)
    threshold_grams = db.Column(db.Float, nullable=False, default=500)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'bean_name': self.bean_name,
            'stock_grams': self.stock_grams,
            'threshold_grams': self.threshold_grams,
            'is_low_stock': self.stock_grams < self.threshold_grams,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)
    bean_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    bean_grams_medium = db.Column(db.Float, nullable=False)
    bean_grams_large = db.Column(db.Float, nullable=False)
    price_medium = db.Column(db.Float, nullable=False)
    price_large = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    bean = db.relationship('Inventory', backref='menu_items')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'bean_id': self.bean_id,
            'bean_name': self.bean.bean_name if self.bean else None,
            'bean_grams_medium': self.bean_grams_medium,
            'bean_grams_large': self.bean_grams_large,
            'price_medium': self.price_medium,
            'price_large': self.price_large,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(32), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default='pending_payment')
    total_amount = db.Column(db.Float, nullable=False, default=0)
    customer_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    def to_dict(self, include_items=True):
        data = {
            'id': self.id,
            'order_no': self.order_no,
            'status': self.status,
            'status_text': ORDER_STATUS_MAP.get(self.status, self.status),
            'total_amount': round(self.total_amount, 2),
            'customer_name': self.customer_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    cup_size = db.Column(db.String(10), nullable=False)
    sugar_level = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    bean_grams_used = db.Column(db.Float, nullable=False)

    menu_item = db.relationship('MenuItem')

    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'menu_item_name': self.menu_item.name if self.menu_item else None,
            'cup_size': self.cup_size,
            'cup_size_text': CUP_SIZE_MAP.get(self.cup_size, self.cup_size),
            'sugar_level': self.sugar_level,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': round(self.subtotal, 2),
            'bean_grams_used': self.bean_grams_used
        }
