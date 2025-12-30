from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import StudySession, Course  # 导入Course用于筛选
from .forms import StudySessionForm

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
    return render(request, 'sessions/session_list.html', context)


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
    template='templates/course'
    
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
    template_name = 'tracker/templates/courses/agent.html'# ?有什么用
    def get(self,request):
        """显示聊天页面"""
        pdf_path=request.session.get('pdf_file_path')
        pdf_name=request.session.get('pdf_file_name', '')
        
        context={
            'has_pdf': bool(pdf_path),
            'pdf_name': pdf_name,
        }
        return render(request,'courses/agent.html', context)


def agent_chat(request):
    """处理Agent聊天请求"""
    if request.method!='POST':
        return JsonResponse({'error':'只支持POST请求'},status=400)
    # 获取用户消息
    question=request.POST.get('question', '').strip()
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
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=temp_dir) as temp_file:
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

