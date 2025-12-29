'''
created by:刘思扬
'''
from django.urls import path
from . import views

urlpatterns=[
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    # Agent智能助手（新版本，支持多工具）
    path('agent/', views.AgentView.as_view(), name='agent'),
    path('agent/chat/', views.agent_chat, name='agent_chat'),
    path('agent/upload/', views.upload_pdf, name='agent_upload'),
    path('agent/clear/', views.clear_chat, name='agent_clear'),
]
# <int:pk>	URL中的动态参数
# int	类型是整数
# pk	变量名（Primary Key = 主键 = id）