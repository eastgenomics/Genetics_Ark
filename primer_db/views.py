# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.template import loader

def index(request):
    template = loader.get_template('primer_db/index.html')
    return render(request, 'primer_db/index.html')
