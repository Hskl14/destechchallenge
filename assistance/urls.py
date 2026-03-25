from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r"^assistance-requests/create/$", views.AssistanceRequestCreateView),
    re_path(r"^assistance-requests/(?P<request_id>\d+)/complete/$", views.AssistanceRequestCompleteView),
    re_path(r"^assistance-requests/(?P<request_id>\d+)/cancel/$", views.AssistanceRequestCancelView),
]
