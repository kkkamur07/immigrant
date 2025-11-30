import os
import asyncio
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Setup Jinja2 template environment
TEMPLATE_DIR = Path(__file__).parent / "email_templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def format_datetime_for_email(date_str: str, time_str: str) -> tuple:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    readable_date = date_obj.strftime("%B %d, %Y")  
    
    time_obj = datetime.strptime(time_str, "%H:%M")
    readable_time = time_obj.strftime("%I:%M %p") 
    
    return readable_date, readable_time


async def send_confirmation_email(
    recipient_email: str,
    recipient_name: str,
    appointment_details: Dict[str, str],
    confirmation_token: str,
    reason: str
) -> Dict[str, Any]:
    """Send confirmation email - fully async"""
    try:
        # Format date and time
        readable_date, readable_time = format_datetime_for_email(
            appointment_details["date"],
            appointment_details["time"]
        )
        
        # Build confirmation URL
        confirmation_url = f"{BASE_URL}/confirm?token={confirmation_token}"
        
        # Prepare template context
        context = {
            "recipient_name": recipient_name,
            "readable_date": readable_date,
            "readable_time": readable_time,
            "reason": reason,
            "confirmation_url": confirmation_url
        }
        
        # Load and render templates
        text_template = jinja_env.get_template("confirmation_email.txt")
        html_template = jinja_env.get_template("confirmation_email.html")
        
        text_content = text_template.render(context)
        html_content = html_template.render(context)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"KVR Munich <{SENDER_EMAIL}>"
        message["To"] = recipient_email
        message["Subject"] = "⚠️ Confirm Your KVR Emergency Appointment"
        
        # Attach both versions
        text_part = MIMEText(text_content, "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")
        
        message.attach(text_part)
        message.attach(html_part)
        
        # Send email using aiosmtplib
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True
        )
        
        print(f"[EMAIL] Confirmation sent to {recipient_email}")
        
        return {
            "status": "success",
            "message": "Confirmation email sent successfully",
            "recipient": recipient_email
        }
        
    except Exception as e:
        print(f"[EMAIL ERROR] {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}",
            "recipient": recipient_email
        }


async def send_booking_confirmation_email(
    recipient_email: str,
    recipient_name: str,
    booking_id: str,
    appointment_details: Dict[str, str],
    reason: str
) -> Dict[str, Any]:
    """Send booking confirmation - fully async"""
    try:
        # Format date and time
        readable_date, readable_time = format_datetime_for_email(
            appointment_details["date"],
            appointment_details["time"]
        )
        
        # Prepare template context
        context = {
            "recipient_name": recipient_name,
            "booking_id": booking_id,
            "readable_date": readable_date,
            "readable_time": readable_time,
            "reason": reason
        }
        
        # Load and render templates
        text_template = jinja_env.get_template("booking_confirmation.txt")
        html_template = jinja_env.get_template("booking_confirmation.html")
        
        text_content = text_template.render(context)
        html_content = html_template.render(context)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"KVR Munich <{SENDER_EMAIL}>"
        message["To"] = recipient_email
        message["Subject"] = f"✅ Appointment Confirmed - Booking #{booking_id}"
        
        # Attach both versions
        text_part = MIMEText(text_content, "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")
        
        message.attach(text_part)
        message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True
        )
        
        print(f"[EMAIL] Booking confirmation sent to {recipient_email}")
        
        return {
            "status": "success",
            "message": "Booking confirmation email sent successfully",
            "recipient": recipient_email
        }
        
    except Exception as e:
        print(f"[EMAIL ERROR] {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}",
            "recipient": recipient_email
        }
