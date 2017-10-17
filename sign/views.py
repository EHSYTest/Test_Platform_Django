# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from sign.models import apis
import requests, xlrd, json, os
from django.contrib import messages
from sign.test_tools import TestTools


def index(request):
    """index首页"""
    api_list = apis.objects.all()
    return render(request, 'index.html', {'api_list': api_list})


def api_detail(request):
    """接口详情页"""
    url = request.path   # 获取当前地址url
    loc_start = url.rindex('_')+1    # 从url中获取接口ID的索引位置
    id = url[loc_start:]            # 获取接口ID
    api = apis.objects.get(id=id)
    params_list = (api.params.strip()).split(',')   # 将数据库中params字段值拆分成列表，在HTML上打印出来
    return render(request, 'api_detail.html', {'api': api, 'params': params_list})


def run_test(request):
    """接口详情-单个接口调用"""
    id = request.POST.getlist('run_button')  # 获取run_button的value值（即接口ID），取得的是列表
    api = apis.objects.get(id=id[0])
    method = api.method.lower()
    url = api.address
    test_data = request.POST.copy()         # copy request请求对象（因为原request请求对象不可更改）
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
    return render(request, 'api_detail.html', {'api': api, 'test_data': test_data})     # 输入框数据原样返回


def upload_case(request):
    """批量测试HTML对应view函数"""
    return render(request, 'upload_case.html',)


def batch_test(request):
    """批量测试按钮触发的动作函数"""
    if request.method == "POST":    # 请求方法为POST时，进行处理
        myFile =request.FILES.get("myfile", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            messages.error(request, "no files for upload!")
            return render(request, 'upload_case.html')
        destination = open(os.path.join("./case", myFile.name), 'wb+')    # 打开特定的文件进行二进制的写操作
        for chunk in myFile.chunks():      # 分块写入文件
            destination.write(chunk)
        flag = True  # 标志是否有用例失败
        p = 0  # 成功的case数量
        f = 0  # 失败的case数量
        rows_fail = []  # excel中失败行
        fail_reason = []    # 失败原因
        file = './case/'+myFile.name    # 文件路径
        data = xlrd.open_workbook(file)
        table = data.sheet_by_index(0)      # 读取excel sheet页
        rows = table.nrows      # 获取当前sheet页数据行数
        for row in range(1, rows):
            excel_data = table.row_values(row)  # 获取当前行的数据（列表对象）
            url = excel_data[2]
            method = excel_data[3].lower()
            params = excel_data[4]
            message_assert = excel_data[5].strip()      # strip去掉首尾空格
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
            if result['message'] == message_assert:     # 断言
                p += 1
            else:
                f += 1
                rows_fail.append(str(row + 1))
                fail_reason.append(result['message'])
        tips = {'成功': p, '失败': f, '失败行数': (','.join(rows_fail) or '无'), '失败原因': (','.join(fail_reason) or '无')}
        if f != 0:
            flag = False
        if flag:    # 根据flag判断message是success还是error（任意一行失败则为失败）
            messages.success(request, tips)
            return render(request, 'upload_case.html')
        else:
            messages.error(request, tips)
            return render(request, 'upload_case.html')


def test_tools(request):
    """测试工具页HTML对应view函数"""
    return render(request, 'test_tools.html')


def tools_button(request):
    """测试工具页button对应处理函数"""
    env = request.POST.get('environment')   # 获取选择的测试环境
    so_value = request.POST.get('so_value', '')     # 获取输入的SO单号
    num = request.POST.get('invoice_num', '')       # 获取输入的发票编号
    tt = TestTools(env, so_value, num)   # test_tools模块类实例
    action = request.POST.get('button')     # 从button的value值分析所需要进行的操作
    if env == 'staging':
        env_b = 'test'   # env_b标志另一个测试环境（select下拉选项的另一个，为了最终原样返回选择的环境）
    elif env == 'test':
        env_b = 'staging'
    if action == '财务收款':
        result = tt.order_payed()       # test_tools模块对应函数
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
    if result['mark'] != '0':   # 接口返回的mark参数不为'0'则提示错误信息
        messages.error(request, result['message'])
        return render(request, 'test_tools.html', {'so_value': so_value, 'env': env, 'env_b': env_b, 'invoice_value': num})



