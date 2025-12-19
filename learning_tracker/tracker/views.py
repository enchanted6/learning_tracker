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

# ========== 接口变化说明 ==========
# 1. LLM模型接口变化：
#    旧：OpenAI() -> 使用 /v1/completions 接口（已废弃，学校API不支持）
#    新：ChatOpenAI() -> 使用 /v1/chat/completions 接口（学校API支持）
#
# 2. Memory接口变化：
#    旧：ConversationBufferMemory(memory_key="...", return_messages=True)
#    新：ConversationBufferMemory(chat_memory=ChatMessageHistory(), ...)
#    原因：消除LangChain deprecation warning，使用新版本API
#
# 3. Embeddings接口（无变化）：
#    OpenAIEmbeddings() 保持不变，但需要设置：
#    - check_embedding_ctx_length=False（关闭Tokenize）
#    - dimensions=1024（学校模型返回1024维向量）
# ====================================

def agent(api_key,question,memory,file):
    ''' 使用chat ecnu的pdf回答助手'''
    import tempfile
    # 使用ChatOpenAI而不是OpenAI（使用chat/completions接口而不是completions接口）
    model = ChatOpenAI(
        model="ecnu-max",
        api_key=api_key,
        base_url="https://chat.ecnu.edu.cn/open/api/v1",
        temperature=0.7
    )
    
    # 保存上传的文件到临时文件
    content=file.read()
    # 使用临时文件，自动清理
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(content)
    loader=PyPDFLoader(temp_file_path)
    docs=loader.load()
    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=['\n\n','\n','.','。','!','?','；','；','：','，','、','']
    )
    texts=text_splitter.split_documents(docs)
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
    try:
        db=FAISS.from_documents(texts,embeddings)
        retriever=db.as_retriever()
        chain=ConversationalRetrievalChain.from_llm(
            llm=model,
            retriever=retriever,
            memory=memory,
        )
        response=chain.invoke({"question":question})
        return response
    finally:
        # 清理临时文件
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except:
            pass


# PDF问答助手视图
class PDFAssistantView(View):
    """PDF学习助手页面"""
    template_name='pdf_assistant.html'
    
    def get(self, request):
        """显示上传页面"""
        return render(request, self.template_name)
    
    def post(self, request):
        """处理PDF上传和问答"""
        file=request.FILES.get('pdf_file')
        question=request.POST.get('question', '')
        
        if not file:
            return JsonResponse({'error': '请上传PDF文件'}, status=400)
        if not question:
            return JsonResponse({'error': '请输入问题'}, status=400)
        
        # 从环境变量获取API密钥
        api_key = os.environ.get('SCHOOL_LLM_API_KEY', '')
        if not api_key:
            return JsonResponse({'error': 'API密钥未配置'}, status=500)
        
        try:
            # 创建会话记忆
            chat_history=ChatMessageHistory()
            memory=ConversationBufferMemory(
                chat_memory=chat_history,
                memory_key="chat_history",
                return_messages=True
            )
            
            # 调用agent函数
            response = agent(api_key, question, memory, file)
            
            # 处理响应格式
            if isinstance(response, dict):
                answer=response.get('answer', response.get('text', '无法获取回答'))
            else:
                answer=str(response)
            
            return JsonResponse({'answer': answer})
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            # 开发环境显示详细错误
            import sys
            print(f"错误详情:\n{error_detail}", file=sys.stderr)
            return JsonResponse({
                'error': f'处理失败: {str(e)}',
                'detail': error_detail  # 开发时显示详细错误
            }, status=500)











