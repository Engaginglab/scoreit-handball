import handball.models
from django.contrib import admin


class ClubMemberInline(admin.TabularInline):
    model = handball.models.ClubMemberRelation
    extra = 1


class TeamPlayerInline(admin.TabularInline):
    model = handball.models.TeamPlayerRelation
    extra = 1


class TeamCoachInline(admin.TabularInline):
    model = handball.models.TeamCoachRelation
    extra = 1


class GamePlayerInline(admin.TabularInline):
    model = handball.models.GamePlayerRelation
    extra = 1


class PersonAdmin(admin.ModelAdmin):
    inlines = (ClubMemberInline, TeamPlayerInline, TeamCoachInline, GamePlayerInline)


class ClubAdmin(admin.ModelAdmin):
    inlines = (ClubMemberInline,)


class TeamAdmin(admin.ModelAdmin):
    inlines = (TeamPlayerInline, TeamCoachInline)


class GameAdmin(admin.ModelAdmin):
    inlines = (GamePlayerInline,)


admin.site.register(handball.models.Person, PersonAdmin)
admin.site.register(handball.models.Club, ClubAdmin)
admin.site.register(handball.models.Group)
admin.site.register(handball.models.District)
admin.site.register(handball.models.Union)
admin.site.register(handball.models.Game, GameAdmin)
admin.site.register(handball.models.Team, TeamAdmin)
admin.site.register(handball.models.Site)
admin.site.register(handball.models.Event)
admin.site.register(handball.models.EventType)
admin.site.register(handball.models.GamePlayerRelation)
admin.site.register(handball.models.LeagueLevel)
admin.site.register(handball.models.AgeGroup)
