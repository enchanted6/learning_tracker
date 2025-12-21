from django import forms
from .models import StudySession


class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['course', 'start_time', 'end_time', 'notes']
        widgets = {
            # 使用 HTML5 datetime-local 输入框
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        # 验证逻辑：结束时间不能早于开始时间
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if start and end and end < start:
            raise forms.ValidationError("结束时间不能早于开始时间！")