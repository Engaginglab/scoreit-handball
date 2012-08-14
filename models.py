# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.utils.translation import ugettext as _
from tastypie.models import create_api_key


class Union(models.Model):
    name = models.CharField(max_length=50)

    managers = models.ManyToManyField('Person', blank=True, related_name='unions_managed', through='UnionManagerRelation')

    def __unicode__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=50)

    union = models.ForeignKey('Union', related_name='districts')
    managers = models.ManyToManyField('Person', blank=True, related_name='districts_managed', through='DistrictManagerRelation')

    def __unicode__(self):
        return self.name


class Club(models.Model):
    name = models.CharField(max_length=50)
    validated = models.BooleanField(blank=True, default=False)

    home_site = models.ForeignKey('Site', blank=True, null=True)
    district = models.ForeignKey('District', related_name='clubs')
    members = models.ManyToManyField('Person', related_name='clubs', blank=True, through='ClubMemberRelation')
    managers = models.ManyToManyField('Person', blank=True, related_name='clubs_managed', through='ClubManagerRelation')

    def __unicode__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=50)
    validated = models.BooleanField(blank=True, default=False)

    players = models.ManyToManyField('Person', blank=True, related_name='teams', through='TeamPlayerRelation')
    coaches = models.ManyToManyField('Person', blank=True, related_name='teams_coached', through='TeamCoachRelation')
    # league = models.ForeignKey('League', related_name='league', blank=True)
    club = models.ForeignKey('Club', related_name='teams')
    managers = models.ManyToManyField('Person', blank=True, related_name='teams_managed', through='TeamManagerRelation')

    def __unicode__(self):
        return self.club.name + ' ' + self.name


class LeagueLevel(models.Model):
    name = models.CharField(max_length=50)

    union_specific = models.BooleanField(default=False)
    district_specific = models.BooleanField(default=False)


class AgeGroup(models.Model):
    name = models.CharField(max_length=20)

    min_age = models.IntegerField()
    max_age = models.IntegerField()


class Group(models.Model):
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=20, choices=(('league', _('league')), ('cup', _('cup')), ('tournament', _('tournament'))))
    gender = models.CharField(max_length=10, choices=(('male', _('male')), ('female', _('female'))), default='male')

    level = models.ForeignKey('LeagueLevel', blank=True, null=True)
    age_group = models.CharField(max_length=20, choices=(('adults', _('adults')), ('juniors_a', _('juniors a')),
        ('juniors_b', _('juniors b')), ('juniors_c', _('juniors c')), ('juniors_d', _('juniors d')), ('juniors_e', _('juniors e'))))
    union = models.ForeignKey('Union', related_name='leagues', blank=True, null=True)
    district = models.ForeignKey('District', related_name='leagues', blank=True, null=True)
    teams = models.ManyToManyField('Team', related_name='groups', through='GroupTeamRelation')
    managers = models.ManyToManyField('Person', blank=True, related_name='groups_managed', through='GroupManagerRelation')

    def __unicode__(self):
        return u'{0}: {1} {2} {3}'.format(self.kind, self.name, self.gender, self.age_group.name)


class GroupTeamRelation(models.Model):
    group = models.ForeignKey('Group')
    team = models.ForeignKey('Team')

    points = models.IntegerField()
    position = models.IntegerField()


class Person(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, related_name='handball_profile')

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    pass_number = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=(('male', _('male')), ('female', _('female'))), default='male')
    mobile_number = models.CharField(max_length=20, blank=True)

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name


class Game(models.Model):
    number = models.IntegerField(unique=True, blank=True, null=True)
    start = models.DateTimeField()
    score_home = models.IntegerField()
    score_away = models.IntegerField()
    duration = models.IntegerField(default=60)

    home = models.ForeignKey('Team', related_name='games_home')
    away = models.ForeignKey('Team', related_name='games_away')
    referee = models.ForeignKey('Person', related_name='games_as_referee')
    timer = models.ForeignKey('Person', related_name='games_as_timer')
    secretary = models.ForeignKey('Person', related_name='games_as_secretary')
    supervisor = models.ForeignKey('Person', related_name='games_as_supervisor')
    winner = models.ForeignKey('Team', related_name='games_won', blank=True, null=True)
    group = models.ForeignKey('Group', related_name='games', blank=True, null=True)
    # game_type = models.CharField(max_length=20, choices=(('cub', _('cub')), ('friendly', _('friendly')), ('league', _('league')), ('tournament', _('tournament'))))
    site = models.ForeignKey('Site')
    players = models.ManyToManyField('Person', through='GamePlayerRelation')

    def __unicode__(self):
        return u'{0}/{1}/{2}: {3} {4} vs. {5} {6}'.format(self.start.year, self.start.month, self.start.day, self.home.club.name, self.home.name, self.away.club.name, self.away.name)


class Site(models.Model):
    # name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zip_code = models.IntegerField()
    number = models.IntegerField(unique=True, blank=True, null=True)

    def __unicode__(self):
        return u'{0}, {1} {2} (#{3})'.format(self.address, self.zip_code, self.city, self.number)


class GamePlayerRelation(models.Model):
    player = models.ForeignKey('Person')
    game = models.ForeignKey('Game')

    team = models.ForeignKey('Team')
    shirt_number = models.IntegerField(blank=True, null=True)
    # goals = models.IntegerField()
    # warnings = models.IntegerField()
    # penalties = models.IntegerField()
    # disqualifications = models.IntegerField()
    # team_penalties = models.IntegerField()
    # penalty_shots_hit = models.IntegerField()
    # penalty_shots_miss = models.IntegerField()


class ClubMemberRelation(models.Model):
    member = models.ForeignKey('Person')
    club = models.ForeignKey('Club')

    primary = models.BooleanField()
    member_confirmed = models.BooleanField(default=False)
    manager_confirmed = models.BooleanField(default=False)


class TeamPlayerRelation(models.Model):
    player = models.ForeignKey('Person')
    team = models.ForeignKey('Team')

    player_confirmed = models.BooleanField(default=False)
    manager_confirmed = models.BooleanField(default=False)


class TeamCoachRelation(models.Model):
    coach = models.ForeignKey('Person')
    team = models.ForeignKey('Team')

    coach_confirmed = models.BooleanField(default=False)
    manager_confirmed = models.BooleanField(default=False)


class ClubManagerRelation(models.Model):
    club = models.ForeignKey('Club')
    manager = models.ForeignKey('Person')
    appointed_by = models.ForeignKey(User, related_name='handball_club_managers_appointed', blank=True, null=True)


class TeamManagerRelation(models.Model):
    team = models.ForeignKey('Team')
    manager = models.ForeignKey('Person')
    appointed_by = models.ForeignKey(User, related_name='handball_team_managers_appointed', blank=True, null=True)


class GroupManagerRelation(models.Model):
    group = models.ForeignKey('Group')
    manager = models.ForeignKey('Person')
    appointed_by = models.ForeignKey(User, related_name='handball_group_managers_appointed', blank=True, null=True)


class DistrictManagerRelation(models.Model):
    district = models.ForeignKey('District')
    manager = models.ForeignKey('Person')
    appointed_by = models.ForeignKey(User, related_name='handball_district_managers_appointed', blank=True, null=True)


class UnionManagerRelation(models.Model):
    union = models.ForeignKey('Union')
    manager = models.ForeignKey('Person')
    appointed_by = models.ForeignKey(User, related_name='handball_union_managers_appointed', blank=True, null=True)


class Event(models.Model):
    time = models.IntegerField()

    person = models.ForeignKey('Person')
    event_type = models.ForeignKey('EventType')
    game = models.ForeignKey('Game', related_name='events')
    team = models.ForeignKey('Team')


class EventType(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


def set_union_by_district(sender, instance, **kwargs):
    # If district is set, set according union
    if instance.district:
        instance.union = instance.district.union


def player_to_club_member(sender, instance, created, **kwargs):
    try:
        ClubMemberRelation.objects.get(member=instance.player, club=instance.team.club)
    except ClubMemberRelation.DoesNotExist:
        ClubMemberRelation.objects.create(member=instance.player, club=instance.team.club,
            manager_confirmed=instance.manager_confirmed, member_confirmed=instance.player_confirmed)


def coach_to_club_member(sender, instance, created, **kwargs):
    try:
        ClubMemberRelation.objects.get(member=instance.coach, club=instance.team.club)
    except ClubMemberRelation.DoesNotExist:
        ClubMemberRelation.objects.create(member=instance.coach, club=instance.team.club,
            manager_confirmed=instance.manager_confirmed, member_confirmed=instance.coach_confirmed)


def add_player_to_team(sender, instance, created, **kwargs):
    try:
        TeamPlayerRelation.objects.get(team=instance.team, player=instance.player)
    except TeamPlayerRelation.DoesNotExist:
        TeamPlayerRelation.objects.create(team=instance.team, player=instance.player, manager_confirmed=True, player_confirmed=True)


def club_member_to_manager(sender, instance, created, **kwargs):
    managers = ClubManagerRelation.objects.filter(club=instance.club)
    if len(managers) == 0:
        ClubManagerRelation.objects.create(club=instance.club, manager=instance.member)


def team_player_to_manager(sender, instance, created, **kwargs):
    managers = TeamManagerRelation.objects.filter(team=instance.team)
    if len(managers) == 0:
        TeamManagerRelation.objects.create(team=instance.team, manager=instance.player)


def team_coach_to_manager(sender, instance, created, **kwargs):
    managers = TeamManagerRelation.objects.filter(team=instance.team)
    if len(managers) == 0:
        TeamManagerRelation.objects.create(team=instance.team, manager=instance.coach)


def club_primary_check(sender, instance, **kwargs):
    clubs = ClubMemberRelation.objects.filter(member=instance.member)

    if len(clubs) == 0:
        instance.primary = True


# Create API key for a new user
post_save.connect(create_api_key, sender=User)
pre_save.connect(set_union_by_district, sender=Group)
post_save.connect(player_to_club_member, sender=TeamPlayerRelation)
post_save.connect(coach_to_club_member, sender=TeamCoachRelation)
post_save.connect(add_player_to_team, sender=GamePlayerRelation)
post_save.connect(club_member_to_manager, sender=ClubMemberRelation)
post_save.connect(team_player_to_manager, sender=TeamPlayerRelation)
post_save.connect(team_coach_to_manager, sender=TeamCoachRelation)
pre_save.connect(club_primary_check, sender=ClubMemberRelation)
# m2m_changed.connect(set_club_by_team, sender=Team.players.through)
