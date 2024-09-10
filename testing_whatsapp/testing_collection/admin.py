from django.contrib import admin

# Register your models here.
from .models import Contact, Upload


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("phone_number", "is_staff", "is_superuser", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "password",
                    "profile_picture",
                )
            },
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")},
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "password",
                    "profile_picture",
                ),
            },
        ),
    )
    search_fields = ("phone_number",)
    ordering = ("phone_number",)


admin.site.register(CustomUser, CustomUserAdmin)


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ("batch_id", "upload_time", "new_contacts", "old_contacts")
    inlines = [ContactInline]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "upload")
