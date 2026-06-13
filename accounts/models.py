from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomerManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra):
        if not phone:
            raise ValueError('Phone number required')
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra)

class Customer(AbstractBaseUser, PermissionsMixin):
    phone      = models.CharField(max_length=15, unique=True)
    name       = models.CharField(max_length=100, blank=True)
    email      = models.EmailField(blank=True)
    address    = models.TextField(blank=True)
    area       = models.CharField(max_length=100, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'phone'
    REQUIRED_FIELDS = []
    objects = CustomerManager()

    def __str__(self):
        return self.name or self.phone
