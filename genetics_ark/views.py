from django.shortcuts import render

import os
import re
import json

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
        panel = Models.Panel.objects.filter( name = sample_panel.panel_name )[0]
        context_dict[ 'panels' ].append( panel )
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

    pp.pprint( context_dict )

        
    return render( request, "genetics_ark/sample_view.html", context_dict )


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


    pp.pprint( genes_dict )

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

    pp.pprint( context_dict )

    return render( request, "genetics_ark/panel_view.html", context_dict )



def gene_view( request, gene_name):

    context_dict = {}
    context_dict[ 'gene_name' ] = gene_name
    
    gene = Models.Gene.objects.filter( name__exact = gene_name )

    pp.pprint( gene )

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

    context_dict['ref']   = variant.ref
    context_dict['alt']   = variant.alt
    context_dict['id']    = variant.id

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
            sample_panels = Models.SamplePanel.objects.filter( sample_id__exact = analysis_variant.analysis.sample.id )
            sample_panels = ", ".join([sample_panel.panel_name for sample_panel in sample_panels])
            analysis_variant.panels = sample_panels

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
                project_dict[ 'samples' ] = Tables.SampleAAFTable( samples )
                RequestConfig(request, paginate={'per_page': 36}).configure( project_dict[ 'samples' ] )

        context_dict[ 'projects' ].append( project_dict )

    return (render(request,'genetics_ark/variant_view.html', context_dict))
    

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

