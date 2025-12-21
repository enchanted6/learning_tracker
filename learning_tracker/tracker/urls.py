from django.urls import path
from . import views

urlpatterns=[
   # 首页
    path('', views.home, name='home'),

    # 学习记录模块 URL (成员B)
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/add/', views.session_create, name='session_create'),
    path('sessions/edit/<int:pk>/', views.session_update, name='session_update'),
    path('sessions/delete/<int:pk>/', views.session_delete, name='session_delete'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('assistant/', views.PDFAssistantView.as_view(), name='pdf_assistant'),
    path('assistant/upload/', views.upload_pdf, name='pdf_upload'),
    path('assistant/chat/', views.chat, name='pdf_chat'),
    path('assistant/clear/', views.clear_chat, name='pdf_clear'),
]
# <int:pk>	URL中的动态参数
# int	类型是整数
# pk	变量名（Primary Key = 主键 = id）
