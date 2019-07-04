from django.shortcuts import render

import os
import string 
import random 
import subprocess
import shlex
import shutil
import time 
import datetime
import json
import pprint as pp
import re

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import primer_designer.forms  as Forms


#@login_required(login_url='/login/')
# def index(request):
#     return render( request, "base.html")


# company related urls
def index( request ):
    """Funcrion is called when primer_designer page is called 
    Outputs a form to give 3 choices to make primers (Position, Range, Fusion)
    Redirects to an appropriate page when submit is pressed

    """
    
    if request.method == 'POST':
        form = Forms.TypeForm(request.POST)
        

        if form.is_valid() :
                
            if form.cleaned_data['position'] == "Position":
                return redirect("position") #redirects to a url with name "position" - look up urls.py 

            elif form.cleaned_data['position'] == "Range": 
                return redirect("range")

            elif form.cleaned_data['position'] == "Fusion": 
                return redirect("fusion")
        else:
            return render( request, "primer_designer/index.html", {'form': form})

    else:
        form = Forms.TypeForm()

    return render( request, "primer_designer/index.html", {'form': form})


def render_position(request):
    """Renders position page and outputs a report for position primer design"""

    if request.method == 'POST': 
        position_form = Forms.PositionForm(request.POST)
        print("POST")
        

        if position_form.is_valid(): 
            print(position_form.cleaned_data)
            # return render(request, "primer_designer/index.html", {'form': position_form})

            return create(request, position_form.cleaned_data)
        else:
            return render(request, "primer_designer/index.html", {'form': position_form})

    else:
        position_form = Forms.PositionForm() 

    print("something")
    return render(request, "primer_designer/index.html", {'form': position_form})

def render_range(request): 
    """Renders range page and outputs a report for range primer design"""

    if request.method == 'POST': 
        range_form = Forms.RangeForm(request.POST)

        if range_form.is_valid():
            return create(request, range_form.cleaned_data)
        else:
            return render(request, "primer_designer/index.html", {'form': range_form})

    else: 
        range_form = Forms.RangeForm()

    return render(request, "primer_designer/index.html", {'form': range_form})

def render_fusion(request): 
    """Renders fusion page and outputs a report for fusion primer design"""

    if request.method == 'POST': 
        fusion_form = Forms.FusionForm(request.POST)

        if fusion_form.is_valid():
            print(fusion_form.cleaned_data)
            return create(request, fusion_form.cleaned_data)

        else:
            return render(request, "primer_designer/index.html", {'form': fusion_form})

    else: 
        fusion_form = Forms.FusionForm()

    return render(request, "primer_designer/index.html", {'form': fusion_form})


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


def time_stamp():
    """ return a time stamp to ensure primer designs dont clash

    Returns
     string 

    """

    now = time.gmtime()
    time_string = time.strftime("%Y%m%d_%H%M%S", now)

    return time_string
    

def create( request, regions, infile=None ):

    path = "static/tmp/"

    random_tmp = random_string() #random string of 10 characters 

    infile = "{}.txt".format( time_stamp() )

    pp.pprint( regions )

    with open( "{path}{infile}".format( path=path, infile=infile), "w") as outfh: 
        
        if len(regions) == 3:
            regions = "-c {chrom} -p {pos} --{ref}".format(chrom = regions['chromosome_choice'], pos = regions['coordinate'], ref = regions['reference_choice'])
            outfh.write(regions) 
            outfh.close()

        elif len(regions) == 4: 
            regions = "-c {chrom} -r {pos} {pos2} --{ref}".format(chrom = regions['chromosome_choice'], pos = regions['coordinate'], pos2 = regions['coordinate2'], ref = regions['reference_choice'])
            outfh.write(regions) 
            outfh.close()

        elif len(regions) == 9:

            if regions['side'] == "Before": 
                regions['side'] = "b"

            if regions['side2'] == "Before": 
                regions['side2'] = "b"

            if regions['side'] == "After": 
                regions['side'] = "a"

            if regions['side2'] == "After": 
                regions['side2'] = "a"

            print("###########")
            print(regions)

            regions = "-b {chrom1}:{pos1}:{side}:{strand1}_{chrom2}:{pos2}:{side2}:{strand2} --{ref}".format(chrom1 = regions['chromosome_choice'], pos1 = regions['coordinate'], side =regions['side'], strand1 = regions['strand'], chrom2 = regions['chromosome_choice2'], pos2 = regions['coordinate2'], side2 = regions['side2'], strand2 = regions['strand2'], ref = regions['reference_choice'])
            outfh.write(regions) 
            outfh.close()


    cmd = "/mnt/storage/home/povarnin/projects/Primer_designer/bulk_design.py {infile} {working_dir} ".format(infile=infile, working_dir=path)

    context_dict =  { 'key': random_string }
    context_dict[ 'infile' ] = infile

    stderr_file_name = "{}{}.stderr".format(path, random_tmp)
    stdout_file_name = "{}{}.stdout".format(path, random_tmp)

    stderr_file = open( stderr_file_name, "w+" )
    stdout_file = open( stdout_file_name, "w+" )

    context_dict['tmp_key'] = random_tmp

    cmd = shlex.split( cmd )

    p = subprocess.Popen( cmd , shell=False, stderr = stderr_file , stdout = stdout_file)

    file_path = infile.strip(".txt")+".zip"


    return render( request, "primer_designer/create.html", context_dict )


def primers_done_ajax( request, tmp_key ):
    
    path = "static/tmp/"

    stdout_name = "{}{}.stdout".format( path, tmp_key)
    print stdout_name

    result_dict = {'status': 'running' }
    print(os.path.abspath( stdout_name ))
    if ( os.path.isfile( stdout_name )):
        print("Hello")
        fh = open( stdout_name, 'rU')
        lines = ""

        for line in fh.readlines():
            line = line.rstrip( "\n" )
            print line
            lines += line +"<br>"

            if line == 'SUCCESS':
                result_dict['status'] = 'done'

            elif re.match('Output file: ', line):
                result_dict['file'] = re.sub(r'Output file: ', '', line)

            elif re.match('Died at', line):
                result_dict['status'] = 'failed'
                
    pp.pprint( lines )
        
    result_dict['progress'] = lines
    
    response_text = json.dumps(result_dict, separators=(',',':'))
#    pp.pprint( response_text )
    return HttpResponse(response_text, content_type="application/json")




