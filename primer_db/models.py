# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import datetime

# Create your models here.

# set all to null=True for testing forms

class PrimerDetails(models.Model):
	primer_name = models.CharField(unique=True, max_length=50)
	sequence = models.CharField(max_length=100)
	gc_percent = models.FloatField(verbose_name='GC %')
	tm = models.FloatField()
	length = models.IntegerField()
	comments = models.CharField(max_length=200)
	arrival_date = models.DateField()
	status = models.ForeignKey("Status")
	scientist = models.ForeignKey("Scientist")
	pcr_program = models.ForeignKey("PCRProgram", verbose_name='PCR Program')
	buffer = models.ForeignKey("Buffer")
	coordinates = models.ForeignKey("Coordinates")

        def __str__(self):
                """String for representing the Model object."""
                return ('{} {} {} {} {} {} {} {} {} {} {} {}'.format(
                self.primer_name, self.sequence, self.gc_percent, self.tm,
                self.length, self.comments, self.arrival_date, self.status, 
                self.scientist, self.pcr_program, self.buffer, self.coordinates)

                )

class Coordinates(models.Model):
	reference = models.CharField(max_length=6)
	chrom_no = models.CharField(max_length=2)
	start_coordinate_37 = models.IntegerField(verbose_name = 'GRCh37 Start')
	end_coordinate_37 = models.IntegerField(verbose_name = 'GRCh37 End')
	

        def __str__(self):
                """String for representing the Model object."""
                return '{} {} {} {}'.format(self.reference, self.chrom_no, 
                	self.start_coordinate_37, self.end_coordinate_37)



class Status(models.Model):
	status = models.CharField(max_length=200)	

        def __str__(self):
                """String for representing the Model object."""
                return str(self.status)

	

class Scientist(models.Model):
        forename = models.CharField(max_length=200)
        surname = models.CharField(max_length=200)


        def __str__(self):
                """String for representing the Model object."""
                return '{} {}'.format(self.forename, self.surname)



class PCRProgram(models.Model):
        pcr_program = models.CharField(max_length=200)

        def __str__(self):
                """String for representing the Model object."""
                return str(self.pcr_program)



class Buffer(models.Model):
        buffer = models.CharField(max_length=200)


        def __str__(self):
                """String for representing the Model object."""
                return str(self.buffer)


