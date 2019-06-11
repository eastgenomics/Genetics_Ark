from django.shortcuts import render

import os
import re
import json
import operator
import subprocess
import shlex
import shutil
import string 
import random 

import pprint as pp

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

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

    context_dict = {}

    projects = Models.Project.objects.all()
    
    for project in projects:
        project.samples = Models.Sample.objects.filter( project_id__exact = project.id).count()
        print "samples in project {}: {}".format(project.name,project.samples)

    projects_table = Tables.ProjectTable( projects )
    projects_table.order_by = "Name"
    context_dict[ 'project_table' ] =  projects_table 
    RequestConfig(request).configure( projects_table )

    return render( request, "genetics_ark/projects_list.html", context_dict )


def igv( request, analysis_id=None, sample_name=None, runfolder_name=None, chrom=None, pos=None):
    """ create a page with the js IGV viewer for the sample

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

    context_dict = {}

    sample = None
    
    if sample_id is not None:
        sample = Models.Sample.objects.get( pk = sample_id )    

    elif sample_name is not None:
        samples = Models.Sample.objects.filter( name__exact = sample_name )
        sample = samples[0]

    context_dict = { 'sample': sample }
    context_dict[ 'panels' ] = []
    sample_panels = Models.SamplePanel.objects.filter( sample_id__exact = sample.id )

    for sample_panel in sample_panels:
        panels = Models.Panel.objects.filter( name = sample_panel.panel_name ).filter( active ='Y')

	if (panels.count() > 0):
	    context_dict[ 'panels' ].append( panels[0] )
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
    deconSamples = Models.DeconCNV.objects.filter(sample_id__exact = sample.id)

    context_dict['decon_runs'] = []

    for deconSample in deconSamples:
        decons = deconSample.decon
        context_dict['decon_runs'].append(decons)

    context_dict['decon_runs'] = sorted(set(context_dict['decon_runs']))
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
    print( cmd )

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

    print stdout_name

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
            print line
            lines += line +"<br>"

    result_dict['progress'] += lines

    response_text = json.dumps(result_dict, separators=(',',':'))
#    pp.pprint( response_text )
    return HttpResponse(response_text, content_type="application/json")
    
    
def analysis_report( request, analysis_id):
    
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

    Args:
       panel_id (int): primary key of the panel

    Returns:
      dict of genes of transcripts

    Raises:
       None

    """

    gene_panels = Models.GenePanel.objects.filter( panel_id__exact = panel_id )
    genes_dict = {}

    for gene_panel in gene_panels:
        transcripts = Models.Transcript.objects.filter( gene_id__exact = gene_panel.gene_id).filter( clinical_transcript__exact = 'Y')

        for transcript in transcripts:
            gene_name = transcript.gene.name

            if ( gene_name not in genes_dict ):
                genes_dict[ gene_name ] = {}
                genes_dict[ gene_name ]['transcripts'] = []
            
            genes_dict[ gene_name ]['transcripts'].append( transcript.refseq )

#    pp.pprint( genes_dict )

    genes_list = []

    for gene in sorted(genes_dict):
        genes_list.append([ gene, ", ".join(genes_dict[ gene ]['transcripts'])])

    return genes_list


def panel_view( request, panel_id):

    context_dict = {}
    
    panel = Models.Panel.objects.get( pk = panel_id )
    context_dict[ 'panel' ] = panel

    sample_panels = Models.SamplePanel.objects.filter( panel_name__exact = panel.name )
    samples = []

    for sample_panel in sample_panels:
        samples.append( sample_panel.sample.name )

    context_dict[ 'samples' ] = samples

    context_dict[ 'genes' ] = genes_in_panel( panel_id )

#    pp.pprint( context_dict )

    return render( request, "genetics_ark/panel_view.html", context_dict )


def gene_view( request, gene_name):

    context_dict = {}
    context_dict[ 'gene_name' ] = gene_name
    
    gene = Models.Gene.objects.filter( name__exact = gene_name )

#    pp.pprint( gene )

    if ( len(gene) == 0 ):
        return render( request, "genetics_ark/gene_not_found.html", context_dict )
        
    gene = gene[0]

    context_dict[ 'gene_id' ] = gene.id
    
    transcripts = Models.Transcript.objects.filter( gene_id__exact = gene.id )

    context_dict[ 'transcripts' ] = transcripts
    
    gene_panels = Models.GenePanel.objects.filter( gene_id__exact = gene.id )

    context_dict[ 'panels' ] = []

    for gene_panel in gene_panels:
        panel = gene_panel.panel
        context_dict[ 'panels' ].append( [panel.name, panel.id])

    context_dict[ 'panels' ] = sorted( context_dict[ 'panels' ] )

    return render( request, "genetics_ark/gene_view.html", context_dict )


def qc_project( request, project_id ):
    
    project =  Models.Project.objects.get( pk = project_id )

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
            print "perc dups: {}".format( runfolder['perc_dups'] )
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
            if ( type(runfolder_stat[ item ]) is not float and  type(runfolder_stat[ item ]) is not int and type(runfolder_stat[ item ]) is not long ):
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

    context_dict = {}
    context_dict['chrom'] = chrom
    context_dict['pos']   = pos

    variants = Models.Variant.objects.filter( chrom__exact = chrom ).filter( pos__exact = pos )

    if variants > 1:
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

    context_dict["comment"] = variant.comment

    # handle the comments in the variant page
    if request.method == "POST":
        # data is sent
        comment_form = Forms.CommentForm(request.POST)

        if comment_form.is_valid():
            # the form is valid
            comment = comment_form.cleaned_data['comment']

            # if the textarea is empty when the submit button is clicked --> get a None to put a NULL in the db
            if comment == "":
                comment = None
                
            # save the comment in the database
            variant.comment = comment
            variant.save()

            context_dict["comment"] = variant.comment

            # recreate the form
            comment_form = Forms.CommentForm()
            context_dict["form"] = comment_form

            # return the page with the new comment
            return render(request, 'genetics_ark/variant_view.html', context_dict)

    else:
        # if data is not sent, just display the form
        comment_form = Forms.CommentForm()
        
    context_dict["form"] = comment_form

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

    print "api-search..."

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
    context_dict = {}

    # get the data from url and filter
    cnv = Models.CNV.objects.filter(pk=CNV_id)

    if (len(cnv) == 0):
        return render(request, "genetics_ark/cnv_not_found.html", context_dict)
        
    # filter return a list? so need only value matching the query
    cnv = cnv[0]

    deconexonsCNVs = Models.DeconexonCNV.objects.filter(CNV_id__exact = cnv.id)

    deconsCNVs = Models.DeconCNV.objects.filter(CNV_id__exact = cnv.id)

    context_dict['decons'] = []

    exons = []

    # i get every individual elements to sort them
    for deconexonsCNV in deconexonsCNVs:
        exon = deconexonsCNV.deconexon

        exons.append("{} {} {} {} {}".format(exon.chr, exon.start, exon.end, exon.name, exon.id))

    # need a list of lists for element accessing in the template
    unsorted_exons = [exon.split() for exon in exons]

    # sorting the deconexons by the chrom, start, end
    context_dict['deconexons'] = sorted(unsorted_exons, key=lambda x: (x[0], int(x[1]), int(x[2])))

    # get every decon using the deconCNV table
    for deconCNV in deconsCNVs:
        decon = deconCNV.decon
        context_dict['decons'].append(decon)

    # call function to get the nb of samples in which the cnv is present
    nb_samples, samples = Models.CNV.calc_nb(cnv)

    context_dict['cnv'] = cnv
    context_dict['decons'] = sorted(context_dict['decons'])
    context_dict['nb_samples'] = nb_samples
    context_dict['samples'] = samples

    return render(request, "genetics_ark/cnv_view.html", context_dict)


def decon_view(request, Decon_id):
    context_dict = {}

    decon = Models.Decon.objects.filter(pk=Decon_id)

    if (len(decon) == 0):
        return render(request, "genetics_ark/decon_not_found.html", context_dict)

    decon = decon[0]

    deconsCNVs = Models.DeconCNV.objects.filter(decon_id__exact = decon.id)

    context_dict['CNVs'] = []

    CNVs = []
    stats_deconCNV = []

    # sort the cnv data
    # id comparison wasn't working in the template because i was comparing a string to an object
    for deconCNV in deconsCNVs:
        CNV = deconCNV.CNV

        CNVs.append("{} {} {} {} {}".format(CNV.chr, CNV.start, CNV.end, CNV.type, CNV.id))

        stats_deconCNV.append("{} {} {} {} {} {} {} {} {} {} {}".format(deconCNV.CNV_id,
                                deconCNV.correlation, 
                                deconCNV.start_b, 
                                deconCNV.end_b, 
                                deconCNV.nb_exons, 
                                deconCNV.BF, 
                                deconCNV.reads_expected, 
                                deconCNV.reads_observed, 
                                deconCNV.reads_ratio,
                                deconCNV.sample,
                                deconCNV.sample_id
        ))

    unsorted_CNVs = [cnv.split() for cnv in CNVs]

    context_dict['CNVs'] = sorted(unsorted_CNVs, key=lambda x: (x[0], int(x[1]), int(x[2])))

    context_dict['decon'] = decon

    context_dict['deconCNVs'] = [stat.split() for stat in stats_deconCNV]

    # form to search for decongenes from the decon run page
    # first check if the submit button is clicked
    if request.method == 'POST':
        decongene_form = Forms.SearchDeconGeneForm( request.POST )

        # check if there's stuff in the field
        if  decongene_form.is_valid():
            # check if the data is clean e.g. no special characters etc
            decongene = decongene_form.clean_decongene()
            # call the page displaying the result of the search
            return decongene_search(request, decon.id, decon.name, decongene)
            
        else:
            # data not clean: recall the page with the error message
            context_dict['decongene'] = decongene_form
            return render(request, "genetics_ark/decon_view.html", context_dict)
        
    else:
        # if not button not clicked just display the form
        decongene_form = Forms.SearchDeconGeneForm()
    
    context_dict['decongene'] = decongene_form

    return render(request, "genetics_ark/decon_view.html", context_dict)


def deconexon_view(request, Deconexon_id):
    """ display decon exons

    """

    context_dict = {}

    deconexon = Models.Deconexon.objects.filter(pk = Deconexon_id)

    if (len(deconexon) == 0):
        return render(request, "genetics_ark/decon_not_found.html", context_dict)

    deconexon = deconexon[0]

    CNVs2deconexons = Models.DeconexonCNV.objects.filter(deconexon_id__exact = deconexon.id)

    context_dict['CNVs'] = []

    for CNV2deconexon in CNVs2deconexons:
        CNV = CNV2deconexon.CNV
        context_dict['CNVs'].append(CNV)

    context_dict["deconexon"] = deconexon
    context_dict["CNVs"] = sorted(context_dict["CNVs"])

    return render(request, "genetics_ark/deconexon_view.html", context_dict)

def decongene_view(request, parameter): 

    context_dict = {}
    exons_display = []
    exons = Models.Deconexon.objects.filter(name__exact = parameter)

    # needed to have good sorting
    for exon in exons:
        exons_display.append("{} {} {} {} {}".format(exon.chr, exon.start, exon.end, exon.name, exon.id))

    unsorted_exons = [exon.split() for exon in exons_display]

    context_dict['decongene'] = parameter
    context_dict['exons'] = sorted(unsorted_exons, key=lambda x: (x[0], int(x[1]), int(x[2])))

    return render(request, 'genetics_ark/decongene_view.html', context_dict)


def decongene_search(request, decon_id, decon_name, decongene_name):

    context_dict = {}

    exons = Models.Deconexon.objects.filter(name__exact = decongene_name)

    exons_display = []
    CNVs_data = []
    rest_sample = []
    decon_sample = []

    # need to display exons and samples
    # so i get CNV to link exons to the samples
    # i also get the exons
    for exon in exons:
        deconexonCNVs = Models.DeconexonCNV.objects.filter(deconexon__exact = exon)
        
        for deconexonCNV in deconexonCNVs:
            CNV = deconexonCNV.CNV
            exon = deconexonCNV.deconexon

            CNVs_data.append(CNV)
            exons_display.append("{} {} {} {} {}".format(exon.chr, exon.start, exon.end, exon.name, exon.id))

    # separate samples in the decon run and those who are not
    for CNV_data in CNVs_data:
        rest_deconCNVSamples = Models.DeconCNV.objects.filter(CNV__exact = CNV_data).exclude(decon_id__exact = decon_id)
        decon_deconCNVSamples = Models.DeconCNV.objects.filter(CNV__exact = CNV_data).filter(decon_id__exact = decon_id)

        for rest_deconCNVSample in rest_deconCNVSamples:
            rest_sample.append(rest_deconCNVSample.sample)

        for decon_deconCNVSample in decon_deconCNVSamples:
            decon_sample.append(decon_deconCNVSample.sample)

    unsorted_exons = [exon.split() for exon in exons_display]

    context_dict['decon_sample'] = set(decon_sample)
    context_dict['rest_sample'] = set(rest_sample)
    context_dict['decongene'] = decongene_name
    context_dict['decon_name'] = decon_name
    context_dict['decon_id'] = decon_id
    # allows sorting according to chrom, start, end
    context_dict['exons'] = sorted(unsorted_exons, key=lambda x: (x[0], int(x[1]), int(x[2])))

    return render(request, "genetics_ark/decongene_search.html", context_dict)