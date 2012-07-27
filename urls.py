from django.conf.urls.defaults import *
from tastypie.api import Api
from handball.api import *


v1_api = Api(api_name='v1')
v1_api.register(UnionResource())
v1_api.register(ClubResource())
v1_api.register(TeamResource())
v1_api.register(PersonResource())
v1_api.register(GameResource())
v1_api.register(LeagueResource())
v1_api.register(DistrictResource())
v1_api.register(ClubMemberRelationResource())

urlpatterns = patterns('handball.views',
    (r'^$', 'index')
)

urlpatterns += patterns('', (r'^api/', include(v1_api.urls)))

# Non-resource api endpoints
urlpatterns += patterns('handball.api',
    (r'^api/v1/unique/$', 'is_unique'),
)
