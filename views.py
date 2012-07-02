import sha
import base64
import datetime
import pytz
from random import random
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from handball.forms import SignUpForm
from handball.models import Person
from handball.api import PersonResource
from django.contrib.auth import authenticate
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


def validate_user(request):
    """
    Checks a user's basic auth credentials and, if valid, returns the users data
    """

    # if not request.META.get('HTTP_AUTHORIZATION'):
    #     return HttpResponseBadRequest('No HTTP_AUTHORIZATION header found')

    # try:
    #     (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split()
    #     if auth_type.lower() != 'basic':
    #         return HttpResponseBadRequest('Wrong auth type. Use basic auth!')
    #     user_pass = base64.b64decode(data)
    # except:
    #     return HttpResponseBadRequest('Could not decode auth credentials.')

    # bits = user_pass.split(':', 1)

    # if len(bits) != 2:
    #     return HttpResponseBadRequest('Could not decode auth credentials.')

    # user = authenticate(username=bits[0], password=bits[1])

    username = request.POST['username']
    password = request.POST['password']

    if not username or not password:
        return HttpResponseBadRequest()

    user = authenticate(username=username, password=password)

    if user is None or not user.is_active:
        return HttpResponseNotFound('User does not exist or password incorrect.')

    person = user.get_profile()

    person_resource = PersonResource()
    bundle = person_resource.build_bundle(obj=person, request=request)
    person_resource.full_dehydrate(bundle)
    bundle.data['api_key'] = user.api_key.key

    return HttpResponse(person_resource.serialize(None, bundle, 'application/json'))
