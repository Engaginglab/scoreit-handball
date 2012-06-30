from tastypie.resources import ModelResource
from tastypie import fields
from handball.models import *
from django.contrib.auth.models import User
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.authentication import BasicAuthentication


class UnionResource(ModelResource):
    clubs = fields.ToManyField('handball.api.ClubResource', 'clubs', full=True)

    class Meta:
        queryset = Union.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()


class ClubResource(ModelResource):
    union = fields.ForeignKey(UnionResource, 'union')
    teams = fields.ToManyField('handball.api.TeamResource', 'teams')

    class Meta:
        queryset = Club.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = DjangoAuthorization()


class LeagueResource(ModelResource):
    class Meta:
        queryset = Team.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = DjangoAuthorization()


class TeamResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    league = fields.ForeignKey(LeagueResource, 'league', full=True)

    class Meta:
        queryset = Team.objects.all()
        authorization = DjangoAuthorization()


class UserResource(ModelResource):
    person = fields.OneToOneField('handball.api.PersonResource', 'person', full=True)

    class Meta:
        queryset = User.objects.all()
        excludes = ["email", "password"]


class PersonResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    teams = fields.ManyToManyField(TeamResource, 'teams')

    class Meta:
        queryset = Person.objects.all()
        authorization = DjangoAuthorization()


class GameTypeResource(ModelResource):
    class Meta:
        queryset = GameType.objects.all()
        include_resource_uri = False
        authorization = DjangoAuthorization()


class SiteResource(ModelResource):
    class Meta:
        queryset = Site.objects.all()
        include_resource_uri = False
        authorization = DjangoAuthorization()


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
        authorization = DjangoAuthorization()


class EventTypeResource(ModelResource):
    game = fields.ForeignKey(GameResource, 'game')

    class Meta:
        queryset = EventType.objects.all()
        include_resource_uri = False
        authorization = DjangoAuthorization()


class EventResource(ModelResource):
    player = fields.ForeignKey(PersonResource, 'person')
    game = fields.ForeignKey(GameResource, 'game')

    class Meta:
        queryset = Event.objects.all()
        authorization = DjangoAuthorization()
        include_resource_uri = False
