from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from handball.models import *
from django.contrib.auth.models import User
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.authentication import BasicAuthentication, Authentication, ApiKeyAuthentication
from handball.authorization import ManagerAuthorization
from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest
from tastypie.serializers import Serializer
from tastypie.utils.mime import determine_format


class UnionResource(ModelResource):
    # clubs = fields.ToManyField('handball.api.ClubResource', 'clubs', full=True)
    managers = fields.ToManyField('handball.api.PersonResource', 'managers')

    class Meta:
        queryset = Union.objects.all()
        allowed_methods = ['get', 'post', 'put', 'patch']
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        filtering = {
            'name': ('exact')
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a union becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(UnionResource, self).obj_create(bundle, request)


class LeagueResource(ModelResource):
    class Meta:
        queryset = League.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authentication = ApiKeyAuthentication()
        authorization = Authorization()


class ClubResource(ModelResource):
    union = fields.ForeignKey(UnionResource, 'union')
    # teams = fields.ToManyField('handball.api.TeamResource', 'teams')

    class Meta:
        queryset = Club.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        filtering = {
            'union': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a club becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(ClubResource, self).obj_create(bundle, request)


class TeamResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    league = fields.ForeignKey(LeagueResource, 'league', full=True)
    players = fields.ManyToManyField('handball.api.PersonResource', 'players', full=True)

    class Meta:
        queryset = Team.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = ApiKeyAuthentication()

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a team becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(TeamResource, self).obj_create(bundle, request)


class UserResource(ModelResource):
    person = fields.OneToOneField('handball.api.PersonResource', 'person', full=True)

    class Meta:
        queryset = User.objects.all()
        excludes = ['email', 'password']


class PersonResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    # teams = fields.ManyToManyField(TeamResource, 'teams')

    class Meta:
        queryset = Person.objects.all()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        excludes = ['activation_key', 'key_expires']


class GameTypeResource(ModelResource):
    class Meta:
        queryset = GameType.objects.all()
        include_resource_uri = False
        authorization = Authorization()
        authentication = ApiKeyAuthentication()


class SiteResource(ModelResource):
    class Meta:
        queryset = Site.objects.all()
        include_resource_uri = False
        authorization = Authorization()
        authentication = ApiKeyAuthentication()


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
        authentication = ApiKeyAuthentication()


class EventTypeResource(ModelResource):
    game = fields.ForeignKey(GameResource, 'game')

    class Meta:
        queryset = EventType.objects.all()
        include_resource_uri = False
        authorization = Authorization()
        authentication = ApiKeyAuthentication()


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


def user_exists(request):
    username = request.GET['username']
    email = request.GET['email']
    username_exists = True
    email_exists = True

    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        username_exists = False
    except User.MultipleObjectsReturned:
        email_exists = True

    try:
        User.objects.get(email=email)
    except User.DoesNotExist:
        email_exists = False
    except User.MultipleObjectsReturned:
        email_exists = True

    data = {
        'username': username_exists,
        'email': email_exists
    }

    serializer = Serializer()

    format = determine_format(request, serializer, default_format='application/json')

    return HttpResponse(serializer.serialize(data, format, {}))
