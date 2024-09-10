from django.db import models


from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone
from django.contrib.auth import get_user_model



class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number field must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, default="Fill Details")
    last_name = models.CharField(max_length=50, default="Fill Details")
    email = models.EmailField(max_length=50, default="Fill Details")
    phone_number = models.CharField(max_length=15, unique=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number


class Upload(models.Model):
    batch_id = models.CharField(max_length=20, unique=True)
    upload_time = models.DateTimeField(auto_now_add=True)
    new_contacts = models.PositiveIntegerField(default=0)
    old_contacts = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Upload {self.batch_id} at {self.upload_time}"


class Contact(models.Model):
    phone_number = models.CharField(max_length=12, unique=True)
    upload = models.ForeignKey(
        Upload, on_delete=models.CASCADE, related_name="contacts"
    )


class WhatsAppMessageStatus(models.Model):
    message_id = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField()
    reply = models.TextField(blank=True, null=True)
    template_type = models.CharField(max_length=50, blank=True, null=True)  # New field
    profile_name = models.CharField(max_length=255, blank=True, null=True)  # New field
    wa_id = models.CharField(max_length=20, blank=True, null=True)  # New field

    def __str__(self):
        return f"{self.message_id} - {self.status}"


class DashboardMessageStatus(models.Model):
    sent_message = models.IntegerField(default=0)
    delivered_message = models.IntegerField(default=0)
    read_message = models.IntegerField(default=0)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="message_status"
    )

    def __str__(self):
        return f"Sent: {self.sent_message}, Delivered: {self.delivered_message}, Read: {self.read_message}"
