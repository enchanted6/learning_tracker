
"""
AI 使用的工具
"""
import json
import os
from langchain_core.tools import tool
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Course, StudyMaterial, StudySession, ReviewSchedule, PomodoroSession, KnowledgePoint

# PDF解析相关导入
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.memory import ConversationBufferMemory

# 解析PDF
@tool
def parse_pdf(pdf_path:str,question:str)->str:
    """
    解析PDF并回答关于PDF文档内容的问题。
    当用户询问PDF中的概念、数据、内容或者需要基于PDF回答时使用这个工具。
    如果用户没有上传PDF并且询问问题，不需要使用这个工具，你根据自己的知识回答即可。
    参数：
        pdf_path: PDF文件的路径
        question: 用户提出的问题
        
    返回：
        基于PDF内容和AI的理解的详细准确的答案
    """
    api_key=os.environ.get('SCHOOL_LLM_API_KEY', '')
    if not api_key:
        raise ValueError("未配置API密钥，请设置环境变量 SCHOOL_LLM_API_KEY")
    model=ChatOpenAI(
        model="ecnu-max",
        api_key=api_key,
        base_url="https://chat.ecnu.edu.cn/open/api/v1",
        temperature=0.7
    )
    loader=PyPDFLoader(pdf_path)
    docs=loader.load()
    if not docs or len(docs)==0:
        raise ValueError("PDF文件为空或无法解析，请检查PDF文件是否有效")
    text_splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=['\n\n', '\n', '.', '。', '!', '?', '；', '；', '：', '，', '、', '']
    )
    texts=text_splitter.split_documents(docs)
    if not texts or len(texts) == 0:
        raise ValueError("PDF文本提取失败，请检查PDF文件内容")
    # 创建嵌入模型
    """
    LangChain 在 OpenAIEmbedding 模式下，
    默认会将 input 的字符串按 openai 的模型进行 Tokenize。
    此时提交接口的 input 将不再是字符串而是 token 数组。
    这对于非 openai 模型下实现的 OpenAI 兼容 api 是无法支持的。
    因此，需要设置 check_embedding_ctx_length=False 来关闭 Tokenize 行为。
    """
    embeddings=OpenAIEmbeddings(
        base_url="https://chat.ecnu.edu.cn/open/api/v1",  # 注意：不要加/embeddings，LangChain会自动添加
        model="ecnu-embedding-small",
        api_key=api_key,
        dimensions=1024,  # 学校模型返回1024维向量
        check_embedding_ctx_length=False  # 重要：关闭Tokenize，确保提交的是字符串而不是token数组
    )
    #  创建向量数据库
    db=FAISS.from_documents(texts, embeddings)
    retriever=db.as_retriever()
    # 创建对话记忆,每次调用都是新的，因为工具函数应该是无状态的
    memory=ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    chain=ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory,
    )
    response = chain.invoke({"question": question})
    if isinstance(response, dict):
        return response.get('answer', str(response))
    return str(response)

# 导入学习记录
# 获取当前时间工具（AI解析相对时间用）
@tool
def get_current_time() -> str:
    """获取当前日期和时间
    
    当用户询问"现在几点了"、"现在什么时间"、"当前时间"时，必须使用此工具。
    当需要解析相对时间（如"今天"、"昨天"、"现在"）时，使用此工具获取当前时间作为参考。
    
    Returns:
        当前时间的字符串，格式：YYYY-MM-DD HH:MM:SS（本地时间）
        例如：2025-12-23 16:01:38
    """
    from datetime import datetime
    # 使用本地时间，而不是UTC时间
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


# 搜索课程工具（帮助AI匹配课程）
@tool
def search_course(course_name: str)->str:
    """搜索课程
    
    当用户要求搜索课程、查找课程时，必须使用此工具。
    根据课程名称搜索数据库中的课程，支持模糊匹配。
    如果找到多个匹配，返回所有匹配的课程列表。
    
    Args:
        course_name: 课程名称（可以是部分名称，例如："数学"、"高等数学"）
        
    Returns:
        找到的课程信息，格式：
        - 单个匹配：{"found": true, "id": 1, "name": "高等数学（二）"}
        - 多个匹配：{"found": true, "matches": [{"id": 1, "name": "..."}, ...]}
        - 未找到：{"found": false, "message": "找不到课程"}
    """
    # 精确匹配
    course=Course.objects.filter(name=course_name).first()
    if course:
        return json.dumps({
            "found": True,
            "id": course.id,
            "name": course.name
        }, ensure_ascii=False)
    
    normalized_name=course_name.replace('（','(').replace('）',')')
    courses=Course.objects.filter(name__icontains=normalized_name)[:5]
    if courses:
        if len(courses)==1:
            return json.dumps({
                "found": True,
                "id": courses[0].id,
                "name": courses[0].name
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "found": True,
                "matches": [{"id": c.id, "name": c.name} for c in courses]
            }, ensure_ascii=False)
    
    return json.dumps({
        "found": False,
        "message": f"找不到课程'{course_name}'，请先创建该课程"
    }, ensure_ascii=False)
# 辅助函数：查找课程
def find_course_by_name(course_name:str):
    """根据课程名称查找课程（内部使用）"""
    # 精确匹配
    course=Course.objects.filter(name=course_name).first()
    if course:
        return course
    # 模糊匹配
    normalized_name = course_name.replace('（', '(').replace('）', ')')
    course = Course.objects.filter(name__icontains=normalized_name).first()
    return course
# 导入学习记录工具
@tool
def import_study_session(course_name:str,start_time:str,end_time:str,notes:str=""
)->str:
    """导入学习记录到数据库
    
    当用户确认学习记录信息后，使用此工具将学习记录导入系统。
    重要说明：
    - 时间参数必须是标准格式：YYYY-MM-DD HH:MM（例如：2025-12-23 13:00）
    - 不能使用相对时间（如"今天"、"昨天"），这些需要AI先调用get_current_time工具解析
    - 如果时间包含相对时间，AI应该先调用get_current_time，然后计算具体日期
    Args:
        course_name: 课程名称（必须与数据库中的课程名称匹配或相似）
        start_time: 开始时间（格式：YYYY-MM-DD HH:MM，例如：2025-12-23 13:00）
        end_time: 结束时间（格式：YYYY-MM-DD HH:MM）
        notes: 学习笔记（可选）
    Returns:
        导入结果信息：
        - 成功：返回详细的学习记录信息
        - 失败：返回错误信息
    """
    try:
        # 1. 查找课程
        course=find_course_by_name(course_name)
        if not course:
            return f"❌ 错误：找不到课程'{course_name}'。请先创建该课程，或使用search_course工具查找相似课程。"
        # 2. 解析时间
        try:
            start_dt=datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            end_dt=datetime.strptime(end_time, "%Y-%m-%d %H:%M")
        except ValueError:
            return f"❌ 时间格式错误。请使用格式：YYYY-MM-DD HH:MM（例如：2025-12-23 13:00）"
        # 3. 验证时间
        if end_dt<=start_dt:
            return f"❌ 错误：结束时间必须晚于开始时间。"
        # 4. 计算时长（分钟）
        duration=(end_dt - start_dt).total_seconds() / 60
        # 5. 创建学习记录
        session=StudySession.objects.create(
            course=course,
            start_time=start_dt,
            end_time=end_dt,
            duration=duration,
            notes=notes
        )
        
        return f"✅ 学习记录已成功导入！\n课程：{course.name}\n时间：{start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}\n时长：{duration:.0f}分钟"
        
    except Exception as e:
        return f"❌ 导入失败：{str(e)}"

# 导入学习资料记录
