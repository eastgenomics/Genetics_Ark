from django.shortcuts import render
from django import forms

import os
import re
import json
import operator
import subprocess
import shlex
import shutil
import string 
import random
import datetime
import pytz


import pprint as pp

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django_tables2   import RequestConfig

import django.utils.safestring
import django.middleware.csrf

from django.forms.models import model_to_dict

import genetics_ark.models as Models
import genetics_ark.forms  as Forms
import genetics_ark.tables as Tables

import genetics_ark.ccbg_misc as ccbg_misc


#@login_required(login_url='/login/')
def index(request):
    return render( request, "base.html")


def projects_list( request ):
    """ displays the project list

    Models:
    - Project
    - Sample

    Template:
    - projects_list.html
    """

    context_dict = {}

    projects = Models.Project.objects.all()
    
    for project in projects:
        project.samples = Models.Sample.objects.filter( project_id__exact = project.id).count()
        print("samples in project {}: {}".format(project.name,project.samples))

    projects_table = Tables.ProjectTable( projects )
    projects_table.order_by = "Name"
    context_dict[ 'project_table' ] =  projects_table 
    RequestConfig(request).configure( projects_table )

    return render( request, "genetics_ark/projects_list.html", context_dict )


def igv( request, analysis_id=None, sample_name=None, runfolder_name=None, chrom=None, pos=None):
    """ create a page with the js IGV viewer for the sample

    Models:
    - Analysis

    Template:
    - igv.html

    """

    if analysis_id is not None:
        analysis = Models.Analysis.objects.get( pk = analysis_id )

        sample_name = analysis.sample.name
        runfolder_name = analysis.runfolder.name

    context_dict = { 'sample_name': sample_name, 
                     'runfolder_name': runfolder_name,
                     }

    if chrom is not None:
        context_dict['chrom'] = chrom

    if pos is not None:
        context_dict['pos'] = pos

    return render( request, "genetics_ark/igv.html", context_dict )


def sample_view( request, sample_id = None, sample_name = None):
    """ displays the sample view

    Models:
    - Sample
    - SamplePanel
    - Panel
    - Analysis
    - Decon

    Template:
    - sample_view.html

    """

    context_dict = {}

    sample = None
    
    if sample_id is not None:
        sample = Models.Sample.objects.get( pk = sample_id )    

    elif sample_name is not None:
        samples = Models.Sample.objects.filter( name__exact = sample_name )
        sample = samples[0]

    context_dict = { 'sample': sample }
    context_dict[ 'panels' ] = []
    sample_panels_names = Models.SamplePanel.objects.filter(sample_id__exact = sample.id).values_list("panel_name")
    panels = Models.Panel.objects.filter(name__in = sample_panels_names, active = "Y").distinct()
    context_dict["panels"] = panels

#    sample_panels = ", ".join([sample_panel.panel_name for sample_panel in sample_panels])
#    sample.panels = sample_panels

    context_dict[ 'sample_name' ] = sample.name
    context_dict[ 'project_name' ] = sample.project.name

    analyses = Models.Analysis.objects.filter( sample_id = sample.id )

    for analysis in analyses:
        if ( analysis.versions is None):
            continue

        versions = analysis.versions.split(";")
        analysis.versions = []

        for version in versions:
            analysis.versions.append(version.split(":"))

        analysis.versions = sorted( analysis.versions )

    context_dict[ 'analyses' ] = analyses

    # get the decon runs associated with the sample
    decons = Models.Decon.objects.filter(deconanalysis__sample_id__exact = sample.id).distinct()
    context_dict["decon_runs"] = decons
#    pp.pprint( context_dict )

    return render( request, "genetics_ark/sample_view.html", context_dict )


def random_string(length=10):
    """ Creates a random string 

    Args:
      length (int): length of string to generate, default 10

    returns:
      string

    raises:
      None
    """

    random_string = ""
    # Choose from lowercase, uppercase,  and digits
    alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits
    for n in range(0, length):
        random_string += random.choice( alphabet )

    return random_string


def report_create( request, analysis_id, tmp_key=None ):
    """ 

    Models:
    - Analysis
    - Panel
    - Transcript

    Template:
    - report_create.html
    """
    
    analysis = Models.Analysis.objects.get( pk = analysis_id)
    context_dict = {'analysis': analysis }

    panel_list = []

    if 'selected_panels' in request.POST and request.POST['selected_panels'] != '':
        for selected_panel in request.POST['selected_panels'].split(","):
            panel = Models.Panel.objects.get( pk = selected_panel )

            panel_list.append( panel.name )

    if 'selected_transcripts' in request.POST and request.POST['selected_transcripts'] != '':
        for selected_transcript in request.POST['selected_transcripts'].split(","):
            transcript = Models.Transcript.objects.get( pk = selected_transcript )

            panel_list.append( "_{}".format(transcript.gene.name ))

    panels = ", ".join( panel_list )

    cmd = "/mnt/storage/apps/software/ccbg_toolbox/1.2.1/bin/vcf2xls_nirvana.pl -p \"{panels}\" -v /mnt/storage/data/NGS/{runfolder}/vcfs/{sample}.refseq_nirvana_203.annotated.vcf -R /mnt/storage/data/NGS/{runfolder}/stats/{runfolder}.refseq_nirvana_5bp.gz".format(runfolder=analysis.runfolder.name, sample=analysis.sample.name, panels=panels)
    print(cmd)

    context_dict['cmd'] = cmd 

    path = "static/tmp/"
    random_tmp = random_string()

    stderr_file_name = "{}{}.stderr".format(path, random_tmp)
    stdout_file_name = "{}{}.stdout".format(path, random_tmp)

    stderr_file = open( stderr_file_name, "w+" )
    stdout_file = open( stdout_file_name, "w+" )

    context_dict['tmp_key'] = random_tmp

    cmd = shlex.split( cmd )
    p = subprocess.Popen( cmd , shell=False, stderr = stderr_file , stdout = stdout_file)

    return render( request, "genetics_ark/report_create.html", context_dict )


def report_done_ajax( request, tmp_key ):
    
    path = 'static/tmp/'

    stdout_name = "{}{}.stdout".format( path, tmp_key)
    stderr_name = "{}{}.stderr".format(path, tmp_key)

    print(stdout_name)

    result_dict = {'status': 'running' }

    if ( os.path.isfile( stdout_name )):
        fh = open( stdout_name, 'rU')
        lines = "<b>PROGRESS</b><br>"

        for line in fh.readlines():
            line = line.rstrip( "\n" )
            lines += line +"<br>"

            if line == 'SUCCESS':
                result_dict['status'] = 'done'

            elif re.match('Output excel file', line):
                result_dict['file'] = re.sub(r'.* == ', '', line)
                shutil.copy2(result_dict['file'], 'static/tmp/')
                result_dict['file'] = re.sub(r'.*/', '', line)

            elif re.match('Died at', line):
                result_dict['status'] = 'failed'
                
    result_dict['progress'] = lines

    if ( os.path.isfile( stderr_name )):
        fh = open( stderr_name, 'rU')
        lines = "<BR> <b>ERRORS: </b><br>"

        for line in fh.readlines():
            line = line.rstrip( "\n" )
            print(line)
            lines += line +"<br>"

    result_dict['progress'] += lines

    response_text = json.dumps(result_dict, separators=(',',':'))
#    pp.pprint( response_text )
    return HttpResponse(response_text, content_type="application/json")
    
    
def analysis_report( request, analysis_id):
    """

    Models:
    - Analysis
    - Panel
    - Transcript
    
    Forms:
    - PanelForm

    Template:
    - analysis_report.html

    """
    
    context = {}
    analysis = Models.Analysis.objects.get( pk = analysis_id)
    context[ 'analysis' ] = analysis
    context['selected_panels'] = []
    context['selected_transcripts'] = []
    
    if request.method == 'POST':

        form = Forms.PanelForm( request.POST )
#        pp.pprint(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():

            if 'create_report' in request.POST:
                return (report_create( request, analysis_id ))

            context[ 'panel_form'] = form

            selected_panels = []
            if 'selected_panels' in form.data and form.data['selected_panels'] != '':
                selected_panels = form.data['selected_panels'].split(",")

            selected_transcripts = []
            if 'selected_transcripts' in form.data and form.data['selected_transcripts'] != '':
                selected_transcripts = form.data['selected_transcripts'].split(",")

            if 'add_panel' in request.POST:
#                pp.pprint(request.POST)
                selected_panels += [request.POST['panel']]
                selected_panels = list( set( selected_panels ))

            if 'rm_panel' in request.POST:
                selected_panels.remove( request.POST['rm_panel'] )

            selected_panels = list( set( selected_panels ))
            context['selected_panels_text'] = ",".join( selected_panels )

            for panel_id in selected_panels:
                if panel_id is None or panel_id == '':
                        continue

                panel = Models.Panel.objects.get( pk = panel_id )
                context['selected_panels'].append( panel )
                    
            context['selected_panels'] = sorted( context['selected_panels'], key=operator.attrgetter('name'))

            if 'add_gene' in request.POST:
#                pp.pprint(request.POST)
                selected_transcripts += [request.POST['gene']]
                selected_transcripts = list( set( selected_transcripts ))

            if 'rm_transcript' in request.POST:
                selected_transcripts.remove( request.POST['rm_transcript'] )

            selected_transcripts = list( set( selected_transcripts ))
            context['selected_transcripts_text'] = ",".join( selected_transcripts )

            for transcript_id in selected_transcripts:
                if transcript_id is None or transcript_id == '':
                        continue

                transcript = Models.Transcript.objects.get( pk = transcript_id )
                context['selected_transcripts'].append( transcript )

            context['selected_transcripts'] = sorted( context['selected_transcripts'], key=operator.attrgetter('gene.name'))
                    
        else:
            pp.pprint( form.errors)
            context[ 'panel_form'] = form

    else:
        context[ 'panel_form'] = Forms.PanelForm(  )

    return render(request, "genetics_ark/analysis_report.html", context)


def genes_in_panel( panel_id ):
    """ Get genes, and their clincial transcripts for genes in a panel 

    Models:
    - Gene
    - Transcript

    Args: panel_id

    Returns: dict{gene_queryset: transcripts_queryset}

    """

    genes = Models.Gene.objects.filter(genepanel__panel_id__exact = panel_id).distinct()
    genes_dict = {}

    for gene in genes:
        transcripts = Models.Transcript.objects.filter(gene_id__exact = gene.id, clinical_transcript__exact = "Y").values_list("refseq", flat = True).distinct()
        genes_dict[gene] = transcripts

    return genes_dict


def panel_view( request, panel_id):
    """ displays the panel view

    Models:
    - Panel
    - Sample

    Template:
    - panel_view.html
    """

    context_dict = {}
    
    panel = Models.Panel.objects.get( pk = panel_id )
    context_dict[ 'panel' ] = panel

    genes = tuple(genes_in_panel( panel_id).items())
    paginator = Paginator(genes, 25)
    page = request.GET.get("page1")

    try:
        context_dict["genes"] = paginator.page(page)

    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        context_dict["genes"] = paginator.page(1)

    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        context_dict["genes"] = paginator.page(paginator.num_pages)

    samples = Models.Sample.objects.filter(samplepanel__panel_name__exact = panel.name)
    paginator = Paginator(samples, 25)
    page = request.GET.get("page2")

    try:
        context_dict["samples"] = paginator.page(page)

    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        context_dict["samples"] = paginator.page(1)

    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        context_dict["samples"] = paginator.page(paginator.num_pages)

#    pp.pprint( context_dict )

    return render( request, "genetics_ark/panel_view.html", context_dict )


def gene_view( request, gene_name):
    """ displays the gene view

    Models:
    - Gene
    - Transcript
    - Panel

    Template:
    - gene_view.html
    """

    context_dict = {}
    context_dict[ 'gene_name' ] = gene_name
    
    gene = Models.Gene.objects.filter( name__exact = gene_name )

#    pp.pprint( gene )

    if ( len(gene) == 0 ):
        return render( request, "genetics_ark/gene_not_found.html", context_dict )
        
    gene = gene[0]

    context_dict[ 'gene_id' ] = gene.id
    
    transcripts = Models.Transcript.objects.filter( gene_id__exact = gene.id ).values("refseq", "clinical_transcript").distinct()

    context_dict[ 'transcripts' ] = transcripts

    panels = Models.Panel.objects.filter(genepanel__gene_id__exact = gene.id)
    context_dict["panels"] = panels

    return render( request, "genetics_ark/gene_view.html", context_dict )


def qc_project( request, project_id ):
    
    project = Models.Project.objects.get( pk = project_id )

    if ( project is None):
        # render a page telling the user that the project does not exsist
        pass
    
    runfolders = list( Models.Runfolder.objects.filter( analysis__sample__project_id = project_id  ).distinct())
    total_reads     = []
    perc_mapped     = []
    perc_dups       = []
    bases_on_target = []
    bases_100x      = []
    mean_isize      = []

    for runfolder in runfolders:

        # Dont have summed stats for the runfolder calculate them
        if ( not ccbg_misc.is_a_number( runfolder.total_reads )):
            runfolder = Models.Runfolder.calc_stats( runfolder )

        runfolder = model_to_dict( runfolder )

        if ( runfolder['total_reads'] is not None ):
            total_reads.append( runfolder['total_reads'] )

        if ( ccbg_misc.is_a_number( runfolder[ 'mapped_reads' ] ) and 
             ccbg_misc.is_a_number(runfolder[ 'total_reads' ])):
            perc_mapped.append( runfolder[ 'mapped_reads' ]*100.0/runfolder['total_reads'] )

        if ( ccbg_misc.is_a_number( runfolder[ 'duplicate_reads' ] ) and 
             ccbg_misc.is_a_number(runfolder[ 'mapped_reads' ])):
#            print "{}/{}"
            perc_dups.append( runfolder[ 'duplicate_reads' ]*100.0/runfolder['mapped_reads'] )

        if ( runfolder['bases_on_target'] is not None ):
            bases_on_target.append( runfolder['bases_on_target'] )

        if ( runfolder['mean_isize'] is not None ):
            mean_isize.append(runfolder['mean_isize'] )

        if ( runfolder['bases_100x_coverage'] is not None ):
            bases_100x.append( runfolder['bases_100x_coverage'] )

    runfolder_avgs = []
    
    for runfolder in runfolders:
 
        if ( not ccbg_misc.is_a_number(runfolder.total_reads )):
            runfolder = Models.Runfolder.calc_stats( runfolder )
#            pp.pprint( runfolder )

        runfolder = model_to_dict( runfolder )

        if ( ccbg_misc.is_a_number( runfolder[ 'duplicate_reads' ] ) and ccbg_misc.is_a_number(runfolder[ 'mapped_reads' ])):
            runfolder[ 'perc_dups' ] = runfolder[ 'duplicate_reads' ]*100.0/runfolder['mapped_reads']
            perc_dups_boxplot = ccbg_misc.svg_boxplot( perc_dups, runfolder['perc_dups'])
            print("perc dups: {}".format( runfolder['perc_dups']))
            runfolder['perc_dups'] = django.utils.safestring.mark_safe( "%.2f%% %s " % (runfolder['perc_dups'],  perc_dups_boxplot ))

        if ( ccbg_misc.is_a_number( runfolder[ 'mapped_reads' ] ) and ccbg_misc.is_a_number(runfolder[ 'total_reads' ])):
            runfolder[ 'perc_mapped' ] = runfolder[ 'mapped_reads' ]*100.0/runfolder['total_reads']

            perc_mapped_boxplot = ccbg_misc.svg_boxplot( perc_mapped, runfolder['perc_mapped'])
            runfolder['perc_mapped'] = django.utils.safestring.mark_safe( "%.2f%% %s " % (runfolder['perc_mapped'],  perc_mapped_boxplot ))

        if (runfolder['total_reads'] is not None ):
            total_reads_boxplot = ccbg_misc.svg_boxplot( total_reads, runfolder['total_reads'])
            runfolder['total_reads'] = django.utils.safestring.mark_safe( "%s %s" %(ccbg_misc.readable_number(runfolder['total_reads']), total_reads_boxplot ))


        if ( runfolder['mean_isize'] is not None ):
            mean_isize_boxplot = ccbg_misc.svg_boxplot( mean_isize, runfolder['mean_isize'])
            runfolder['mean_isize'] = django.utils.safestring.mark_safe( "%.2f %s" % ( runfolder['mean_isize'], mean_isize_boxplot ))


        if ( 'bases_on_target' in runfolder and  runfolder['bases_on_target'] is not None and runfolder['bases_on_target'] ):
            bases_on_target_boxplot = ccbg_misc.svg_boxplot( bases_on_target, runfolder['bases_on_target'])
            runfolder['bases_on_target'] = django.utils.safestring.mark_safe( "%.2f%% %s" % ( 100*runfolder['bases_on_target'], bases_on_target_boxplot ))

        if ( runfolder['bases_100x_coverage'] is not None ):
            bases_100x_boxplot = ccbg_misc.svg_boxplot( bases_100x, runfolder['bases_100x_coverage'])
            runfolder['coverage_100x'] = django.utils.safestring.mark_safe( "%.2f%% %s " % (runfolder['bases_100x_coverage']*100,  bases_100x_boxplot ))
             
        runfolder_avgs.append( runfolder )

    stats_table = Tables.StatsTable( runfolder_avgs )
    # sort the table by decreasing name
    stats_table.order_by = "-name"

    context = { 'stats_table': stats_table }
    context[ 'project_name' ] = project.name
    RequestConfig(request).configure( stats_table )

    return render( request, "genetics_ark/qc_project.html", context)


def qc_runfolder( request, runfolder_id):

#    runfolder_stats = Stats.objects.filter( sample__runfolder = runfolder_name)

    runfolder_stats = Models.Analysis.objects.filter( runfolder = runfolder_id )

    stats = []
    average = {}
    samples = 0

    for runfolder_stat in runfolder_stats:
        if ( ccbg_misc.is_a_number( runfolder_stat.total_reads ) and  ccbg_misc.is_a_number( runfolder_stat.mapped_reads )):
            runfolder_stat.perc_mapped = runfolder_stat.mapped_reads*100.0/runfolder_stat.total_reads

        if ( ccbg_misc.is_a_number( runfolder_stat.duplicate_reads ) and  ccbg_misc.is_a_number( runfolder_stat.mapped_reads )):
            runfolder_stat.perc_dups = runfolder_stat.duplicate_reads*100.0/runfolder_stat.total_reads

        samples += 1

        sample = runfolder_stat.sample.name

        runfolder_stat = model_to_dict( runfolder_stat )

        runfolder_stat ['name'] = sample

        if ( runfolder_stat['bases_on_target'] is None):
            runfolder_stat ['bases_on_target'] = -1

        if ( runfolder_stat['mapped_reads'] is None):
            runfolder_stat ['mapped_reads'] = -1

        if ( runfolder_stat['total_reads'] is None):
            runfolder_stat ['total_reads'] = -1

        if ( runfolder_stat['duplicate_reads'] is None):
            runfolder_stat ['duplicate_reads'] = -1

        runfolder_stat ['perc_mapped'] = runfolder_stat[ 'mapped_reads' ]*100.0/runfolder_stat[ 'total_reads' ]
        runfolder_stat ['perc_dups']   = runfolder_stat[ 'duplicate_reads' ]*100/runfolder_stat[ 'mapped_reads' ]

        runfolder_stat ['bases_on_target'] = runfolder_stat ['bases_on_target']*100

        for item in runfolder_stat:
            if ( type(runfolder_stat[ item ]) is not float and type(runfolder_stat[ item ]) is not int ):
                continue

            if item not in average:
                average[ item ] = 0
                
            average[ item ] += runfolder_stat[ item ]

        stats.append( runfolder_stat )

    for item in average:
        if ( type(runfolder_stat[ item ]) is float):
            average[ item ] = average[ item ]*1.0/samples

        average[ item ] = ccbg_misc.readable_number( average[ item ])

    rf_table = Tables.SampleTable( stats )

    context = { 'rf_table': rf_table }
    context[ 'runfolder_stats' ] = stats 
    runfolder = Models.Runfolder.objects.get( pk = runfolder_id )
    context[ 'runfolder_name' ] = runfolder.name
    context[ 'average'        ] = average

    RequestConfig(request).configure( rf_table )

    return render(request, "genetics_ark/qc_runfolder.html", context)


def variant_view( request, chrom=None, pos=None, ref=None, alt=None):
    """ displays variant view

    Models:
    - Variant
    - Comment
    - Project
    - Sample
    - AnalysisVariant
    - SamplePanel
    - Panel

    Forms:
    - UserForm
    - CommentForm

    Template:
    - variant_view.html
    """

    context_dict = {}
    context_dict['chrom'] = chrom
    context_dict['pos']   = pos

    variants = Models.Variant.objects.filter( chrom__exact = chrom ).filter( pos__exact = pos )

    if len(variants) > 1:
        context_dict['multi_allelic'] = variants

    if ref is not None and alt is not None:
        variants = variants.filter( ref__exact = ref ).filter( alt__exact = alt )

    if ( not variants ):
        context_dict['nothing_found'] = 1
        return  render(request,'genetics_ark/variant_view.html', context_dict)
        
    if ( len( variants ) > 1 ):
        return  render(request,'genetics_ark/variant_multi_alleles.html', {})

    variants_stats = []

    variant = variants[ 0 ]

    context_dict['ref'] = variant.ref
    context_dict['alt'] = variant.alt
    context_dict['id']  = variant.id

    context_dict[ 'projects' ] = []

    for project in Models.Project.objects.all().order_by('name'):
        total = len( Models.Sample.objects.filter( project__exact = project.id) )

        if total == 0:
            continue
        
        homs = 0
        hets = 0

        samples = []
        AnalysisVariants = Models.AnalysisVariant.objects.filter( variant__exact = variant.id ).filter( analysis__sample__project__exact = project.id)

        for analysis_variant in AnalysisVariants:
            analysis_variant.name = analysis_variant.analysis.sample.name

            if analysis_variant.allele_count == 2:
                homs += 1
                analysis_variant.zygosity = "HOM"

            else:
                hets += 1
                analysis_variant.zygosity = "HET"

#            print "analysis id {}".format( analysis_variant.analysis_id )
#            sample_panels = ", ".join([sample_panel.panel_name for sample_panel in sample_panels])
#            analysis_variant.panels = sample_panels

            sample_panels = Models.SamplePanel.objects.filter( sample_id__exact = analysis_variant.analysis.sample.id )
            analysis_variant.panels = []

            for sample_panel in sample_panels:
                panels = Models.Panel.objects.filter( name = sample_panel.panel_name ).filter( active ='Y')

                if ( panels.len() > 0):
                    analysis_variant.panels.append( panels[0] )
            
            samples.append( analysis_variant)
 
        project_dict = {}
        project_dict[ 'name' ] = project.name
        project_dict[ 'total'] = total
        project_dict[ 'homs' ] = homs
        project_dict[ 'hets' ] = hets
        project_dict[ 'freq' ] = 0

        if (total > 0 and (hets+homs) >= 1 ):
            freq = (hets + homs*2.0)/(total*2.0)

            if freq < 0.0001:
                project_dict[ 'freq' ] = "{0:.4E}".format( freq )

            else:
                project_dict[ 'freq' ] = "{0:.4f}".format( freq )

            if ( freq < 0.10 ):
#                project_dict[ 'samples' ] = Tables.SampleAAFTable( samples )
#                RequestConfig(request, paginate={'per_page': 36}).configure( project_dict[ 'samples' ] )
                project_dict[ 'samples' ] =  samples 

        context_dict[ 'projects' ].append( project_dict )

    comments = Models.Comment.objects.filter(variant_id__exact = variant.id)

    context_dict["comments"] = comments

    utc    = pytz.utc
    london = pytz.timezone('Europe/London')
    utc_dt = datetime.datetime.now(tz=utc)
    loc_dt = utc_dt.astimezone(london)
    time   = loc_dt.strftime("%Y-%m-%d %H:%M:%S")

    # handle the comments in the variant page
    if request.method == "POST":
        # data is sent
        user_form = Forms.UserForm(request.POST)
        comment_form = Forms.CommentForm(request.POST)

        if user_form.is_valid() and comment_form.is_valid():
            # the form is valid
            user = user_form.cleaned_data["user"]
            comment = comment_form.cleaned_data["comment"]
                
            # save the comment in the database
            new_comment = Models.Comment.objects.create(user = user, date = time, comment = comment, variant = variant)

            comments = Models.Comment.objects.filter(variant_id__exact = variant.id)

            context_dict["comments"] = comments

            # recreate the form
            user_form = Forms.UserForm()
            comment_form = Forms.CommentForm()

            context_dict["user_form"] = user_form
            context_dict["comment_form"] = comment_form

            # return the page with the new comment
            return render(request, 'genetics_ark/variant_view.html', context_dict)

    else:
        # if data is not sent, just display the form
        user_form = Forms.UserForm()
        comment_form = Forms.CommentForm()
        
    context_dict["user_form"] = user_form
    context_dict["comment_form"] = comment_form

    return render(request, 'genetics_ark/variant_view.html', context_dict)
    

def doc_notes( request ):
    return render( request, 'genetics_ark/doc_notes.html')


def _awesome_search(max_results=0, starts_with=''):

    search_list = []
    if starts_with:
#        search_list = search_list ]
        search_list  = [ {'value':x.name} for x in  Models.Sample.objects.filter(name__istartswith=starts_with)[:max_results] ][:5]
        search_list += [ {'value':x.name} for x in  Models.Gene.objects.filter(name__istartswith=starts_with)[:max_results] ][:5]
        search_list += [ {'value':x.name} for x in  Models.Runfolder.objects.filter(name__istartswith=starts_with)[:max_results] ][:5]
        search_list += [ {'value':x.name} for x in  Models.Panel.objects.filter(name__istartswith=starts_with)[:max_results] ][:5]

        search_list = sorted( search_list )

    if max_results > 0:
        if search_list and len(search_list) > max_results:
            search_list = search_list[:max_results]

    return search_list


def api_search( request, query ):

    print("api-search...")

    search_list = []
    starts_with = ''
        
    search_list = _awesome_search(12, query )

    response_text = json.dumps(search_list, separators=(',',':'))

#    pp.pprint( search_list)

    return HttpResponse(response_text, content_type="application/json")


def search(request):


    if request.method == 'GET':  
        query = request.GET['query']

        if ( Models.Sample.objects.filter( name__exact = query)):
            return HttpResponseRedirect(reverse("sample_view", args=[query] ))

        elif ( Models.Runfolder.objects.filter( name__exact = query)):
            runfolder = Models.Runfolder.objects.filter( name__exact = query)[0]
            return HttpResponseRedirect(reverse("runfolder", args=[query] ))

        elif ( Models.Gene.objects.filter( name__exact = query)):
            gene = Models.Gene.objects.filter( name__exact = query)[0]
            return HttpResponseRedirect(reverse("gene_view", args=[gene.name] ))

        elif ( Models.Panel.objects.filter( name__exact = query)):
            panel = Models.Panel.objects.filter( name__exact = query)[0]
            return HttpResponseRedirect(reverse("panel_view", args=[panel.id] ))

        elif ( re.match(r'(\w+):(\d+)', query )):
            query = re.sub(r'\s+', '', query )
            (chrom, position ) = query.split(":")
            return HttpResponseRedirect(reverse('variant_view', args=[chrom, position] ))

        context_dict = {}

        context_dict['query']      = query
        context_dict['samples']    = Models.Sample.objects.filter(name__istartswith=query)
        context_dict['runfolders'] = Models.Runfolder.objects.filter(name__istartswith=query)

#        pp.pprint( context_dict )

        return render( request, 'genetics_ark/search.html', context_dict)

    return HttpResponse( reverse('index') )


def cnv_view(request, CNV_id):
    """ Display the cnv view

    Models:
    - CNV
    - Decon
    - CNV_region
    - Transcript
    - Gene

    Template:
    - cnv_view.html

    - Get the genes affected by the CNV
    - Get the decon run associated
    - Get the samples and call function to get the nb of samples affected by this CNV
    """
    context_dict = {}

    # get the cnv from id in url
    cnv = Models.CNV.objects.filter(pk=CNV_id)

    if (len(cnv) == 0):
        return HttpResponseNotFound("<h1>CNV not found in Genetics Ark</h1>")

    cnv = cnv[0]
    context_dict["cnv"] = cnv

    decons = Models.Decon.objects.filter(deconanalysis__CNV_id__exact = cnv.id).distinct()
    context_dict["decons"] = decons

    # get the genes from the cnv coordinates aka region id
    region_ids = Models.CNV_region.objects.filter(CNV_id__exact = cnv.id).values_list("region_id", flat = True)
    transcript_ids = Models.Transcript.objects.filter(transcriptregion__region_id__in = list(region_ids)).values_list("id", flat = True)
    genes = Models.Gene.objects.filter(transcript__id__in = list(transcript_ids)).distinct()
    context_dict["genes"] = genes

    region_ids = Models.Region.objects.filter(cnv_region__CNV_id__exact = cnv.id).values_list("id", flat = True)
    reference = Models.Reference.objects.filter(region__id__in = list(region_ids))
    context_dict["ref"] = reference[0].name

    # call function to get the samples in which the cnv is present
    nb_samples, samples = Models.CNV.get_samples(cnv)

    context_dict["nb_samples"] = nb_samples
    context_dict["samples"] = samples

    return render(request, "genetics_ark/cnv_view.html", context_dict)


def decon_view(request, Decon_id):
    """ Display the decon run view

    Models:
    - Decon
    - DeconAnalysis
    - CNV_target
    - Reference

    Forms:
    - SearchGeneForm
    - SearchSampleForm
    - SearchPositionForm

    Template:
    - decon_view.html
    
    - Get the cnvs from the run with sample associated
    - Search bars for a gene, sample, position
    - Set up the pagination
    - get the cnv target file
    - get the runfolder
    """

    context_dict = {}
    decon = Models.Decon.objects.filter(pk=Decon_id)

    if (len(decon) == 0):
        return HttpResponseNotFound("<h1>Decon run not found in Genetics Ark</h1>")
    else:
        context_dict["results"] = True

    decon = decon[0]
    context_dict["decon"] = decon
    context_dict["runfolder"] = decon.runfolder

    decon_analysis = Models.DeconAnalysis.objects.filter(decon_id__exact = decon.id)

    cnv_target = Models.CNV_target.objects.filter(decon__exact = decon)
    cnv_target = cnv_target[0]
    context_dict["bedfile"] = cnv_target

    ref = Models.Reference.objects.filter(name__exact = cnv_target.ref)
    context_dict["ref"] = ref[0]

    # form to search for genes, samples, positions from the decon run page
    # first check if the submit button is clicked
    if request.method == "POST":
        gene = None
        sample = None
        position = None
        
        gene_form = Forms.SearchGeneForm(request.POST)
        sample_form = Forms.SearchSampleForm(request.POST)
        position_form = Forms.SearchPositionForm(request.POST)

        # check if the data is clean e.g. no special characters etc
        # or matches a genomic position
        # need individual check to have forms working individually
        if gene_form.is_valid():
            gene = gene_form.cleaned_data
    
        if sample_form.is_valid():
            sample = sample_form.cleaned_data
    
        if position_form.is_valid():
            position = position_form.cleaned_data

        # one of the forms is valid
        if gene or sample or position:
            # search cnvs with genes/sample/position
            decon_analysis = filter_cnvs(request, decon, gene, sample, position)

            # needed to display what the user is filtering for
            if gene:
                context_dict["filter_gene"] = gene

            if sample:
                context_dict["filter_sample"] = sample

            if position:
                if isinstance(position, tuple):
                    context_dict["filter_position"] = position

                else:
                    context_dict["filter_chrom"] = position.upper()

            # the search doesn't give any results 
            if not decon_analysis:
                context_dict["results"] = False
                context_dict["search_gene"] = Forms.SearchGeneForm()
                context_dict["search_sample"] = Forms.SearchSampleForm()
                context_dict["search_position"] = Forms.SearchPositionForm()
                return render(request, "genetics_ark/decon_view.html", context_dict)
        
    else:
        # if not button not clicked just display the form
        gene_form = Forms.SearchGeneForm()
        sample_form = Forms.SearchSampleForm()
        position_form = Forms.SearchPositionForm()
    
    context_dict["search_gene"] = gene_form
    context_dict["search_sample"] = sample_form
    context_dict["search_position"] = position_form

    # pagination set up
    # - display 50 CNVs analysis per page
    paginator = Paginator(decon_analysis, 50)
    page = request.GET.get("page")

    try:
        context_dict["decon_analysis"] = paginator.page(page)

    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        context_dict["decon_analysis"] = paginator.page(1)

    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        context_dict["decon_analysis"] = paginator.page(paginator.num_pages)

    return render(request, "genetics_ark/decon_view.html", context_dict)


def filter_cnvs(request, decon, gene = None, sample = None, position = None):
    """ filter cnvs

    Models:
    - Gene
    - TranscriptRegion
    - CNV_region
    - CNV
    - Sample
    - DeconAnalysis 

    - get the cnvs depending on gene, sample, position
    - intersect the results from every search
    - return in adequate format for decon_view

    P.S. (queryset | queryset) combines the 2 querysets (union)
         (queryset | queryset) takes the intersection of querysets
    """

    # looking for cnvs with gene from form
    if gene:
        gene_object = Models.Gene.objects.filter(name__exact = gene)

        if gene_object:
            # look for cnvs from gene to cnvs
            regions_ids = Models.TranscriptRegion.objects.filter(transcript__gene_id__exact = gene_object[0].id).values_list("region_id", flat = True)
            cnv_ids = Models.CNV_region.objects.filter(region__id__in = list(regions_ids)).values_list("CNV_id", flat = True)
            cnvs_gene = Models.CNV.objects.filter(id__in = list(cnv_ids))
        
        else:
            cnvs_gene = Models.CNV.objects.none()

    else:
        cnvs_gene = Models.CNV.objects.none()

    # looking for cnvs with sample from form
    if sample:
        # check if the sample exists
        sample_object = Models.Sample.objects.filter(name__exact = sample)

        if sample_object:
            cnvs_sample = Models.CNV.objects.filter(deconanalysis__decon_id__exact = decon.id, deconanalysis__sample_id__exact = sample_object[0].id)
        
        else:
            cnvs_sample = Models.CNV.objects.none()

    else:
        sample_object = None
        cnvs_sample = Models.CNV.objects.none()

    # looking for cnvs at that position
    if position:
        if isinstance(position, tuple):
            chrom = position[0]
            start = position[1]
            stop = position[2]
            
            cnvs_position = Models.CNV.objects.filter(chrom__exact = chrom, start__lte = stop, end__gte = start, deconanalysis__decon_id__exact = decon)
        
        else:
            cnvs_position = Models.CNV.objects.filter(chrom__exact = position, deconanalysis__decon_id__exact = decon)

    else:
        cnvs_position = Models.CNV.objects.none()

    # need to intersect the queries
    if cnvs_gene and cnvs_sample:
        if cnvs_position:
            cnvs_ids = (cnvs_gene & cnvs_sample & cnvs_position).values_list("id", flat = True)
        else:
            cnvs_ids = (cnvs_gene & cnvs_sample).values_list("id", flat = True)
    
    elif cnvs_sample and cnvs_position:
        cnvs_ids = (cnvs_sample & cnvs_position).values_list("id", flat = True)

    elif cnvs_gene and cnvs_position:
        cnvs_ids = (cnvs_gene & cnvs_position).values_list("id", flat = True)

    # if only one of the fields used
    else:
        cnvs_ids = (cnvs_gene | cnvs_sample | cnvs_position).values_list("id", flat = True)

    # use the cnv ids to get the decon analysis row we finally want
    if sample_object:
        decon_analysis = Models.DeconAnalysis.objects.filter(decon_id__exact = decon.id, CNV_id__in = list(cnvs_ids), sample_id__exact = sample_object[0].id)
    else:
        decon_analysis = Models.DeconAnalysis.objects.filter(decon_id__exact = decon.id, CNV_id__in = list(cnvs_ids))

    return decon_analysis
