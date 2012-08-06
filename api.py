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

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


class GroupResource(ModelResource):
    class Meta:
        queryset = Group.objects.all()
        authorization = Authorization()
        authentication = Authentication()


class ClubResource(ModelResource):
    district = fields.ForeignKey(DistrictResource, 'district', full=True)
    # teams = fields.ToManyField('handball.api.TeamResource', 'teams')
    # members = fields.ToManyField('handball.api.PersonResource', 'members', blank=True)
    managers = fields.ToManyField('handball.api.PersonResource', 'managers', blank=True)

    class Meta:
        queryset = Club.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'district': ALL_WITH_RELATIONS,
            'managers': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a club becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/handball/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(ClubResource, self).obj_create(bundle, request)

    def dehydrate(self, bundle):
        del bundle.data['managers']
        return bundle


class TeamResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    # players = fields.ManyToManyField('handball.api.PersonResource', 'players')
    # coaches = fields.ManyToManyField('handball.api.PersonResource', 'coaches')
    managers = fields.ManyToManyField('handball.api.PersonResource', 'managers')

    class Meta:
        queryset = Team.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'club': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        # The user to create a team becomes its first manager (for lack of other people)
        bundle.data['managers'] = ['/handball/api/v1/person/' + str(request.user.get_profile().id) + '/']
        return super(TeamResource, self).obj_create(bundle, request)

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)

        bundle.data['players'] = []
        resource = PersonResource()
        for membership in TeamPlayerRelation.objects.filter(player=bundle.obj, manager_confirmed=True):
            playerBundle = resource.build_bundle(obj=membership.player, request=bundle.request)
            bundle.data['players'].append(resource.full_dehydrate(playerBundle))
        return bundle


class PersonResource(ModelResource):
    user = fields.OneToOneField(UserResource, 'user', blank=True, null=True, related_name='handball_profile')
    # clubs = fields.ManyToManyField(ClubResource, 'clubs', blank=True)
    clubs_managed = fields.ManyToManyField(ClubResource, 'clubs_managed', blank=True)
    # teams = fields.ManyToManyField(TeamResource, 'teams', blank=True)
    teams_managed = fields.ManyToManyField(TeamResource, 'teams_managed', blank=True)
    # teams_coached = fields.ManyToManyField(TeamResource, 'teams_coached', blank=True)

    class Meta:
        queryset = Person.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        excludes = ['activation_key', 'key_expires']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            # 'clubs': ALL_WITH_RELATIONS,
            'clubs_managed': ALL_WITH_RELATIONS,
            # 'teams': ALL_WITH_RELATIONS,
            'teams_managed': ALL_WITH_RELATIONS,
            # 'teams_coached': ALL_WITH_RELATIONS,
            'first_name': ['exact'],
            'last_name': ['exact']
        }
        always_return_data = True

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)

        bundle.data['clubs'] = []
        resource = ClubResource()
        for membership in ClubMemberRelation.objects.filter(member=bundle.obj):
            clubBundle = resource.build_bundle(obj=membership.club, request=bundle.request)
            bundle.data['clubs'].append(resource.full_dehydrate(clubBundle))

        return bundle


class GameTypeResource(ModelResource):
    class Meta:
        queryset = GameType.objects.all()
        authorization = Authorization()
        authentication = Authentication()


class SiteResource(ModelResource):
    class Meta:
        queryset = Site.objects.all()
        authorization = Authorization()
        authentication = Authentication()


class GameResource(ModelResource):
    home = fields.ForeignKey(TeamResource, 'home')
    away = fields.ForeignKey(TeamResource, 'away')
    referee = fields.ForeignKey(PersonResource, 'referee')
    timer = fields.ForeignKey(PersonResource, 'timer')
    secretary = fields.ForeignKey(PersonResource, 'secretary')
    supervisor = fields.ForeignKey(PersonResource, 'supervisor')
    winner = fields.ForeignKey(TeamResource, 'winner', null=True)
    group = fields.ForeignKey(GroupResource, 'group')
    game_type = fields.ForeignKey(GameTypeResource, 'game_type')
    site = fields.ForeignKey(SiteResource, 'site')
    events = fields.ToManyField('handball.api.EventResource', 'events', full=True)

    class Meta:
        queryset = Game.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True

    def hydrate_m2m(self, bundle):
        for item in bundle.data['events']:
            item[u'game'] = self.get_resource_uri(bundle)
        return super(GameResource, self).hydrate_m2m(bundle)


class EventTypeResource(ModelResource):
    class Meta:
        queryset = EventType.objects.all()
        authorization = Authorization()
        authentication = Authentication()


class EventResource(ModelResource):
    person = fields.ForeignKey(PersonResource, 'person', full=True)
    game = fields.ForeignKey(GameResource, 'game')
    event_type = fields.ForeignKey(EventTypeResource, 'event_type')
    team = fields.ForeignKey(TeamResource, 'team')

    class Meta:
        queryset = Event.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        include_resource_uri = False


class ClubMemberRelationResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    member = fields.ForeignKey(PersonResource, 'member', full=True)

    class Meta:
        queryset = ClubMemberRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'member': ALL_WITH_RELATIONS,
            'club': ALL_WITH_RELATIONS
        }


class GamePlayerRelationResource(ModelResource):
    game = fields.ForeignKey(GameResource, 'game', full=True)
    player = fields.ForeignKey(PersonResource, 'player', full=True)
    team = fields.ForeignKey(TeamResource, 'team')

    class Meta:
        queryset = GamePlayerRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True


class TeamPlayerRelationResource(ModelResource):
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    player = fields.ForeignKey(PersonResource, 'player', full=True)

    class Meta:
        queryset = TeamPlayerRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'player': ALL_WITH_RELATIONS,
            'team': ALL_WITH_RELATIONS
        }


class SiteResource(ModelResource):
    class Meta:
        queryset = Site.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


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
