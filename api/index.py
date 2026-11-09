from http.server import BaseHTTPRequestHandler
import urllib.parse
import json
import imaplib
import email
import re
from datetime import datetime, timedelta

# ========== CONFIG ==========
GMAIL_USER = "sumiikashyap16@gmail.com"
GMAIL_PASS = "eyyvodxeheikkxqt"   # Tera naya App Password (bina space)
API_KEY = "FAMAPI"
# ============================

def check_fampay(amount, utr_input):
    try:
        # 1. Gmail Connect
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('"[Gmail]/All Mail"')
        
        # 2. Pichle 2 din ke emails search karo
        date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{date}")')

        if status != "OK" or not messages[0]:
            mail.logout()
            return False, "No recent emails found"

        # 3. Har email check karo
        for num in reversed(messages[0].split()):
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK": continue

            msg = email.message_from_bytes(data[0][1])
            sender = str(msg.get("From", "")).lower()

            if "famapp" in sender or "fam" in sender:
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                # 4. Amount Check (₹1000.0 aur 1000 dono match karega)
                amount_str = str(int(float(amount)))
                amount_pattern = rf'₹\s*{amount_str}(?:\.0+)?'
                
                if re.search(amount_pattern, body, re.IGNORECASE):
                    # 5. UTR Check
                    if str(utr_input) in body:
                        mail.logout()
                        return True, "Payment verified"
        
        mail.logout()
        return False, "Payment not found or amount mismatch"
    except Exception as e:
        return False, f"Gmail Error: {str(e)}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)

        api_key = query.get('api_key', [None])[0]
        utr = query.get('utr', [None])[0]
        amount = query.get('amount', [None])[0]

        if api_key != API_KEY:
            self.wfile.write(json.dumps({"status": "error", "message": "Invalid API Key"}).encode())
            return

        if not utr or not amount:
            self.wfile.write(json.dumps({"status": "error", "message": "UTR and Amount required"}).encode())
            return

        success, message = check_fampay(float(amount), utr)

        if success:
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Payment verified",
                "utr": utr,
                "amount": amount
            }).encode())
        else:
            self.wfile.write(json.dumps({
                "status": "error",
                "message": message
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
