# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class PrimerDetails(models.Model):
	primer_ID = models.AutoField(primary_key=True)
	primer_name = models.CharField(unique=True, max_length=50)
	sequence = models.CharField(max_length=100)
	gc_percent = models.FloatField()
	tm = models.FloatField()
	length = models.IntegerField()
	comments = models.CharField(max_length=200, blank=True)
	arrival_date = models.DateField(auto_now_add=True)
	status_ID = models.ForeignKey("Status")
	scientist_ID = models.ForeignKey("Scientist")
	pcr_ID = models.ForeignKey("PCRProgram")
	buffer_ID = models.ForeignKey("Buffer")

        def __str__(self):
                """String for representing the Model object."""
                return str(self.primer_ID)



class Coordinates(models.Model):
	coordinate_ID = models.AutoField(primary_key=True)
	primer_ID = models.ForeignKey(PrimerDetails)
	ref_ID = models.ForeignKey("Reference")
	coordiantes = models.CharField(max_length=200)
	chrom_no = models.CharField(max_length=2)

        def __str__(self):
                """String for representing the Model object."""
                return self.coordinate_ID



class Reference(models.Model):
	ref_ID = models.CharField(primary_key=True, max_length=200)
	grch37 = models.CharField(max_length=10)
	grch38 = models.CharField(max_length=10)

        def __str__(self):
                """String for representing the Model object."""
                return str(self.ref_ID)


class Status(models.Model):
	STATUS_OPTIONS = (
		('o', 'On order'),
		('i', 'In bank'),
		('a', 'Archived'),
	)		

	status_ID = models.CharField(
		primary_key=True, 
		max_length=200, 
		choices=STATUS_OPTIONS
	)


        def __str__(self):
                """String for representing the Model object."""
                return str(self.status_ID)

	

class Scientist(models.Model):
        scientist_ID = models.CharField(primary_key=True, max_length=200)

        def __str__(self):
                """String for representing the Model object."""
                return str(self.scientist_ID)



class PCRProgram(models.Model):
        pcr_ID = models.CharField(primary_key=True, max_length=200)

        def __str__(self):
                """String for representing the Model object."""
                return str(self.pcr_ID)



class Buffer(models.Model):
        buffer_ID = models.CharField(
		primary_key=True, 
		max_length=200,
		default='Buffer D',
	)


        def __str__(self):
                """String for representing the Model object."""
                return str(self.buffer_ID)


