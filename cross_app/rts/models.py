from django.db import models
from cross_app.cross_order.models import Supplier
from django.contrib.auth.models import User
from datetime import  datetime
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
import settings

class OrderItemBaseForReturns(models.Model):
    id_sales_order_item = models.PositiveIntegerField(max_length=10,null=False,default=0,unique=True,primary_key=True)
    id_sales_order = models.PositiveIntegerField(max_length=10,null=True)
    id_catalog_simple = models.IntegerField(max_length=11,null=False)
    order_nr = models.CharField(max_length=45,null=True)
    sku = models.CharField(max_length=255,null=True)
    order_date = models.DateTimeField(blank=True)
    supplier_id = models.PositiveIntegerField(max_length=10,default=0)
    supplier_name = models.CharField(max_length=511,null=True)
    barcode_ean = models.CharField(max_length=255,null=True)
    name = models.CharField(max_length=255,null=True)
    suborder_number = models.CharField(max_length=20,null=True)
    paid_price = models.DecimalField(max_digits=10,decimal_places=2,null=False)
    customer_email = models.CharField(max_length=511,null=True)
    billing_name = models.CharField(max_length=511,null=True)
    billing_address = models.CharField(max_length=255,null=True)
    billing_address2 = models.CharField(max_length=255,null=True)
    billing_city = models.CharField(max_length=255,null=True)
    billing_phone = models.CharField(max_length=255,null=True)

    shipping_name = models.CharField(max_length=511,null=True)
    shipping_address = models.CharField(max_length=255,null=True)
    shipping_address2 = models.CharField(max_length=255,null=True)
    shipping_city = models.CharField(max_length=255,null=True)
    shipping_phone = models.CharField(max_length=255,null=True)

    payment_method = models.CharField(max_length=511,null=True)
    coupon_code = models.CharField(max_length=511,null=True)
    coupon_money_value = models.DecimalField(max_digits=10,decimal_places=2, null=True)
    coupon_percent = models.IntegerField(max_length=11,null=True)
    bob_status = models.CharField(max_length=255,null=True)
    
    def __unicode__(self):
        return str(self.id_sales_order_item)

    class Meta:
        db_table = 'orderitem_base_for_returns'

class ActionType(models.Model):
    name = models.CharField(max_length=250,null=False)
    isInvalid = models.BooleanField(null=False,default=False)
    order = models.IntegerField(default=9999)
    def __unicode__(self):
        return self.name

class ReturnReason(models.Model):
    name = models.CharField(max_length=250,null=False)
    isInvalid = models.BooleanField(null=False,default=False)
    order = models.IntegerField(default=9999)
    def __unicode__(self):
        return self.name

class rts_status():

    RETURNED = 0
    REFUNDED = 1
    COUPON_PENDING = 2
    RETURN_DENIED = 3

    TYPE = (
            (RETURNED ,_("RTS_RETURNED")),
            (REFUNDED,_("RTS_REFUNDED")),
            (COUPON_PENDING,_("RTS_COUPON_PENDING")),
            (RETURN_DENIED ,_("RTS_RETURN_DENIED")),
            )

class ReturnedItemDetails(models.Model):
    order_item = models.OneToOneField(OrderItemBaseForReturns, to_field='id_sales_order_item',unique=True,null=False)
    return_reason = models.ForeignKey(ReturnReason,unique=False,null=True)
    action_type = models.ForeignKey(ActionType,unique=False,null=True)
    comment = models.TextField(null=True)

    create_date = models.DateTimeField(default= datetime.now())
    create_user = models.ForeignKey(User, related_name='%(class)s_user_create')
    update_date = models.DateTimeField(default= datetime.now())
    update_user = models.ForeignKey(User, related_name='%(class)s_user_update')

    status = models.IntegerField(default=rts_status.REFUNDED,choices=rts_status.TYPE)

    customer_contacted = models.CharField(max_length=250,null=True)
    refund_reference_number = models.CharField(max_length=250,null=True)
    isCouponNeeded = models.BooleanField(null=False,default=False)
    new_coupon = models.CharField(max_length=511,null=True)

    def __unicode__(self):
        return self.order_item.name + ' ' + self.return_reason.name + ' ' + self.action_type.name