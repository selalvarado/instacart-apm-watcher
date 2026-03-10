import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
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
        print(f"Failed to disable workflow: {response.status_code} {response.text}")

def check_for_apm():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(CAREERS_URL, wait_until="networkidle")

        # Print all clickable text elements to see what's on the page
        print("=== PAGE TEXT ===")
        print(page.inner_text("body")[:3000])  # first 3000 chars

        # Print all elements that contain "Product"
        print("=== PRODUCT ELEMENTS ===")
        product_elements = page.locator("text=Product").all()
        print(f"Found {len(product_elements)} elements with 'Product'")
        for el in product_elements:
            print(f"  Tag: {el.evaluate('el => el.tagName')}, Text: {el.inner_text()[:100]}")

        # Find and click the "Product" section to expand it
        product_section = page.locator("text=Product").first
        product_section.click()

        # Wait for the section to expand
        page.wait_for_timeout(2000)

        # Now grab the full page content
        content = page.content()
        text = page.inner_text("body").lower()

        apm_keywords = ["associate product manager", "apm program"]
        found = any(kw in text for kw in apm_keywords)

        job_link = None
        if found:
            # Look for a link containing APM keywords
            links = page.locator("a").all()
            for link in links:
                link_text = link.inner_text().lower()
                if any(kw in link_text for kw in apm_keywords):
                    href = link.get_attribute("href")
                    if href:
                        job_link = href if href.startswith("http") else "https://instacart.careers" + href
                    break

        browser.close()
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
        disable_workflow()
    else:
        body = "<p>No leads yet. The Instacart APM program is not currently listed.</p>"
        send_email("no leads yet", body)
        print("APM not found — email sent.")

main()
