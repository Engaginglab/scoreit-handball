import handball.models
from django.contrib import admin


class MemberClubInline(admin.TabularInline):
    model = handball.models.MemberClubRelation
    extra = 1


class TeamPlayerInline(admin.TabularInline):
    model = handball.models.TeamPlayerRelation
    extra = 1


class TeamCoachInline(admin.TabularInline):
    model = handball.models.TeamCoachRelation
    extra = 1


class PersonAdmin(admin.ModelAdmin):
    inlines = (MemberClubInline, TeamPlayerInline, TeamCoachInline)


class ClubAdmin(admin.ModelAdmin):
    inlines = (MemberClubInline,)


class TeamAdmin(admin.ModelAdmin):
    inlines = (TeamPlayerInline, TeamCoachInline)


admin.site.register(handball.models.Person, PersonAdmin)
admin.site.register(handball.models.Club, ClubAdmin)
admin.site.register(handball.models.Group)
admin.site.register(handball.models.League)
admin.site.register(handball.models.LeagueTemplate)
admin.site.register(handball.models.District)
admin.site.register(handball.models.Union)
admin.site.register(handball.models.Game)
admin.site.register(handball.models.GameType)
admin.site.register(handball.models.Team, TeamAdmin)
admin.site.register(handball.models.Site)
admin.site.register(handball.models.Event)
admin.site.register(handball.models.EventType)
