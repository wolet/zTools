# Create your views here.

from django.template import RequestContext
from django.http import Http404, HttpResponse
import datetime
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from datetime import date
from django.contrib.auth import authenticate, login, logout
from django.utils import simplejson
from models import *
from string import *
import xlwt
import random , re
import csv


def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return render_to_response(*args, **kwargs)

def main(request):
    return render_to_response('main.html', context_instance = RequestContext(request))

class SupplierDetails:
    item_count = 0
    supplier_name = ""

@login_required
def order(request):
    supNameDetail = ""
    end_date=""
    start_date=""
    counter = 0
    initStartDate = ""
    initEndDate = ""
    if "dateEnd" in request.POST:
        end_date = datetime.datetime.strptime(request.POST['dateEnd'], "%m/%d/%Y")
        initEndDate = request.POST['dateEnd']
    if "dateStart" in request.POST:
        start_date = datetime.datetime.strptime(request.POST['dateStart'], "%m/%d/%Y")
        initStartDate = request.POST['dateStart']
    else:
        initEndDate = datetime.datetime.now()
        initEndDate = initEndDate.strftime("%m/%d/%Y")

        initStartDate = datetime.datetime.now()- datetime.timedelta(days=999)
        orderList = Order.objects.order_by('order_date')
        initStartDate = orderList[0].order_date.strftime("%m/%d/%Y")
#        initStartDate = initStartDate.strftime("%m/%d/%Y")


    if "supname" in request.GET:
       supNameDetail = request.GET["supname"]
    try:
        if start_date != "" and end_date != "":
            ordersAll = Order.objects.filter(order_date__range =[start_date,end_date] )
        else:
            ordersAll = Order.objects.all()
            
        suppliers = list()
        for anOrder in ordersAll:
            if not suppliers.__contains__(anOrder.supplier_name):
                suppliers.append(anOrder.supplier_name)


        supplierIndex = 0
        supplierDetailList = []
        for aSupplier in suppliers:
            if start_date !="" and end_date != "":
                ic = Order.objects.filter(supplier_name=suppliers.__getitem__(supplierIndex),order_date__range =[start_date,end_date]).count()
            else:
                ic = Order.objects.filter(supplier_name=suppliers.__getitem__(supplierIndex)).count()

            sd = SupplierDetails()
            sd.item_count = ic
            sd.supplier_name = suppliers.__getitem__(supplierIndex)
            supplierDetailList.append(sd)
            supplierIndex = supplierIndex + 1

        if supNameDetail == "":
            supNameDetail = "All Suppliers"
            
        return render_to_response('orders.html', {'supplierDetailList' : supplierDetailList,'supNameDetail':supNameDetail,'end_date':end_date,'start_date':start_date,'initStartDate':initStartDate,'initEndDate':initEndDate,'counter':counter},context_instance = RequestContext(request))
    except Order.DoesNotExist:
        raise Http404

def listOrders(request):

    supNameDetail=""
    start_date = ""
    end_date = ""
    initStartDate = ""
    initEndDate = ""
    
    if "supname" in request.GET:
        supNameDetail = request.GET["supname"]
    if "startdate" in request.GET:
        start_date = datetime.datetime.strptime(request.GET['startdate'], "%m/%d/%Y")
        initStartDate = request.GET['startdate']
    if "enddate" in request.GET:
        end_date = datetime.datetime.strptime(request.GET['enddate'], "%m/%d/%Y")
        initEndDate = request.GET['enddate']

    if supNameDetail == "":
        filteredOrders = Order.objects.all()
    else:
        filteredOrders = Order.objects.filter(supplier_name=supNameDetail,order_date__range =[start_date,end_date])

    if request.GET.has_key('page'):
        page = request.GET['page']
    else:
        page = 1

    paginator = Paginator(filteredOrders, 1000)
    try:
        orders = paginator.page(page)
    except (EmptyPage, InvalidPage):
        orders = paginator.page(paginator.num_pages)

    return render_to_response('orderList.html',
            {'orders' : orders,
             'supNameDetail':supNameDetail,
             'endDate':end_date,
             'startDate':start_date,
             'initStartDate':initStartDate,
             'initEndDate':initEndDate,
             },context_instance = RequestContext(request))

def acronym(phrase):
    result = ""
    for word in split(phrase):
        result += word[0].upper()

    return result

def generateTransactionString(supplier_name):


    today = convertDatetimeToString(datetime.datetime.today())
    number = str(random.randint(0,9999))
    #number yerine id, acronym yerine supplier table'dan abbreviation gelecek!
    transaction_string = 'TR'  + today + '-' + acronym(supplier_name) + '-' + number

    return transaction_string

def convertDatetimeToString(o):

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"


    if isinstance(o, datetime.date):
        return o.strftime(DATE_FORMAT)
    elif isinstance(o, datetime.time):
        return o.strftime(TIME_FORMAT)
    elif isinstance(o, datetime.datetime):
        return o.strftime("%s %s" % (DATE_FORMAT, TIME_FORMAT))

def exportExcel(request):
    supNameDetail=""
    start_date = ""
    end_date = ""

    if "supname" in request.GET:
        supNameDetail = request.GET["supname"]
    if "startdate" in request.GET:
        start_date = datetime.datetime.strptime(request.GET['startdate'], "%m/%d/%Y")
    if "enddate" in request.GET:
        end_date = datetime.datetime.strptime(request.GET['enddate'], "%m/%d/%Y")

    if supNameDetail == "" and "transaction_keyword" in request.GET:
        tr_keyword = request.GET['transaction_keyword']
        try :
            given_transaction = Transactions.objects.get(transaction_string = tr_keyword)
            orderTransactionPairs = OrderTransaction.objects.filter(tr_id = given_transaction)
            orders = list()
            for aPair in orderTransactionPairs:
                anOrder = Order.objects.get(pk = aPair.order_id.id)
                orders.append(anOrder)
        except:
            raise Http404
    else:
        orders = Order.objects.filter(supplier_name=supNameDetail,order_date__range =[start_date,end_date])


    book = xlwt.Workbook(encoding='utf8')
    sheet = book.add_sheet('untitled')

    field_names = ['id_sales_order_item','order_nr','size','sku','sku_supplier_simple','barcode_ean','supplier_name','name','status','suborder_number','paid_price','cost','order_date']
    cross_status_fields = ['order_attribute','inbound_order_number','supplier_order_date','order_status']

    index_counter = 0
    for index_i,field in enumerate(field_names):
         sheet.write(0,index_i,[unicode(field).encode('utf-8') ])
         index_counter +=1

    for index_i,field in enumerate(cross_status_fields):
         sheet.write(0,index_counter+index_i,[unicode(field).encode('utf-8') ])


    for index_i,an_order in enumerate(orders):
        for index_j,field in enumerate(field_names):
            sheet.write(index_i+1,index_j,[unicode(getattr(an_order, field)).encode('utf-8') ])

        a_cross_statuss = CrossStatus.objects.get( order_id = an_order)
        for index_j,field in enumerate(cross_status_fields):
            sheet.write(index_i+1,index_j+index_counter,[unicode(getattr(a_cross_statuss, field)).encode('utf-8') ])

    response = HttpResponse(mimetype='application/vnd.ms-excel')

    if supNameDetail == "" and "transaction_keyword" in request.GET:
        file_string = 'attachment; filename='+request.GET['transaction_keyword']+'.xls'
        response['Content-Disposition'] = file_string
    else:
        file_string = 'attachment; filename='+supNameDetail+'_'+str(end_date)+'_'+str(start_date)+'.xls'
        response['Content-Disposition'] = file_string

#    response['Content-Disposition'] = 'attachment; filename=TR2012-04-19-RD-5782.xls'
    
    book.save(response)
    return response

def UpdateInboundOrderNumber(request):
    orderIDs = list()
    orderIDs = request.POST.getlist('orderChecked')
    for anOrderID in orderIDs:
        try:
            anOrder = Order.objects.get(pk = int(anOrderID))
        except Order.DoesNotExist:
            raise Http404
        try:
            toBeUpdated = CrossStatus.objects.get(pk = anOrder.id)
        except CrossStatus.DoesNotExist:
            toBeUpdated = CrossStatus.objects.create(order_id = anOrder)
        toBeUpdated.inbound_order_number =  request.POST["ion"]
        toBeUpdated.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
@login_required
def updateOrder(request):

    orderIDs = list()
    orderIDs = request.POST.getlist('orderChecked')
    active_user = UserProfile.objects.get(user = request.user)
    if request.POST["ion"] == "":
        if request.POST["status"] == 'supplier_informed':
            supplier_name = request.POST["supplier_name"]
            tr_string = generateTransactionString(supplier_name)
            new_tr = Transactions.objects.create(transaction_string = tr_string, created_at = datetime.datetime.now() , user_id = active_user)

        for anOrderID in orderIDs:
            try:
                anOrder = Order.objects.get(pk = int(anOrderID))
            except Order.DoesNotExist:
                raise Http404
            try:
                toBeUpdated = CrossStatus.objects.get(pk = anOrder.id)
            except CrossStatus.DoesNotExist:
                toBeUpdated = CrossStatus.objects.create(order_id = anOrder)
            toBeUpdated.order_status =  request.POST["status"]
            if request.POST["status"] == 'supplier_informed':
                toBeUpdated.supplier_order_date = datetime.datetime.now()
            toBeUpdated.save()
            active_user = UserProfile.objects.get(user = request.user)
            LastUpdate.objects.create(updated_on = datetime.datetime.now() , cross_status = toBeUpdated.order_status, order_id = anOrder, user_id =  active_user )
            if request.POST["status"] == 'supplier_informed':
                OrderTransaction.objects.create(tr_id = new_tr,order_id = anOrder)
    else:
        inbound_order_number = request.POST["ion"]
        for anOrderID in orderIDs:
            try:
                anOrder = Order.objects.get(pk = int(anOrderID))
            except Order.DoesNotExist:
                raise Http404
            try:
                toBeUpdated = CrossStatus.objects.get(pk = anOrder.id)
            except CrossStatus.DoesNotExist:
                toBeUpdated = CrossStatus.objects.create(order_id = anOrder)
            toBeUpdated.inbound_order_number =  inbound_order_number
            toBeUpdated.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

def sort(request,criteria):

    if criteria == "order_id":
        orders = Order.objects.order_by('-order_nr')
    for anOrder in orders:
        try:
            statusForAnOrder = CrossStatus.objects.get( pk = anOrder.id)
            anOrder.status = statusForAnOrder.order_status
        except CrossStatus.DoesNotExist:
            statusForAnOrder = CrossStatus.objects.create(order_id = anOrder,order_status = 'Unprocessed')
            anOrder.status = 'Unprocessed'
    return render_to_response('orders.html', {'orders' : orders},context_instance = RequestContext(request) )

def test(request):
    return render_to_response('asd.html',context_instance = RequestContext(request) )

def tabletest(request):
    return render_to_response('tableTest.html',context_instance = RequestContext(request) )

def registerUser(request):
    if request.POST:
        firstName = request.POST["firstName"]
        lastName = request.POST["lastName"]
        email = request.POST["email"]
        password = request.POST["password"]

        try:
            User.objects.get(username = email.split('@')[0])
        except User.DoesNotExist:
            user = User.objects.create_user(email.split('@')[0], email, password)
            user.first_name = firstName
            user.last_name = lastName
        else:
            return render_to_response('main.html')

        #profile = user.get_profile()
        #profile.role = 2

        user.save()
        login(request, user)
        return HttpResponseRedirect("/orders/")
    
    else:
        return HttpResponseRedirect("/orders/")

def loginUser(request):
    if request.POST:
        email = request.POST["email"]
        password = request.POST["password"]

        user = authenticate(username=email.split('@')[0], password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect("/orders/")
            else:
                print "Your account has been disabled!"
        else:
            print "Your username and password were incorrect."


    else:
            return HttpResponseRedirect("/orders/")

def orderHistory(request,order_id):

    
    update_list = LastUpdate.objects.filter( order_id = order_id).order_by('updated_on')

    user_list = list()
    date_list = list()
    status_list = list()

    for anUpdate in update_list:
        date_list.append(str(anUpdate.updated_on))
        user_list.append(str(anUpdate.user_id.user.username))
        status_list.append(str(anUpdate.cross_status))

    return HttpResponse(simplejson.dumps({'users': user_list, 'dates' : date_list,'statuses' : status_list}),mimetype='application/json')

def logoutUser(request):
    logout(request)
    return HttpResponseRedirect("/") # return HttpResponseRedirect('/')


def excelList(request):

    supNameDetail=""
    start_date = ""
    end_date = ""
    initStartDate = ""
    initEndDate = ""

    if "supname" in request.GET:
        supNameDetail = request.GET["supname"]
    if "startdate" in request.GET:
        start_date = datetime.datetime.strptime(request.GET['startdate'], "%m/%d/%Y")
        initStartDate = request.GET['startdate']
    if "enddate" in request.GET:
        end_date = datetime.datetime.strptime(request.GET['enddate'], "%m/%d/%Y")
        initEndDate = request.GET['enddate']

    if supNameDetail == "":
        filteredOrders = Order.objects.all()
    else:
        filteredOrders = Order.objects.filter(supplier_name=supNameDetail,order_date__range =[start_date,end_date])

    return HttpResponse(simplejson.dumps({'orders': filteredOrders}),mimetype='application/json')

@login_required()
def listTransactions(request):

    active_user = UserProfile.objects.get(user = request.user)
    tr_list = Transactions.objects.filter( user_id = active_user).order_by('created_at')

    tr_string_list = list()
    date_list = list()

    for aTransaction in tr_list:
        tr_string_list.append(aTransaction.transaction_string)
        date_list.append(str(aTransaction.created_at))
        
    return HttpResponse(simplejson.dumps({'tr_string': tr_string_list, 'dates' : date_list}),mimetype='application/json')


def listOrdersTransactions(request):


    if "transaction_keyword" in request.GET:
        tr_keyword = request.GET['transaction_keyword']
        try :
            given_transaction = Transactions.objects.get(transaction_string = tr_keyword)
            return render_to_response('transactionOrderList.html', {'given_transaction' : given_transaction,},context_instance = RequestContext(request))
        except Transactions.DoesNotExist:
            raise Http404

    return HttpResponseRedirect("/") # return HttpResponseRedirect('/')

