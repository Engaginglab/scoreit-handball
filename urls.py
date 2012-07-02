from django.conf.urls.defaults import *


urlpatterns = patterns('handball.views',
    (r'^$', 'index'),
    (r'^auth/signup/$', 'sign_up'),
    (r'^auth/activate/([abcdef0123456789]+)$', 'activate'),
    (r'^thanks/$', 'thanks'),
    (r'^auth/validate/$', 'validate_user')
)
