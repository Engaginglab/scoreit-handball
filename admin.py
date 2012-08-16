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


class GroupTeamInline(admin.TabularInline):
    model = handball.models.GroupTeamRelation
    extra = 1


class UnionManagerInline(admin.TabularInline):
    model = handball.models.UnionManagerRelation
    extra = 1


class DistrictManagerInline(admin.TabularInline):
    model = handball.models.DistrictManagerRelation
    extra = 1


class GroupManagerInline(admin.TabularInline):
    model = handball.models.GroupManagerRelation
    extra = 1


class ClubManagerInline(admin.TabularInline):
    model = handball.models.ClubManagerRelation
    extra = 1


class TeamManagerInline(admin.TabularInline):
    model = handball.models.TeamManagerRelation
    extra = 1


class PersonAdmin(admin.ModelAdmin):
    inlines = (ClubMemberInline, TeamPlayerInline, TeamCoachInline, GamePlayerInline)


class UnionAdmin(admin.ModelAdmin):
    inlines = (UnionManagerInline,)


class DistrictAdmin(admin.ModelAdmin):
    inlines = (DistrictManagerInline,)


class GroupAdmin(admin.ModelAdmin):
    inlines = (GroupManagerInline,)


class ClubAdmin(admin.ModelAdmin):
    inlines = (ClubMemberInline, ClubManagerInline)


class TeamAdmin(admin.ModelAdmin):
    inlines = (TeamPlayerInline, TeamCoachInline, GroupTeamInline, TeamManagerInline)


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
admin.site.register(handball.models.GamePlayerRelation)
admin.site.register(handball.models.LeagueLevel)
