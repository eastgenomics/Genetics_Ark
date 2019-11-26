# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import datetime
from django.core.exceptions import ValidationError


# Create your models here.

# set all to null=True for testing forms

class PrimerDetails(models.Model):
    primer_name = models.CharField(unique=True, max_length=50)
    gene = models.CharField(max_length=15)
    sequence = models.CharField(max_length=100)
    gc_percent = models.FloatField(verbose_name='GC %')
    tm = models.FloatField()
    comments = models.TextField(max_length=500, null=True)
    arrival_date = models.DateField(null=True)
    location = models.CharField(max_length=20, verbose_name='Storage location', null=True)
    snp_status = models.CharField(default=0, max_length=1, null=True, blank=False, verbose_name='SNP')
    snp_info = models.TextField(max_length=500, null=True, blank = False)
    snp_date = models.DateField(null = True, blank = True)
    status = models.ForeignKey("Status")
    scientist = models.ForeignKey("Scientist" )
    pcr_program = models.ForeignKey("PCRProgram", verbose_name='PCR Program', )
    buffer = models.ForeignKey("Buffer" )
    coordinates = models.ForeignKey("Coordinates", on_delete=models.CASCADE)
    pairs = models.ForeignKey("Pairs", blank=True, null=True)

    def __str__(self):
        """String for representing the Model object."""
        return ('{} {} {} {} {} {} {} {} {} {} {} {}'.format(
        self.primer_name, self.sequence, self.gc_percent, self.tm,
        self.comments, self.arrival_date, self.location, self.status, 
        self.scientist, self.pcr_program, self.buffer, self.coordinates)

                )


class Coordinates(models.Model):
    reference = models.CharField(max_length=6)
    chrom_no = models.CharField(max_length=2)
    start_coordinate_37 = models.IntegerField(verbose_name = 'GRCh37 Start', null=True)
    end_coordinate_37 = models.IntegerField(verbose_name = 'GRCh37 End', null=True)
    start_coordinate_38 = models.IntegerField(verbose_name = 'GRCh38 Start', null=True)
    end_coordinate_38 = models.IntegerField(verbose_name = 'GRCh38 End',  null=True)
    

    def __str__(self):
        """String for representing the Model object."""
        return '{} {} {} {} {}'.format(self.chrom_no, self.start_coordinate_37, 
            self.end_coordinate_37, self.start_coordinate_38, self.end_coordinate_38)


class Pairs(models.Model):
    coverage_37 = models.CharField(max_length = 50, verbose_name = 'GRCh37 Coverage', null = True)
    coverage_38 = models.CharField(max_length = 50, verbose_name = 'GRCh38 Coverage', null = True)
    #length = models.IntegerField()

        


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


