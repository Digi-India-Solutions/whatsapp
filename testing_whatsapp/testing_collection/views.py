import json
import requests
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import WhatsAppMessageStatus, Upload, Contact, DashboardMessageStatus
import tempfile
import pandas as pd
from django.db import IntegrityError
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from datetime import datetime


# For login
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import update_session_auth_hash
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from .forms import CustomUserCreationForm, CustomPasswordResetForm


def generate_otp():
    import random

    return str(random.randint(100000, 999999))


def send_otp_via_whatsapp(phone_number, otp_code):
    url = "https://graph.facebook.com/v20.0/381616421708874/messages"
    access_token = settings.WHATSAPP_ACCESS_TOKEN
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "second_auth",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": otp_code}],
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": otp_code}],
                },
            ],
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    requests.post(url, json=data, headers=headers)


def login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            otp_code = generate_otp()
            request.session["otp_code"] = otp_code
            request.session["login_user"] = user.phone_number
            send_otp_via_whatsapp(user.phone_number, otp_code)
            return redirect("otp_verification")
    else:
        form = AuthenticationForm()
    return render(request, "pages/login.html", {"form": form})


def otp_verification(request):
    if request.method == "POST":
        otp_code = request.POST.get("otp_code")
        session_otp = request.session.get("otp_code")
        phone_number = request.session.get("login_user")
        if otp_code == session_otp:
            user = get_user_model().objects.get(phone_number=phone_number)
            auth_login(request, user)
            return redirect("dashboard")
        else:
            return render(
                request, "pages/otp_verification.html", {"error": "Invalid OTP"}
            )
    return render(request, "pages/otp_verification.html")


def password_reset_request(request):
    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data["phone_number"]
            user = get_user_model().objects.filter(phone_number=phone_number).first()
            if user:
                otp_code = generate_otp()
                request.session["otp_code"] = otp_code
                send_otp_via_whatsapp(user.phone_number, otp_code)
                return redirect("password_reset_otp_verification")
    else:
        form = CustomPasswordResetForm()
    return render(request, "pages/password_reset_request.html", {"form": form})


def password_reset_otp_verification(request):
    if request.method == "POST":
        otp_code = request.POST.get("otp_code")
        session_otp = request.session.get("otp_code")
        if otp_code == session_otp:
            # Here you'd typically redirect to a page where the user can enter a new password
            return redirect("password_reset_complete")
        else:
            return render(
                request,
                "pages/password_reset_otp_verification.html",
                {"error": "Invalid OTP"},
            )
    return render(request, "pages/password_reset_otp_verification.html")


def password_reset_complete(request):
    # Implement the password reset completion view here
    return render(request, "pages/password_reset_complete.html")


# Dashboard
@login_required
def dashboard(request):
    # Fetch the current logged-in user
    current_user = request.user
    current_user_ip = request.META.get("REMOTE_ADDR", "unknown")

    # Get or create DashboardMessageStatus for the current user
    message_status, created = DashboardMessageStatus.objects.get_or_create(
        user=current_user
    )

    context = {
        "sent_message": message_status.sent_message,
        "delivered_message": message_status.delivered_message,
        "read_message": message_status.read_message,
        "current_user": current_user,
        "current_user_ip": current_user_ip,
        "current_user_phone": current_user.phone_number,
        "current_user_email": current_user.email,
        "current_user_first_name": current_user.first_name,
    }

    return render(request, "pages/index.html", context)


# Function to send a WhatsApp template message
def send_message(phone_number, template_name, template_language, image_link):
    url = (
        f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": template_language,
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [{"type": "image", "image": {"link": image_link}}],
                }
            ],
        },
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


# @csrf_exempt
# def send_message_view(request):
#     response_data = None
#     error_message = None

#     if request.method == "POST":
#         template_name = request.POST.get("template_name")
#         template_language = request.POST.get("template_language", "en")
#         image_link = request.POST.get("link")
#         upload_id = request.POST.get("upload_id")

#         if not template_name or not image_link or not upload_id:
#             error_message = (
#                 "Template name, image link, and file selection are required."
#             )
#         else:
#             try:
#                 upload = Upload.objects.get(id=upload_id)
#                 contacts = Contact.objects.filter(upload=upload)
#                 if not contacts.exists():
#                     error_message = "No contacts found in the selected file."
#                 else:
#                     responses = []
#                     for contact in contacts:
#                         response = send_message(
#                             contact.phone_number,
#                             template_name,
#                             template_language,
#                             image_link,
#                         )
#                         responses.append(response)

#                     response_data = (
#                         f"Messages sent successfully. Responses: {responses}"
#                     )
#             except Upload.DoesNotExist:
#                 error_message = "Selected file does not exist."

#     return render(
#         request,
#         "pages/send-media-message.html",
#         {
#             "response_data": response_data,
#             "error_message": error_message,
#             "uploads": Upload.objects.all(),  # Pass all uploads to the template
#         },
#     )


@csrf_exempt
def send_message_view(request):
    response_data = None
    error_message = None

    if request.method == "POST":
        # Check if sending to a single phone number
        phone_number = request.POST.get("phone_number")
        template_name = request.POST.get("template_name")
        template_language = request.POST.get("template_language", "en")
        image_link = request.POST.get("link")

        # Check if sending from a file
        upload_id = request.POST.get("upload_id")

        if phone_number and template_name and image_link and not upload_id:
            # Sending to a single phone number
            if not phone_number:
                error_message = "Phone number is required."
            else:
                response = send_message(
                    phone_number,
                    template_name,
                    template_language,
                    image_link,
                )
                response_data = (
                    f"Message sent successfully to {phone_number}. Response: {response}"
                )

        elif not phone_number and template_name and image_link and upload_id:
            # Sending messages from a file
            if not template_name or not image_link or not upload_id:
                error_message = (
                    "Template name, image link, and file selection are required."
                )
            else:
                try:
                    upload = Upload.objects.get(id=upload_id)
                    contacts = Contact.objects.filter(upload=upload)
                    if not contacts.exists():
                        error_message = "No contacts found in the selected file."
                    else:
                        responses = []
                        for contact in contacts:
                            response = send_message(
                                contact.phone_number,
                                template_name,
                                template_language,
                                image_link,
                            )
                            responses.append(response)

                        response_data = (
                            f"Messages sent successfully. Responses: {responses}"
                        )
                except Upload.DoesNotExist:
                    error_message = "Selected file does not exist."

        else:
            error_message = "Required fields are missing."

    return render(
        request,
        "pages/send-media-message.html",
        {
            "response_data": response_data,
            "error_message": error_message,
            "uploads": Upload.objects.all(),  # Pass all uploads to the template
        },
    )


# @csrf_exempt
# def whatsapp_webhook(request):
#     if request.method == "GET":
#         # Handle verification from WhatsApp
#         verify_token = settings.WHATSAPP_VERIFY_TOKEN
#         mode = request.GET.get("hub.mode")
#         token = request.GET.get("hub.verify_token")
#         challenge = request.GET.get("hub.challenge")

#         if mode == "subscribe" and token == verify_token:
#             return HttpResponse(challenge, status=200)
#         return HttpResponse("Verification failed", status=403)

#     elif request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             print(json.dumps(data, indent=4))  # Print the incoming data for debugging

#             # Process the webhook data
#             for entry in data.get("entry", []):
#                 for change in entry.get("changes", []):
#                     value = change.get("value", {})
#                     messaging_product = value.get("messaging_product")

#                     if messaging_product == "whatsapp":
#                         messages = value.get("statuses", [])
#                         for message in messages:
#                             message_id = message.get("id")
#                             status = message.get("status")
#                             phone_number = message.get("recipient_id")
#                             reply_text = (
#                                 message.get("conversation", {})
#                                 .get("origin", {})
#                                 .get("type", "")
#                             )  # Extract reply text if available

#                             # Save the status to the database
#                             WhatsAppMessageStatus.objects.update_or_create(
#                                 message_id=message_id,
#                                 defaults={
#                                     "phone_number": phone_number,
#                                     "status": status,
#                                     "reply": reply_text,
#                                 },
#                             )

#                             # Print status to the terminal
#                             print(
#                                 f"Message ID {message_id} from {phone_number} has status {status}."
#                             )

#             return JsonResponse({"status": "received"}, status=200)
#         except json.JSONDecodeError:
#             return JsonResponse({"status": "invalid JSON"}, status=400)

#     return JsonResponse({"status": "invalid request"}, status=400)


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "GET":
        # Verify the webhook setup with Facebook
        verify_token = settings.WHATSAPP_VERIFY_TOKEN
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            return HttpResponse(challenge, status=200)
        return HttpResponse("Verification failed", status=403)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            print(json.dumps(data, indent=4))  # Print the incoming data for debugging

            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messaging_product = value.get("messaging_product")

                    if messaging_product == "whatsapp":
                        messages = value.get("statuses", [])
                        for message in messages:
                            message_id = message.get("id")
                            status = message.get("status")
                            phone_number = message.get("recipient_id")
                            timestamp = message.get("timestamp")
                            reply_text = (
                                message.get("conversation", {})
                                .get("origin", {})
                                .get("type", "")
                            )

                            # Extract profile name and WA ID if available
                            profile_name = ""
                            wa_id = ""
                            if "contacts" in value:
                                contact = value.get("contacts", [{}])[0]
                                profile_name = contact.get("profile", {}).get(
                                    "name", ""
                                )
                                wa_id = contact.get("wa_id", "")

                            # Extract template type from pricing if available
                            template_type = message.get("pricing", {}).get(
                                "category", ""
                            )

                            # Update or create the WhatsAppMessageStatus object
                            WhatsAppMessageStatus.objects.update_or_create(
                                message_id=message_id,
                                defaults={
                                    "phone_number": phone_number,
                                    "status": status,
                                    "timestamp": datetime.fromtimestamp(int(timestamp)),
                                    "reply": reply_text,
                                    "template_type": template_type,
                                    "profile_name": profile_name,
                                    "wa_id": wa_id,
                                },
                            )

                            # Try to associate the user
                            user = None
                            if phone_number:
                                try:
                                    user = get_user_model().objects.get(
                                        phone_number=phone_number
                                    )
                                except get_user_model().DoesNotExist:
                                    print(
                                        f"No user found with phone number {phone_number}"
                                    )

                            if user:
                                # Update or create the DashboardMessageStatus object
                                dashboard_status, created = (
                                    DashboardMessageStatus.objects.get_or_create(
                                        user=user,
                                        defaults={
                                            "sent_message": 0,
                                            "delivered_message": 0,
                                            "read_message": 0,
                                        },
                                    )
                                )

                                if status == "sent":
                                    dashboard_status.sent_message += 1
                                elif status == "delivered":
                                    dashboard_status.delivered_message += 1
                                elif status == "read":
                                    dashboard_status.read_message += 1

                                dashboard_status.save()
                                print(
                                    f"Updated dashboard status for user {user.phone_number}"
                                )

                            else:
                                print(
                                    f"No dashboard status updated for phone number {phone_number}"
                                )

            return JsonResponse({"status": "received"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"status": "invalid JSON"}, status=400)

    return JsonResponse({"status": "invalid request"}, status=400)


def message_status_list(request):
    statuses = WhatsAppMessageStatus.objects.all().order_by("-timestamp")
    return render(request, "pages/status-report.html", {"statuses": statuses})


# for creation of templates


def create_text_template(request):
    if request.method == "POST":
        name = request.POST.get("name")
        header_text = request.POST.get("header_text")
        body_text = request.POST.get("body_text")
        footer_text = request.POST.get("footer_text")
        button_1_text = request.POST.get("button_1_text")
        button_1_type = request.POST.get("button_1_type")
        button_1_action = request.POST.get("button_1_action")
        button_2_text = request.POST.get("button_2_text")
        button_2_type = request.POST.get("button_2_type")
        button_2_action = request.POST.get("button_2_action")

        # Build the payload
        payload = {
            "name": name,
            "category": "MARKETING",
            "language": "en_US",
            "components": [],
        }

        # Add header if provided
        if header_text:
            payload["components"].append(
                {"type": "HEADER", "format": "TEXT", "text": header_text}
            )

        # Add body if provided
        if body_text:
            payload["components"].append({"type": "BODY", "text": body_text})

        # Add footer if provided
        if footer_text:
            payload["components"].append({"type": "FOOTER", "text": footer_text})

        # Add buttons if provided
        buttons = []
        if button_1_text and button_1_type:
            button = {"type": button_1_type, "text": button_1_text}
            if button_1_type == "URL" and button_1_action:
                button["url"] = button_1_action
            elif button_1_type == "PHONE_NUMBER" and button_1_action:
                button["phone_number"] = button_1_action
            buttons.append(button)

        if button_2_text and button_2_type:
            button = {"type": button_2_type, "text": button_2_text}
            if button_2_type == "URL" and button_2_action:
                button["url"] = button_2_action
            elif button_2_type == "PHONE_NUMBER" and button_2_action:
                button["phone_number"] = button_2_action
            buttons.append(button)

        if buttons:
            payload["components"].append({"type": "BUTTONS", "buttons": buttons})

        # API call
        url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            return render(
                request, "pages/create-text-template.html", {"response": response}
            )
        else:
            return HttpResponse(
                f"Failed to create template: {response.json()}", status=400
            )

    return render(request, "pages/create-text-template.html")


# Creation of Image Templates and Their assets

# Constants
UPLOAD_URL = f"https://graph.facebook.com/v20.0/{settings.APP_ID}/uploads"


def start_upload_session(image_path):
    file_name = os.path.basename(image_path)
    file_length = os.path.getsize(image_path)
    file_type = "image/jpeg"  # Update based on your file type

    params = {
        "file_name": file_name,
        "file_length": file_length,
        "file_type": file_type,
        "access_token": settings.WHATSAPP_ACCESS_TOKEN,
    }

    response = requests.post(UPLOAD_URL, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to start upload session: {response.json()}")

    response_data = response.json()
    upload_session_id = response_data.get("id")

    if not upload_session_id:
        raise Exception("No upload session ID returned in the response.")

    return upload_session_id


def upload_file(upload_session_id, image_file):
    upload_url = f"https://graph.facebook.com/v20.0/{upload_session_id}"
    headers = {
        "Authorization": f"OAuth {settings.WHATSAPP_ACCESS_TOKEN}",
        "file_offset": "0",
    }

    response = requests.post(upload_url, headers=headers, data=image_file)

    if response.status_code != 200:
        raise Exception(f"Failed to upload file: {response.json()}")

    response_data = response.json()
    file_handle = response_data.get("h")

    if not file_handle:
        raise Exception("No file handle returned in the response.")

    return file_handle


@csrf_exempt
def upload_image_view(request):
    if request.method == "POST" and request.FILES.get("image"):
        image_file = request.FILES["image"]
        try:
            # Use tempfile to handle the temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                # Save the uploaded image to the temporary file
                for chunk in image_file.chunks():
                    temp_file.write(chunk)

                temp_image_path = temp_file.name

            # Start upload session
            upload_session_id = start_upload_session(temp_image_path)

            # Upload file
            with open(temp_image_path, "rb") as temp_file:
                file_handle = upload_file(upload_session_id, temp_file)

            # Clean up the temporary file
            os.remove(temp_image_path)

            # Return results in the HTTP response
            response_text = (
                f"File uploaded successfully.<br>"
                f"<strong>Upload Session ID:</strong> {upload_session_id}<br>"
                f"<strong>File Handle:</strong> {file_handle}"
            )
            # return HttpResponse(response_text, content_type="text/html")
            return render(
                request, "pages/handle-asset.html", {"response_text": response_text}
            )

        except Exception as e:
            return HttpResponse(f"Error: {e}", status=500)

    # Render the form if GET request or invalid POST
    return render(request, "pages/handle-asset.html")


# Create media templates
@csrf_exempt
def create_media_template_view(request):
    if request.method == "POST":
        template_name = request.POST.get("template_name")
        language_code = request.POST.get("language_code")
        image_handle = request.POST.get("image_handle")
        body_text = request.POST.get("body_text", "Check out our latest offer!")
        footer_text = request.POST.get(
            "footer_text", "Use the buttons below to learn more"
        )
        button_url_text = request.POST.get("button_url_text", "Shop Now")
        button_url = request.POST.get(
            "button_url", "https://www.digiindiasolutions.com/"
        )
        button_call_text = request.POST.get("button_call_text", "Call Us")
        button_call_number = request.POST.get("button_call_number", "+1234567890")
        quick_reply_text = request.POST.get("quick_reply_text", "Contact Us")

        if not template_name or not language_code or not image_handle:
            return HttpResponse(
                "Template name, language code, and image handle are required.",
                status=400,
            )

        # Create the template
        response = create_media_template(
            template_name,
            language_code,
            image_handle,
            body_text,
            footer_text,
            button_url_text,
            button_url,
            button_call_text,
            button_call_number,
            quick_reply_text,
        )

        # Handle response
        if response.get("status") == "error":
            error_message = response.get("message", "Unknown error")
            return HttpResponse(
                f"Failed to create template: {error_message}", status=500
            )
        else:
            return HttpResponse(f"Template created successfully: {response}")

    return render(request, "pages/create-media-template.html")


def create_media_template(
    template_name,
    language_code,
    image_handle,
    body_text,
    footer_text,
    button_url_text,
    button_url,
    button_call_text,
    button_call_number,
    quick_reply_text,
):
    create_template_url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    buttons = [
        {"type": "URL", "text": button_url_text, "url": button_url},
        {
            "type": "PHONE_NUMBER",
            "text": button_call_text,
            "phone_number": button_call_number,
        },
        {"type": "QUICK_REPLY", "text": quick_reply_text},
    ]

    template_data = {
        "name": template_name,
        "language": language_code,
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "IMAGE",
                "example": {"header_handle": [image_handle]},
            },
            {"type": "BODY", "text": body_text},
            {"type": "FOOTER", "text": footer_text},
            {"type": "BUTTONS", "buttons": buttons},
        ],
    }

    response = requests.post(create_template_url, headers=headers, json=template_data)

    return response.json()


def import_contacts(request):
    if request.method == "POST":
        excel_file = request.FILES["file"]  # Get the uploaded Excel file

        # Generate a unique batch ID based on the current date and time
        batch_id = timezone.now().strftime("%Y%m%d%H%M%S")

        # Create an Upload record
        upload = Upload.objects.create(batch_id=batch_id)

        # Read the Excel file into a DataFrame
        df = pd.read_excel(excel_file)

        # Collect phone numbers from the uploaded file
        phone_numbers = df["Phone Number"].tolist()

        # Get existing phone numbers from the database
        existing_phone_numbers = set(
            Contact.objects.values_list("phone_number", flat=True)
        )

        # Track phone numbers that have been processed and their status
        processed_phone_numbers = set()
        new_contacts = 0
        old_contacts = 0

        for phone_number in phone_numbers:
            if phone_number in processed_phone_numbers:
                continue  # Skip if this phone number has already been handled

            processed_phone_numbers.add(phone_number)

            if phone_number in existing_phone_numbers:
                # Increment old_contacts counter if phone number already exists
                old_contacts += 1
            else:
                try:
                    # Create a new Contact instance with the upload reference
                    Contact.objects.create(phone_number=phone_number, upload=upload)
                    new_contacts += 1
                except IntegrityError:
                    # Handle the integrity error and show a message to the user
                    messages.error(
                        request,
                        f"An error occurred while processing phone number {phone_number}. It may be a duplicate.",
                    )
                    continue

        # Update the Upload record with new and old contact counts
        upload.new_contacts = new_contacts
        upload.old_contacts = old_contacts
        upload.save()

        # Use Django's messages framework to display a success message
        messages.success(
            request,
            f"Contacts imported successfully! Batch ID: {batch_id}. New contacts: {new_contacts}. Old contacts: {old_contacts}",
        )

        # Redirect to the same page or another page to display the message
        return render(request, "pages/import_contacts.html")

    return render(request, "pages/import_contacts.html")


def get_templates():
    url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        templates = response.json()
        return templates
    else:
        print(f"Failed to retrieve templates. Status code: {response.status_code}")
        print(response.json())
        return None


def template_list_view(request):
    templates = get_templates()
    template_data = []
    if templates:
        for template in templates.get("data", []):
            template_data.append(
                {
                    "name": template.get("name"),
                    "status": template.get("status"),  # Add status if available
                    "category": template.get("category"),  # Add category if available
                    "messages_sent": template.get("messages_sent", "N/A"),
                    "messages_opened": template.get("messages_opened", "N/A"),
                    "last_updated": template.get("last_updated"),
                }
            )

    return render(request, "pages/list_templates.html", {"templates": template_data})


def template_creation_catalogue(request):
    return render(request, "pages/template-creation-catalogue.html")


@csrf_exempt
def send_text_message(request):
    response_data = None
    error_message = None

    if request.method == "POST":
        phone_number = request.POST.get("phone_number")
        template_name = request.POST.get("template_name")
        upload_id = request.POST.get("upload_id")

        # Sending message to a single phone number
        if phone_number and template_name and not upload_id:
            url = "https://graph.facebook.com/v20.0/381616421708874/messages"
            headers = {
                "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {"name": template_name, "language": {"code": "en_US"}},
            }

            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()

        # Sending messages to all phone numbers in a selected file
        elif upload_id and template_name:
            try:
                upload = Upload.objects.get(id=upload_id)
                contacts = Contact.objects.filter(upload=upload)

                if not contacts.exists():
                    error_message = "No contacts found in the selected file."
                else:
                    responses = []
                    for contact in contacts:
                        url = (
                            "https://graph.facebook.com/v20.0/381616421708874/messages"
                        )
                        headers = {
                            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                            "Content-Type": "application/json",
                        }
                        data = {
                            "messaging_product": "whatsapp",
                            "to": contact.phone_number,
                            "type": "template",
                            "template": {
                                "name": template_name,
                                "language": {"code": "en_US"},
                            },
                        }

                        response = requests.post(url, headers=headers, json=data)
                        responses.append(response.json())

                    response_data = (
                        f"Messages sent successfully. Responses: {responses}"
                    )

            except Upload.DoesNotExist:
                error_message = "Selected file does not exist."

        else:
            error_message = "Either phone number and template name, or a file and template name are required."

    return render(
        request,
        "pages/send-text-message.html",
        {
            "response_data": response_data,
            "error_message": error_message,
            "uploads": Upload.objects.all(),  # Pass all uploads to the template
        },
    )


# Create Authentication Templates


def create_auth_template(request):
    response = None
    if request.method == "POST":
        access_token = "EAAKFdxtt2sMBOz5mQNHZAWt8bTwfhVeZCbCnHWsOw03AflmyRcp5cBeMqIUNgr6bR3K0ZAwjbTlzywWG6ZCMc4p9epcQCt5vM49CL5tgypcNJFjU1dUxJlrkSvrxVIW6pBveqdMbx4sUKvNZAFMmMl7h3VisrNV9u1mMrmlbJoGVT2iF7Sz0g7Hw6kcsfBSeQ1UxNs04MxhdULJEZCOhMZD"
        url = (
            "https://graph.facebook.com/v20.0/392799230586870/upsert_message_templates"
        )

        template_name = request.POST.get("template_name")
        code_expiration_minutes = request.POST.get("code_expiration_minutes")

        data = {
            "name": template_name,
            "languages": ["en_US"],
            "category": "AUTHENTICATION",
            "components": [
                {
                    "type": "BODY",
                    "add_security_recommendation": True,
                },
                {
                    "type": "FOOTER",
                    "code_expiration_minutes": int(code_expiration_minutes),
                },
                {
                    "type": "BUTTONS",
                    "buttons": [{"type": "OTP", "otp_type": "COPY_CODE"}],
                },
            ],
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.post(url, json=data, headers=headers).json()

    return render(request, "pages/create-auth-template.html", {"response": response})


def send_auth_message(request):
    response = None
    if request.method == "POST":
        access_token = settings.WHATSAPP_ACCESS_TOKEN
        url = "https://graph.facebook.com/v20.0/381616421708874/messages"

        phone_number = request.POST.get("phone_number")
        template_name = request.POST.get("template_name")
        otp_code = request.POST.get("otp_code")

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": otp_code}],
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [{"type": "text", "text": otp_code}],
                    },
                ],
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.post(url, json=data, headers=headers).json()

    return render(request, "pages/send-auth-message.html", {"response": response})


# Update Media Template


def update_media_template(request):
    if request.method == "POST":
        template_id = request.POST.get("template_id")
        header_handle = request.POST.get("header_handle")
        body_text = request.POST.get("body_text")
        footer_text = request.POST.get("footer_text")
        button_call_text = request.POST.get("button_call_text")
        button_call_number = request.POST.get("button_call_number")
        button_url_text = request.POST.get("button_url_text")
        button_url = request.POST.get("button_url")
        quick_reply_text = request.POST.get("quick_reply_text")

        updated_components = []

        # Add HEADER component if data is provided
        if header_handle:
            updated_components.append(
                {
                    "type": "HEADER",
                    "format": "IMAGE",
                    "example": {"header_handle": [header_handle]},
                }
            )

        # Add BODY component if data is provided
        if body_text:
            updated_components.append(
                {
                    "type": "BODY",
                    "text": body_text,
                }
            )

        # Add FOOTER component if data is provided
        if footer_text:
            updated_components.append(
                {
                    "type": "FOOTER",
                    "text": footer_text,
                }
            )

        # Add BUTTONS component if data is provided
        buttons = []
        if button_call_text and button_call_number:
            buttons.append(
                {
                    "type": "PHONE_NUMBER",
                    "text": button_call_text,
                    "phone_number": button_call_number,
                }
            )
        if button_url_text and button_url:
            buttons.append(
                {
                    "type": "URL",
                    "text": button_url_text,
                    "url": button_url,
                }
            )
        if quick_reply_text:
            buttons.append(
                {
                    "type": "QUICK_REPLY",
                    "text": quick_reply_text,
                }
            )
        if buttons:
            updated_components.append(
                {
                    "type": "BUTTONS",
                    "buttons": buttons,
                }
            )

        # Prepare the data to update
        update_data = {
            "components": updated_components,
        }

        # Call the API to update the template
        edit_template_url = f"https://graph.facebook.com/v20.0/{template_id}"
        headers = {
            "Authorization": f"Bearer EAAKFdxtt2sMBO1ohfcDSS7XH31G0onsfi52GTx4sE8ZAz5HfZBgv0PvTThGiHTv9yLDWO6icXxL5jiZCVODugQ0Du2RLXdD5d9FZANe9sVvZAI9VZBNRuiaPnEYgnHoiBEUSpO49DfWbzQTTkNZA1TWGsW8fZAykUZCDJZCDlic3iuxH7QUQT7iZAd417rEhod12455X97GsaGmcJWZCls0rmjtwMZBRJm2xiC2wec8EZD",
            "Content-Type": "application/json",
        }

        response = requests.post(edit_template_url, headers=headers, json=update_data)

        if response.status_code == 200:
            return JsonResponse(
                {"status": "success", "message": "Template edited successfully!"}
            )
        else:
            return JsonResponse({"status": "error", "message": response.json()})

    return render(request, "pages/update-media-template.html")


# Delete Templates
def delete_template(request):
    if request.method == "POST":
        hsm_id = request.POST.get("hsm_id")
        name = request.POST.get("name")

        if not hsm_id or not name:
            return render(
                request,
                "delete_template.html",
                {"result_message": "Both HSM ID and name are required."},
            )

        url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
        params = {"hsm_id": hsm_id, "name": name}

        response = requests.delete(url, headers=headers, params=params)

        if response.status_code == 200:
            result_message = "Template deleted successfully."
        else:
            result_message = f"Failed to delete template. Status code: {response.status_code}. Error: {response.json()}"

        return render(
            request, "pages/delete-template.html", {"result_message": result_message}
        )
    else:
        return render(
            request,
            "pages/delete-template.html",
            {"result_message": "Invalid request method."},
        )


# retrieve IMAGE templates data

# Replace these with your actual values
ACCESS_TOKEN = settings.WHATSAPP_ACCESS_TOKEN
WABA_ID = settings.WHATSAPP_BUSINESS_ACCOUNT_ID  # The WhatsApp Business Account ID


def get_image_header_templates():
    url = f"https://graph.facebook.com/v20.0/{WABA_ID}/message_templates"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        templates = response.json()
        all_templates = templates.get("data", [])

        # Filter for HEADER type IMAGE
        image_header_templates = [
            {"name": template["name"], "id": template["id"]}
            for template in all_templates
            if any(
                comp.get("type") == "HEADER" and comp.get("format") == "IMAGE"
                for comp in template.get("components", [])
            )
        ]
        return image_header_templates
    else:
        print(f"Failed to retrieve templates. Status code: {response.status_code}")
        print(response.json())
        return []


@login_required
def display_image_header_templates(request):
    templates = get_image_header_templates()
    return render(request, "pages/update-media-template.html", {"templates": templates})


def list_contacts(request):
    contacts = Contact.objects.all()  # Fetch all contacts from the database
    return render(request, "pages/list-contact.html", {"contacts": contacts})


def list_uploads(request):
    uploads = Upload.objects.all()  # Fetch all uploads
    return render(request, "pages/list-excel-uploaded-file.html", {"uploads": uploads})


def delete_upload(request, upload_id):
    upload = get_object_or_404(Upload, id=upload_id)
    upload.delete()
    messages.success(request, f"Upload {upload.batch_id} deleted successfully.")
    return redirect("list_uploads")
