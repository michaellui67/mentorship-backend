import datetime

from flask import render_template
from flask_mail import Message
from itsdangerous import BadSignature, URLSafeTimedSerializer

import config
from app.api.mail_extension import mail


def generate_confirmation_token(email):
    from run import application

    serializer = URLSafeTimedSerializer(application.config["SECRET_KEY"])
    return serializer.dumps(email, salt=application.config["SECURITY_PASSWORD_SALT"])


def confirm_token(token, expiration=config.BaseConfig.UNVERIFIED_USER_THRESHOLD):

    from run import application

    serializer = URLSafeTimedSerializer(application.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=application.config["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
    except BadSignature:
        return False
    return email


def mock_send_email(recipient, subject, template):

    print("Mock Email Service")
    print(f"Subject: {subject}")
    print(f"Recipient: {recipient}")
    print(template)


def send_email(recipient, subject, template):
    from run import application

    if application.config["MOCK_EMAIL"]:
        mock_send_email(recipient, subject, template)
    else:
        msg = Message(
            subject,
            recipients=[recipient],
            html=template,
            sender=application.config["MAIL_DEFAULT_SENDER"],
        )
        mail.send(msg)


def send_email_verification_message(user_name, email):

    confirmation_token = generate_confirmation_token(email)
    from app.api.api_extension import api
    from app.api.resources.user import (
        UserEmailConfirmation,
    )

    confirm_url = api.url_for(
        UserEmailConfirmation, token=confirmation_token, _external=True
    )
    html = render_template(
        "email_confirmation.html",
        confirm_url=confirm_url,
        user_name=user_name,
        threshold=config.BaseConfig.UNVERIFIED_USER_THRESHOLD,
    )
    subject = "Mentorship System - Please confirm your email"
    send_email(email, subject, html)


def send_email_mentorship_relation_accepted(request_id):

    from app.database.models.mentorship_relation import MentorshipRelationModel
    from app.database.models.user import UserModel

    request = MentorshipRelationModel.find_by_id(request_id)

    if request.action_user_id == request.mentor_id:
        request_sender = UserModel.find_by_id(request.mentor_id)
        request_receiver = UserModel.find_by_id(request.mentee_id)
        role = "mentee"
    else:
        request_sender = UserModel.find_by_id(request.mentee_id)
        request_receiver = UserModel.find_by_id(request.mentor_id)
        role = "mentor"

    end_date = request.end_date
    date = datetime.datetime.fromtimestamp(end_date).strftime("%d-%m-%Y")

    subject = "Mentorship relation accepted!"
    html = render_template(
        "mentorship_relation_accepted.html",
        request_sender=request_sender.name,
        request_receiver=request_receiver.name,
        role=role,
        end_date=date,
    )
    send_email(request_sender.email, subject, html)


def send_email_new_request(user_sender, user_recipient, notes, sender_role):

    html = render_template(
        "email_relation_request.html",
        user_recipient_name=user_recipient.name,
        user_sender_name=user_sender.name,
        notes=notes,
        sender_role=sender_role,
    )
    subject = "Mentorship System - You have got new relation request"
    send_email(user_recipient.email, subject, html)
