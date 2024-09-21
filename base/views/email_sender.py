import base64
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def send_email(subject, message, from_email, to_email):
    # Set up OAuth 2.0 credentials
    creds = None
    if creds is None or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                {
                    "web": {
                        "client_id": "845512665517-sqrndab2vlttb0o4lba1nivu6civ38h4",
                        "client_secret": "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",
                        "redirect_uris": ["https://www.example.com/oauth2callback"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://accounts.google.com/o/oauth2/token"
                    }
                    },
                scopes=['https://mail.google.com/']
            )
            creds = flow.run_local_server(port=0)

    # Set up email backend
    email_backend = EmailBackend(
        host='smtp.gmail.com',
        port=587,
        username='your_email_address',
        password=creds.token,
        use_tls=True
    )

    # Create email message
    email = EmailMessage(
        subject,
        message,
        from_email,
        [to_email]
    )

    # Send email
    email_backend.send_messages([email])