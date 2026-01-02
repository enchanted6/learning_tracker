from django import forms
from .models import Course, StudySession, PomodoroSession, ReviewSchedule, KnowledgePoint, StudyMaterial

class CourseForm(forms.ModelForm):
    """课程表单"""
    class Meta:
        model=Course
        fields=['name','description']
        widgets={
            'name':forms.TextInput(attrs={'class':'form-control','placeholder':'请输入课程名称'}),
            'description':forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入课程描述（可选）'}),
        }

class StudySessionForm(forms.ModelForm):
    """学习记录表单"""
    class Meta:
        model=StudySession
        fields=['course','material','start_time','end_time','notes']
        widgets={
            'course':forms.Select(attrs={'class':'form-control'}),
            'material':forms.Select(attrs={'class':'form-control'}),
            'start_time':forms.DateTimeInput(attrs={'class':'form-control','type':'datetime-local'}),
            'end_time':forms.DateTimeInput(attrs={'class':'form-control','type':'datetime-local'}),
            'notes':forms.Textarea(attrs={'class':'form-control','rows': 3, 'placeholder':'学习笔记（可选）'}),
        }

class PomodoroSessionForm(forms.ModelForm):
    """番茄钟表单"""
    class Meta:
        model=PomodoroSession
        fields=['course','focus_time','break_time']
        widgets={
            'course':forms.Select(attrs={'class':'form-control'}),
            'focus_time':forms.NumberInput(attrs={'class':'form-control','min': 1,'max':60,'value':25}),
            'break_time':forms.NumberInput(attrs={'class':'form-control','min': 1,'max':30,'value':5}),
        }

class ReviewScheduleForm(forms.ModelForm):
    """复习计划表单"""
    class Meta:
        model=ReviewSchedule
        fields=['course','material','review_date']
        widgets = {
            'course':forms.Select(attrs={'class':'form-control'}),
            'material':forms.Select(attrs={'class':'form-control'}),
            'review_date':forms.DateInput(attrs={'class':'form-control', 'type': 'date'}),
        }

class KnowledgePointForm(forms.ModelForm):
    """知识点表单"""
    class Meta:
        model=KnowledgePoint
        fields=['course','name','description']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入知识点名称'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入知识点描述（可选）'}),
        }

class StudyMaterialForm(forms.ModelForm):
    """学习资料表单"""
    class Meta:
        model=StudyMaterial
        fields=['course','name','description', 'material_type', 'file_path', 'estimated_time']
        widgets = {
            'course':forms.Select(attrs={'class': 'form-control'}),
            'name':forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入资料名称'}),
            'description':forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入资料描述（可选）'}),
            'material_type':forms.Select(attrs={'class': 'form-control'}),
            'file_path':forms.TextInput(attrs={'class': 'form-control', 'placeholder': '文件路径或链接（可选）'}),
            'estimated_time':forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': '预计学习时长（分钟）'}),
        }

