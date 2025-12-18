from django.shortcuts import render
from .models import Course
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
# Create your views here.
'''
Created by :刘思扬 
'''
class CourseListView(ListView):
    """课程列表视图"""
    model=Course# 用什么模型
    template='' # 模版路径
    context_object_name='courses' # 模版中使用的变量


class CourseDetailView(DetailView):
    """课程详细视图"""
    model=Course
    template=''
    
class CourseCreateView(CreateView):
    model=Course
    fields=['name','description','created_at']
    template=''
    success_url=reverse_lazy('course_list')# 成功后跳转到的表页

class CourseDeleteView(DeleteView):
    """课程删除视图"""
    model=Course
    template=''
    success_url=reverse_lazy('course_list')# 成功后跳转到的表页  # pyright: ignore[reportUndefinedVariable]

class CourseUpdateView(UpdateView):
    """课程更新视图"""
    model = Course
    fields=['name','description','created_at']
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('course_list')












