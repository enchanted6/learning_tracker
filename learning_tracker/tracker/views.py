from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import StudySession, Course, PomodoroSession, ReviewSchedule, KnowledgePoint, StudyMaterial  # 导入所有模型
from .forms import StudySessionForm, PomodoroSessionForm, ReviewScheduleForm, KnowledgePointForm, CourseForm, StudyMaterialForm
from .utils.forgetting_curve import generate_review_schedule,get_next_review_date
from datetime import datetime, timedelta

def home(request):
    return render(request, 'tracker/home.html', context={})

def pdf_assistant(request):
    return render(request, 'pdf_assistant.html', context={})

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


from django.views import View
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
import os
# Create your views here.
'''
Created by :刘思扬 
利用通用视图ListView, DetailView, CreateView, UpdateView, DeleteView
编写视图
'''
class CourseListView(ListView):
    """课程列表视图"""
    model=Course# 用什么模型
    template_name='course/course_list.html' # 模版路径（Django自动找templates目录）
    context_object_name='courses' # 模版中使用的变量

class CourseDetailView(DetailView):
    """课程详细视图"""
    model=Course
    template_name='course/course_detail.html'
    
class CourseCreateView(CreateView):
    model=Course
    form_class=CourseForm
    template_name='course/course_form.html'
    success_url=reverse_lazy('course_list')# 成功后跳转到的表页

class CourseDeleteView(DeleteView):
    """课程删除视图"""
    model=Course
    template_name='course/course_confirm_delete.html'
    success_url=reverse_lazy('course_list')# 成功后跳转到的表页  # pyright: ignore[reportUndefinedVariable]

class CourseUpdateView(UpdateView):
    """课程更新视图"""
    model = Course
    form_class=CourseForm
    template_name = 'course/course_form.html'
    success_url = reverse_lazy('course_list')

# AI Agent相关导入
import sys
import tempfile
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from .tools import parse_pdf, get_current_time, search_course, import_study_session

def simple_agent(question: str, pdf_path=None, chat_history=None)->str:
    """简单的Agent实现：直接判断并调用工具"""
    # 获取API密钥
    api_key=os.environ.get('SCHOOL_LLM_API_KEY','')
    if not api_key:
        raise ValueError("未配置API密钥，请设置环境变量 SCHOOL_LLM_API_KEY")
    # 创建LLM
    llm=ChatOpenAI(
        model="ecnu-max",
        api_key=api_key,
        base_url="https://chat.ecnu.edu.cn/open/api/v1",
        temperature=0.7
    )
    # 1. 判断是否需要调用工具
    # 检查是否需要获取时间
    time_keywords=["现在几点了", "现在什么时间", "当前时间", "现在时间", "几点了"]
    if any(keyword in question for keyword in time_keywords):
        current_time = get_current_time.invoke({})
        return f"当前时间是：{current_time}"
    # 检查是否需要搜索课程
    course_keywords = ["搜索课程", "找课程", "查找课程", "课程搜索", "找一下", "帮我找"]
    if any(keyword in question for keyword in course_keywords):
        course_name = question
        for keyword in course_keywords:
            course_name = course_name.replace(keyword, "").strip()
        # 如果提取不到课程名，提示用户
        if not course_name or len(course_name) < 2:
            return "请告诉我你想搜索哪个课程，例如：'搜索高等数学'、'找Python编程课程'"
        
        result = search_course.invoke({"course_name": course_name})
        return f"搜索结果：{result}"

    # 检查是否需要导入学习记录
    import_keywords = ["导入学习记录", "添加学习记录", "记录学习", "保存学习", "记录一下", "导入记录"]
    if any(keyword in question for keyword in import_keywords):
        # 使用LLM提取学习记录信息
        # 先获取当前时间，帮助处理相对时间
        current_time_str = get_current_time.invoke({})

        extract_prompt = f"""从用户的问题中提取学习记录信息，返回JSON格式：
{{
    "course_name": "课程名称",
    "start_time": "开始时间（格式：YYYY-MM-DD HH:MM，例如：2025-12-30 14:00）",
    "end_time": "结束时间（格式：YYYY-MM-DD HH:MM）",
    "notes": "学习笔记（可选）"
}}

当前时间：{current_time_str}

用户问题：{question}

重要提示：
1. 如果用户说"今天"、"现在"等，请根据当前时间计算具体时间
2. 如果用户说"刚才"、"刚刚"，请使用当前时间
3. 时间格式必须是：YYYY-MM-DD HH:MM（例如：2025-12-30 14:00）
4. 只返回JSON，不要其他文字
5. 如果信息不完整，在notes字段中说明缺少什么信息

只返回JSON格式，例如：
{{"course_name": "Python基础", "start_time": "2025-12-30 14:00", "end_time": "2025-12-30 16:00", "notes": ""}}"""

        try:
            extract_response = llm.invoke([("system", "你是一个数据提取助手，必须只返回有效的JSON格式数据，不要添加任何解释文字。"), ("human", extract_prompt)])
            import json
            import re
            # 尝试从响应中提取JSON
            response_text = extract_response.content if hasattr(extract_response, 'content') else str(extract_response)
            # 清理响应文本，移除可能的markdown代码块标记
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # 移除markdown代码块
                response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)

            # 查找JSON部分（更宽松的匹配）
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    record_data = json.loads(json_match.group())
                    course_name = record_data.get("course_name", "").strip()
                    start_time = record_data.get("start_time", "").strip()
                    end_time = record_data.get("end_time", "").strip()
                    notes = record_data.get("notes", "").strip()

                    # 验证必要字段
                    if not course_name:
                        return "❌ 缺少课程名称，请提供课程名称，例如：'导入学习记录：Python基础，2025-12-30 14:00到16:00'"
                    if not start_time:
                        return "❌ 缺少开始时间，请提供开始时间（格式：YYYY-MM-DD HH:MM），例如：2025-12-30 14:00"
                    if not end_time:
                        return "❌ 缺少结束时间，请提供结束时间（格式：YYYY-MM-DD HH:MM），例如：2025-12-30 16:00"

                    # 调用导入工具
                    result = import_study_session.invoke({
                        "course_name": course_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "notes": notes
                    })
                    return result
                except json.JSONDecodeError as je:
                    return f"❌ JSON解析失败：{str(je)}。AI返回的内容：{response_text[:200]}"
            else:
                return f"❌ 无法从AI响应中提取JSON格式。AI返回的内容：{response_text[:200]}。请直接提供：课程名称、开始时间、结束时间（格式：YYYY-MM-DD HH:MM）"
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return f"❌ 导入学习记录时出错：{str(e)}。详细信息：{error_detail[:300]}。请直接提供：课程名称、开始时间、结束时间（格式：YYYY-MM-DD HH:MM）"
    # 检查是否需要解析PDF
    if pdf_path and os.path.exists(pdf_path):
        pdf_keywords=["pdf","文档","文件","内容","总结","概述"]
        if any(keyword in question.lower() for keyword in pdf_keywords) or len(question) > 10:
            try:
                answer=parse_pdf.invoke({"pdf_path":pdf_path, "question":question})
                return answer
            except Exception as e:
                return f"PDF解析出错：{str(e)}"
    
    # 2. 如果不需要工具，直接使用LLM回答
    if chat_history:
        messages=[]
        for msg in chat_history[-5:]:  # 只取最近5条
            if msg['type']=='human':
                messages.append(("human",msg['content']))
            elif msg['type']=='ai':
                messages.append(("ai",msg['content']))
        messages.append(("human",question))
    else:
        messages = [("system", "你是一个智能学习助手，可以帮助用户学习各种知识。"), ("human", question)]
    response = llm.invoke(messages)
    return response.content if hasattr(response, 'content') else str(response)

# Agent视图
class AgentView(View):
    """智能助手页面"""
    template_name = 'tracker/agent.html'
    def get(self,request):
        """显示聊天页面"""
        pdf_path=request.session.get('pdf_file_path')
        pdf_name=request.session.get('pdf_file_name', '')
        
        context={
            'has_pdf': bool(pdf_path),
            'pdf_name': pdf_name,
        }
        return render(request, self.template_name, context)


def agent_chat(request):
    """处理Agent聊天请求"""
    if request.method!='POST':
        return JsonResponse({'error':'只支持POST请求'},status=400)
    # 获取用户消息
    question=request.POST.get('question','').strip()
    if not question:
        return JsonResponse({'error':'请输入问题'},status=400)
    # 获取PDF路径
    pdf_path=request.session.get('pdf_file_path')
    # 初始化对话历史（从session获取）
    if 'chat_history' not in request.session:
        request.session['chat_history']=[]
    # 创建Memory（从session恢复）
    chat_history=ChatMessageHistory()
    # 恢复历史消息
    for msg in request.session['chat_history']:
        if msg['type']=='human':
            chat_history.add_user_message(msg['content'])
        elif msg['type']=='ai':
            chat_history.add_ai_message(msg['content'])
    
    memory=ConversationBufferMemory(
        chat_memory=chat_history,
        memory_key="chat_history",
        return_messages=True
    )
    
    try:
        # Agent实现
        chat_history_list=request.session.get('chat_history',[])
        answer=simple_agent(question,pdf_path,chat_history_list)
        request.session['chat_history'].append({
            'type':'human',
            'content':question
        })
        request.session['chat_history'].append({
            'type':'ai',
            'content':answer
        })
        if len(request.session['chat_history']) > 20:
            request.session['chat_history'] = request.session['chat_history'][-20:]
        return JsonResponse({
            'success': True,
            'answer':answer
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Agent错误:\n{error_detail}", file=sys.stderr)
        return JsonResponse({
            'error': f'处理失败: {str(e)}'
        }, status=500)

def upload_pdf(request):
    """上传PDF文件（只上传一次）"""
    if request.method!='POST':
        return JsonResponse({'error':'只支持POST请求'},status=400)
    file=request.FILES.get('pdf_file')
    if not file:
        return JsonResponse({'error':'请上传PDF文件'},status=400)
    try:
        # 确保temp目录存在
        temp_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)),'temp')
        # 保存PDF到临时文件
        content=file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf',dir=temp_dir) as temp_file:
            temp_file_path=temp_file.name
            temp_file.write(content)
        # 保存文件路径到session
        request.session['pdf_file_path']=temp_file_path
        request.session['pdf_file_name']=file.name
        # 初始化对话历史（新的PDF，重置对话）
        request.session['chat_history']=[]
        return JsonResponse({
            'success':True,
            'filename':file.name,
            'message':'PDF上传成功，可以开始对话了！'
        })
    except Exception as e:
        import traceback
        error_detail=traceback.format_exc()
        print(f"上传错误:\n{error_detail}",file=sys.stderr)
        return JsonResponse({'error': f'上传失败: {str(e)}'},status=500)

def clear_chat(request):
    """清空对话历史"""
    if 'chat_history' in request.session:
        del request.session['chat_history']
    return JsonResponse({'success':True,'message':'对话历史已清空'})

def pomodoro_list(request):
    """番茄钟记录列表"""
    pomodoros = PomodoroSession.objects.all().order_by('-session_date')
    courses = Course.objects.all()

    # 筛选
    course_id = request.GET.get('course')
    if course_id:
        pomodoros = pomodoros.filter(course_id=course_id)

    context = {
        'pomodoros': pomodoros,
        'courses': courses,
    }
    return render(request, 'tracker/pomodoro_list.html', context)

def pomodoro_start(request):
    """开始番茄钟"""
    if request.method=='POST':
        form=PomodoroSessionForm(request.POST)
        if form.is_valid():
            pomodoro = form.save(commit=False)
            pomodoro.start_time=timezone.now()
            pomodoro.save()
            messages.success(request, f'番茄钟已开始！专注时间：{pomodoro.focus_time}分钟')
            return redirect('pomodoro_running',pk=pomodoro.pk)  # 跳转到进行中页面
    else:
        form=PomodoroSessionForm()

    return render(request,'tracker/pomodoro_form.html',{'form': form,'title': '开始番茄钟'})

def pomodoro_running(request, pk):
    """番茄钟进行中页面"""
    pomodoro = get_object_or_404(PomodoroSession, pk=pk)

    if pomodoro.completed:
        messages.info(request,'番茄钟已完成！')
        return redirect('pomodoro_list')

    # 计算剩余时间
    elapsed=timezone.now()-pomodoro.start_time
    elapsed_minutes=elapsed.total_seconds()/60
    remaining_minutes=pomodoro.focus_time-elapsed_minutes

    # 判断是否到时间
    is_time_up=remaining_minutes<= 0

    context={
        'pomodoro':pomodoro,
        'elapsed_minutes':round(elapsed_minutes,1),
        'remaining_minutes':round(remaining_minutes,1) if remaining_minutes > 0 else 0,
        'is_time_up':is_time_up,
    }
    return render(request,'tracker/pomodoro_running.html',context)

def pomodoro_complete(request,pk):
    """完成番茄钟"""
    pomodoro = get_object_or_404(PomodoroSession, pk=pk)
    if pomodoro.completed:
        messages.warning(request, '这个番茄钟已经完成了！')
        return redirect('pomodoro_list')

    pomodoro.end_time = timezone.now()
    pomodoro.completed = True
    pomodoro.save()

    # 自动创建学习记录
    duration = (pomodoro.end_time - pomodoro.start_time).total_seconds() / 60
    StudySession.objects.create(
        course=pomodoro.course,
        start_time=pomodoro.start_time,
        end_time=pomodoro.end_time,
        duration=duration,
        notes=f'番茄钟学习 - 专注时长：{pomodoro.focus_time}分钟'
    )

    messages.success(request, f'番茄钟完成！已自动创建学习记录（{duration:.1f}分钟）')
    return redirect('pomodoro_list')


def review_list(request):
    """复习计划列表"""
    reviews=ReviewSchedule.objects.all().order_by('review_date')
    courses=Course.objects.all()

    # 筛选
    course_id=request.GET.get('course')
    if course_id:
        reviews = reviews.filter(course_id=course_id)

    # 筛选未完成的
    show_completed = request.GET.get('show_completed', 'false') == 'true'
    if not show_completed:
        reviews = reviews.filter(completed=False)

    context={
        'reviews':reviews,
        'courses':courses,
    }
    return render(request, 'tracker/review_list.html', context)

def review_create(request):
    """创建复习计划"""
    if request.method=='POST':
        form=ReviewScheduleForm(request.POST)
        if form.is_valid():
            review=form.save(commit=False)
            # 如果用户没有指定复习日期，使用遗忘曲线算法自动生成
            if not review.review_date:
                from .utils.forgetting_curve import get_next_review_date
                from datetime import datetime
                # 使用当前日期作为学习日期
                study_date=datetime.now()
                next_review=get_next_review_date(study_date, review.review_count)
                review.review_date=next_review.date()
            review.save()
            messages.success(request,f'复习计划已创建！下次复习日期：{review.review_date}')
            return redirect('review_list')
    else:
        form = ReviewScheduleForm()

    return render(request,'tracker/review_form.html',{'form': form,'title':'创建复习计划'})

def review_auto_generate(request):
    """根据学习记录自动生成复习计划（使用遗忘曲线算法）"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        material_id = request.POST.get('material_id', '')

        if not course_id:
            messages.error(request, '请选择课程')
            return redirect('review_list')

        course=get_object_or_404(Course, pk=course_id)
        material=None
        if material_id:
            material = get_object_or_404(StudyMaterial, pk=material_id)

        # 获取该课程/资料最近的学习记录
        sessions=StudySession.objects.filter(course=course)
        if material:
            sessions=sessions.filter(material=material)
        sessions=sessions.order_by('-start_time')[:1]  # 只取最近一次

        if not sessions:
            messages.warning(request, f'课程"{course.name}"还没有学习记录，无法生成复习计划')
            return redirect('review_list')

        # 使用最近一次学习记录的开始时间作为学习日期
        last_session = sessions[0]
        study_date = last_session.start_time

        # 检查是否已有复习计划
        existing_reviews = ReviewSchedule.objects.filter(course=course, material=material)
        if material:
            existing_reviews = existing_reviews.filter(material=material)

        # 获取已完成的复习次数（使用最近的复习计划）
        completed_reviews = existing_reviews.filter(completed=True).order_by('-review_date')
        review_count = completed_reviews.count() if completed_reviews.exists() else 0

        # 生成复习计划（生成3个）
        schedule = generate_review_schedule(study_date, review_count, max_reviews=3)

        created_count = 0
        for review_date, review_num in schedule:
            # 检查是否已存在该日期的复习计划
            if not existing_reviews.filter(review_date=review_date.date()).exists():
                ReviewSchedule.objects.create(
                    course=course,
                    material=material,
                    review_date=review_date.date(),
                    review_count=review_count,
                    completed=False
                )
                created_count += 1

        if created_count > 0:
            messages.success(request, f'已为"{course.name}"自动生成{created_count}个复习计划（基于遗忘曲线算法）')
        else:
            messages.info(request, '复习计划已存在，无需重复生成')

        return redirect('review_list')

    # GET请求：显示选择表单
    courses = Course.objects.all()
    # 获取所有课程的学习资料（用于JavaScript动态加载）
    materials_by_course = {}
    for course in courses:
        materials = StudyMaterial.objects.filter(course=course)
        materials_by_course[course.pk] = [
            {'id': m.pk, 'name': m.name} for m in materials
        ]

    import json
    context = {
        'courses': courses,
        'materials_by_course_json': json.dumps(materials_by_course, ensure_ascii=False),
    }
    return render(request, 'tracker/review_auto_generate.html', context)

def review_complete(request, pk):
    """标记复习完成"""

    review=get_object_or_404(ReviewSchedule, pk=pk)
    review.completed=True
    review.review_count += 1
    review.save()

    # 自动生成下一次复习计划（基于遗忘曲线）
    # 使用创建时间作为学习日期，或者使用当前日期
    study_date = review.created_at if review.created_at else datetime.now()
    next_review_date = get_next_review_date(study_date, review.review_count)

    # 检查是否已存在下一次复习计划
    existing = ReviewSchedule.objects.filter(
        course=review.course,
        material=review.material,
        review_date=next_review_date.date()
    ).exists()

    if not existing:
        ReviewSchedule.objects.create(
            course=review.course,
            material=review.material,
            review_date=next_review_date.date(),
            review_count=review.review_count,
            completed=False
        )
        messages.success(request, f'复习已完成！已自动生成下次复习计划：{next_review_date.date()}')
    else:
        messages.success(request, '复习已完成！')

    return redirect('review_list')

def review_delete(request, pk):
    """删除复习计划"""
    review = get_object_or_404(ReviewSchedule, pk=pk)
    if request.method=='POST':
        review.delete()
        messages.success(request,'复习计划已删除')
        return redirect('review_list')
    return render(request, 'tracker/review_confirm_delete.html', {'review': review})


def knowledge_list(request):
    """知识点列表"""
    knowledge_points = KnowledgePoint.objects.all()
    courses = Course.objects.all()

    # 筛选
    course_id = request.GET.get('course')
    if course_id:
        knowledge_points = knowledge_points.filter(course_id=course_id)

    context = {
        'knowledge_points': knowledge_points,
        'courses': courses,
    }
    return render(request, 'tracker/knowledge_list.html', context)

def knowledge_create(request):
    """创建知识点"""
    if request.method == 'POST':
        form = KnowledgePointForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '知识点已创建！')
            return redirect('knowledge_list')
    else:
        form = KnowledgePointForm()

    return render(request, 'tracker/knowledge_form.html', {'form': form, 'title': '创建知识点'})

def knowledge_delete(request, pk):
    """删除知识点"""
    knowledge = get_object_or_404(KnowledgePoint, pk=pk)
    if request.method == 'POST':
        knowledge.delete()
        messages.success(request, '知识点已删除')
        return redirect('knowledge_list')
    return render(request, 'tracker/knowledge_confirm_delete.html', {'knowledge': knowledge})

# ========== 学习资料管理 ==========
def material_list(request):
    """学习资料列表"""
    materials=StudyMaterial.objects.all()
    courses=Course.objects.all()

    # 筛选
    course_id=request.GET.get('course')
    if course_id:
        materials=materials.filter(course_id=course_id)

    material_type=request.GET.get('material_type')
    if material_type:
        materials=materials.filter(material_type=material_type)

    context = {
        'materials':materials,
        'courses':courses,
        'material_types':StudyMaterial.MATERIAL_TYPES,
    }
    return render(request,'tracker/material_list.html',context)

def material_create(request):
    """创建学习资料"""
    if request.method=='POST':
        form=StudyMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'学习资料已创建！')
            return redirect('material_list')
    else:
        form = StudyMaterialForm()

    return render(request,'tracker/material_form.html',{'form': form, 'title': '创建学习资料'})

def material_update(request,pk):
    """编辑学习资料"""
    material=get_object_or_404(StudyMaterial, pk=pk)
    if request.method=='POST':
        form=StudyMaterialForm(request.POST,instance=material)
        if form.is_valid():
            form.save()
            messages.success(request,'学习资料已更新！')
            return redirect('material_list')
    else:
        form=StudyMaterialForm(instance=material)

    return render(request,'tracker/material_form.html',{'form': form, 'title': '编辑学习资料'})

def material_delete(request,pk):
    """删除学习资料"""
    material=get_object_or_404(StudyMaterial, pk=pk)
    if request.method=='POST':
        material.delete()
        messages.success(request,'学习资料已删除')
        return redirect('material_list')
    return render(request,'tracker/material_confirm_delete.html', {'material': material})


def dashboard(request):
    """仪表板：显示统计数据和图表"""
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    from pathlib import Path
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    from django.conf import settings
    import platform

    # 配置中文字体
    system = platform.system()
    if system == 'Windows':
        # Windows系统常用中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong', 'sans-serif']
    elif system == 'Darwin':  # macOS
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'STHeiti', 'sans-serif']
    else:  # Linux
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 统计数据
    total_sessions = StudySession.objects.count()
    total_time = StudySession.objects.aggregate(Sum('duration'))['duration__sum'] or 0
    total_time_hours = round(total_time / 60, 2)

    # 今日学习
    today = timezone.now().date()
    today_sessions = StudySession.objects.filter(start_time__date=today)
    today_time = today_sessions.aggregate(Sum('duration'))['duration__sum'] or 0
    today_time_hours = round(today_time / 60, 2)

    # 课程统计
    course_stats = Course.objects.annotate(
        total_time=Sum('studysession__duration')
    ).order_by('-total_time')[:5]

    # 生成图表
    charts_dir = Path(settings.BASE_DIR) / 'static' / 'charts'
    charts_dir.mkdir(parents=True, exist_ok=True)

    # 1. 学习时长趋势图（最近30天）
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_stats = StudySession.objects.filter(
        start_time__gte=thirty_days_ago
    ).extra(
        select={'day': "DATE(start_time)"}
    ).values('day').annotate(
        total_duration=Sum('duration')
    ).order_by('day')

    if daily_stats:
        dates = [item['day'] for item in daily_stats]
        hours = [round(item['total_duration'] / 60, 2) for item in daily_stats]

        plt.figure(figsize=(10, 6))
        plt.plot(dates, hours, marker='o')
        plt.title('学习时长趋势（最近30天）')
        plt.xlabel('日期')
        plt.ylabel('学习时长（小时）')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(str(charts_dir / 'trend.png'))
        plt.close()
        trend_chart = '/static/charts/trend.png'
    else:
        trend_chart = None

    # 2. 课程时间分布饼图
    if course_stats:
        course_names = [c.name for c in course_stats if c.total_time]
        course_times = [round((c.total_time or 0) / 60, 2) for c in course_stats if c.total_time]

        if course_names and course_times:
            plt.figure(figsize=(8, 8))
            plt.pie(course_times, labels=course_names, autopct='%1.1f%%')
            plt.title('课程时间分布')
            plt.savefig(str(charts_dir / 'course_distribution.png'))
            plt.close()
            distribution_chart = '/static/charts/course_distribution.png'
        else:
            distribution_chart = None
    else:
        distribution_chart = None

    context = {
        'total_sessions': total_sessions,
        'total_time_hours': total_time_hours,
        'today_time_hours': today_time_hours,
        'course_stats': course_stats,
        'trend_chart': trend_chart,
        'distribution_chart': distribution_chart,
    }
    return render(request, 'tracker/dashboard.html', context)


