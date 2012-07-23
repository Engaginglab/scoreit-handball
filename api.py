from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie import fields
from handball.models import *
from django.contrib.auth.models import User
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication
from django.http import HttpResponse, HttpResponseBadRequest
from tastypie.serializers import Serializer
from tastypie.utils.mime import determine_format
from auth.api import UserResource


class UnionResource(ModelResource):
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
        bundle.data['managers'] = ['/handball/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(UnionResource, self).obj_create(bundle, request)


class DistrictResource(ModelResource):
    union = fields.ForeignKey(UnionResource, 'union')

    class Meta:
        queryset = District.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'union': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a union becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/handball/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(DistrictResource, self).obj_create(bundle, request)

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
    managers = fields.ToManyField('handball.api.PersonResource', 'managers')

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
        bundle.data['managers'] = ['/handball/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(ClubResource, self).obj_create(bundle, request)


class TeamResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    players = fields.ManyToManyField('handball.api.PersonResource', 'players')
    coaches = fields.ManyToManyField('handball.api.PersonResource', 'coaches')
    managers = fields.ManyToManyField('handball.api.PersonResource', 'managers')

    class Meta:
        queryset = Team.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a team becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/handball/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(TeamResource, self).obj_create(bundle, request)

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


class PersonResource(ModelResource):
    user = fields.OneToOneField(UserResource, 'user', blank=True, null=True)
    clubs = fields.ManyToManyField(ClubResource, 'clubs')
    clubs_managed = fields.ManyToManyField(ClubResource, 'clubs_managed', blank=True)
    teams = fields.ManyToManyField(TeamResource, 'teams', blank=True)
    teams_managed = fields.ManyToManyField(TeamResource, 'teams_managed', blank=True)
    teams_coached = fields.ManyToManyField(TeamResource, 'teams_coached', blank=True)

    class Meta:
        queryset = Person.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        excludes = ['activation_key', 'key_expires']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            'clubs': ALL_WITH_RELATIONS,
            'clubs_managed': ALL_WITH_RELATIONS,
            'teams': ALL_WITH_RELATIONS,
            'teams_managed': ALL_WITH_RELATIONS,
            'teams_coached': ALL_WITH_RELATIONS,
            'first_name': ['exact'],
            'last_name': ['exact']
        }

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)
        # del bundle.data['clubs']
        del bundle.data['clubs_managed']
        del bundle.data['teams']
        del bundle.data['teams_managed']
        del bundle.data['teams_coached']
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


def is_unique(request):
    data = {}

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
