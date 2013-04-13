from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'words.views.index', name='index'),
    url(r'^(?P<language>\w{2})/$', 'words.views.home', name='home'),
    url(r'^(?P<language>\w{2})/words/$', 'words.views.words', name='words'),
    url(r'^(?P<language>\w{2})/anki/$', 'words.views.anki', name='anki'),
    url(r'^(?P<language>\w{2})/set-anki/$', 'words.views.set_anki', name='set-anki'),
    url(r'^(?P<language>\w{2})/texts/$', 'words.views.texts', name='texts'),
    url(r'^(?P<language>\w{2})/text_edit/(?P<id>[\d]+)/$', 'words.views.text_edit', name='text_edit'),
    url(r'^(?P<language>\w{2})/text/(?P<id>[\d]+)/$', 'words.views.text', name='text'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^evaluate/$', 'words.views.ajax_evaluate'),
    url(r'^get_translations/$', 'words.views.ajax_get_translations'),
    url(r'^add_reference/$', 'words.views.ajax_add_reference'),
    url(r'^logout/$', 'words.views.logout_view'),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
