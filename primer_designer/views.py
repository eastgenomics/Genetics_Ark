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
def index(request):
    return render( request, "base.html")


# company related urls
def index( request ):

    if request.method == 'POST':
        regions_form = Forms.RegionsForm( request.POST )

#        pp.pprint( request.POST )
#        pp.pprint( company_form['name'] )

        # One or more valid regions where entered.
        if  regions_form.is_valid():
            print("Passing data along")
            pp.pprint( regions_form.data['regions'] )

            return create( request, regions_form.data['regions'] )

        else:
            pp.pprint( regions_form.errors)

            return render( request, "primer_designer/index.html", {'regions_form': regions_form})
        
    else:
        return render( request, "primer_designer/index.html", {'regions_form': Forms.RegionsForm()})


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

    random_tmp = random_string()

    infile = "{}.txt".format( time_stamp() )

    pp.pprint( regions )

    if infile is None:
        infile = random_tmp

    outfh = open( "{path}{infile}".format( path=path, infile=infile), "w")
    outfh.write( regions )
    outfh.close()

    cmd = "/software/packages/primer_designer/bulk_design.py {infile} {working_dir} ".format(infile=infile, working_dir=path)
    cmd = "/mnt/storage/apps/software/primer_designer/1.1/bulk_design.py {infile} {working_dir} ".format(infile=infile, working_dir=path)

    context_dict =  { 'key': random_string }
    context_dict[ 'infile' ] = infile

    stderr_file_name = "{}{}.stderr".format(path, random_tmp)
    stdout_file_name = "{}{}.stdout".format(path, random_tmp)

    stderr_file = open( stderr_file_name, "w+" )
    stdout_file = open( stdout_file_name, "w+" )

    context_dict['tmp_key'] = random_tmp

    cmd = shlex.split( cmd )

    p = subprocess.Popen( cmd , shell=False, stderr = stderr_file , stdout = stdout_file)

    return render( request, "primer_designer/create.html", context_dict )


def primers_done_ajax( request, tmp_key ):
    
    path = 'static/tmp/'

    stdout_name = "{}{}.stdout".format( path, tmp_key)
    print(stdout_name)

    result_dict = {'status': 'running' }

    if ( os.path.isfile( stdout_name )):
        fh = open( stdout_name, 'rU')
        lines = ""

        for line in fh.readlines():
            line = line.rstrip( "\n" )
            print(line)
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




