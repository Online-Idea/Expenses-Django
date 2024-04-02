from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.db.models import Q
from slugify import slugify
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ClientManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self.create_user(email, password, **extra_fields)


class Client(AbstractUser, PermissionsMixin):
    class ChargeType(models.TextChoices):
        CALLS = 'звонки', _('Звонки')
        COMMISSION_PERCENT = 'комиссия процент', _('Комиссия Процент')
        COMMISSION_SUM = 'комиссия сумма', _('Комиссия Сумма')

    username = models.CharField(max_length=255, verbose_name='Имя')
    email = models.EmailField(unique=True)
    slug = models.SlugField(max_length=300, allow_unicode=True, db_index=True, verbose_name='Slug')
    manager = models.CharField(max_length=255, null=True, verbose_name='Менеджер')
    active = models.BooleanField(default='1', verbose_name='Активен')
    charge_type = models.CharField(max_length=255, choices=ChargeType.choices, default='звонки', verbose_name='Тип')
    commission_size = models.FloatField(null=True, blank=True, verbose_name='Размер комиссии')
    teleph_id = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name='Имя в телефонии')
    autoru_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id авто.ру')
    autoru_name = models.CharField(max_length=500, null=True, blank=True, verbose_name='Имя на авто.ру')
    avito_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id авито')
    drom_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='id drom')
    is_staff = models.BooleanField(default=False)

    objects = ClientManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        self.slug = slugify(self.username)
        if not self.slug:
            slug_str = f'{self.username}'
            self.slug = slugify(slug_str)
        slug_exists = Client.objects.filter(~Q(id=self.id), slug=self.slug)
        if slug_exists.count() > 0:
            self.slug = f'{self.slug}-2'
        super(Client, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['username']


class Application(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        ACCEPTED = 'accepted', 'Принята'
        REJECTED = 'rejected', 'Отклонена'

    username = models.CharField(max_length=255, verbose_name="Имя")
    email = models.EmailField(verbose_name="Электронная почта")
    comment = models.TextField(verbose_name="Комментарий")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Статус"
    )
    admin_comment = models.TextField(blank=True, verbose_name="Комментарий администратора")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    user_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP адрес пользователя")

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Заявка на регистрацию"
        verbose_name_plural = "Заявки на регистрацию"
        ordering = ['-created_at']
