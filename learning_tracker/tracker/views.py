from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from .models import Course
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from langchain.memory import ConversationBufferMemory
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
from langchain_openai import OpenAIEmbeddings
from langchain_openai import OpenAI

def agent(api_key,question,memory,file):
    ''' 使用chat ecnu的pdf回答助手'''
    model=OpenAI(model="ecnu-max",api_key=api_key,base_url="https://chat.ecnu.edu.cn/open/api/v1")
    content=file.read()
    temp_file_path="./temp.pdf"
    with open(temp_file_path,"wb") as f:
        f.write(content)
    loader=PyPDFLoader(temp_file_path)
    docs=loader.load()
    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=['\n\n','\n','.','。','!','?','；','；','：','，','、','']
    )
    texts=text_splitter.split_documents(docs)
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small",api_key=api_key,base_url="https://api.aigc369.com/v1")
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
    template_name = 'pdf_assistant.html'
    
    def get(self, request):
        """显示上传页面"""
        return render(request, self.template_name)
    
    def post(self, request):
        """处理PDF上传和问答"""
        file = request.FILES.get('pdf_file')
        question = request.POST.get('question', '')
        
        if not file:
            return JsonResponse({'error': '请上传PDF文件'}, status=400)
        if not question:
            return JsonResponse({'error': '请输入问题'}, status=400)
        
        # 从环境变量获取API密钥
        api_key = os.environ.get('OPENAI_API_KEY', '')
        if not api_key:
            return JsonResponse({'error': 'API密钥未配置'}, status=500)
        
        try:
            # 创建会话记忆
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            # 调用agent函数
            response = agent(api_key, question, memory, file)
            answer = response.get('answer', '无法获取回答')
            return JsonResponse({'answer': answer})
        except Exception as e:
            return JsonResponse({'error': f'处理失败: {str(e)}'}, status=500)











