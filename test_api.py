import requests
import json

BASE_URL = 'http://localhost:5000/api'

def print_response(title, response):
    print(f'\n{"="*60}')
    print(f'📌 {title}')
    print(f'   URL: {response.request.url}')
    print(f'   Method: {response.request.method}')
    print(f'   Status: {response.status_code}')
    print(f'   Response:')
    print(json.dumps(response.json(), ensure_ascii=False, indent=3))

def test():
    print('🚀 开始测试咖啡店订单与库存管理 API\n')

    # 1. 测试菜单管理
    print('\n' + '='*60)
    print('【第一部分：菜单管理模块测试】')

    r = requests.get(f'{BASE_URL}/menu')
    print_response('1.1 获取菜单列表', r)
    menu_items = r.json()['data']

    if menu_items:
        item_id = menu_items[0]['id']
        r = requests.get(f'{BASE_URL}/menu/{item_id}')
        print_response(f'1.2 获取单个菜单项 (ID={item_id})', r)

    new_item = {
        'name': '卡布奇诺',
        'category': '经典咖啡',
        'bean_id': 1,
        'bean_grams_medium': 18,
        'bean_grams_large': 25,
        'price_medium': 26,
        'price_large': 32
    }
    r = requests.post(f'{BASE_URL}/menu', json=new_item)
    print_response('1.3 新增菜单项 (卡布奇诺)', r)

    r = requests.put(f'{BASE_URL}/menu/5', json={'price_medium': 28})
    print_response('1.4 更新菜单项 (修改价格)', r)

    # 2. 测试库存查询
    print('\n' + '='*60)
    print('【第二部分：库存查询模块测试】')

    r = requests.get(f'{BASE_URL}/inventory')
    print_response('2.1 获取全部库存', r)

    r = requests.get(f'{BASE_URL}/inventory/low-stock')
    print_response('2.2 获取低库存预警', r)

    # 3. 测试下单模块 - 核心功能
    print('\n' + '='*60)
    print('【第三部分：下单模块测试 (自动扣库存)】')

    order_data = {
        'customer_name': '张先生',
        'items': [
            {
                'menu_item_id': 2,
                'cup_size': 'medium',
                'sugar_level': '50%',
                'quantity': 2
            },
            {
                'menu_item_id': 1,
                'cup_size': 'large',
                'sugar_level': '0%',
                'quantity': 1
            }
        ]
    }
    print('\n   📝 订单详情:')
    print(f'   - 2杯中杯拿铁 (18g豆/杯) = 36g 意式拼配豆')
    print(f'   - 1杯大杯美式 (25g豆/杯) = 25g 意式拼配豆')
    print(f'   - 合计扣减: 61g 意式拼配豆')

    r = requests.post(f'{BASE_URL}/orders', json=order_data)
    print_response('3.1 创建订单 (2杯拿铁+1杯美式)', r)

    order_id = r.json()['data']['id']

    r = requests.get(f'{BASE_URL}/inventory')
    print_response('3.2 下单后查看库存 (意式拼配豆应减少61g)', r)

    # 4. 测试订单状态推进
    print('\n' + '='*60)
    print('【第四部分：订单状态流转测试】')

    print('\n   🔄 状态流转顺序: 待支付 → 已支付 → 制作中 → 完成 → 已取单')

    for i in range(5):
        r = requests.post(f'{BASE_URL}/orders/{order_id}/next-status')
        if r.status_code == 200:
            current_status = r.json()['data']['status_text']
            print(f'   第{i+1}次推进 → {current_status}')
        else:
            print(f'   第{i+1}次推进 → {r.json()["message"]}')
            break

    print_response('4.1 订单完成全部状态流转后详情', r)

    # 5. 测试跳状态错误
    order_data2 = {
        'customer_name': '李先生',
        'items': [
            {'menu_item_id': 3, 'cup_size': 'medium', 'sugar_level': '0%', 'quantity': 1}
        ]
    }
    r = requests.post(f'{BASE_URL}/orders', json=order_data2)
    order_id2 = r.json()['data']['id']

    r = requests.put(f'{BASE_URL}/orders/{order_id2}/status', json={'status': 'making'})
    print_response('5.1 测试跳状态错误 (待支付→制作中)', r)

    # 6. 测试库存预警场景
    print('\n' + '='*60)
    print('【第五部分：低库存预警测试】')

    print('\n   📦 把意式拼配豆库存调到接近阈值(500g)，然后下大单触发预警')
    requests.put(f'{BASE_URL}/inventory/1', json={'stock_grams': 550})

    big_order = {
        'customer_name': '王总',
        'items': [
            {'menu_item_id': 2, 'cup_size': 'large', 'sugar_level': '30%', 'quantity': 5}
        ]
    }
    print(f'   - 5杯大杯拿铁 (25g豆/杯) = 125g 意式拼配豆')
    print(f'   - 当前库存550g - 125g = 425g < 阈值500g，应触发预警')

    r = requests.post(f'{BASE_URL}/orders', json=big_order)
    print_response('6.1 下单触发低库存预警', r)

    r = requests.get(f'{BASE_URL}/inventory/low-stock')
    print_response('6.2 查看低库存列表 (应有意式拼配豆)', r)

    # 7. 测试补货
    r = requests.post(f'{BASE_URL}/inventory/1/restock', json={'add_grams': 1000})
    print_response('7.1 补货 1000g 意式拼配豆', r)

    r = requests.get(f'{BASE_URL}/inventory/low-stock')
    print_response('7.2 补货后查看低库存 (应无预警)', r)

    # 8. 测试库存不足场景
    print('\n' + '='*60)
    print('【第六部分：库存不足测试】')

    requests.put(f'{BASE_URL}/inventory/2', json={'stock_grams': 50})

    fail_order = {
        'customer_name': '测试用户',
        'items': [
            {'menu_item_id': 3, 'cup_size': 'large', 'sugar_level': '0%', 'quantity': 10}
        ]
    }
    print(f'   - 10杯大手冲耶加 (20g豆/杯) = 200g，库存仅50g，应失败')

    r = requests.post(f'{BASE_URL}/orders', json=fail_order)
    print_response('8.1 测试库存不足下单失败', r)

    # 9. 测试删除菜单项
    r = requests.delete(f'{BASE_URL}/menu/5')
    print_response('9.1 删除菜单项 (卡布奇诺)', r)

    print('\n' + '='*60)
    print('✅ 所有测试完成！')
    print('='*60)

if __name__ == '__main__':
    test()
