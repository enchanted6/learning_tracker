from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from .models import Course
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
import os
# Create your views here.
'''
Created by :刘思扬 
利用通用视图ListView, DetailView, CreateView, UpdateView, DeleteView
编写视图（我是懒人）
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

# ai pdf 回答助手函数
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

def agent(api_key, question, memory, pdf_file_path):
    ''' 使用chat ecnu的pdf回答助手（接受文件路径）'''
    # 使用ChatOpenAI而不是OpenAI（使用chat/completions接口而不是completions接口）
    model = ChatOpenAI(
        model="ecnu-max",
        api_key=api_key,
        base_url="https://chat.ecnu.edu.cn/open/api/v1",
        temperature=0.7
    )
    
    # 从文件路径加载PDF
    loader = PyPDFLoader(pdf_file_path)
    docs=loader.load()
    
    # 检查PDF是否为空
    if not docs or len(docs) == 0:
        raise ValueError("PDF文件为空或无法解析，请检查PDF文件是否有效")
    
    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=['\n\n','\n','.','。','!','?','；','；','：','，','、','']
    )
    texts=text_splitter.split_documents(docs)
    
    # 检查文本是否为空
    if not texts or len(texts) == 0:
        raise ValueError("PDF文本提取失败，请检查PDF文件内容")
    # 使用学校提供的嵌入模型（根据官方文档配置）
    """
    LangChain 在 OpenAIEmbedding 模式下，
    默认会将 input 的字符串按 openai 的模型进行
     Tokenize。此时提交接口的 input 将不再是字
     符串而是 token 数组。这对于非 openai 模型
     下实现的的 OpenAI 兼容 api 是无法支持的。
     因此，需要设置 check_embedding_ctx_length=False 
     来关闭 Tokenize 行为。
    """
    embeddings = OpenAIEmbeddings(
        base_url="https://chat.ecnu.edu.cn/open/api/v1",  # 注意：不要加/embeddings，LangChain会自动添加
        model="ecnu-embedding-small",
        api_key=api_key,
        dimensions=1024,  # 学校模型返回1024维向量
        check_embedding_ctx_length=False  # 重要：关闭Tokenize，确保提交的是字符串而不是token数组
    )
    db=FAISS.from_documents(texts,embeddings)
    retriever=db.as_retriever()
    chain=ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory,
    )
    response=chain.invoke({"question":question})
    return response


# PDF问答助手视图
class PDFAssistantView(View):
    """PDF学习助手页面"""
    template_name='pdf_assistant.html'
    
    def get(self, request):
        """显示聊天页面"""
        return render(request, self.template_name)


def upload_pdf(request):
    """上传PDF文件（只上传一次）"""
    if request.method != 'POST':
        return JsonResponse({'error': '只支持POST请求'}, status=400)
    
    file = request.FILES.get('pdf_file')
    if not file:
        return JsonResponse({'error': '请上传PDF文件'}, status=400)
    
    import tempfile
    import pickle
    
    try:
        # 确保temp目录存在
        temp_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存PDF到临时文件
        content=file.read()
        with tempfile.NamedTemporaryFile(delete=False,suffix='.pdf',dir=temp_dir) as temp_file:
            temp_file_path=temp_file.name
            temp_file.write(content)
        
        # 保存文件路径到session
        request.session['pdf_file_path'] = temp_file_path
        request.session['pdf_file_name'] = file.name
        
        # 初始化对话历史（新的PDF，重置对话）
        request.session['chat_messages'] = []  # 存储消息列表：[{'role': 'human', 'content': '...'}, ...]
        
        return JsonResponse({
            'success': True,
            'filename': file.name,
            'message': 'PDF上传成功，可以开始对话了！'
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        import sys
        print(f"上传错误:\n{error_detail}", file=sys.stderr)
        return JsonResponse({
            'error': f'上传失败: {str(e)}'
        }, status=500)


def chat(request):
    """对话接口"""
    if request.method!='POST':
        return JsonResponse({'error': '只支持POST请求'}, status=400)
    
    question=request.POST.get('question', '').strip()
    if not question:
        return JsonResponse({'error': '请输入问题'}, status=400)
    
    # 检查是否已上传PDF
    pdf_file_path=request.session.get('pdf_file_path')
    if not pdf_file_path or not os.path.exists(pdf_file_path):
        return JsonResponse({'error': '请先上传PDF文件'}, status=400)
    
    # 从环境变量获取API密钥
    api_key=os.environ.get('SCHOOL_LLM_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'API密钥未配置'}, status=500)
    
    try:
        # 从session恢复对话历史
        chat_messages=request.session.get('chat_messages', [])
        chat_history=ChatMessageHistory()
        
        # 重建历史消息
        for msg in chat_messages:
            if msg['role']== 'human':
                chat_history.add_user_message(msg['content'])
            elif msg['role']== 'ai':
                chat_history.add_ai_message(msg['content'])
        
        memory=ConversationBufferMemory(
            chat_memory=chat_history,
            memory_key="chat_history",
            return_messages=True
        )
        
        # 调用agent函数
        response=agent(api_key, question, memory, pdf_file_path)

        # 处理响应格式 - ConversationalRetrievalChain返回的是字典
        if isinstance(response, dict):
            # 从字典中提取答案
            answer = response.get('answer', '')
            if not answer:
                # 如果没有answer键，尝试其他可能的键
                answer = response.get('text', '') or response.get('result', '')
            if not answer:
                # 如果还是没有，打印调试信息
                print(f"响应格式: {response.keys()}")
                answer = '无法获取回答，请检查响应格式'
        else:
            # 如果不是字典，直接转字符串
            answer = str(response)
        
        # 确保答案不为空
        if not answer or answer.strip() == '':
            answer = '抱歉，无法获取回答，请重试。'
        
        # 保存新的对话到session
        chat_messages.append({'role': 'human', 'content': question})
        chat_messages.append({'role': 'ai', 'content': answer})
        request.session['chat_messages'] = chat_messages
        
        return JsonResponse({
            'answer': answer,
            'question': question
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        import sys
        print(f"对话错误:\n{error_detail}", file=sys.stderr)
        return JsonResponse({
            'error': f'处理失败: {str(e)}',
            'detail': error_detail
        }, status=500)


def clear_chat(request):
    """清除对话历史"""
    if request.method == 'POST':
        import os
        # 删除PDF文件
        pdf_file_path=request.session.get('pdf_file_path')
        if pdf_file_path and os.path.exists(pdf_file_path):
            try:
                os.remove(pdf_file_path)
            except:
                pass
        request.session.pop('pdf_file_path', None)
        request.session.pop('pdf_file_name', None)
        request.session.pop('chat_messages', None)
        return JsonResponse({'success': True, 'message': '对话已清除'})
    return JsonResponse({'error': '只支持POST请求'}, status=400)











