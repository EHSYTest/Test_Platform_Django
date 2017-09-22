# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponse
from sign.models import apis
import requests, xlrd, json
from  django.contrib import messages


def index(request):
    api_list = apis.objects.all()
    return render(request, 'sign_index.html', {'api_list': api_list})


def batch_test(request):
    api_list = apis.objects.all()
    tips = []  # 返回信息
    flag = True  # 标志是否有用例失败
    id_list = request.POST.getlist('checkbox_id')
    for id in id_list:
        q = apis.objects.get(id=id)
        if q.files == '无':
            return render(request, 'sign_index.html', {'api_list': api_list, 'message': False, 'result': '请添加TestCase'})
        p = 0  # 成功的case数量
        f = 0  # 失败的case数量
        rows_fail = []
        file = str(q.files)
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
                return render(request, 'sign_index.html', {'api_list': api_list, 'message': False, 'result': 'Method填写错误'})
            result = r.json()
            print(result['message'])
            if result['message'] == message_assert:
                p += 1
            else:
                f += 1
                rows_fail.append(str(row + 1))
        tips.append({'URL': url, '成功': p, '失败': f, '失败行数': (','.join(rows_fail) or '无')})
        if f != 0:
            flag = False
    if flag:
        messages.success(request, tips)
        return render(request, 'sign_index.html', {'api_list': api_list, 'message': True, 'result': tips})
    else:
        messages.error(request, tips)
        return render(request, 'sign_index.html', {'api_list': api_list, 'message': False, 'result': tips})


def api_detail(request):
    url = request.path
    loc_start = url.rindex('_')+1
    id = url[loc_start:]
    print(id)
    api = apis.objects.get(id=id)
    params_list = (api.params.strip()).split(',')
    return render(request, 'api_detail.html', {'api': api, 'params': params_list})


def run_test(request):
    id = request.POST.getlist('run_button')  # 取得的是列表
    api = apis.objects.get(id=id)
    method = api.method
    url = api.address
    params_list = list(request.POST.keys())
    params_list.pop()   # 去掉最后一个'run_button键'
    params = {}
    for param in params_list:
        value = request.POST.get(param)  # param为键，value为值
        params[param] = value
    r = requests.post(url, data=params)
    result = r.json()
    messages.error(request, tips)
    return render(request, 'sign_index.html', {'api_list': api_list, 'message': False, 'result': tips})
