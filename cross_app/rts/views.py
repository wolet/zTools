# Create your views here.

from datetime import  datetime,time,timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from cross_order.helper_functions import render_response
#from dms.forms import DocumentUploadForm
from cross_order.utils import check_permission
from rts.helper import not_in_rts_warehouse_group, not_in_rts_customer_group
from rts.models import OrderItemBaseForReturns, ReturnedItemDetails,ReturnReason,ActionType,rts_status
from settings import MEDIA_ROOT, LOGIN_URL

@login_required
@check_permission('RtsCustomer')
def home_order_management(request):
    dict = {
        'statusList':rts_status.TYPE,
        'reasonList':ReturnReason.objects.all().order_by("order"),
        'status':request.POST.get('statusFilter',rts_status.RETURNED)
    }

    start_date = datetime.now() - timedelta(days = 3)
    start_date = datetime.combine(start_date, time.min)

    end_date = datetime.now()
    if "dateStart" in request.POST:
        start_date = datetime.strptime(request.POST['dateStart'], "%m/%d/%Y")
    if "dateEnd" in request.POST:
        end_date = datetime.strptime(request.POST['dateEnd'], "%m/%d/%Y")
        end_date = datetime.combine(end_date, time.max)

    dict.update({ 'start_date':start_date})
    dict.update({ 'end_date':end_date,})

    oibfr_list = OrderItemBaseForReturns.objects.filter(returneditemdetails__status=rts_status.RETURNED,returneditemdetails__create_date__range = [start_date, end_date])
    dict.update({'oibfr_list':oibfr_list})

    if request.method == 'POST':
        status = request.POST.get('statusFilter','')
        try:
            dict.update({'oibfr_list': OrderItemBaseForReturns.objects.filter(returneditemdetails__status=int(status),returneditemdetails__create_date__range = [start_date, end_date])})
        except:
            dict.update({'oibfr_list': OrderItemBaseForReturns.objects.filter(returneditemdetails__create_date__range = [start_date, end_date])})

    return render_response(request, 'rts/home_order_management.html',dict)

@login_required
@check_permission('RtsWarehouse')
def home_warehouse(request):
    suborder_nr = request.GET.get('suborder_nr','')

    dict = {
        'actionList':ActionType.objects.all().order_by("order"),
        'reasonList':ReturnReason.objects.all().order_by("order"),
        'suborder_nr':suborder_nr
    }

    if request.method == 'GET' and suborder_nr != '':
        dict.update({'oibfr_list': OrderItemBaseForReturns.objects.filter(suborder_number__icontains=suborder_nr)})
        
    return render_response(request, 'rts/home_warehouse.html',dict)


def update_refunded_order(request):
    if request.method == 'POST':
        oib = OrderItemBaseForReturns.objects.get(pk = int(request.POST['returnedItemID']))
        customerContacted = request.POST['customerContacted']
        refundReferenceNumber = request.POST['refundReferenceNumber']
        newCoupon = ""
        isCouponNeeded = request.POST.get('isCouponNeeded',False)
        comment = request.POST['comment']

        oib.returneditemdetails.status = rts_status.REFUNDED
        if isCouponNeeded:
            isCouponNeeded = True
            newCoupon = request.POST.get('newCoupon','')
            if newCoupon == '':
                oib.returneditemdetails.status = rts_status.COUPON_PENDING

        oib.returneditemdetails.update_date = datetime.now()
        oib.returneditemdetails.update_user = request.user
        oib.returneditemdetails.customer_contacted = customerContacted
        oib.returneditemdetails.refund_reference_number = refundReferenceNumber
        oib.returneditemdetails.isCouponNeeded = isCouponNeeded
        oib.returneditemdetails.new_coupon = newCoupon
        oib.returneditemdetails.comment = comment
        if oib.payment_method.lower() == "codpayment":
            oib.returneditemdetails.isEmailSent = True
        oib.returneditemdetails.save()

        return redirect('/rts/home_order_management/?returnedItemID='+str(oib.pk))

def update_returned_order(request):
    if request.method == 'POST':
        oib = OrderItemBaseForReturns.objects.get(id_sales_order_item = int(request.POST['returnedItemID']))
        returnReason = None
        if ReturnReason.objects.filter(pk = int(request.POST['reasonList'])).count() > 0:
            returnReason = ReturnReason.objects.get(pk = int(request.POST['reasonList']))
        actionType = None
        if ActionType.objects.filter(pk = int(request.POST['actionList'])).count() > 0:
            actionType = ActionType.objects.get(pk = int(request.POST['actionList']))
        comment = request.POST['comment']

        isWithInvoice = False
        if request.POST.get("isWithInvoice",False):
            isWithInvoice = True

        rid = ReturnedItemDetails()
        if ReturnedItemDetails.objects.filter(order_item=oib).count() > 0:
            rid = ReturnedItemDetails.objects.get(order_item=oib)
        else:
            rid.create_user = request.user
            rid.create_date = datetime.now()

        rid.is_with_invoice = isWithInvoice
        rid.return_reason = returnReason
        rid.action_type = actionType
        rid.inbound_tracking_number = request.POST.get('inboundTrackingNumber',"")
        rid.comment = comment
        rid.status = rts_status.RETURNED
        rid.update_user = request.user
        rid.update_date = datetime.now()
        rid.order_item = oib
        rid.save()

        return redirect('/rts/home_warehouse/?suborder_nr='+oib.suborder_number)
    else:
        return redirect('/rts/home_warehouse/')

