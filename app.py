import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import pandas as pd

# Load environmental variables from the .env file
load_dotenv()

# ==================== CONFIGURATION FROM ENV ====================
EMAIL_ADDRESS = os.getenv("GMAIL_USER")
EMAIL_PASSWORD = os.getenv("GMAIL_PASS")
GROQ_KEY = os.getenv("GROQ_API_KEY")  
EXCEL_FILE = os.getenv("EXCEL_FILE")

# Static Configuration
SUBJECT = "Official Group Invitation Link"
TEMPLATE_FILE = "email_template.html"
DELAY_SECONDS = 3  # Time gap between emails to bypass spam blocks
# ================================================================


def verify_environment():
    """Checks that the core environmental configurations are loaded correctly."""
    missing = []
    if not EMAIL_ADDRESS:
        missing.append("GMAIL_USER")
    if not EMAIL_PASSWORD:
        missing.append("GMAIL_PASS")
    if not EXCEL_FILE:
        missing.append("EXCEL_FILE")

    if missing:
        print(f"Error: Missing required configuration keys in .env: {missing}")
        return False
    return True


def load_template(template_path):
    """Reads the HTML template file."""
    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()


def send_emails():
    # 0. Safety check on environment configurations
    if not verify_environment():
        return

    # 1. Prompt user for the Excel Column Name manually
    email_column = input("Enter the exact name of your Excel email column (e.g., Email): ").strip()
    if not email_column:
        print("Error: Column name cannot be empty.")
        return

    # 2. Prompt user for the manually entered group link
    invite_link = input("Please paste the group invite link: ").strip()
    if not invite_link:
        print("Error: Invite link cannot be empty.")
        return

    # 3. Read the template file
    try:
        template_content = load_template(TEMPLATE_FILE)
    except FileNotFoundError:
        print(f"Error: Template file '{TEMPLATE_FILE}' not found.")
        return

    # 4. Read the Excel file
    try:
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        print(f"Error: Excel file '{EXCEL_FILE}' not found.")
        return

    # Validate that the typed column actually exists in Excel
    if email_column not in df.columns:
        print(f"\nError: Column '{email_column}' was not found in '{EXCEL_FILE}'.")
        print(f"Available columns in your file are: {list(df.columns)}")
        return

    # Extract emails and drop any blank/NaN rows
    email_list = df[email_column].dropna().tolist()
    print(f"\nFound {len(email_list)} email addresses to process.")

    if not email_list:
        print("No emails found to process. Exiting.")
        return

    # 5. Connect to Gmail's SMTP Server
    print("Connecting to Gmail server securely...")
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    except Exception as e:
        print(f"Failed to connect or login to Gmail: {e}")
        return

    # 6. Loop and send emails
    success_count = 0
    total_emails = len(email_list)

    for index, recipient in enumerate(email_list, start=1):
        recipient = str(recipient).strip()

        # Skip invalid formats
        if "@" not in recipient:
            print(f"[{index}/{total_emails}] Skipping invalid email format: {recipient}")
            continue

        try:
            # Interpolate the HTML template with the provided link
            html_body = template_content.replace("{invite_link}", invite_link)

            # Setup the MIME message
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = recipient
            msg["Subject"] = SUBJECT
            
            # Attach body content as explicit HTML format
            msg.attach(MIMEText(html_body, "html"))

            # Send the email
            server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
            print(f"[{index}/{total_emails}] Successfully sent to: {recipient}")
            success_count += 1

            # Human mimicry delay execution (skip delay on the final email)
            if index < total_emails:
                print(f"Pausing for {DELAY_SECONDS} seconds to avoid spam filters...")
                time.sleep(DELAY_SECONDS)

        except Exception as e:
            print(f"[{index}/{total_emails}] Failed to send to {recipient}: {e}")

    # Close the server connection cleanly
    server.quit()
    print(f"\nFinished! Successfully processed and sent {success_count} emails.")


if __name__ == "__main__":
    send_emails()
