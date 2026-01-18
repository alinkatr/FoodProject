from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, RecommendationTemplate

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_shelf_life_days', 'icon', 'product_count')
    search_fields = ('name',)
    list_editable = ('default_shelf_life_days', 'icon')
    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Количество продуктов'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'expiration_date', 
                   'days_remaining_display', 'status', 'priority')
    list_filter = ('status', 'category', 'priority', 'storage', 'expiration_date')
    search_fields = ('name', 'user__username', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'days_remaining_display')
    date_hierarchy = 'expiration_date'
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'name', 'category', 'status')
        }),
        ('Даты', {
            'fields': ('purchase_date', 'expiration_date')
        }),
        ('Характеристики', {
            'fields': ('quantity', 'unit', 'storage', 'priority', 'estimated_price')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'notifications')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days < 0:
            return format_html('<span style="color: red;">Просрочен</span>')
        elif days <= 2:
            return format_html('<span style="color: orange;">{} дней</span>', days)
        elif days <= 7:
            return format_html('<span style="color: blue;">{} дней</span>', days)
        else:
            return format_html('<span style="color: green;">{} дней</span>', days)
    days_remaining_display.short_description = 'Осталось дней'


@admin.register(RecommendationTemplate)
class RecommendationTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'days_before_expiry', 'is_active')
    list_filter = ('category', 'is_active', 'days_before_expiry')
    search_fields = ('title', 'text', 'category__name')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'days_before_expiry', 'title', 'text')
        }),
        ('Дополнительно', {
            'fields': ('icon', 'action_text', 'is_active')
        }),
    )