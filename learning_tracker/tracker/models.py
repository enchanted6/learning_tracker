from django.db import models
from django.utils import timezone
import datetime


# 假设成员A已经创建了Course，如果没有，暂时取消注释下面几行用于测试
# class Course(models.Model):
#     name = models.CharField(max_length=100)
#     def __str__(self): return self.name

class StudySession(models.Model):
    # 外键关联课程 (确保 'Course' 模型存在)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, verbose_name="关联课程")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")

    # 自动计算，允许为空，后续在save中填充
    duration = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="学习时长(分钟)")
    notes = models.TextField(blank=True, verbose_name="学习笔记/备注")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']  # 默认按时间倒序排列
        verbose_name = "学习记录"

    def save(self, *args, **kwargs):
        # 自动计算时长的逻辑
        if self.start_time and self.end_time:
            # 计算时间差
            diff = self.end_time - self.start_time
            # 转换为分钟 (total_seconds / 60)
            self.duration = round(diff.total_seconds() / 60, 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.name} - {self.start_time.strftime('%Y-%m-%d')}"