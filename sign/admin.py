from django.contrib import admin
from sign.models import apis
import xlrd, requests
from django.contrib import messages


admin.site.site_header = 'EHSY测试平台'
admin.site.site_title = 'EHSY测试平台'


def api_test(adminmodel, request, queryset):
    tips = []  # 返回信息
    flag = True     # 标志messages.error还是messages.success
    for q in queryset:
        p = 0       # 成功的case数量
        f = 0       # 失败的case数量
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
                params = eval(params)   # excel表中的字符串转换为字典
                r = requests.post(url, data=params)
            if method == 'get':
                params = eval(params)
                r = requests.get(url, params=params)
            if method != 'post' and method != 'get':
                raise ('Method填写错误')
            result = r.json()
            if result['message'] == message_assert:
                p += 1
            else:
                f += 1
                rows_fail.append(str(row+1))
        tips.append({'URL': q.address, '成功': p, '失败': f, '失败行数': (','.join(rows_fail) or '无')})
        if f != 0:
            flag = False
    if flag:
        messages.add_message(request, messages.SUCCESS, tips)
    else:
        messages.add_message(request, messages.ERROR, tips)
api_test.short_description = "执行测试"

"""
class SiteForm(forms.ModelForm):

    class Meta:
        forms.model = apis
        widgets = {
            'address': forms.TextInput(),
            'method': forms.TextInput(),

        }
"""


class display_apis(admin.ModelAdmin):
    list_display = ['id', 'name', 'address', 'method', 'params', 'create_time', 'status', 'files']
    search_fields = ['name', 'address']    # 搜索栏
    list_filter = ['status']    # 过滤器
    actions = [api_test]
    list_display_links = ['name']


admin.site.register(apis, display_apis)

