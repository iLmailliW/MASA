from django.urls import path
from . import views

app_name = "home"
urlpatterns = [
    path("", views.index, name="index"),
    path('esg_considerations/', views.esg_considerations, name='esg_considerations'),
    path('corporate_vision/', views.corporate_vision, name='corporate_vision'),

]
