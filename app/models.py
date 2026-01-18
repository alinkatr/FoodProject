from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    default_shelf_life_days = models.IntegerField(
        default=7, 
        verbose_name="Срок хранения по умолчанию (дней)",
        validators=[MinValueValidator(1)]
    )
    icon = models.CharField(
        max_length=50, 
        default='fas fa-archive',
        verbose_name="Иконка"
    )
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Продукт пользователя"""
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('used', 'Использован'),
        ('expired', 'Просрочен'),
        ('thrown', 'Выброшен'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    STORAGE_CHOICES = [
        ('fridge', 'Холодильник'),
        ('freezer', 'Морозилка'),
        ('pantry', 'Кладовая'),
        ('room', 'Комнатная температура'),
    ]
    
    UNIT_CHOICES = [
        ('шт', 'шт'),
        ('кг', 'кг'),
        ('г', 'г'),
        ('л', 'л'),
        ('мл', 'мл'),
        ('уп', 'уп'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name="Пользователь"
    )
    name = models.CharField(max_length=200, verbose_name="Название продукта")
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        verbose_name="Категория"
    )
    expiration_date = models.DateField(verbose_name="Срок годности до")
    purchase_date = models.DateField(
        default=timezone.now, 
        verbose_name="Дата покупки"
    )
    quantity = models.FloatField(
        default=1, 
        verbose_name="Количество",
        validators=[MinValueValidator(0.1)]
    )
    unit = models.CharField(
        max_length=10, 
        default='шт',
        choices=UNIT_CHOICES,
        verbose_name="Единица измерения"
    )
    storage = models.CharField(
        max_length=20,
        choices=STORAGE_CHOICES,
        blank=True,
        verbose_name="Место хранения"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Приоритет использования"
    )
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Примерная стоимость"
    )
    notes = models.TextField(blank=True, verbose_name="Заметки")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус"
    )
    notifications = models.BooleanField(
        default=True,
        verbose_name="Уведомления"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ['expiration_date', 'priority']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    @property
    def days_remaining(self):
        delta = self.expiration_date - timezone.now().date()
        return delta.days
    
    @property
    def status_color(self):
        days = self.days_remaining
        if days < 0:
            return 'danger'
        elif days <= 2:
            return 'warning'
        elif days <= 7:
            return 'info'
        else:
            return 'success'


class RecommendationTemplate(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name="Категория"
    )
    days_before_expiry = models.IntegerField(
        verbose_name="За сколько дней до истечения срока",
        validators=[MinValueValidator(0)]
    )
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст рекомендации")
    action_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Текст действия"
    )
    icon = models.CharField(
        max_length=50,
        default='fas fa-lightbulb',
        verbose_name="Иконка"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    class Meta:
        verbose_name = "Шаблон рекомендации"
        verbose_name_plural = "Шаблоны рекомендаций"
        ordering = ['days_before_expiry']
    
    def __str__(self):
        return f"{self.title} ({self.days_before_expiry} дней)"
