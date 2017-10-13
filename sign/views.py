# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from sign.models import apis
import requests, xlrd, json, os
from django.contrib import messages
from sign.test_tools import TestTools


def index(request):
    api_list = apis.objects.all()
    return render(request, 'index.html', {'api_list': api_list})


def api_detail(request):
    url = request.path
    loc_start = url.rindex('_')+1
    id = url[loc_start:]
    api = apis.objects.get(id=id)
    params_list = (api.params.strip()).split(',')
    return render(request, 'api_detail.html', {'api': api, 'params': params_list})


def run_test(request):
    id = request.POST.getlist('run_button')  # 取得的是列表
    api = apis.objects.get(id=id[0])
    method = api.method.lower()
    url = api.address
    test_data = request.POST.copy()
    test_data.pop('run_button')  # 只留下输入框填写的数据，去掉带过来的id值
    if method == 'post':
        r = requests.post(url, data=test_data)
    if method == 'get':
        r = requests.get(url, data=test_data)
    result = r.json()
    if result['mark'] == '0':
        messages.success(request, result['message'])
    if result['mark'] != '0':
        messages.error(request, result['message'])
    return render(request, 'api_detail.html', {'api': api, 'test_data': test_data})


def upload_case(request):
    return render(request, 'upload_case.html',)


def batch_test(request):
    if request.method == "POST":    # 请求方法为POST时，进行处理
        myFile =request.FILES.get("myfile", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            messages.error(request, "no files for upload!")
            return render(request, 'upload_case.html')
        destination = open(os.path.join("./case", myFile.name), 'wb+')    # 打开特定的文件进行二进制的写操作
        for chunk in myFile.chunks():      # 分块写入文件
            destination.write(chunk)
        flag = True  # 标志是否有用例失败
        p = 0
        f = 0  # 失败的case数量
        rows_fail = []
        fail_reason = []
        file = './case/'+myFile.name
        data = xlrd.open_workbook(file)
        table = data.sheet_by_index(0)
        rows = table.nrows
        for row in range(1, rows):
            excel_data = table.row_values(row)
            url = excel_data[2]
            method = excel_data[3].lower()
            params = excel_data[4]
            message_assert = excel_data[5].strip()
            if method == 'post':
                params = eval(params)    # excel表中的字符串转换为字典
                r = requests.post(url, data=params)
            if method == 'get':
                params = eval(params)
                r = requests.get(url, params=params)
            if method != 'post' and method != 'get':
                messages.error(request, 'Method填写错误')
                return render(request, 'upload_case.html')
            result = r.json()
            print(result['message'])
            if result['message'] == message_assert:
                p += 1
            else:
                f += 1
                rows_fail.append(str(row + 1))
                fail_reason.append(result['message'])
        tips = {'成功': p, '失败': f, '失败行数': (','.join(rows_fail) or '无'), '失败原因': (','.join(fail_reason) or '无')}
        if f != 0:
            flag = False
        if flag:
            messages.success(request, tips)
            return render(request, 'upload_case.html')
        else:
            messages.error(request, tips)
            return render(request, 'upload_case.html')


def test_tools(request):
    return render(request, 'test_tools.html')


def tools_button(request):
    env = request.POST.get('environment')
    so_value = request.POST.get('so_value', '')
    num = request.POST.get('invoice_num', '')
    tt = TestTools(env, so_value, num)   # TestTools类实例
    action = request.POST.get('button')
    if env == 'staging':
        env_b = 'test'   # env_b标志另一个测试环境
    elif env == 'test':
        env_b = 'staging'
    # if so_value == '':
    #     messages.error(request, '请输入SO单号')
    #     return render(request, 'test_tools.html', {'so_value': so_value, 'env': env, 'env_b': env_b})
    if action == '财务收款':
        result = tt.order_payed()
    if action == '确认订单':
        result = tt.order_confirm()
    if action == '生成PO':
        result = tt.create_po()
    if action == '确认PO':
        result = tt.confirm_po()
        messages.success(request, result)
        return render(request, 'test_tools.html', {'so_value': so_value, 'env': env, 'env_b': env_b, 'invoice_value': num})
    if action == '非直发转直发':
        result = tt.po_change_to_zhifa()
    if action == '直发转非直发':
        result = tt.po_change_to_feizhifa()
    if action == '供应商确认':
        result = tt.supplier_confirm()
    if action == 'PO发货':
        result = tt.po_send()
    if action == 'SO开票':
        result = tt.so_invoice()
        if result == 'error':
            messages.error(request, 'Error')
            return render(request, 'test_tools.html', {'so_value': so_value, 'env': env, 'env_b': env_b, 'invoice_value': num})
        else:
            messages.success(request, result)
            return render(request, 'test_tools.html', {'so_value': so_value, 'env': env, 'env_b': env_b, 'invoice_value': num})

    if result['mark'] == '0':   # 接口返回mark为0表示成功
        messages.success(request, result['message'])
        return render(request, 'test_tools.html', {'so_value': so_value, 'env': env, 'env_b': env_b, 'invoice_value': num})
    if result['mark'] != '0':
        messages.error(request, result['message'])
        return render(request, 'test_tools.html', {'so_value': so_value, 'env': env, 'env_b': env_b, 'invoice_value': num})



