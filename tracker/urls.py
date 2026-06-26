from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.signup, name="signup"),
    path("expense/<int:pk>/delete/", views.delete_expense, name="delete_expense"),
]