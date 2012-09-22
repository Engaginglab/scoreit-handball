# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.utils.translation import ugettext as _
from tastypie.models import create_api_key


class Union(models.Model):
    """
       Top-level organizational institution in handball.
    """
    name = models.CharField(max_length=50)

    managers = models.ManyToManyField('Person', blank=True, related_name='unions_managed', through='UnionManagerRelation')

    def __unicode__(self):
        return self.name


class District(models.Model):
    """
        Regional division of a union
    """
    name = models.CharField(max_length=50)

    union = models.ForeignKey('Union', related_name='districts')  # union the district belongs to
    managers = models.ManyToManyField('Person', blank=True, related_name='districts_managed', through='DistrictManagerRelation')

    def __unicode__(self):
        return self.name


class Club(models.Model):
    """
        A handball club
    """
    name = models.CharField(max_length=50)
    validated = models.BooleanField(blank=True, default=False)  # Whether or not the club has been validated by a handball authority

    home_site = models.ForeignKey('Site', blank=True, null=True)  # Default site/ of this club
    district = models.ForeignKey('District', related_name='clubs')  # District the club belongs to
    members = models.ManyToManyField('Person', related_name='clubs', blank=True, through='ClubMemberRelation')  # Club members
    managers = models.ManyToManyField('Person', blank=True, related_name='clubs_managed', through='ClubManagerRelation')  # People with administrative rights limited to this club
    created_by = models.ForeignKey('Person', blank=True, null=True, related_name='clubs_created')  # Person this club was created by

    def __unicode__(self):
        return self.name


class Team(models.Model):
    """
        A handball team
    """
    name = models.CharField(max_length=50)
    validated = models.BooleanField(blank=True, default=False)  # Whether or not the team has been validated by a manager of the respective club

    players = models.ManyToManyField('Person', blank=True, related_name='teams', through='TeamPlayerRelation')  # People playing in this team
    coaches = models.ManyToManyField('Person', blank=True, related_name='teams_coached', through='TeamCoachRelation')  # People coaching this team
    club = models.ForeignKey('Club', related_name='teams')  # Club the team belongs to
    managers = models.ManyToManyField('Person', blank=True, related_name='teams_managed', through='TeamManagerRelation')  # People with administrative rights limited to this team
    created_by = models.ForeignKey('Person', blank=True, null=True, related_name='teams_created')  # Person this team was created by

    def __unicode__(self):
        return self.club.name + ' ' + self.name


class LeagueLevel(models.Model):
    """
        A league level like 'Bezirksliga' or 'Kreisklasse'. There is a clearly defined number of
        league levels while there can be an arbitrary number of leagues of each level.
    """
    name = models.CharField(max_length=50)

    union_specific = models.BooleanField(default=False)  # Wheter or not leagues of this level belong to a specific union
    district_specific = models.BooleanField(default=False)  # Wheter or not leagues of this level belong of a specific district

    def __unicode__(self):
        return self.name


class Group(models.Model):
    """
        A group of teams that play against each other. A league is a kind of group, for example.
    """
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=20, choices=(('league', _('league')), ('cup', _('cup')), ('tournament', _('tournament'))))  # The kind of the group
    gender = models.CharField(max_length=10, choices=(('male', _('male')), ('female', _('female'))), default='male')  # The gender of the players playing in this group
    validated = models.BooleanField(default=False)  # Whether or not this group has been validated by a handball authority

    level = models.ForeignKey('LeagueLevel', blank=True, null=True)  # The level of this league
    age_group = models.CharField(max_length=20, choices=(('adults', _('adults')), ('juniors_a', _('juniors a')),
        ('juniors_b', _('juniors b')), ('juniors_c', _('juniors c')), ('juniors_d', _('juniors d')), ('juniors_e', _('juniors e'))))  # The age group of the players playing in this league
    union = models.ForeignKey('Union', related_name='leagues', blank=True, null=True)  # The union this group belongs to, if union specific
    district = models.ForeignKey('District', related_name='leagues', blank=True, null=True)  # The district this group belongs to, if district specific
    teams = models.ManyToManyField('Team', related_name='groups', through='GroupTeamRelation')  # Teams playing in this group
    managers = models.ManyToManyField('Person', blank=True, related_name='groups_managed', through='GroupManagerRelation')  # People with administrative rights for this group

    def __unicode__(self):
        return u'{0}: {1} {2} {3}'.format(self.kind, self.name, self.gender, self.age_group)


class GroupTeamRelation(models.Model):
    """
        Intermediate model for the m2m relation between Group and Team
    """
    group = models.ForeignKey('Group')
    team = models.ForeignKey('Team')

    score = models.IntegerField(default=0)  # The teams score in this group. Teams get points by winning games
    validated = models.BooleanField(default=False)  # Whether or not this teams membership in this group has been validated


class Person(models.Model):
    """
        A person within the handball graph. Can be a player, coach, referee or person with any other function within handball.
    """
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
    validated = models.BooleanField(default=False)  # Wheter or not the authentity of the person has been validated

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name


class Game(models.Model):
    """
        A handball game.
    """
    number = models.IntegerField(unique=True, blank=True, null=True)  # Official handball game number
    start = models.DateTimeField()  # Start time
    score_home = models.IntegerField()  # Score of the home team
    score_away = models.IntegerField()  # Score of the away team
    duration = models.IntegerField(default=60)  # Duration of the game in minutes
    home_validated = models.BooleanField(default=False)  # Wheter or not a representative of the home team has validated the correctness of this game
    away_validated = models.BooleanField(default=False)  # Wheter or not a representative of the away team has validated the correctness of this game
    referee_validated = models.BooleanField(default=False)  # Wheter or not the referee has validated the correctness of this game

    home = models.ForeignKey('Team', related_name='games_home')  # home team
    away = models.ForeignKey('Team', related_name='games_away')  # away team
    referee = models.ForeignKey('Person', related_name='games_as_referee')
    timer = models.ForeignKey('Person', related_name='games_as_timer')  # Person operating the timer
    secretary = models.ForeignKey('Person', related_name='games_as_secretary')  # Person recording the game data
    supervisor = models.ForeignKey('Person', related_name='games_as_supervisor')  # Person supervising the game. Usually a representative of the home team.
    winner = models.ForeignKey('Team', related_name='games_won', blank=True, null=True)  # The winning team
    group = models.ForeignKey('Group', related_name='games', blank=True, null=True)  # The group this game belongs to
    # game_type = models.CharField(max_length=20, choices=(('cub', _('cub')), ('friendly', _('friendly')), ('league', _('league')), ('tournament', _('tournament'))))
    site = models.ForeignKey('Site')  # Where this game took place
    players = models.ManyToManyField('Person', through='GamePlayerRelation')  # Players involved in this game

    def __unicode__(self):
        return u'{0}/{1}/{2}: {3} {4} vs. {5} {6}'.format(self.start.year, self.start.month, self.start.day, self.home.club.name, self.home.name, self.away.club.name, self.away.name)


class Site(models.Model):
    """
        A place where handball games can take place.
    """
    # name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zip_code = models.IntegerField()
    number = models.IntegerField(unique=True, blank=True, null=True)  # Official number fo this site

    def __unicode__(self):
        return u'{0}, {1} {2} (#{3})'.format(self.address, self.zip_code, self.city, self.number)


class GamePlayerRelation(models.Model):
    """
        Intermediate model for the m2m relation between Game and Player
    """
    player = models.ForeignKey('Person')
    game = models.ForeignKey('Game')

    team = models.ForeignKey('Team')  # The team the player was playing for in this game
    shirt_number = models.IntegerField(blank=True, null=True)  # The shirt number the player was wearing in this game


class ClubMemberRelation(models.Model):
    """
        Intermediate model for the club membership m2m relation
    """
    member = models.ForeignKey('Person')
    club = models.ForeignKey('Club')

    primary = models.BooleanField(default=False)  # Whether or not this club is the primary club of this player
    validated = models.BooleanField(default=False)  # Wheter or not this membership has been validated


class TeamPlayerRelation(models.Model):
    """
        Intermediate model for the team membership m2m relation
    """
    player = models.ForeignKey('Person')
    team = models.ForeignKey('Team')

    validated = models.BooleanField(default=False)  # Whether or not the membership in this team has been validated


class TeamCoachRelation(models.Model):
    """
        Intermediate model for the m2m relation specifying the coaches of a team
    """
    coach = models.ForeignKey('Person')
    team = models.ForeignKey('Team')

    validated = models.BooleanField(default=False)  # Whether or not this person has been validated as a coach for this team


class ClubManagerRelation(models.Model):
    """
        Intermediate model for the m2m relation specifying the managers of a club
    """
    club = models.ForeignKey('Club')
    manager = models.ForeignKey('Person')

    validated = models.BooleanField(default=False)  # Whether or not this person has been validated as a manager for this club


class TeamManagerRelation(models.Model):
    """
        Intermediate model for the m2m relation specifying the managers of a team
    """
    team = models.ForeignKey('Team')
    manager = models.ForeignKey('Person')

    validated = models.BooleanField(default=False)  # Wheter or not this person has been validated as a manager of this team


class GroupManagerRelation(models.Model):
    """
        Intermediate model for the m2m relation specifying the managers of a group
    """
    group = models.ForeignKey('Group')
    manager = models.ForeignKey('Person')

    validated = models.BooleanField(default=False)  # Whether or not this person has been validated as a manager of this group


class DistrictManagerRelation(models.Model):
    """
        Intermediate model for the m2m relation specifying the managers of a district
    """
    district = models.ForeignKey('District')
    manager = models.ForeignKey('Person')

    validated = models.BooleanField(default=False)  # Whether or not this person has been validated as a manager of this district


class UnionManagerRelation(models.Model):
    """
        Intermediate model for the m2m relation specifying the managers of a union
    """
    union = models.ForeignKey('Union')
    manager = models.ForeignKey('Person')

    validated = models.BooleanField(default=False)  # Whether or not this person has been validated as a manager of this union


class Event(models.Model):
    """
        An event in a handball game. E.g. a goal, penalty etc.
    """
    time = models.IntegerField()  # The time this events occured at
    event_type = models.CharField(max_length=20, choices=(('goal', _('goal')), ('warning', _('yellow card')),
        ('disqualification', _('disqualification')), ('time_penalty', _('time penalty')), ('team_time_penalty', _('team time penalty')),
        ('penalty_shot_goal', _('penalty shot (goal)')), ('penalty_shot_miss', _('penalty shot (miss)'))))  # Type of the event

    person = models.ForeignKey('Person')  # The person associated with this event
    game = models.ForeignKey('Game', related_name='events')  # The game this events occurred in
    team = models.ForeignKey('Team')  # The team the respective person was playing in when this event occurred


def group_post_save(sender, instance, **kwargs):
    """
        This function is called after a Group object has been saved
    """
    # If district is set, set according union
    if instance.district:
        instance.union = instance.district.union


def team_player_post_save(sender, instance, created, **kwargs):
    """
        This function is called after a TeamPlayerRelation object has been saved
    """
    # Add player to club if not member already
    try:
        ClubMemberRelation.objects.get(member=instance.player, club=instance.team.club)
    except ClubMemberRelation.DoesNotExist:
        ClubMemberRelation.objects.create(member=instance.player, club=instance.team.club, validated=instance.validated)

    # If first team member, asign as manager
    managers = TeamManagerRelation.objects.filter(team=instance.team)
    if len(managers) == 0:
        TeamManagerRelation.objects.create(team=instance.team, manager=instance.player)


def team_coach_post_save(sender, instance, created, **kwargs):
    """
        This function is called after a TeamCoachRelation object has been saved
    """
    # Add coach to club if not member already
    try:
        ClubMemberRelation.objects.get(member=instance.coach, club=instance.team.club)
    except ClubMemberRelation.DoesNotExist:
        ClubMemberRelation.objects.create(member=instance.coach, club=instance.team.club, validated=instance.validated)

    # If first team member, asign as manager
    managers = TeamManagerRelation.objects.filter(team=instance.team)
    if len(managers) == 0:
        TeamManagerRelation.objects.create(team=instance.team, manager=instance.coach)


def game_player_post_save(sender, instance, created, **kwargs):
    """
        This function is called after a GamePlayerRelation object has been saved
    """
    # Add player to team if he's not a member already
    try:
        TeamPlayerRelation.objects.get(team=instance.team, player=instance.player)
    except TeamPlayerRelation.DoesNotExist:
        TeamPlayerRelation.objects.create(team=instance.team, player=instance.player, validated=True)


def club_member_post_save(sender, instance, created, **kwargs):
    """
        This function is called after a ClubMemberRelation object has been saved
    """
    # If first member, make manager
    managers = ClubManagerRelation.objects.filter(club=instance.club)
    if len(managers) == 0:
        ClubManagerRelation.objects.create(club=instance.club, manager=instance.member, validated=True)

    # If first club, make primary
    clubs = ClubMemberRelation.objects.filter(member=instance.member)
    if len(clubs) == 1 and clubs[0].primary == False:
        instance.primary = True
        instance.save()


def game_post_save(sender, instance, created, **kwargs):
    """
        This function is called after a Game object has been saved
    """
    if created:
        if not instance.winner:
            home_score = 1
            away_score = 1
        elif instance.home.id == instance.winner.id:
            home_score = 2
            away_score = 0
        elif instance.away.id == instance.winner.id:
            home_score = 0
            away_score = 2

        # Set site as default home site if not set yet
        if not instance.home.club.home_site:
            instance.home.club.home_site = instance.site
            instance.home.club.save()

        # Add teams to group if not already in it,
        # Add score to winner team
        try:
            rel = GroupTeamRelation.objects.get(team=instance.home, group=instance.group)
            rel.score += home_score
            rel.save()
        except GroupTeamRelation.DoesNotExist:
            GroupTeamRelation.objects.create(team=instance.home, group=instance.group, score=home_score)

        try:
            rel = GroupTeamRelation.objects.get(team=instance.away, group=instance.group)
            rel.score += away_score
            rel.save()
        except GroupTeamRelation.DoesNotExist:
            GroupTeamRelation.objects.create(team=instance.away, group=instance.group, score=away_score)


# Create API key for a new user
post_save.connect(create_api_key, sender=User)

pre_save.connect(group_post_save, sender=Group)
post_save.connect(team_player_post_save, sender=TeamPlayerRelation)
post_save.connect(team_coach_post_save, sender=TeamCoachRelation)
post_save.connect(game_player_post_save, sender=GamePlayerRelation)
post_save.connect(club_member_post_save, sender=ClubMemberRelation)
post_save.connect(game_post_save, sender=Game)
