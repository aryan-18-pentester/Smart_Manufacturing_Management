import os
import resend
from flask import Flask, request, render_template, flash, redirect, url_for
resend.api_key = os.getenv("RESEND_API_KEY")

export RESEND_API_KEY="your_resend_api_key"


@app.route('/send-mail', methods=['GET', 'POST'])
@login_required
def send_mail():

    if request.method == 'POST':

        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not recipient or not subject or not message:
            flash('All fields are required.', 'danger')
            return redirect(url_for('send_mail'))

        try:
            email = resend.Emails.send({
                "from": "Smart Manufacturing <onboarding@resend.dev>",
                "to": [recipient],
                "subject": subject,
                "html": f"""
                    <h2>Smart Manufacturing Management System</h2>

                    <p>{message}</p>

                    <hr>

                    <p>This email was sent from the
                    Smart Manufacturing Management System.</p>
                """
            })

            flash('Email sent successfully.', 'success')

        except Exception as e:
            print("Email error:", e)
            flash('Failed to send email.', 'danger')

        return redirect(url_for('send_mail'))

    return render_template('send_mail.html')
