from django.conf.urls.defaults import *


urlpatterns = patterns('handball.views',
    (r'^$', 'index'),
    (r'^signup/$', 'sign_up'),
    (r'^activate/([abcdef0123456789]+)$', 'activate'),
    (r'^thanks/$', 'thanks')
)
