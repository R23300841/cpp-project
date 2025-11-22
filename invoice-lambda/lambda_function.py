import json
import boto3
import os
import smtplib
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from datetime import datetime

# Load environment variables
s3_bucket = os.environ.get("BILL_BUCKET", "s3-cpp-x23300841")
SMTP_HOST = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
# SMTP_USER = os.environ.get("projectmail2223@gmail.com")
# SMTP_PASS = os.environ.get("qkhc idzh thts lqkj")

SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")



def generate_pdf(order_id, name, email, products, total):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, f"Order Invoice #{order_id}")

    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Customer Name: {name}")
    c.drawString(50, 750, f"Customer Email: {email}")
    c.drawString(50, 730, f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

    y = 700
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Products:")
    y -= 20

    c.setFont("Helvetica", 11)
    for item in products:
        c.drawString(50, y, f"{item['name']}  x{item['qty']}  ${item['price']}")
        y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 10, f"Total Amount: ${total}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()


def upload_to_s3(pdf_bytes, pdf_filename):
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=s3_bucket,
        Key=pdf_filename,
        Body=pdf_bytes,
        ContentType="application/pdf"
    )
    return f"s3://{s3_bucket}/{pdf_filename}"


def send_email_smtp(to_email, subject, body, pdf_bytes, filename):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    msg.attach(MIMEText(body, "plain"))

    # Attach PDF
    part = MIMEApplication(pdf_bytes, Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)

    # Send via SMTP
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.sendmail(SMTP_USER, to_email, msg.as_string())


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))

        order_id = body["order_id"]
        name = body["name"]
        email = body["email"]
        products = body["products"]   # [{'name': 'Laptop', 'qty': 1, 'price': 750}]
        total = body["total"]

        # Generate PDF
        pdf_data = generate_pdf(order_id, name, email, products, total)
        pdf_filename = f"invoice_{order_id}.pdf"

        # Upload to S3
        s3_path = upload_to_s3(pdf_data, pdf_filename)

        # Email the PDF
        send_email_smtp(
            to_email=email,
            subject=f"Your Invoice - Order #{order_id}",
            body="Thank you for shopping with us! Your invoice is attached.",
            pdf_bytes=pdf_data,
            filename=pdf_filename
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "message": "Invoice generated and emailed successfully",
                "file": s3_path
            })
        }

    except Exception as e:
        print("ERROR:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(e)})
        }
