from threading import Thread

from flask import current_app, render_template
from flask_mailman import EmailMessage


def _send_async_mail(app, message):
    with app.app_context():
        message.send()


def send_mail(subject, body, to, attachments=None, sync=False):
    app = current_app._get_current_object()
    message = EmailMessage(subject, body, to=[to])
    message.content_subtype = "html"
    if attachments:
        for attachment in attachments:
            message.attach(*attachment)
    if sync:
        message.send()
    else:
        Thread(target=_send_async_mail, args=(app, message)).start()


def send_confirmation_mail(user):
    token = user.get_confirmation_token()
    send_mail(
        "[Flasky] Confirm Your Account",
        render_template("email/confirm.html", user=user, token=token),
        to=user.email,
    )
