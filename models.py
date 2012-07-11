# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _
from tastypie.models import create_api_key


class Person(models.Model):
    user = models.OneToOneField(User, blank=True)

    # Fields used for user activation after signup
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    pass_number = models.IntegerField(unique=True, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=(('male', _('male')), ('female', _('female'))), default='male')
    mobile_number = models.CharField(max_length=20, blank=True)
    is_coach = models.BooleanField(default=False)
    is_referee = models.BooleanField(default=False)
    is_player = models.BooleanField(default=True)
    is_exec = models.BooleanField(default=False)

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name


class Team(models.Model):
    name = models.CharField(max_length=50)

    players = models.ManyToManyField('Person', blank=True, related_name='teams')
    coaches = models.ManyToManyField('Person', blank=True, related_name='teams_coaching')
    league = models.ForeignKey('League', related_name='league')
    club = models.ForeignKey('Club', related_name='teams')
    managers = models.ManyToManyField('Person', blank=True)

    def __unicode__(self):
        return self.club.name + ' ' + self.name


class Club(models.Model):
    name = models.CharField(max_length=50)

    union = models.ForeignKey('Union', related_name='clubs')
    managers = models.ManyToManyField('Person', blank=True)

    def __unicode__(self):
        return self.name


class League(models.Model):
    name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=(('male', _('male')), ('female', _('female'))))

    def __unicode__(self):
        return self.name


class Union(models.Model):
    name = models.CharField(max_length=50)

    managers = models.ManyToManyField('Person', blank=True)

    def __unicode__(self):
        return self.name


class Game(models.Model):
    number = models.IntegerField(primary_key=True)
    start = models.DateTimeField()
    goals_home = models.IntegerField()
    goals_away = models.IntegerField()

    home = models.ForeignKey('Team', related_name='games_home')
    away = models.ForeignKey('Team', related_name='games_away')
    referee = models.ForeignKey('Person', related_name='games_as_referee')
    timer = models.ForeignKey('Person', related_name='games_as_timer')
    secretary = models.ForeignKey('Person', related_name='games_as_secretary')
    winner = models.ForeignKey('Team', related_name='games_won')
    union = models.ForeignKey('Union')
    league = models.ForeignKey('League')
    game_type = models.ForeignKey('GameType')
    site = models.ForeignKey('Site')
    players = models.ManyToManyField('Person', through='PlayerGameRelation')

    def __unicode__(self):
        return '{0}/{1}/{2}: {3} {4} vs. {5} {6}'.format(self.start.year, self.start.month, self.start.day, self.home.club.name, self.home.name, self.away.club.name, self.away.name)


class GameType(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


class Site(models.Model):
    name = models.CharField(max_length=50)
    adress = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zip_code = models.IntegerField()
    number = models.IntegerField(primary_key=True)

    def __unicode__(self):
        return self.name


class PlayerGameRelation(models.Model):
    player = models.ForeignKey('Person')
    game = models.ForeignKey('Game')

    team = models.ForeignKey('Team')
    shirt_number = models.IntegerField()
    goals = models.IntegerField()
    warnings = models.IntegerField()
    penalties = models.IntegerField()
    disqualifications = models.IntegerField()
    team_penalties = models.IntegerField()
    penalty_shots_hit = models.IntegerField()
    penalty_shots_miss = models.IntegerField()


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


def create_user_profile(sender, instance, created, **kwargs):
    # Create user profile for user after creation
    if created:
        Person.objects.create(user=instance, first_name=instance.first_name, last_name=instance.last_name)

# post_save.connect(create_user_profile, sender=User)

# Create API key for a new user
post_save.connect(create_api_key, sender=User)
