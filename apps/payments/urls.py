# apps/payments/urls.py
from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("topup/", views.create_topup, name="create-topup"),
    path("status/", views.payment_status, name="payment-status"),
    path("click/webhook/", views.click_webhook, name="click-webhook"),
]
