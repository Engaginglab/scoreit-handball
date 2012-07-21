import handball.models
from django.contrib import admin

admin.site.register(handball.models.Person)
admin.site.register(handball.models.Club)
admin.site.register(handball.models.Group)
admin.site.register(handball.models.League)
admin.site.register(handball.models.LeagueTemplate)
admin.site.register(handball.models.District)
admin.site.register(handball.models.Union)
admin.site.register(handball.models.Game)
admin.site.register(handball.models.GameType)
admin.site.register(handball.models.Team)
admin.site.register(handball.models.Site)
admin.site.register(handball.models.Event)
admin.site.register(handball.models.EventType)
admin.site.register(handball.models.PlayerGameRelation)
