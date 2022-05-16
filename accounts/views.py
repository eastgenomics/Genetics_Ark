from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

import logging


from .forms import SignUpForm
from .tokens import account_activation_token
from ga_core.settings import ALLOWED_HOSTS, DEFAULT_FROM_EMAIL, LOGGING

error_log = logging.getLogger("ga_error")


@login_required
def index(request):
    return render(request, '/')


def log_out(request):
    logout(request)
    messages.add_message(
        request,
        messages.SUCCESS,
        "Successfully logged out"
    )
    # redirect to home page which goes back to login
    return redirect('/')


def activate(request, uid, token):
    try:
        user = User.objects.get(pk=uid)
    except Exception as e:
        user = None
        error_log.error(f"User is none: {e}")

    if user is not None and user.profile.signup_confirmation is True:
        # user already activated, included after activation if user goes
        # back to stop an error
        return redirect('/')

    if user is not None and account_activation_token.check_token(user, token):
        # if valid activate user
        user.is_active = True
        user.profile.signup_confirmation = True
        user.save()
        login(request, user)
        messages.add_message(
            request,
            messages.SUCCESS,
            "Activation successful!"
        )
        return redirect('/')
    else:
        messages.add_message(
            request,
            messages.ERROR,
            "Error activating account, contact the bioinformatics team for "
            "support."
        )

        error_log.error(
            f"Error authenticating user: {user}"
        )

        return render(request, 'registration/activation_invalid.html')


def sign_up(request):
    context = {}
    form = SignUpForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():

            user = form.save()
            user.refresh_from_db()
            user.profile.first_name = form.cleaned_data.get('first_name')
            user.profile.last_name = form.cleaned_data.get('last_name')
            user.profile.email = form.cleaned_data.get('email')

            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Please Activate Your Account'

            message = render_to_string(
                'registration/activation_request.html',
                {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': user.pk,
                    'token': account_activation_token.make_token(user),
                }
            )
            try:
                send_mail(
                    subject, message, DEFAULT_FROM_EMAIL,
                    [user.profile.email], fail_silently=False
                )
                return render(request, 'registration/activation_sent.html')
            except Exception as e:
                print(e)
                err_msg = "Error generating confirmation email, please raise a ticket with the bioinformatics helpdesk"

                messages.add_message(
                    request,
                    messages.ERROR,
                    err_msg
                )
        else:
            # error in form
            messages.add_message(
                request,
                messages.ERROR,
                "Error in sign up form, please check the form and try again"
            )

    return render(request, 'registration/sign_up.html', {'form': form})
