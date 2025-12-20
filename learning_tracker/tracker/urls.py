from django.urls import path
from . import views

urlpatterns = [
    # 首页
    path('', views.home, name='home'),

    # 学习记录模块 URL (成员B)
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/add/', views.session_create, name='session_create'),
    path('sessions/edit/<int:pk>/', views.session_update, name='session_update'),
    path('sessions/delete/<int:pk>/', views.session_delete, name='session_delete'),
]