from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from handball.models import *
from django.contrib.auth.models import User
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.authentication import BasicAuthentication, Authentication, ApiKeyAuthentication
from handball.authorization import ManagerAuthorization


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
        queryset = Team.objects.all()
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
        authentication = ApiKeyAuthentication()
        include_resource_uri = False
