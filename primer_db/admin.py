# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.

from .models import PrimerDetails, Buffer, Coordinates, PCRProgram, Reference, Scientist, Status

admin.site.register(PrimerDetails)
admin.site.register(Buffer)
admin.site.register(Coordinates)
admin.site.register(PCRProgram)
admin.site.register(Reference)
admin.site.register(Scientist)
admin.site.register(Status)
