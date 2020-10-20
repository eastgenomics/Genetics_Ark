from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode

from .forms import SignUpForm
from .tokens import account_activation_token
from ga_core.settings import ALLOWED_HOSTS


@login_required
def index(request):
    return render(request, '/')


def log_out(request):
    logout(request)
    messages.add_message(
        request,
        messages.SUCCESS,
        """Successfully logged out"""
    )
    # redirect to home page which goes back to login
    return redirect('/')


def activate(request, uid, token):
    print("uid", uid)
    print("token", token)
    try:
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # checking if the user exists, if the token is valid.
    if user is not None:
        print("valid user", user)
    if account_activation_token.check_token(user, token):
        print("activation token goodness", token)

    if user is not None and account_activation_token.check_token(user, token):
        print("valid and activating")
        # if valid set active true
        user.is_active = True
        # set signup_confirmation true
        user.profile.signup_confirmation = True
        user.save()
        login(request, user)
        return redirect('home')
    else:
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

            # print(message)

            # email = EmailMessage(subject, message)
            # email.send()
            print(user.profile.email)
            send_mail(subject, message, 'emeeglh@gmail.com',
                      [user.profile.email], fail_silently=False)

            return render(request, 'registration/activation_sent.html')
        else:
            # error in form
            messages.add_message(
                request,
                messages.ERROR,
                """Error in sign up form""",
                extra_tags="alert-danger"
            )
    return render(request, 'registration/sign_up.html', {'form': form})
