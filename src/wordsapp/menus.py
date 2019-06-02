# -*- coding: utf-8 -*-

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from menu import Menu, MenuItem

from wordsapp.models import Language

Menu.add_item('main', MenuItem(_('Home'), reverse('home')))

languages = Language.objects.all()

for language in languages:
    Menu.add_item('main', MenuItem(_(language.name), reverse('language', args=(language.short_name,))))
