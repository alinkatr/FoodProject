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
    """Главная страница с аналитикой"""
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
    """Страница "О проекте" """
    return render(request, 'about.html')
