from django.contrib import admin
from .models import Course,StudySession,KnowledgePoint,StudyMaterial,ReviewSchedule,PomodoroSession # 导入数据库模型

# Register your models here.
# 注册模型
admin.site.register(Course)
admin.site.register(StudySession)
admin.site.register(KnowledgePoint)
admin.site.register(ReviewSchedule)
admin.site.register(PomodoroSession)
admin.site.register(StudyMaterial)




