from django.urls import path

from . import views

app_name = "user"
urlpatterns = [
    path("", views.index, name="index"),
    path("response/<str:name>", views.response, name="response")
]
