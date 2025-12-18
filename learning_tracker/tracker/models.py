from django.db import models
from django.utils import timezone
# Create your models here.
'''
created by:刘思扬
数据库模型

Course（课程）
   │
   ├── StudyMaterial（学习资料）
   │      ├── StudySession（学习记录）可选关联
   │      └── ReviewSchedule（复习计划）可选关联
   │
   ├── PomodoroSession（番茄钟）只关联课程
   │
   └── KnowledgePoint（知识点）

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

class StudyMaterial(models.Model):
    '''学习资料模型'''
    MATERIAL_TYPES = [
        ('text', '文本/文档'),
        ('video', '视频'),
        ('audio', '音频'),
        ('link', '网页链接'),
        ('other', '其他'),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='所属课程'
    )
    name = models.CharField(max_length=200, verbose_name='资料名称')
    description = models.TextField(blank=True, verbose_name='资料描述')
    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPES,
        default='text',
        verbose_name='资料类型'
    )
    file_path=models.CharField(max_length=500, blank=True, verbose_name='文件路径或链接')
    estimated_time=models.IntegerField(default=0, verbose_name='预计学习时长（分钟）')
    created_at=models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.name} - {self.name}"
    
    def get_total_study_time(self):
        '''计算该资料的总学习时长（分钟）'''
        total = sum(session.duration for session in self.studysession_set.all())
        return round(total, 2)


class StudySession(models.Model):
    '''学习记录模型'''
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='课程'
    )
    material = models.ForeignKey(
        StudyMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='学习资料（可选）'
    )
    start_time=models.DateTimeField(verbose_name='开始时间')
    end_time=models.DateTimeField(verbose_name='结束时间')
    duration=models.FloatField(verbose_name='学习时长（分钟）')
    created_at=models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    notes=models.TextField(blank=True, verbose_name='学习笔记')
    
    class Meta:
        verbose_name = '学习记录'
        verbose_name_plural = '学习记录'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.course.name} - {self.start_time.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        '''自动计算学习时长'''
        if self.start_time and self.end_time:
            delta=self.end_time - self.start_time
            self.duration=delta.total_seconds() / 60
        super().save(*args, **kwargs)

class PomodoroSession(models.Model):
    '''番茄钟模型'''
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程')
    session_date=models.DateTimeField(auto_now_add=True, verbose_name='会话时间')
    start_time=models.DateTimeField(verbose_name='开始时间')
    end_time=models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    focus_time=models.IntegerField(default=25, verbose_name='专注时长（分钟）')
    break_time=models.IntegerField(default=5, verbose_name='休息时长（分钟）')
    completed=models.BooleanField(default=False, verbose_name='是否完成')
    
    class Meta:
        verbose_name = '番茄钟'
        verbose_name_plural = '番茄钟'
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.course.name} - {self.session_date.strftime('%Y-%m-%d %H:%M')}"


class ReviewSchedule(models.Model):
    '''复习计划模型'''
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='课程'
    )
    material = models.ForeignKey(
        StudyMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='学习资料（可选）'
    )
    review_date=models.DateField(verbose_name='复习日期')
    completed=models.BooleanField(default=False, verbose_name='是否完成')
    review_count=models.IntegerField(default=0, verbose_name='复习次数')
    created_at=models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '复习计划'
        verbose_name_plural = '复习计划'
        ordering = ['review_date']
    
    def __str__(self):
        if self.material:
            return f"{self.course.name} - {self.material.name} - {self.review_date}"
        return f"{self.course.name} - {self.review_date}"

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