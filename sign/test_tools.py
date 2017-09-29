import requests
import psycopg2
import time
from django.shortcuts import render
from django.contrib import messages

def test_tools(request):
    return render(request, 'test_tools.html')


def order_payed(order_id):
    url = 'http://oc-staging.ehsy.com/orderCenter/payed'
    data = {'orderId': order_id, 'payWay': '0'}
    r = requests.post(url, data=data)
    result = r.json()
    print(result)


def order_confirm(order_id):
    url = 'http://oc-staging.ehsy.com/orderCenter/confirmOrder'
    data = {"orderId": order_id}
    r = requests.post(url, data=data)
    result = r.json()
    print(result)


def invoice(request):
    num = request.POST.get('num', '')
    if num == '':
        messages.error(request, '请输入发票编号')
        return render(request, 'test_tools.html')
    connection = psycopg2.connect(
        database="odoo-staging", user="openerp", password="openerp2016", host="118.178.133.107", port="5432"
    )
    try:
        cur = connection.cursor()
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        cur.execute("update account_invoice_apply set invoiced_num='123456789', name='123456789', invoiced_date='" + now_time + "', state = 'done' where num = '"+num+"'")
        connection.commit()
    except Exception:
        return 'Error'

    else:
        return '受影响的行数： ' + str(cur.rowcount)