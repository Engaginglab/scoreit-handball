import sha
import datetime
import pytz
from random import random
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from handball.forms import SignUpForm
from handball.models import Person
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


def index(request):
    return HttpResponse("This is the index page. There's nothing here yet!")


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']

            user = User.objects.create(username=username, password=password, email=email)
            user_profile = user.get_profile()

            # Build the activation key
            salt = sha.new(str(random())).hexdigest()[:5]
            activation_key = sha.new(salt + user.username).hexdigest()
            key_expires = datetime.datetime.now(pytz.utc) + datetime.timedelta(2)

            # User is unactive until visiting activation link
            user.is_active = False
            user_profile.activation_key = activation_key
            user_profile.key_expires = key_expires
            activation_link = 'http://127.0.0.1/activate/' + activation_key

            user.save()
            user_profile.save()  # Is it necessary to explicitly call the profiles save method?

            from django.core.mail import send_mail
            subject = _('Welcome to ScoreIt!')
            message = _('To activate, please click the following link:\n' + activation_link)
            sender = _('noreply@score-it.de')
            recipients = [email]
            send_mail(subject, message, sender, recipients)

            return HttpResponseRedirect('/thanks/')
    else:
        form = SignUpForm()

    return render_to_response('signup.html', {
        'form': form,
    })


def activate(request, activation_key):
    user_profile = get_object_or_404(Person, activation_key=activation_key)
    user_account = user_profile.user

    if user_profile.key_expires < datetime.datetime.now(pytz.utc):
        user_account.delete()
        return render_to_response('activate.html', {'expired': True})

    user_account.is_active = True
    user_account.save()
    return render_to_response('activate.html', {'success': True})


def thanks(request):
    return render_to_response('thanks.html')
