import requests, json

url = 'http://oc-staging.ehsy.com/supplier/purchaseorder/deliver'
delivery_list = [
    {
        'id': 'PU150535436477793264',
        'orderId': 'SO150167110713833000',
        'skuCode': 'LAB263',
        'productName': '经济洗瓶，低密度聚乙烯瓶体，聚丙烯螺旋物吸管，1000ml容量',
        'sendQuantity': '25.00',
        'unit': '个'
    }
]

operateData = {
    "purOrderId": 'PO150537917818894966',
    "supplierId": '8174',
    "sendNo": "100023456",
    "sendCompanyName": "韵达快递",
    "deliveryList": delivery_list
}
print(operateData)
r = requests.post(url, data={'operateData': json.dumps(operateData)})
result = r.json()
print(result)
