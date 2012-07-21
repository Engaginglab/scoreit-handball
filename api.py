import sha
import datetime
from random import random
import pytz
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from handball.models import *
from handball.forms import SignUpForm
from django.contrib.auth.models import User
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from tastypie.serializers import Serializer
from tastypie.utils.mime import determine_format
from django.utils.translation import ugettext as _


class UnionResource(ModelResource):
    # clubs = fields.ToManyField('handball.api.ClubResource', 'clubs', full=True)
    managers = fields.ToManyField('handball.api.PersonResource', 'managers')

    class Meta:
        queryset = Union.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'name': ('exact')
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a union becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(UnionResource, self).obj_create(bundle, request)


class DistrictResource(ModelResource):
    union = fields.ForeignKey(UnionResource, 'union', full=True)

    class Meta:
        queryset = District.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'union': ALL_WITH_RELATIONS
        }

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


class LeagueResource(ModelResource):
    class Meta:
        queryset = League.objects.all()
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = Authorization()


class ClubResource(ModelResource):
    district = fields.ForeignKey(DistrictResource, 'district', full=True)
    # teams = fields.ToManyField('handball.api.TeamResource', 'teams')

    class Meta:
        queryset = Club.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'union': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a club becomes its first manager (for lack of other people)
        # bundle.data['managers'] = ['/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(ClubResource, self).obj_create(bundle, request)


class TeamResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    league = fields.ForeignKey(LeagueResource, 'league', full=True)
    players = fields.ManyToManyField('handball.api.PersonResource', 'players', full=True)

    class Meta:
        queryset = Team.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a team becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(TeamResource, self).obj_create(bundle, request)

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


class UserResource(ModelResource):
    person = fields.OneToOneField('handball.api.PersonResource', 'person', full=True)

    class Meta:
        queryset = User.objects.all()
        excludes = ['email', 'password']


class PersonResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user', blank=True, null=True)
    clubs = fields.ManyToManyField(ClubResource, 'clubs')
    # teams = fields.ManyToManyField(TeamResource, 'teams')

    class Meta:
        queryset = Person.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        excludes = ['activation_key', 'key_expires']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            'first_name': ['exact'],
            'last_name': ['exact']
        }

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


class GameTypeResource(ModelResource):
    class Meta:
        queryset = GameType.objects.all()
        include_resource_uri = False
        authorization = Authorization()
        authentication = Authentication()


class SiteResource(ModelResource):
    class Meta:
        queryset = Site.objects.all()
        include_resource_uri = False
        authorization = Authorization()
        authentication = Authentication()


class GameResource(ModelResource):
    home = fields.ForeignKey(TeamResource, 'home')
    away = fields.ForeignKey(TeamResource, 'away')
    referee = fields.ForeignKey(PersonResource, 'referee')
    timer = fields.ForeignKey(PersonResource, 'timer')
    secretary = fields.ForeignKey(PersonResource, 'secretary')
    winner = fields.ForeignKey(TeamResource, 'winner')
    union = fields.ForeignKey(UnionResource, 'union', full=True)
    league = fields.ForeignKey(LeagueResource, 'league', full=True)
    game_type = fields.ForeignKey(GameTypeResource, 'game_type', full=True)
    site = fields.ForeignKey(SiteResource, 'site', full=True)
    players = fields.ManyToManyField(PersonResource, 'players')
    events = fields.ToManyField('handball.api.EventResource', 'events', full=True)

    class Meta:
        queryset = Game.objects.all()
        authorization = Authorization()
        authentication = Authentication()


class EventTypeResource(ModelResource):
    game = fields.ForeignKey(GameResource, 'game')

    class Meta:
        queryset = EventType.objects.all()
        include_resource_uri = False
        authorization = Authorization()
        authentication = Authentication()


class EventResource(ModelResource):
    player = fields.ForeignKey(PersonResource, 'person')
    game = fields.ForeignKey(GameResource, 'game')

    class Meta:
        queryset = Event.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        include_resource_uri = False


"""
Non-resource api endpoints
"""


def sign_up(request):
    form = SignUpForm(request.POST)
    serializer = Serializer()
    format = determine_format(request, serializer, default_format='application/json')

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        email = form.cleaned_data['email']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        # gender = form.cleaned_data['gender']
        # pass_number = form.cleaned_data['pass_number']
        # address = form.cleaned_data['address']
        # city = form.cleaned_data['city']
        # zip_code = form.cleaned_data['zip_code']
        # mobile_number = form.cleaned_data['mobile_number']

        user = User.objects.create(username=username, password=password, first_name=first_name, last_name=last_name, email=email)

        profile = form.cleaned_data['profile'] or Person.objects.create()
        profile.first_name = first_name
        profile.last_name = last_name
        # profile.gender = gender
        # profile.pass_number = pass_number
        # profile.address = address
        # profile.city = city
        # profile.zip_code = zip_code
        # profile.mobile_number = mobile_number
        profile.user = user

        # Build the activation key
        salt = sha.new(str(random())).hexdigest()[:5]
        activation_key = sha.new(salt + user.username).hexdigest()
        key_expires = datetime.datetime.now(pytz.utc) + datetime.timedelta(2)

        # User is unactive until visiting activation link
        user.is_active = False
        profile.activation_key = activation_key
        profile.key_expires = key_expires
        activation_link = 'http://127.0.0.1:8000/auth/activate/' + activation_key

        user.save()
        profile.save()

        subject = _('Welcome to ScoreIt!')
        message = _('To activate, please click the following link:\n' + activation_link)
        sender = _('noreply@score-it.de')
        recipients = [email]
        send_mail(subject, message, sender, recipients)

        user_resource = UserResource()
        person_resource = PersonResource()

        data = {
            'user': user_resource.get_resource_uri(user),
            'profile': person_resource.get_resource_uri(profile),
            'activation_key': activation_key
        }

        return HttpResponse(serializer.serialize(data, format, {}))

    else:
        return HttpResponseBadRequest(serializer.serialize(form.errors, format, {}))


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


def is_unique(request):
    data = {}

    if 'user_name' in request.GET:
        user_name = request.GET['user_name']

        try:
            User.objects.get(username=user_name)
            unique = False
        except User.DoesNotExist:
            unique = True
        except User.MultipleObjectsReturned:
            unique = False

        data['user_name'] = unique

    if 'email' in request.GET:
        email = request.GET['email']

        try:
            User.objects.get(email=email)
            unique = False
        except User.DoesNotExist:
            unique = True
        except User.MultipleObjectsReturned:
            unique = False

        data['email'] = unique

    if 'pass_number' in request.GET:
        pass_number = request.GET['pass_number']

        try:
            Person.objects.get(pass_number=pass_number)
            unique = False
        except Person.DoesNotExist:
            unique = True
        except Person.MultipleObjectsReturned:
            unique = False

        data['pass_number'] = unique

    serializer = Serializer()

    format = determine_format(request, serializer, default_format='application/json')

    return HttpResponse(serializer.serialize(data, format, {}))
