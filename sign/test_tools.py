import requests
import psycopg2, pymysql, json
import time
from django.shortcuts import render
from django.contrib import messages
import sys
import datetime
from xmlrpc import client


class TestTools(object):
    def __init__(self, env, order_id, num):
        self.env = env       # 测试环境标志： 1 - staging； 0 - test
        if self.env == 'staging':
            # 连接staging——OC数据库
            self.connection = pymysql.connect(
                host='118.178.189.137',
                user='ehsy_pc',
                password='ehsy2016',
                port=3306,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor   # sql查询结果转为字典类型
            )
        elif self.env == 'test':
            # test——OC数据库
            self.connection = pymysql.connect(
                host='118.178.135.2',
                user='root',
                password='ehsy2016',
                port=3306,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor
            )
        self.order_id = order_id        # 传入的SO编号
        self.num = num      # 传入的发票编号

    def order_payed(self):
        """财务收款"""
        url = 'http://oc-' + self.env + '.ehsy.com/orderCenter/payed'
        data = {'orderId': self.order_id, 'payWay': '0'}
        r = requests.post(url, data=data)
        result = r.json()
        return result

    def order_confirm(self):
        """SO确认"""
        url = 'http://oc-' + self.env + '.ehsy.com/orderCenter/confirmOrder'
        data = {"orderId": self.order_id}
        r = requests.post(url, data=data)
        result = r.json()
        return result

    def create_po(self):
        """创建PO"""
        cursor = self.connection.cursor()

        # 查SO的所有PU
        cursor.execute("select pu_id, sku_code, quantity from oc.purchase_order_unit where order_id='"+self.order_id+"'")
        query_dict = cursor.fetchall()
        url = 'http://oc-' + self.env + '.ehsy.com/puPoolManage/mergePuList'
        data_data = []

        # 遍历PU，构建接口调用的data参数信息
        for pu in query_dict:
            param = {}
            param['puId'] = pu['pu_id']
            param['skuCode'] = pu['sku_code']
            param['finalBidPrice'] = '100'
            param['QUANTITY'] = str(pu['quantity'])
            data_data.append(param)
        print(data_data)

        # 接口参数赋值
        queryData = {
            "supplierId": "2",
            "userId": "1000",
            "userName": "1000",
            "data": data_data,
            "poFinalTransferAmt": "20",
            "payType": "1",
            "supplierWarehouse": "C01"
        }

        # 接口调用
        r = requests.post(url, data={'queryData': json.dumps(queryData)})
        result = r.json()
        print(result)
        return result

    def confirm_po(self):
        """确认PO"""

        # 更改数据库purchase_order表po_status字段值
        cursor = self.connection.cursor()
        cursor.execute("update oc.purchase_order set po_status =0 where order_id = '"+self.order_id+"'")
        self.connection.commit()
        row_count = cursor.rowcount
        return '更新行数:'+str(row_count)

    def po_change_to_zhifa(self):
        """PO单非直发转直发"""
        cursor = self.connection.cursor()
        cursor.execute("select pur_order_id from oc.purchase_order where order_id= '"+self.order_id+"'")
        po = cursor.fetchall()[0]['pur_order_id']   # 获取PO单号
        url = 'http://oc-' + self.env + '.ehsy.com/admin/purchaseorder/poChangeNonStopFlag'
        r = requests.post(url, data={
            'purOrderId': po, 'nonStopFlag': '1'})
        result = r.json()
        return result

    def po_change_to_feizhifa(self):
        """直发转非直发"""
        cursor = self.connection.cursor()
        # 获取PO单号
        cursor.execute("select pur_order_id from oc.purchase_order where order_id= '" + self.order_id + "'")
        po = cursor.fetchall()[0]['pur_order_id']
        url = 'http://oc-' + self.env + '.ehsy.com/admin/purchaseorder/poChangeNonStopFlag'
        r = requests.post(url, data={
            'purOrderId': po, 'nonStopFlag': '0', 'warehouseCode': 'C01'})
        result = r.json()
        return result

    def supplier_confirm(self):
        """供应商确认"""
        cursor = self.connection.cursor()
        cursor.execute("select pur_order_id,supplier_id from oc.purchase_order where order_id= '" + self.order_id + "'")
        sql_result = cursor.fetchall()
        po = sql_result[0]['pur_order_id']
        supplier_id = str(sql_result[0]['supplier_id'])
        url = 'http://oc-' + self.env + '.ehsy.com/supplier/purchaseorder/confirm'
        operateData = {
            'purOrderId': po,
            'supplierId': supplier_id
        }
        r = requests.post(url, data={'operateData': json.dumps(operateData)})
        result = r.json()
        return result

    def po_send(self):
        """PO发货（全部发货）"""
        cursor = self.connection.cursor()
        cursor.execute("select id,pur_order_id,sku_code,quantity,product_name,unit from oc.purchase_order_unit where order_id='"+self.order_id+"'")
        query_dict1 = cursor.fetchall()
        cursor.execute("select pur_order_id, supplier_id from oc.purchase_order where order_id='"+self.order_id+"'")
        query_dict2 = cursor.fetchall()
        deliveryList = []   # 发货详情参数
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
        url = 'http://oc-' + self.env + '.ehsy.com/supplier/purchaseorder/deliver'
        operateData = {
            "purOrderId": po_id,
            "supplierId": supplier_id,
            "sendNo": "100023456",
            "sendCompanyName": "韵达快递",
            "deliveryList": deliveryList
        }
        r = requests.post(url, data={'operateData': json.dumps(operateData)})   # 接口为key:json格式
        result = r.json()
        return result

    def so_invoice(self):
        """SO开票-Odoo"""
        dbname = 'odoo-staging'
        usr = 'admin'
        pwd = 'admin'
        oe_ip = '118.178.133.107:8069'

        try:
            sock_common = client.ServerProxy('http://' + oe_ip + '/xmlrpc/common')
            uid = sock_common.login(dbname, usr, pwd)

            sock = client.ServerProxy('http://' + oe_ip + '/xmlrpc/object')
            a = sock.execute(dbname, uid, pwd, 'account.invoice.apply', 'search_read',
                             [('num', '=', self.num), ('state', '!=', 'cancel')])
            for i in a:
                sock.execute(dbname, uid, pwd, 'account.invoice.apply', 'write', i['id'],
                             {'state': 'done', 'invoiced_num': '123456789', 'name': '123456789',
                              'invoiced_date': datetime.datetime.now().strftime('%Y -%m-%d %H:%M:%S')})
        except Exception:
            return 'error'
        else:
            return 'Success'
