from django.conf.urls.defaults import *
from tastypie.api import Api
from handball.api import *


v1_api = Api(api_name='v1')
v1_api.register(UnionResource())
v1_api.register(ClubResource())
v1_api.register(TeamResource())
v1_api.register(UserResource())
v1_api.register(PersonResource())
v1_api.register(GameResource())
v1_api.register(LeagueResource())
v1_api.register(DistrictResource())

urlpatterns = patterns('handball.views',
    (r'^$', 'index'),
    (r'^auth/signup/$', 'sign_up'),
    (r'^auth/activate/([abcdef0123456789]+)$', 'activate'),
    (r'^thanks/$', 'thanks')
)

urlpatterns += patterns('', (r'^api/', include(v1_api.urls)))

# Non-resource api endpoints
urlpatterns += patterns('handball.api',
    (r'^api/v1/auth/validate/$', 'validate_user'),
    (r'^api/v1/auth/unique/$', 'is_unique'),
    (r'^api/v1/auth/signup/$', 'sign_up')
)
