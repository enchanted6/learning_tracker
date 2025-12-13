# cd learning_tracker
# python test_models.py 直接运行（推荐，避免编码问题）
# 测试模型 简易脚本

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_tracker.settings')
django.setup()

# 导入模型
from tracker.models import Course, StudySession


# 查询所有
print("所有课程:")
print(Course.objects.all())

# 查询单个
try:
    course1 = Course.objects.get(id=1)
    print(f"\nID=1的课程: {course1}")
except Course.DoesNotExist:
    print("\nID=1的课程不存在")

# 创建课程
course = Course.objects.create(name="Java基础", description="不知道随便写点啥没人知道吧")
print(f"创建成功: {course}")

# 查询所有
print("\n所有课程:")
for c in Course.objects.all():
    print(f"  - {c}")

# 删除刚创建的课程
course.delete()
print(f"\n已删除: {course.name}")