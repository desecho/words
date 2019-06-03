from django.urls import path, re_path
from django.contrib.auth.views import LoginView
from django.views.i18n import JavaScriptCatalog
from django.conf.urls import include
from django.views.defaults import page_not_found
from django.contrib import admin
from wordsapp.views import LanguageView, HomeView, WordsView, MarkWordsAsExportedToAnkiView, AnkiExportView, ExportToAnkiView, MarkAsKnownView
from wordsapp.views.user import logout_view

admin.autodiscover()

urlpatterns = [
    re_path(r'^$', HomeView.as_view(), name='home'),
    re_path(r'^(?P<language>\w{2})/$', LanguageView.as_view(), name='language'),
    re_path(r'^(?P<language>\w{2})/words/$', WordsView.as_view(), name='words'),
    re_path(r'^(?P<language>\w{2})/anki-export/export.txt$', AnkiExportView.as_view(), name='anki_export'),
    re_path(r'^(?P<language>\w{2})/mark-as-exported-to-anki/$', MarkWordsAsExportedToAnkiView.as_view(), name='mark_as_exported_to_anki'),
    # re_path(r'^(?P<language>\w{2})/texts/$', texts, name='texts'),
    # re_path(r'^(?P<language>\w{2})/text_edit/(?P<id>[\d]+)/$', text_edit, name='text_edit'),
    # re_path(r'^(?P<language>\w{2})/text/(?P<id>[\d]+)/$', text, name='text'),
    path('login/', LoginView.as_view(template_name='user/login.html'), name='login'),
    re_path(r'words/(?P<id>\d+)/export-to-anki/', ExportToAnkiView.as_view()),
    re_path(r'words/(?P<id>\d+)/mark-as-known/', MarkAsKnownView.as_view()),
    re_path(r'words/', page_not_found, name='words'),

    # path('get_translations/', ajax_get_translations),
    # path('add_reference/', ajax_add_reference),
    path('logout/', logout_view, name='logout'),
    path('admin/', admin.site.urls),
    path('jsi18n/', JavaScriptCatalog.as_view(packages=('wordsapp', ), domain='djangojs'), name='javascript-catalog'),
    path('i18n/', include('django.conf.urls.i18n')),
]
