import requests
import psycopg2, pymysql, json
import time
from django.shortcuts import render
from django.contrib import messages


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
        self.num = num      # 传入的发票编

    def login(self):
        url = 'http://passport-' + self.env + '.ehsy.com/uc/user/login.action'
        data = {'login_name': '18751551645', 'login_password': '111qqq', 'terminal_type': 'pc',
                'isRememberCount': 'false'}
        r = requests.post(url, data=data)
        result = r.json()
        token = result['sys']['token']
        print(token)
        return result

    def create_order(self, token):
        """生成订单"""
        url1 = 'http://oc-' + self.env + '.ehsy.com/cart/add'
        data1 = [{'skuCode':'MVX456','quantity':'2'}, {'skuCode':'MAB243','quantity':'2'}]
        data = {'token': token, 'data': data1}
        r1 = requests.post(url1, json=data)
        result1 = r1.json()
        url2 = 'http://oc-' + self.env + '.ehsy.com/order/createOrderNew'
        addedInvoices = [{"bank": "招商银行", "bankAccount": "2343345466", "hasAdminAuth": "0", "invoiceId": "10008247487",
                         'isDefault': "0",  "regAdd": "金科路1122号", "regTel": "18751551645", "selected": 'true',"subType":'',
                          "taxpayerCode": "123456789009876123", "title": "测试账号公司tina", "type":"2", "typeCompany":'false',
                          'typeDesc': '增值税发票'}]
        deliverAdds = [{ "address":"江苏省南京市高淳县新街口", "addressId": "10008284154", "addressUserType":"1", "areaId":"220",
                         "city":"南京市", "company":"测试账号", "detailedAddress":"新街口", "district":"高淳县",
                         "email":"233213@qq.com", "hasAdminAuth":"0", "isDefault":"1", "mobile":"18751551645", "name":"史佐兄",
                         "postcode":"900414", "province":"江苏省", "selected":'true', "tel":"021-33338888"}]
        invoicesAdds = [{"address":"上海市上海市浦东新区金科路", "addressId":"10008284152", "addressUserType":"1", "areaId":"321",
                         "city":"上海市", "company":"测试账号电子公司", "detailedAddress":"金科路", "district":"浦东新区",
                         "email":"", "hasAdminAuth":"0", "isDefault":"1", "mobile":"18751551645", "name":"史佐兄",
                         "postcode": "900414","province": "上海市", "selected": 'true', "tel":""}]
        data = {'token': token, 'addedInvoices': addedInvoices, 'deliverAdds': deliverAdds, 'deliveryTimeType': '0',
                'invoicesAdds': invoicesAdds, 'payType': '0', 'createFrom': 'pc'}
        r2 = requests.post(url2, json=data)
        result2 = r2.json()  #字典格式
        # result = json.dumps(result2)  #json格式
        # orderId = result2['data']['orderId']
        return result2

    # def order_detail(self, token, orderId):
    def order_detail(self, token):
        url = 'http://oc-' + self.env + '.ehsy.com/order/getInfo'
        data = {'token': token, 'orderId':self.order_id, 'createTimeFrom':'2017-02-15', 'createTimeTo':'2017-08-15'}
        r = requests.post(url,data)
        result = r.json()
        return result

    def order_cancel(self):
        """查询so中可取消sku"""
        url = 'http://oc-' + self.env + '.ehsy.com/orderCenter/cancel'
        data = {'orderId': self.order_id,'userId':'508110571'}
        r = requests.post(url, data)
        result = r.json()
        return result

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
        cursor.execute("select pu_id, sku_code, quantity from oc.purchase_order_unit where order_id='SO150900275843271000'")
        query_dict = cursor.fetchall()
        print(query_dict)
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
        if self.env == 'staging':
            connection = psycopg2.connect(
                database="odoo-staging", user="openerp", password="openerp2016", host="118.178.133.107", port="5432"
            )
        if self.env == 'test':
            connection = psycopg2.connect(
                database="odoo-test", user="openerp", password="ehsy_erp", host="118.178.238.29", port="5432"
            )
        try:
            cur = connection.cursor()
            now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            cur.execute("update account_invoice_apply set invoiced_num='123456789', name='123456789', invoiced_date='" + now_time + "', state = 'done' where num = '"+self.num+"'")
            connection.commit()
        except Exception:
            return 'error'

        else:
            result = '受影响的行数：' + str(cur.rowcount)
            return result
