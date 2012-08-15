# -*- coding: utf-8 -*-

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, ALL
from tastypie import fields
from handball.models import *
from django.contrib.auth.models import User
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication
from django.http import HttpResponse, HttpResponseBadRequest
from tastypie.http import HttpUnauthorized
from tastypie.serializers import Serializer
from tastypie.utils.mime import determine_format
from auth.api import UserResource
from django.core.mail import send_mail


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
    union = fields.ForeignKey(UnionResource, 'union', full=True)

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


class GroupResource(ModelResource):
    union = fields.ForeignKey(UnionResource, 'union', blank=True, null=True, full=True)
    district = fields.ForeignKey(DistrictResource, 'district', blank=True, null=True, full=True)

    class Meta:
        queryset = Group.objects.all()
        # allowed_methods = ['get', '']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'union': ALL_WITH_RELATIONS,
            'district': ALL_WITH_RELATIONS,
            'kind': ALL
        }


class PersonResource(ModelResource):
    user = fields.OneToOneField(UserResource, 'user', blank=True, null=True, related_name='handball_profile')

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


class ClubResource(ModelResource):
    district = fields.ForeignKey(DistrictResource, 'district', full=True)

    class Meta:
        queryset = Club.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'district': ALL_WITH_RELATIONS,
            'managers': ALL_WITH_RELATIONS
        }

    # def obj_create(self, bundle, request=None, **kwargs):
    #     # The user to create a club becomes its first manager (for lack of other people)
    #     try:
    #         person = Person.objects.get(user=request.user)
    #         person_resource = PersonResource()
    #         bundle.data['managers'] = [person_resource.get_resource_uri(person)]
    #     except Person.DoesNotExist:
    #         pass
    #     return super(ClubResource, self).obj_create(bundle, request)


class TeamResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)

    class Meta:
        queryset = Team.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'club': ALL_WITH_RELATIONS,
            'managers': ALL_WITH_RELATIONS
        }

    # def obj_create(self, bundle, request=None, **kwargs):
    #     # The user to create a team becomes its first manager (for lack of other people)
    #     try:
    #         person = Person.objects.get(user=request.user)
    #         person_resource = PersonResource()
    #         bundle.data['managers'] = [person_resource.get_resource_uri(person)]
    #     except Person.DoesNotExist:
    #         pass
    #     return super(TeamResource, self).obj_create(bundle, request)

    def dehydrate(self, bundle):
        bundle.data['display_name'] = str(bundle.obj)

        bundle.data['players'] = []
        resource = PersonResource()
        for membership in TeamPlayerRelation.objects.filter(player=bundle.obj, manager_confirmed=True):
            playerBundle = resource.build_bundle(obj=membership.player, request=bundle.request)
            bundle.data['players'].append(resource.full_dehydrate(playerBundle))
        return bundle


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


class TeamCoachRelationResource(ModelResource):
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    coach = fields.ForeignKey(PersonResource, 'coach', full=True)

    class Meta:
        queryset = TeamCoachRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'coach': ALL_WITH_RELATIONS,
            'team': ALL_WITH_RELATIONS
        }


class ClubManagerRelationResource(ModelResource):
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    manager = fields.ForeignKey(PersonResource, 'manager', full=True)
    appointed_by = fields.ForeignKey(UserResource, 'appointed_by', null=True, blank=True)

    class Meta:
        queryset = ClubManagerRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'club': ALL_WITH_RELATIONS,
            'manager': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        if request.user:
            user_resource = UserResource()
            bundle.data['appointed_by'] = user_resource.get_resource_uri(request.user)

        return super(ClubManagerRelationResource, self).obj_create(bundle, request)


class TeamManagerRelationResource(ModelResource):
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    manager = fields.ForeignKey(PersonResource, 'manager', full=True)
    appointed_by = fields.ForeignKey(UserResource, 'appointed_by', null=True, blank=True)

    class Meta:
        queryset = TeamManagerRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'team': ALL_WITH_RELATIONS,
            'manager': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        if request.user:
            user_resource = UserResource()
            bundle.data['appointed_by'] = user_resource.get_resource_uri(request.user)

        return super(TeamManagerRelationResource, self).obj_create(bundle, request)


class LeagueLevelResource(ModelResource):
    class Meta:
        queryset = LeagueLevel.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        allowed_methods = ['get']


class GroupTeamRelationResource(ModelResource):
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    group = fields.ForeignKey(GroupResource, 'group', full=True)

    class Meta:
        queryset = GroupTeamRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'group': ALL_WITH_RELATIONS,
            'team': ALL_WITH_RELATIONS
        }


# class LeagueManagerRelationResource(ModelResource):
#     league = fields.ForeignKey(LeagueResource, 'league', full=True)
#     manager = fields.ForeignKey(PersonResource, 'manager', full=True)

#     class Meta:
#         queryset = LeagueManagerRelation.objects.all()
#         authorization = Authorization()
#         authentication = Authentication()
#         always_return_data = True
#         filtering = {
#             'league': ALL_WITH_RELATIONS,
#             'manager': ALL_WITH_RELATIONS
#         }


# class DistrictManagerRelationResource(ModelResource):
#     district = fields.ForeignKey(DistrictResource, 'club', full=True)
#     manager = fields.ForeignKey(PersonResource, 'manager', full=True)

#     class Meta:
#         queryset = DistrictManagerRelation.objects.all()
#         authorization = Authorization()
#         authentication = Authentication()
#         always_return_data = True
#         filtering = {
#             'district': ALL_WITH_RELATIONS,
#             'manager': ALL_WITH_RELATIONS
#         }


# class UnionManagerRelationResource(ModelResource):
#     union = fields.ForeignKey(ClubResource, 'union', full=True)
#     manager = fields.ForeignKey(PersonResource, 'manager', full=True)

#     class Meta:
#         queryset = ClubManagerRelation.objects.all()
#         authorization = Authorization()
#         authentication = Authentication()
#         always_return_data = True
#         filtering = {
#             'union': ALL_WITH_RELATIONS,
#             'manager': ALL_WITH_RELATIONS
#         }


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


def send_invitation(request):
    if request.user.is_authenticated() and request.user.is_active:
        if 'email' in request.POST:
            email = request.POST['email']
        else:
            return HttpResponseBadRequest('Mandatory email parameter not provided.')

        if 'message' in request.POST:
            message = request.POST['message']
        else:
            message = 'Tritt Score.it bei und sehe deine Handballergebnisse online!'

        profile = None
        if 'profile' in request.POST:
            serializer = Serializer()
            profile = serializer.deserialize(request.POST['profile'])

        subject = '{0} {1} lädt dich zu Score.it ein!'.format(request.user.first_name, request.user.last_name)

        if profile:
            profile_link = 'http://score-it.de/?a=invite&p={0}'.format(profile.id)
            body = '{0} {1} hat ein Spielerprofil bei Score.it für dich erstellt. Melde dich jetzt bei Score.it an, um deine Handballergebnisse online abzurufen! Zum anmelden, klicke einfach folgenden Link: {3}'.format(request.user.first_name, request.user.last_name, profile_link)
        else:
            body = '{0} {1} hat dir eine Einladung zu der Sportplatform Score.it geschickt:<br>{2}Um dich anzumelden, besuche einfach http://score-it.de/!'.format(request.user.first_name, request.user.last_name, message)

        sender = 'noreply@score-it.de'
        recipients = [email]
        send_mail(subject, body, sender, recipients)
        return HttpResponse('')
    else:
        return HttpUnauthorized('Authentication through active user required.')
