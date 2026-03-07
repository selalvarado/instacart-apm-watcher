import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re

CAREERS_URL = "https://instacart.careers/current-openings/"
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]  # Gmail App Password

def send_email(subject, body_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

def check_for_apm():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(CAREERS_URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    full_text = soup.get_text(separator=" ").lower()

    # Look for APM-related keywords
    apm_keywords = ["associate product manager", "apm program", "apm "]
    found = any(kw in full_text for kw in apm_keywords)

    # Try to find a direct link to the role
    job_link = None
    for a in soup.find_all("a", href=True):
        link_text = a.get_text(separator=" ").lower()
        if any(kw in link_text for kw in apm_keywords):
            href = a["href"]
            job_link = href if href.startswith("http") else "https://instacart.careers" + href
            break

    return found, job_link

def main():
    found, job_link = check_for_apm()

    if found:
        if job_link:
            body = f'<p>It\'s time! 🎉 The Instacart APM program is open.</p><p><a href="{job_link}">Click here to apply</a></p>'
        else:
            body = f'<p>It\'s time! 🎉 The Instacart APM program appears to be open. <a href="{CAREERS_URL}">Check the careers page.</a></p>'
        send_email("it's time!", body)
        print("APM found — email sent!")
    else:
        body = "<p>No leads yet. The Instacart APM program is not currently listed.</p>"
        send_email("no leads yet", body)
        print("APM not found — email sent.")

if __name__ == "__main__":
    main()
