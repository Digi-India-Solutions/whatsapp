from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path("dashboard", dashboard, name="dashboard"),
    path("webhook/", whatsapp_webhook, name="whatsapp-webhook"),
    path("send-message/", send_message_view, name="send_message_view"),
    # path("message-status/", message_status_view, name="message_status_view"),
    path("create-text-template/", create_text_template, name="create_text_template"),
    # path("", list_templates, name="list_templates"),
    path("upload/", upload_image_view, name="upload_image_view"),
    path(
        "create-media-template/",
        create_media_template_view,
        name="create_media_template_view",
    ),
    path("import-contacts/", import_contacts, name="import_contacts"),
    path("templates/", template_list_view, name="templates_view"),
    path(
        "template-creation-catalogue",
        template_creation_catalogue,
        name="template-creation-catalogue",
    ),
    path("send-text-message", send_text_message, name="send_text_message"),
    path("create-auth-template/", create_auth_template, name="create_auth_template"),
    path("send-auth-message/", send_auth_message, name="send_auth_message"),
    path("update-media-template/", update_media_template, name="update_media_template"),
    path(
        "retrieve/",
        display_image_header_templates,
        name="retrieve_header_image_templates",
    ),
    path("delete_template/", delete_template, name="delete_template"),
    path("list-contact/", list_contacts, name="list_contacts"),
    path("list-uploads/", list_uploads, name="list_uploads"),
    path("delete-upload/<int:upload_id>/", delete_upload, name="delete_upload"),
    path("message-status/", message_status_list, name="message_status_list"),
    path("", login, name="login"),
    path("otp-verification/", otp_verification, name="otp_verification"),
    path(
        "password-reset-request/", password_reset_request, name="password_reset_request"
    ),
    path("register/", register, name="register"),
    path(
        "password-reset-otp-verification/",
        password_reset_otp_verification,
        name="password_reset_otp_verification",
    ),
    path(
        "password-reset-complete/",
        password_reset_complete,
        name="password_reset_complete",
    ),
]
