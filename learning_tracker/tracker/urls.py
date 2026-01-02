'''
created by:刘思扬
'''
from django.urls import path
from . import views

urlpatterns=[
    path('', views.home, name='home'),
    # 课程管理
    path('courses/',views.CourseListView.as_view(),name='course_list'),
    path('courses/<int:pk>/',views.CourseDetailView.as_view(),name='course_detail'),
    path('courses/create/',views.CourseCreateView.as_view(),name='course_create'),
    path('courses/<int:pk>/update/',views.CourseUpdateView.as_view(),name='course_update'),
    path('courses/<int:pk>/delete/',views.CourseDeleteView.as_view(),name='course_delete'),
    # 学习记录
    path('sessions/',views.session_list,name='session_list'),
    path('sessions/create/',views.session_create,name='session_create'),
    path('sessions/<int:pk>/update/',views.session_update,name='session_update'),
    path('sessions/<int:pk>/delete/',views.session_delete,name='session_delete'),
    # 番茄钟
    path('pomodoro/',views.pomodoro_list,name='pomodoro_list'),
    path('pomodoro/start/',views.pomodoro_start,name='pomodoro_start'),
    path('pomodoro/<int:pk>/running/',views.pomodoro_running,name='pomodoro_running'),
    path('pomodoro/<int:pk>/complete/',views.pomodoro_complete,name='pomodoro_complete'),
    # 复习计划
    path('reviews/',views.review_list,name='review_list'),
    path('reviews/create/',views.review_create,name='review_create'),
    path('reviews/auto-generate/',views.review_auto_generate,name='review_auto_generate'),
    path('reviews/<int:pk>/complete/',views.review_complete,name='review_complete'),
    path('reviews/<int:pk>/delete/',views.review_delete,name='review_delete'),
    # 知识点
    path('knowledge/',views.knowledge_list,name='knowledge_list'),
    path('knowledge/create/',views.knowledge_create,name='knowledge_create'),
    path('knowledge/<int:pk>/delete/',views.knowledge_delete,name='knowledge_delete'),
    # 学习资料
    path('materials/',views.material_list,name='material_list'),
    path('materials/create/',views.material_create,name='material_create'),
    path('materials/<int:pk>/update/',views.material_update,name='material_update'),
    path('materials/<int:pk>/delete/',views.material_delete,name='material_delete'),
    # 仪表板
    path('dashboard/',views.dashboard,name='dashboard'),
    # Agent智能助手（新版本，支持多工具）
    path('agent/',views.AgentView.as_view(),name='agent'),
    path('agent/chat/',views.agent_chat,name='agent_chat'),
    path('agent/upload/',views.upload_pdf,name='agent_upload'),
    path('agent/clear/',views.clear_chat,name='agent_clear'),
]
# <int:pk>	URL中的动态参数
# int	类型是整数
# pk	变量名（Primary Key = 主键 = id）