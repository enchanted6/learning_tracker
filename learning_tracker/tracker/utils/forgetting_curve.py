"""
遗忘曲线算法（艾宾浩斯遗忘曲线）
用于自动生成复习计划
"""
from datetime import datetime, timedelta
from typing import List, Tuple


def calculate_review_dates(study_date: datetime, review_count: int = 0) -> List[datetime]:
    """
    根据艾宾浩斯遗忘曲线计算复习日期
    
    复习间隔（基于遗忘曲线）：
    - 第1次复习：学习后1天
    - 第2次复习：学习后3天（第1次复习后2天）
    - 第3次复习：学习后7天（第2次复习后4天）
    - 第4次复习：学习后15天（第3次复习后8天）
    - 第5次复习：学习后30天（第4次复习后15天）
    - 第6次复习：学习后60天（第5次复习后30天）
    - 之后每30天复习一次
    
    Args:
        study_date: 学习日期（datetime对象）
        review_count: 已完成的复习次数（默认0，表示首次学习）
    
    Returns:
        复习日期列表（datetime对象列表）
    """
    # 复习间隔（天）
    intervals = [1, 2, 4, 8, 15, 30]  # 前6次复习的间隔
    
    review_dates = []
    current_date = study_date
    
    # 如果已经完成了一些复习，从对应的间隔开始
    if review_count > 0:
        # 计算已完成的复习日期
        cumulative_days = 0
        for i in range(min(review_count, len(intervals))):
            cumulative_days += intervals[i]
            current_date = study_date + timedelta(days=cumulative_days)
        
        # 如果已完成所有基础间隔，使用固定30天间隔
        if review_count >= len(intervals):
            days_since_last = 30 * (review_count - len(intervals) + 1)
            current_date = study_date + timedelta(days=sum(intervals) + days_since_last)
    
    # 生成未来的复习日期（最多生成5个）
    max_future_reviews = 5
    for i in range(max_future_reviews):
        if review_count == 0 and i == 0:
            # 第一次复习：学习后1天
            next_date = study_date + timedelta(days=intervals[0])
        elif review_count + i < len(intervals):
            # 使用预定义的间隔
            cumulative_days = sum(intervals[:review_count + i + 1])
            next_date = study_date + timedelta(days=cumulative_days)
        else:
            # 使用固定30天间隔
            base_days = sum(intervals)
            additional_days = 30 * (review_count + i - len(intervals) + 1)
            next_date = study_date + timedelta(days=base_days + additional_days)
        
        review_dates.append(next_date)
    
    return review_dates


def get_next_review_date(study_date: datetime, review_count: int = 0) -> datetime:
    """
    获取下一次复习日期
    
    Args:
        study_date: 学习日期
        review_count: 已完成的复习次数
    
    Returns:
        下一次复习日期
    """
    review_dates = calculate_review_dates(study_date, review_count)
    return review_dates[0] if review_dates else study_date + timedelta(days=1)


def generate_review_schedule(study_date: datetime, review_count: int = 0, max_reviews: int = 5) -> List[Tuple[datetime, int]]:
    """
    生成完整的复习计划
    
    Args:
        study_date: 学习日期
        review_count: 已完成的复习次数
        max_reviews: 最多生成多少个复习计划
    
    Returns:
        [(复习日期, 复习次数), ...] 列表
    """
    review_dates = calculate_review_dates(study_date, review_count)
    
    schedule = []
    for i, review_date in enumerate(review_dates[:max_reviews]):
        schedule.append((review_date, review_count + i + 1))
    
    return schedule


def get_retention_rate(days_since_study: int, review_count: int = 0) -> float:
    """
    计算记忆保留率（基于遗忘曲线）
    
    艾宾浩斯遗忘曲线：
    - 1小时后：保留率约44%
    - 1天后：保留率约26%
    - 1周后：保留率约23%
    - 1个月后：保留率约21%
    
    每次复习后，遗忘速度会减慢
    
    Args:
        days_since_study: 距离学习的天数
        review_count: 已完成的复习次数
    
    Returns:
        记忆保留率（0-1之间的小数）
    """
    # 基础遗忘曲线（无复习）
    if days_since_study <= 0:
        return 1.0
    elif days_since_study == 1:
        base_retention = 0.26
    elif days_since_study <= 7:
        base_retention = 0.23
    elif days_since_study <= 30:
        base_retention = 0.21
    else:
        base_retention = max(0.1, 0.21 - (days_since_study - 30) * 0.001)
    
    # 每次复习可以提高保留率
    review_boost = review_count * 0.15
    retention = min(1.0, base_retention + review_boost)
    
    return retention


def should_review_now(study_date: datetime, review_count: int = 0, current_date: datetime = None) -> bool:
    """
    判断是否应该现在复习
    
    Args:
        study_date: 学习日期
        review_count: 已完成的复习次数
        current_date: 当前日期（如果为None，使用datetime.now()）
    
    Returns:
        是否应该复习
    """
    if current_date is None:
        current_date = datetime.now()
    
    next_review_date = get_next_review_date(study_date, review_count)
    
    # 如果当前日期已经到达或超过复习日期，应该复习
    return current_date.date() >= next_review_date.date()

