from django.http import JsonResponse
from sign.models import Event, Guest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import time


# 添加发布会接口
def add_event(request):
    eid = request.POST.get('eid', '')
    name = request.POST.get('name', '')
    limit = request.POST.get('limit', '')
    status = request.POST.get('status', '')
    address = request.POST.get('address', '')
    start_time = request.POST.get('start_time', '')
    if not (eid and name and limit and address and start_time):
        return JsonResponse({'status': 10021, 'message': 'parameter error'})
    result = Event.objects.filter(id=eid)
    if result:
        return JsonResponse({'status': 10022, 'message': 'event id already exists'})
    result = Event.objects.filter(name=name)
    if result:
        return JsonResponse({'status': 10023, 'message': 'event name already exists'})
    if not status:
        status = 1
    try:
        Event.objects.create(id=eid, name=name, limit=limit, status=status, address=address, start_time=start_time)
    except ValidationError:
        error = 'start_time format error. It must be in YYYY-MM-DD HH:MM:SS format.'
        return JsonResponse({'status': 10024, 'message': error})
    return JsonResponse({'status': '200', 'message': 'add event success'})


# 查询发布会接口
def get_event_list(request):
    eid = request.GET.get('eid', '')
    name = request.GET.get('name', '')
    if eid == '' and name == '':
        return JsonResponse({'status': 10021, 'message': 'parameter error'})
    if eid != '':
        event = {}
        try:
            result = Event.objects.get(id=eid)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})
        else:
            event['name'] = result.name
            event['limit'] = result.limit
            event['status'] = result.status
            event['address'] = result.address
            event['start_time'] = result.start_time
            return JsonResponse({'status': 200, 'message': 'success', 'data': event})
    if name != '':
        event = {}
        try:
            results = Event.objects.get(name__contains=name)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})
        else:
            for result in results:
                event['name'] = result.name
                event['limit'] = result.limit
                event['status'] = result.status
                event['address'] = result.address
                event['start_time'] = result.start_time
                return JsonResponse({'status': 200, 'message': 'success', 'data': event})


# 添加嘉宾接口
def add_guest(request):
    eid = request.POST.get('eid', '')  # 关联发布会id
    realname = request.POST.get('realname', '')  # 姓名
    phone = request.POST.get('phone', '')  # 手机号
    email = request.POST.get('email', '')  # 邮箱

    if eid == '' or realname == '' or phone == '':
        return JsonResponse({'status': 10021, 'message': 'parameter error'})

    result = Event.objects.filter(id=eid)
    if not result:
        return JsonResponse({'status': 10022, 'message': 'event id null'})

    result = Event.objects.get(id=eid).status
    if not result:
        return JsonResponse({'status': 10023, 'message': 'event status is not available'})

    event_limit = Event.objects.get(id=eid).limit  # 发布会限制人数
    guest_limit = Guest.objects.filter(event_id=eid)  # 发布会已添加的嘉宾数

    if len(guest_limit) >= event_limit:
        return JsonResponse({'status': 10024, 'message': 'event number is full'})

    event_time = Event.objects.get(id=eid).start_time  # 发布会时间
    timeArray = time.strptime(str(event_time), "%Y-%m-%d %H:%M:%S")
    e_time = int(time.mktime(timeArray))

    now_time = str(time.time())  # 当前时间
    ntime = now_time.split(".")[0]
    n_time = int(ntime)

    if n_time >= e_time:
        return JsonResponse({'status': 10025, 'message': 'event has started'})

    try:
        Guest.objects.create(realname=realname, phone=int(phone), email=email, sign=0, event_id=int(eid))
    except IntegrityError:
        return JsonResponse({'status': 10026, 'message': 'the event guest phone number repeat'})

    return JsonResponse({'status': 200, 'message': 'add guest success'})


# 查询嘉宾接口
def get_guest_list(request):
    eid = request.GET.get('eid', '')
    phone = request.GET.get('phone', '')
    if eid == '':
        return JsonResponse({'status': '10021', 'message': 'eid cannot be empty'})
    elif phone == '':
        datas = []
        results = Guest.objects.filter(event_id=eid)
        if results:
            for r in results:
                guest = {}
                guest['realname'] = r.realname
                guest['phone'] = r.phone
                guest['email'] = r.email
                guest['sign'] = r.sign
                guest['create_time'] = r.create_time
                datas.append(guest)
            return JsonResponse({'status': 200, 'message': 'success', 'datas': datas})
        else:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})
    else:
        datas = []
        results = Guest.objects.filter(event_id=eid, phone=phone)
        if results:
            for r in results:
                guest = {}
                guest['realname'] = r.realname
                guest['phone'] = r.phone
                guest['email'] = r.email
                guest['sign'] = r.sign
                guest['create_time'] = r.create_time
                datas.append(guest)
            return JsonResponse({'status': 200, 'message': 'success', 'datas': datas})
        else:
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})


# 用户签到接口
def user_sign(request):
    eid = request.POST.get('eid', '')       # 发布会id
    phone = request.POST.get('phone', '')   # 嘉宾手机号

    if eid == '' or phone == '':
        return JsonResponse({'status': 10021, 'message': 'parameter error'})

    result = Event.objects.filter(id=eid)
    if not result:
        return JsonResponse({'status': 10022, 'message': 'event id null'})

    result = Event.objects.get(id=eid).status
    if not result:
        return JsonResponse({'status': 10023, 'message': 'event status is not available'})

    event_time = Event.objects.get(id=eid).start_time     # 发布会时间
    timeArray = time.strptime(str(event_time), "%Y-%m-%d %H:%M:%S")
    e_time = int(time.mktime(timeArray))

    now_time = str(time.time())          # 当前时间
    ntime = now_time.split(".")[0]
    n_time = int(ntime)

    if n_time >= e_time:
        return JsonResponse({'status': 10024, 'message': 'event has started'})

    result = Guest.objects.filter(phone=phone)
    if not result:
        return JsonResponse({'status': 10025, 'message': 'user phone null'})

    result = Guest.objects.filter(phone=phone, event_id=eid)
    if not result:
        return JsonResponse({'status': 10026, 'message': 'user did not participate in the conference'})

    result = Guest.objects.get(event_id=eid, phone=phone).sign
    if result:
        return JsonResponse({'status': 10027, 'message': 'user has sign in'})
    else:
        Guest.objects.filter(phone=phone).update(sign='1')
        return JsonResponse({'status': 200, 'message': 'sign success'})

