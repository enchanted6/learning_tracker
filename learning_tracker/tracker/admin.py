from django.contrib import admin
from .models import Course,StudySession,KnowledgePoint # 导入数据库模型

# Register your models here.
# 注册模型
admin.site.register(Course)
admin.site.register(StudySession)
admin.site.register(KnowledgePoint)




