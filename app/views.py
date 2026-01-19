from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, F
from datetime import timedelta, datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np

from .models import Product, Category, RecommendationTemplate
from .forms import ProductForm, ProductFilterForm, UserRegisterForm, UserLoginForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

def index(request):
    context = {}
    if request.user.is_authenticated:
        products = Product.objects.filter(user=request.user)
        
        total = products.count()
        expiring = products.filter(
            expiration_date__lte=timezone.now().date() + timedelta(days=2),
            expiration_date__gte=timezone.now().date(),
            status='active'
        ).count()
        expired = products.filter(
            expiration_date__lt=timezone.now().date(),
            status='active'
        ).count()

        if products.exists():

            data = []
            for p in products.filter(status='active'):
                data.append({
                    'name': p.name,
                    'category': p.category.name if p.category else 'Без категории',
                    'days_left': p.days_remaining,
                    'expiration_date': p.expiration_date,
                })
            
            if data:
                df = pd.DataFrame(data)
                category_stats = df.groupby('category').agg({
                    'name': 'count',
                    'days_left': ['mean', 'min']
                }).round(1)

                plt.figure(figsize=(10, 5))
                categories = df['category'].value_counts().head(5)
                plt.bar(categories.index, categories.values, color=['#28a745', '#17a2b8', '#ffc107', '#dc3545', '#6c757d'])
                plt.title('Топ-5 категорий продуктов')
                plt.xlabel('Категория')
                plt.ylabel('Количество')
                plt.xticks(rotation=45)
                plt.tight_layout()
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                plt.close()
                
                graphic = base64.b64encode(image_png).decode('utf-8')
                context['graphic'] = graphic

        recent_products = products.filter(status='active').order_by('-created_at')[:5]

        recommendations = get_recommendations(request.user)
        
        context.update({
            'total': total,
            'expiring': expiring,
            'expired': expired,
            'recent_products': recent_products,
            'recommendations': recommendations[:3],
        })
    
    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html')


@login_required
def product_list(request):
    products = Product.objects.filter(user=request.user)
    
    form = ProductFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['category']:
            products = products.filter(category=form.cleaned_data['category'])
        
        status = form.cleaned_data['status']
        if status == 'warning':
            products = products.filter(
                expiration_date__lte=timezone.now().date() + timedelta(days=2),
                expiration_date__gte=timezone.now().date(),
                status='active'
            )
        elif status == 'danger':
            products = products.filter(
                expiration_date__lt=timezone.now().date(),
                status='active'
            )
        elif status == 'used':
            products = products.filter(status='used')
        elif status == 'active':
            products = products.filter(status='active')
        
        if form.cleaned_data['search']:
            search_term = form.cleaned_data['search']
            products = products.filter(
                Q(name__icontains=search_term) | 
                Q(notes__icontains=search_term)
            )
        
        if form.cleaned_data['sort']:
            products = products.order_by(form.cleaned_data['sort'])
        else:
            products = products.order_by('expiration_date')
    else:
        products = products.order_by('expiration_date')

    product_stats = products.aggregate(
        total_quantity=Count('id'),
        avg_days_left=Count('expiration_date')
    )
    
    context = {
        'products': products,
        'form': form,
        'categories': Category.objects.all(),
        'product_stats': product_stats,
    }
    return render(request, 'product_list.html', context)


@login_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            messages.success(request, f'Продукт "{product.name}" успешно добавлен!')
            
            similar_products = Product.objects.filter(
                user=request.user,
                name__icontains=product.name,
                status='active'
            ).exclude(id=product.id)[:3]
            
            if similar_products:
                context = {
                    'product': product,
                    'similar_products': similar_products,
                }
                return render(request, 'product_add_success.html', context)
            
            return redirect('product_list')
    else:
        form = ProductForm()
    
    if not form.is_bound:
        tomorrow = timezone.now().date() + timedelta(days=1)
        form.initial['expiration_date'] = tomorrow
        form.initial['purchase_date'] = timezone.now().date()
    
    context = {
        'form': form,
        'categories': Category.objects.all(),
    }
    return render(request, 'product_add.html', context)


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Продукт "{product.name}" успешно обновлен!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'product_edit.html', context)


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Продукт "{product_name}" успешно удален!')
        return redirect('product_list')
    
    return render(request, 'product_delete.html', {'product': product})


@login_required
def product_mark_used(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        product.status = 'used'
        product.save()
        used_today = Product.objects.filter(
            user=request.user,
            status='used',
            updated_at__date=timezone.now().date()
        ).count()
        
        messages.success(request, 
            f'Продукт "{product.name}" отмечен как использованный! '
            f'Сегодня вы использовали {used_today} продуктов.'
        )
    
    return redirect('product_list')


@login_required
def product_statistics(request):
    products = Product.objects.filter(user=request.user, status='active')
    
    if not products.exists():
        return render(request, 'product_statistics.html', {
            'message': 'У вас пока нет активных продуктов для анализа.'
        })

    data = []
    for p in products:
        data.append({
            'name': p.name,
            'category': p.category.name if p.category else 'Без категории',
            'days_left': p.days_remaining,
            'expiration_date': p.expiration_date,
            'priority': p.priority,
            'quantity': p.quantity,
        })
    
    df = pd.DataFrame(data)

    category_stats = df.groupby('category').agg({
        'name': 'count',
        'days_left': ['mean', 'min', 'max'],
        'quantity': 'sum'
    }).round(2)
    
    urgency_stats = {
        'danger': len(df[df['days_left'] < 0]),
        'warning': len(df[(df['days_left'] >= 0) & (df['days_left'] <= 2)]),
        'info': len(df[(df['days_left'] > 2) & (df['days_left'] <= 7)]),
        'safe': len(df[df['days_left'] > 7]),
    }

    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    category_counts = df['category'].value_counts()
    plt.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%')
    plt.title('Распределение по категориям')

    plt.subplot(1, 2, 2)
    urgency_labels = ['Просрочено', 'Скоро истекает', 'На этой неделе', 'В норме']
    urgency_values = [urgency_stats['danger'], urgency_stats['warning'], 
                     urgency_stats['info'], urgency_stats['safe']]
    colors = ['#dc3545', '#ffc107', '#17a2b8', '#28a745']
    plt.bar(urgency_labels, urgency_values, color=colors)
    plt.title('Статус продуктов по срочности')
    plt.ylabel('Количество')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    context = {
        'total_products': len(df),
        'category_stats': category_stats.to_dict(),
        'urgency_stats': urgency_stats,
        'graphic': graphic,
        'avg_days_left': df['days_left'].mean(),
        'min_days_left': df['days_left'].min(),
        'max_days_left': df['days_left'].max(),
    }
    
    return render(request, 'product_statistics.html', context)


@login_required
def recommendations(request):
    user_products = Product.objects.filter(
        user=request.user,
        status='active',
        expiration_date__gte=timezone.now().date()
    )
    
    recommendations_list = get_recommendations(request.user)
    if user_products.exists():
        data = []
        for p in user_products:
            data.append({
                'name': p.name,
                'days_left': p.days_remaining,
                'category': p.category.name if p.category else 'Без категории',
            })
        
        df = pd.DataFrame(data)

        soon_expiring = df[df['days_left'] <= 3]
        if not soon_expiring.empty:
            category_rec = soon_expiring['category'].mode()
            if len(category_rec) > 0:
                most_common_category = category_rec[0]

                personal_recommendation = {
                    'title': f'Сосредоточьтесь на {most_common_category}',
                    'text': f'У вас {len(soon_expiring[soon_expiring["category"] == most_common_category])} '
                           f'продуктов из категории "{most_common_category}" скоро истекает. '
                           f'Рекомендуем использовать их в первую очередь.',
                    'urgency': 'urgent'
                }

                recommendations_list.insert(0, {
                    'product': None,
                    'template': type('obj', (object,), personal_recommendation),
                    'days_remaining': 0,
                    'urgency': 'urgent'
                })
    # money_saved = len(recommendations_list) * 150
    
    context = {
        'recommendations': recommendations_list,
        'total_recommendations': len(recommendations_list),
        'expiring_count': user_products.filter(
            expiration_date__lte=timezone.now().date() + timedelta(days=3)
        ).count(),
        # 'monthly_savings': money_saved,
        'saved_products': len(recommendations_list),
    }
    return render(request, 'recommendations.html', context)


def get_recommendations(user):
    recommendations = []
    today = timezone.now().date()
    
    user_products = Product.objects.filter(
        user=user,
        status='active'
    ).select_related('category')
    
    for product in user_products:
        days_remaining = (product.expiration_date - today).days
        if days_remaining <= 0:
            recommendations.append({
                'product': product,
                'template': type('obj', (object,), {
                    'title': 'Продукт просрочен!',
                    'text': f'Продукт "{product.name}" уже просрочен. Рекомендуем проверить его состояние и выбросить, если испорчен.',
                    'icon': 'fas fa-skull-crossbones',
                    'action_text': 'Удалить продукт',
                    'action_link': f'/products/{product.id}/delete/'
                }),
                'days_remaining': days_remaining,
                'urgency': 'danger'
            })
        elif days_remaining <= 2:
            recommendations.append({
                'product': product,
                'template': type('obj', (object,), {
                    'title': 'Срочно используйте!',
                    'text': f'Продукт "{product.name}" истекает через {days_remaining} дня. '
                           f'Рекомендуем использовать сегодня.',
                    'icon': 'fas fa-exclamation-triangle',
                    'action_text': 'Отметить использованным',
                    'action_link': f'/products/{product.id}/mark_used/'
                }),
                'days_remaining': days_remaining,
                'urgency': 'warning'
            })
        elif days_remaining <= 7:
            recommendations.append({
                'product': product,
                'template': type('obj', (object,), {
                    'title': 'Запланируйте использование',
                    'text': f'Продукт "{product.name}" истекает через {days_remaining} дней. '
                           f'Рекомендуем запланировать его использование на этой неделе.',
                    'icon': 'fas fa-calendar-check',
                    'action_text': 'Посмотреть рецепты',
                    'action_link': f'https://www.russianfood.com/search/?query={product.name}'
                }),
                'days_remaining': days_remaining,
                'urgency': 'info'
            })
    
    recommendations.sort(key=lambda x: x['days_remaining'])
    
    return recommendations


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            login(request, user)
            
            messages.success(request, f'Аккаунт {user.username} успешно создан! Добро пожаловать!')
            return redirect('index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegisterForm()
    
    return render(request, 'register.html', {'form': form})



def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            remember_me = request.POST.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)
            
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})



@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('index')