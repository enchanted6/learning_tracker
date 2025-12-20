from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import StudySession, Course  # 导入Course用于筛选
from .forms import StudySessionForm


# 首页
def home(request):
    return render(request, 'tracker/home.html')


# --- 学习记录模块 (成员B) ---

def session_list(request):
    """显示学习记录列表，支持按课程和日期筛选"""
    sessions = StudySession.objects.all()
    courses = Course.objects.all()  # 用于下拉筛选框

    # 获取筛选参数
    course_id = request.GET.get('course')
    date_start = request.GET.get('date_start')
    date_end = request.GET.get('date_end')

    # 筛选逻辑
    if course_id:
        sessions = sessions.filter(course_id=course_id)
    if date_start:
        sessions = sessions.filter(start_time__date__gte=date_start)
    if date_end:
        sessions = sessions.filter(end_time__date__lte=date_end)

    context = {
        'sessions': sessions,
        'courses': courses,
    }
    return render(request, 'tracker/session_list.html', context)


def session_create(request):
    """添加新的学习记录"""
    if request.method == 'POST':
        form = StudySessionForm(request.POST)
        if form.is_valid():
            form.save()  # 模型中的 save() 方法会自动计算时长
            messages.success(request, '学习记录添加成功！')
            return redirect('session_list')
    else:
        form = StudySessionForm()

    return render(request, 'tracker/session_form.html', {'form': form, 'title': '添加记录'})


def session_update(request, pk):
    """编辑学习记录"""
    session = get_object_or_404(StudySession, pk=pk)
    if request.method == 'POST':
        form = StudySessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()  # 重新计算时长
            messages.success(request, '记录已更新！')
            return redirect('session_list')
    else:
        form = StudySessionForm(instance=session)

    return render(request, 'tracker/session_form.html', {'form': form, 'title': '编辑记录'})


def session_delete(request, pk):
    """删除学习记录"""
    session = get_object_or_404(StudySession, pk=pk)
    if request.method == 'POST':
        session.delete()
        messages.success(request, '记录已删除。')
        return redirect('session_list')

    return render(request, 'tracker/session_confirm_delete.html', {'session': session})