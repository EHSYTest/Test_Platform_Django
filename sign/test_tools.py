import requests
import psycopg2, pymysql, json
import time
from django.shortcuts import render
from django.contrib import messages


class TestTools(object):
    def __init__(self, env, order_id):
        self.env = env       # 测试环境标志： 1 - staging； 0 - test
        if self.env == 'staging':
            self.connection = pymysql.connect(
                host='118.178.189.137',
                user='ehsy_pc',
                password='ehsy2016',
                port=3306,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor   # sql查询结果转为字典类型
            )
        elif self.env == 'test':
            self.connection = pymysql.connect(
                host='118.178.135.2',
                user='root',
                password='ehsy2016',
                port=3306,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor
            )
        self.order_id = order_id

    def order_payed(self):
        url = 'http://oc-' + self.env + '.ehsy.com/orderCenter/payed'
        data = {'orderId': self.order_id, 'payWay': '0'}
        r = requests.post(url, data=data)
        result = r.json()
        return result

    def order_confirm(self):
        url = 'http://oc-' + self.env + '.ehsy.com/orderCenter/confirmOrder'
        data = {"orderId": self.order_id}
        r = requests.post(url, data=data)
        result = r.json()
        return result

    def create_po(self):
        cursor = self.connection.cursor()
        cursor.execute("select pu_id, sku_code, quantity from oc.purchase_order_unit where order_id='"+self.order_id+"'")
        query_dict = cursor.fetchall()
        url = 'http://oc-' + self.env + '.ehsy.com/puPoolManage/mergePuList'
        data_data = []
        for pu in query_dict:
            param = {}
            param['puId'] = pu['pu_id']
            param['skuCode'] = pu['sku_code']
            param['finalBidPrice'] = '100'
            param['QUANTITY'] = str(pu['quantity'])
            data_data.append(param)
        print(data_data)
        queryData = {
            "supplierId": "2",
            "userId": "1000",
            "userName": "1000",
            "data": data_data,
            "poFinalTransferAmt": "20",
            "payType": "1",
            "supplierWarehouse": "C01"
        }
        r = requests.post(url, data={'queryData': json.dumps(queryData)})
        result = r.json()
        print(result)
        return result

    def confirm_po(self):
        cursor = self.connection.cursor()
        cursor.execute("update oc.purchase_order set po_status =0 where order_id = '"+self.order_id+"'")
        self.connection.commit()
        row_count = cursor.rowcount
        return '更新行数:'+str(row_count)

    def po_change_to_zhifa(self):
        cursor = self.connection.cursor()
        cursor.execute("select pur_order_id from oc.purchase_order where order_id= '"+self.order_id+"'")
        po = cursor.fetchall()[0]['pur_order_id']
        url = 'http://oc-' + self.env + '.ehsy.com/admin/purchaseorder/poChangeNonStopFlag'
        r = requests.post(url, data={
            'purOrderId': po, 'nonStopFlag': '1'})
        result = r.json()
        return result

    def po_change_to_feizhifa(self):
        cursor = self.connection.cursor()
        cursor.execute("select pur_order_id from oc.purchase_order where order_id= '" + self.order_id + "'")
        po = cursor.fetchall()[0]['pur_order_id']
        url = 'http://oc-' + self.env + '.ehsy.com/admin/purchaseorder/poChangeNonStopFlag'
        r = requests.post(url, data={
            'purOrderId': po, 'nonStopFlag': '0', 'warehouseCode': 'C01'})
        result = r.json()
        return result

    def supplier_confirm(self):
        cursor = self.connection.cursor()
        cursor.execute("select pur_order_id from oc.purchase_order where order_id= '" + self.order_id + "'")
        po = cursor.fetchall()[0]['pur_order_id']
        url = 'http://oc-' + self.env + '.ehsy.com/supplier/purchaseorder/confirm'
        operateData = {
            'purOrderId': 'PO150667554030163175',
            'supplierId': '2'
        }
        r = requests.post(url, data={'operateData': json.dumps(operateData)})
        result = r.json()
        return result

    def po_send(self):
        cursor = self.connection.cursor()
        cursor.execute("select id,pur_order_id,sku_code,quantity,product_name,unit from oc.purchase_order_unit where order_id='"+self.order_id+"'")
        query_dict1 = cursor.fetchall()
        cursor.execute("select pur_order_id, supplier_id from oc.purchase_order where order_id='"+self.order_id+"'")
        query_dict2 = cursor.fetchall()
        deliveryList = []
        po_id = query_dict2[0]['pur_order_id']
        supplier_id = str(query_dict2[0]['supplier_id'])
        for pu in query_dict1:
            params = {}
            params['id'] = pu['id']
            params['orderId'] = self.order_id
            params['skuCode'] = pu['sku_code']
            params['productName'] = pu['product_name']
            params['sendQuantity'] = str(pu['quantity'])
            params['unit'] = pu['unit']
            deliveryList.append(params)
        print(deliveryList)
        url = 'http://oc-' + self.env + '.ehsy.com/supplier/purchaseorder/deliver'
        operateData = {
            "purOrderId": po_id,
            "supplierId": supplier_id,
            "sendNo": "100023456",
            "sendCompanyName": "韵达快递",
            "deliveryList": deliveryList
        }
        print(operateData)
        r = requests.post(url, data={'operateData': json.dumps(operateData)})
        result = r.json()
        return result



    # def invoice(self):
    #     num = request.POST.get('num', '')
    #     if num == '':
    #         messages.error(request, '请输入发票编号')
    #         return render(request, 'test_tools.html', {'invoice_value': num})
    #     env = request.POST.get('environment')
    #     if env == '1':
    #         connection = psycopg2.connect(
    #             database="odoo-staging", user="openerp", password="openerp2016", host="118.178.133.107", port="5432"
    #         )
    #     if env == '0':
    #         connection = psycopg2.connect(
    #             database="odoo-test", user="openerp", password="ehsy_erp", host="118.178.238.29", port="5432"
    #         )
    #     try:
    #         cur = connection.cursor()
    #         now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    #         cur.execute("update account_invoice_apply set invoiced_num='123456789', name='123456789', invoiced_date='" + now_time + "', state = 'done' where num = '"+num+"'")
    #         connection.commit()
    #     except Exception:
    #         messages.error(request, 'Error')
    #         return render(request, 'test_tools.html', {'invoice_value': num})
    #
    #     else:
    #         messages.success(request, '受影响的行数：' + str(cur.rowcount))
    #         return render(request, 'test_tools.html', {'invoice_value': num})
