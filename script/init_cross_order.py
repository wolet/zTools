#! /usr/bin/env python

import sys
import os
import datetime

def setup_environment():

    sys.path.append('/home/opsland/opsland/bin/zTools/')
    sys.path.append('/home/opsland/opsland/bin/zTools/cross_app/')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cross_app.settings_cross2'
setup_environment()

def fixStatus():

    from cross_app.cross_order.models import OrderLive,CrossStatus,LastUpdate,Supplier,Order
    from django.contrib.auth.models import User
    from cross_app.cross_order.models import OrderCrossDetails,SimpleSize



#    startdate = datetime.datetime.strptime("03/05/2012:18:00:00","%d/%m/%Y:%H:%M:%S")
#    enddate = startdate + datetime.timedelta(hours=1)
     t = OrderLive.objects.all().order_by('-last_status_change')[:1][0]


#    startdate = Order.objects.all().order_by('-order_date')[:1][0].order_date
#    enddate = startdate + datetime.timedelta(hours=1)

    startdate = t.last_status_change - datetime.timedelta(hours=2)
    orderList = OrderLive.objects.filter(order_date__range=[startdate,t.last_status_change])

#    orderList = OrderLive.objects.using('baytas').filter(order_date__range=[startdate,enddate])
    newOrderList = []
    print str(t.last_status_change)
    print str(startdate)
    for o in orderList:
	    if Order.objects.filter(id_sales_order_item = o.id_sales_order_item).count() > 0:
            live = OrderLive.objects.get(id_sales_order_item = o.id_sales_order_item)
            cs = None
    
            o.status = live.status
            o.save()
            if live.status == "shipped" and o.ordercrossdetails.cross_status.pk != 7:
                cs = CrossStatus.objects.get(pk=7)
                shipCounter += 1

            if live.status == "canceled" and o.ordercrossdetails.cross_status.pk != 6:
                cs = CrossStatus.objects.get(pk=6)
                cancelCounter += 1


            if cs is not None:
                o.ordercrossdetails.cross_status = cs
                o.ordercrossdetails.save()

                lu = LastUpdate()
                lu.update_date = datetime.datetime.now()
                lu.cross_status = cs
                lu.order = o
                lu.user = User.objects.filter(groups__name="fetcher")[0]
                lu.save()
            continue


        if o.status != "exported" and o.status != "office_pending":
            continue

        if not o.shipment_type.lower().__contains__("crossdocking"):
            continue

        supplier = None
        if Supplier.objects.filter(name = o.supplier_name).count() is 0:
            supplier = Supplier()
            supplier.name = o.supplier_name
            supplier.save()
        else:
            supplier = Supplier.objects.filter(name = o.supplier_name)[0]

        no = Order()
        no.id_sales_order_item = o.id_sales_order_item
        no.id_sales_order = o.id_sales_order
        no.order_nr = o.order_nr
        no.size = o.size
        no.sku = o.sku
        no.supplier = supplier
        no.sku_supplier_simple = o.sku_supplier_simple
        no.shipment_type = o.shipment_type
        no.barcode_ean = o.barcode_ean
        no.sku_supplier_config = o.sku_supplier_config
        no.buysheet_id = o.buysheet_id
        no.name = o.name
        no.status = o.status
        no.id_sales_order_item_shipment = o.id_sales_order_item_shipment
        no.tracking_url = o.tracking_url
        no.suborder_number = o.suborder_number
        no.paid_price = o.paid_price
        no.cost = o.cost
        no.shipping_name = o.shipping_name
        no.shipping_city = o.shipping_city
        no.billing_name = o.billing_name
        no.billing_city = o.billing_city
        no.customer_first_name = o.customer_first_name
        no.customer_last_name = o.customer_last_name
        no.amount_paid = o.amount_paid
        no.tax_percent = o.tax_percent
        no.original_unit_price = o.original_unit_price
        no.unit_price = o.unit_price
        no.tax_amount = o.tax_amount
        no.phone = o.phone
        no.coupon_money_value = o.coupon_money_value
        no.coupon_percent = o.coupon_percent
        no.address1 = o.address1
        no.address2 = o.address2
        no.billing_address = o.billing_address
        no.billing_address2 = o.billing_address2
        no.order_date = o.order_date


        no.save()
        newOrderList.append(no)

        # Extended order table is created
        # 5-7 digits in SKU gives the attribute of the order
        # "Unprocessed" status must be the first status in CrossStatus table. Basically its order is 0
        cs = CrossStatus.objects.all().order_by("order")[0]
        ocd = OrderCrossDetails()
        ocd.order = no
        ocd.cross_status = cs
        ocd.order_attribute = no.sku[5:7]
        ocd.save()

        # Superuser is the owner of the fetched row
        lu = LastUpdate()
        lu.update_date = datetime.datetime.now()
        lu.cross_status = cs
        lu.order = no
        lu.user = User.objects.filter(groups__name="fetcher")[0]
        lu.save()

    print str(len(newOrderList)) + " cross order added" 
fixStatus()
