from django import forms
from django.core.validators import RegexValidator


class SessionForm(forms.Form):
    name = forms.CharField(
        label="ФИО",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше ФИО',
            'style': 'font-size: 16px; height: 40px;'
        })
    )

    run_number = forms.CharField(
        label="Номер прогона",
        max_length=20,
        validators=[RegexValidator(r'^\d+$', 'Введите только цифры')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите номер прогона',
            'style': 'font-size: 16px; height: 40px;'
        })
    )