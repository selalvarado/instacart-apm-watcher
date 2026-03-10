import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from playwright.sync_api import sync_playwright

CAREERS_URL = "https://instacart.careers/current-openings/"
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"]

def send_email(subject, body_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

def disable_workflow():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/check_instacart.yml/disable"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.put(url, headers=headers)
    if response.status_code == 204:
        print("Workflow disabled successfully.")
    else:
        print(f"Failed to disable: {response.status_code} {response.text}")

def check_for_apm():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(CAREERS_URL, wait_until="networkidle")

        apm_keywords = ["associate product manager", "apm program"]

        # Find all links and check for APM keywords
        job_link = None
        links = page.locator("a").all()
        for link in links:
            try:
                link_text = link.inner_text().lower()
                if any(kw in link_text for kw in apm_keywords):
                    href = link.get_attribute("href")
                    if href:
                        job_link = href if href.startswith("http") else "https://instacart.careers" + href
                        break
            except:
                continue

        browser.close()
        found = job_link is not None
        return found, job_link

def main():
    found, job_link = check_for_apm()
    if found:
        body = f'<p>It\'s time! 🎉 The Instacart APM program is open.</p><p><a href="{job_link}">Click here to apply</a></p>'
        send_email("it's time!", body)
        print(f"APM found at {job_link} — email sent!")
        disable_workflow()
    else:
        body = "<p>No leads yet. The Instacart APM program is not currently listed.</p>"
        send_email("no leads yet", body)
        print("APM not found — email sent.")

main()
