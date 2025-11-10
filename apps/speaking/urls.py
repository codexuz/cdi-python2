from django.urls import path
from . import views

urlpatterns = [
    path("request/", views.request_speaking, name="speaking-request"),
    path("my/", views.my_speaking_requests, name="speaking-my-requests"),
]
