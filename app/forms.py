from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Product, Category
from django.utils import timezone

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com (необязательно)'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваше имя (необязательно)'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['password1', 'password2']:
                field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'username':
                field.widget.attrs.update({'placeholder': 'Придумайте логин'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

class UserLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Запомнить меня'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'expiration_date', 'purchase_date',
            'quantity', 'unit', 'storage', 'priority', 
            'estimated_price', 'notes', 'notifications'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Молоко "Домик в деревне"'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'expiration_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'purchase_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1'
            }),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'storage': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'estimated_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительная информация о продукте...'
            }),
            'notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Выберите категорию..."
        
    def clean_expiration_date(self):
        expiration_date = self.cleaned_data['expiration_date']
        if expiration_date < timezone.now().date():
            raise forms.ValidationError("Дата истечения срока не может быть в прошлом!")
        return expiration_date
    
    def clean_purchase_date(self):
        purchase_date = self.cleaned_data.get('purchase_date')
        if purchase_date and purchase_date > timezone.now().date():
            raise forms.ValidationError("Дата покупки не может быть в будущем!")
        return purchase_date
    
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError("Количество должно быть больше 0")
        return quantity

class ProductFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Все категории",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'Все продукты'),
            ('active', 'Активные'),
            ('warning', 'Скоро истекает'),
            ('danger', 'Просрочено'),
            ('used', 'Использовано')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    storage = forms.ChoiceField(
        choices=[
            ('', 'Любое место хранения'),
            ('fridge', 'Холодильник'),
            ('freezer', 'Морозилка'),
            ('pantry', 'Кладовая'),
            ('room', 'Комнатная температура'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=[
            ('', 'Любой приоритет'),
            ('high', 'Высокий'),
            ('medium', 'Средний'),
            ('low', 'Низкий'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию...'
        })
    )
    sort = forms.ChoiceField(
        choices=[
            ('expiration_date', 'По сроку годности'),
            ('-expiration_date', 'По сроку годности (обратно)'),
            ('name', 'По названию'),
            ('priority', 'По приоритету'),
            ('-created_at', 'Сначала новые')
        ],
        required=False,
        initial='expiration_date',
        widget=forms.Select(attrs={'class': 'form-select'})
    )