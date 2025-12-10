from django.db import models
from django.utils import timezone
# Create your models here.
'''
created by:刘思扬
数据库模型
'''

class Course(models.Model):
    '''课程模型'''
    name=models.CharField(max_length=100,verbose_name='课程名称',help_text='请输入课程名称',null=True,blank=True,default='')
    description=models.TextField(blank=True,verbose_name='课程描述')
    created_at=models.DateTimeField(auto_now_add=True,verbose_name='创建时间')

    def __str__(self):
        return self.name
    def get_total_study_time(self):
        '''计算总学习时长（h)'''
        total_minutes=sum(session.duration for session in self.studysession_set.all())
        return round(total_minutes/60,2)

class StudySession(models.Model):
    course=models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='课程'
    )
    start_time=models.DateTimeField(verbose_name='开始时间')
    end_time=models.DateTimeField(verbose_name='结束时间')
    duration=models.FloatField(verbose_name='学习时长（分钟）')
    created_at=models.DateTimeField(auto_now_add=True,blank=True,verbose_name='创建时间')
    notes = models.TextField(blank=True, verbose_name='学习笔记')
    def __str__(self):
        return f"{self.course.name} - {self.start_time.strftime('%Y-%m-%d')}"


class KnowledgePoint(models.Model):
    course=models.ForeignKey(
    Course,
    on_delete=models.CASCADE,
    verbose_name='课程') 
    name=models.CharField(max_length=100,verbose_name='知识点名称')
    description=models.TextField(blank=True,verbose_name='知识点描述')
    created_at=models.DateTimeField(auto_now_add=True,verbose_name='创建时间')

    def __str__(self):
        return f"{self.course.name} - {self.name}"      