# -*- coding: utf-8 -*-
"""
    Resources for handball models.

    TODO: Use ApiKeyAuthentication for models that need authentication. Implement custom authorization based on handball graph.
"""

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, ALL
from tastypie import fields
from handball.models import *
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication
from django.http import HttpResponse, HttpResponseBadRequest
from tastypie.http import HttpUnauthorized
from tastypie.serializers import Serializer
from tastypie.utils.mime import determine_format
from auth.api import UserResource
from django.core.mail import send_mail


class UnionResource(ModelResource):
    """
        Resource for Union model
    """
    class Meta:
        queryset = Union.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'name': ('exact')
        }


class DistrictResource(ModelResource):
    """
        Resource for District model
    """
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
        """
            Insert 'display_name' field for use in UI
        """
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


class GroupResource(ModelResource):
    """
        Resource for Group model
    """
    union = fields.ForeignKey(UnionResource, 'union', blank=True, null=True, full=True)
    district = fields.ForeignKey(DistrictResource, 'district', blank=True, null=True, full=True)
    level = fields.ForeignKey('handball.api.LeagueLevelResource', 'level', blank=True, null=True, full=True)

    class Meta:
        queryset = Group.objects.all()
        # allowed_methods = ['get', '']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'union': ALL_WITH_RELATIONS,
            'district': ALL_WITH_RELATIONS,
            'kind': ALL,
            'age_group': ALL,
            'gender': ALL
        }


class PersonResource(ModelResource):
    """
        Resource for Person model
    """
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
        """
            Insert 'display_name' field for use in UI.
            'Manually' add clubs since the ManyToMany field is (for various reasons) not specified in the Resource.
        """
        bundle.data['display_name'] = str(bundle.obj)

        bundle.data['clubs'] = []
        resource = ClubResource()
        for membership in ClubMemberRelation.objects.filter(member=bundle.obj):
            clubBundle = resource.build_bundle(obj=membership.club, request=bundle.request)
            bundle.data['clubs'].append(resource.full_dehydrate(clubBundle))

        return bundle


class ClubResource(ModelResource):
    """
        Resource for the Club model
    """
    district = fields.ForeignKey(DistrictResource, 'district', full=True)
    home_site = fields.ForeignKey('handball.api.SiteResource', 'home_site', full=True, null=True)
    created_by = fields.ForeignKey(PersonResource, 'created_by', null=True)

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
        """
            Automatically fill created_by field if there is an authenticated user
        """
        bundle = super(TeamResource, self).obj_create(bundle, request)

        if request.user:
            try:
                profile = Person.objects.get(user=request.user)

                # Set created_by field
                bundle.obj.created_by = profile

                bundle.obj.save()
            except Person.DoesNotExist:
                pass

        return bundle


class TeamResource(ModelResource):
    """
        Resource for Team model
    """
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    created_by = fields.ForeignKey(PersonResource, 'created_by', null=True)

    class Meta:
        queryset = Team.objects.all()
        allowed_methods = ['get', 'post', 'put']
        authorization = Authorization()
        authentication = Authentication()
        filtering = {
            'club': ALL_WITH_RELATIONS,
            'managers': ALL_WITH_RELATIONS
        }

    def obj_create(self, bundle, request=None, **kwargs):
        """
            Automatically fill created_by field and instantly validate under certain conditions
        """
        bundle = super(TeamResource, self).obj_create(bundle, request)

        if request.user:
            try:
                profile = Person.objects.get(user=request.user)

                # Set created_by field
                bundle.obj.created_by = profile

                try:
                    # Instantly validate if user is manager of the respective club
                    ClubManagerRelation.objects.get(manager=profile, club=bundle.obj.club, validated=True)
                    bundle.obj.validated = True
                except ClubManagerRelation.DoesNotExist:
                    pass

                bundle.obj.save()
            except Person.DoesNotExist:
                pass

        return bundle

    def dehydrate(self, bundle):
        """
            Insert 'display_name' field for use in UI.
            'Manually' add players since the ManyToMany field is (for various reasons) not specified in the Resource.
        """
        bundle.data['display_name'] = str(bundle.obj)

        bundle.data['players'] = []
        resource = PersonResource()
        for membership in TeamPlayerRelation.objects.filter(player=bundle.obj, validated=True):
            playerBundle = resource.build_bundle(obj=membership.player, request=bundle.request)
            bundle.data['players'].append(resource.full_dehydrate(playerBundle))
        return bundle


class SiteResource(ModelResource):
    """
        Resource for Site model
    """
    class Meta:
        queryset = Site.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True

    def dehydrate(self, bundle):
        """
            Add display_name for user in UI
        """
        bundle.data['display_name'] = str(bundle.obj)
        return bundle


class GameResource(ModelResource):
    """
        Resource for the Game model
    """
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
        """
            For some reason tastypie does not correctly create ManyToMany relations. This is a simple fix for that.
        """
        for item in bundle.data['events']:
            item[u'game'] = self.get_resource_uri(bundle)
        return super(GameResource, self).hydrate_m2m(bundle)


class EventResource(ModelResource):
    """
        Resource for the Event model
    """
    person = fields.ForeignKey(PersonResource, 'person', full=True)
    game = fields.ForeignKey(GameResource, 'game')
    team = fields.ForeignKey(TeamResource, 'team')

    class Meta:
        queryset = Event.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        include_resource_uri = False


class ClubMemberRelationResource(ModelResource):
    """
        Resource for the ClubMemberRelation model
    """
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    member = fields.ForeignKey(PersonResource, 'member', full=True)

    class Meta:
        queryset = ClubMemberRelation.objects.all()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        always_return_data = True
        filtering = {
            'member': ALL_WITH_RELATIONS,
            'club': ALL_WITH_RELATIONS,
            'validated': ALL
        }

    def obj_create(self, bundle, request=None, **kwargs):
        """
            Instantly validate relation under certain condititions
        """
        bundle = super(ClubMemberRelationResource, self).obj_create(bundle, request)

        if request.user:
            try:
                profile = Person.objects.get(user=request.user)

                # Instantly validate if user is a manager or member of the respective club
                managers = ClubManagerRelation.objects.filter(manager=profile, club=bundle.obj.club, validated=True)
                members = ClubMemberRelation.objects.filter(member=profile, club=bundle.obj.club, validated=True)

                if (len(managers) or len(members)):
                    bundle.obj.validated = True
                    bundle.obj.save()
            except Person.DoesNotExist:
                pass

        return bundle


class GamePlayerRelationResource(ModelResource):
    """
        Resource for GamePlayerRelation resource
    """
    game = fields.ForeignKey(GameResource, 'game', full=True)
    player = fields.ForeignKey(PersonResource, 'player', full=True)
    team = fields.ForeignKey(TeamResource, 'team')

    class Meta:
        queryset = GamePlayerRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True


class TeamPlayerRelationResource(ModelResource):
    """
        Resource for TeamPlayerRelation resource
    """
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    player = fields.ForeignKey(PersonResource, 'player', full=True)

    class Meta:
        queryset = TeamPlayerRelation.objects.all()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        always_return_data = True
        filtering = {
            'player': ALL_WITH_RELATIONS,
            'team': ALL_WITH_RELATIONS,
            'validated': ALL
        }

    def obj_create(self, bundle, request=None, **kwargs):
        """
            Instantly validate relation under certain conditions
        """
        bundle = super(TeamPlayerRelationResource, self).obj_create(bundle, request)

        if request.user:
            try:
                profile = Person.objects.get(user=request.user)

                club_managers = ClubManagerRelation.objects.filter(manager=profile, club=bundle.obj.team.club, validated=True)
                team_managers = TeamManagerRelation.objects.filter(manager=profile, team=bundle.obj.team, validated=True)
                players = TeamPlayerRelation.objects.filter(player=profile, team=bundle.obj.team, validated=True)
                coaches = TeamCoachRelation.objects.filter(coach=profile, team=bundle.obj.team, validated=True)

                if (len(club_managers) or len(team_managers) or len(players) or len(coaches)):
                    bundle.obj.validated = True
                    bundle.obj.save()
            except Person.DoesNotExist:
                pass

        return bundle


class TeamCoachRelationResource(ModelResource):
    """
        Resource for TeamCoachRelation model
    """
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    coach = fields.ForeignKey(PersonResource, 'coach', full=True)

    class Meta:
        queryset = TeamCoachRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'coach': ALL_WITH_RELATIONS,
            'team': ALL_WITH_RELATIONS,
            'validated': ALL
        }

    def obj_create(self, bundle, request=None, **kwargs):
        """
            Instantly validate relation under certain conditions
        """
        bundle = super(TeamCoachRelationResource, self).obj_create(bundle, request)

        if request.user:
            try:
                profile = Person.objects.get(user=request.user)

                club_managers = ClubManagerRelation.objects.filter(manager=profile, club=bundle.obj.team.club, validated=True)
                managers = TeamManagerRelation.objects.filter(manager=profile, team=bundle.obj.team, validated=True)
                coaches = TeamCoachRelation.objects.filter(coach=profile, team=bundle.obj.team, validated=True)

                if (len(managers) or len(club_managers) or len(coaches)):
                    bundle.obj.validated = True
                    bundle.obj.save()
            except Person.DoesNotExist:
                pass

        return bundle


class ClubManagerRelationResource(ModelResource):
    """
        Resource for ClubManagerRelation model
    """
    club = fields.ForeignKey(ClubResource, 'club', full=True)
    manager = fields.ForeignKey(PersonResource, 'manager', full=True)

    class Meta:
        queryset = ClubManagerRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'club': ALL_WITH_RELATIONS,
            'manager': ALL_WITH_RELATIONS,
            'validated': ALL
        }

    def obj_create(self, bundle, request=None, **kwargs):
        """
            Instantly validate under certain conditions
        """
        bundle = super(ClubManagerRelationResource, self).obj_create(bundle, request)

        if request.user:
            try:
                profile = Person.objects.get(user=request.user)

                # Instantly validate if user is a manager of the respective club
                ClubManagerRelation.objects.get(manager=profile, club=bundle.obj.club, validated=True)
                bundle.obj.validated = True

                bundle.obj.save()
            except (Person.DoesNotExist, ClubManagerRelation.DoesNotExist):
                pass

        return bundle


class TeamManagerRelationResource(ModelResource):
    """
        Resource for TeamManagerRelation resource
    """
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    manager = fields.ForeignKey(PersonResource, 'manager', full=True)

    class Meta:
        queryset = TeamManagerRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'team': ALL_WITH_RELATIONS,
            'manager': ALL_WITH_RELATIONS,
            'validated': ALL
        }

    def obj_create(self, bundle, request=None, **kwargs):
        """
            Instantly validate relation under certain conditions
        """
        bundle = super(TeamManagerRelationResource, self).obj_create(bundle, request)

        if request.user:
            try:
                profile = Person.objects.get(user=request.user)

                # Instantly validate if user is a manager of the respective team
                TeamManagerRelation.objects.get(manager=profile, team=bundle.obj.team, validated=True)
                bundle.obj.validated = True

                bundle.obj.save()
            except (Person.DoesNotExist, TeamManagerRelation.DoesNotExist):
                pass

        return bundle


class LeagueLevelResource(ModelResource):
    """
        Resource for LeagueLevel model
    """
    class Meta:
        queryset = LeagueLevel.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        allowed_methods = ['get']


class GroupTeamRelationResource(ModelResource):
    """
        Resource for GroupTeamRelation resource
    """
    team = fields.ForeignKey(TeamResource, 'team', full=True)
    group = fields.ForeignKey(GroupResource, 'group', full=True)

    class Meta:
        queryset = GroupTeamRelation.objects.all()
        authorization = Authorization()
        authentication = Authentication()
        always_return_data = True
        filtering = {
            'group': ALL_WITH_RELATIONS,
            'team': ALL_WITH_RELATIONS,
            'validated': ALL
        }


"""
Non-resource api endpoints
"""


def is_unique(request):
    """
        Check if pass number already exists
    """
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
    """
        Send an invitation to another person via email. NOT TESTED YET
    """
    if request.user.is_authenticated() and request.user.is_active:
        if 'email' in request.POST:
            email = request.POST['email']
        else:
            return HttpResponseBadRequest('Mandatory email parameter not provided.')

        if 'message' in request.POST:
            message = request.POST['message']
        else:
            message = 'Tritt score.it bei und sehe deine Handballergebnisse online!'

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
