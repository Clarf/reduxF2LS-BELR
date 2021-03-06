# bookkeeping.py module
"""
Bookkeeping functions to help reduce F2 data.
"""

def mkdirectories(program, targetname, obsdate, reduxdate, bands):
    """
    Create the directory structure organizing the reduction of data.
    Can process only one target and obsdate/reduxdate combination 
    at a time.  Multiple bands is okay.
    
    :param program: Program name, eg. GS-2013B-Q-73
    :type program: str
    :parma targetname: Target name, eg. SDSSJ011758.83+002021.4
    :type targetname: str
    :param obsdate: Observation date, eg. 20131015
    :type obsdate: str
    :param reduxdate: Date the reduction was done, 16Oct2013
    :type reduxdate: str
    :param bands: List of bands for which data was taken that night.
        Each band will be given its own directory. Eg. ['JH', 'HK']
    :type bands: list of str
    """

    import os
    import os.path
    
    rootdir = os.getcwd()
    
    # Program # directory
    if not os.path.exists(program):
        os.makedirs(program)
    
    #-----
    os.chdir(program)

    # Raw directory
    if not os.path.exists('raw'):
        os.makedirs('raw')
    # Target directory
    if not os.path.exists(targetname):
        os.makedirs(targetname)
    
    #-----
    os.chdir(targetname)
    
    # sciproducts directory
    if not os.path.exists('sciproducts'):
        os.makedirs('sciproducts')
    # date directory
    datedir = '-'.join([obsdate, reduxdate])
    if not os.path.exists(datedir):
        os.makedirs(datedir)
    
    #-----
    os.chdir(datedir)
    
    # redux directories
    for band in bands:
        reduxdir = ''.join(['redux', band])
        if not os.path.exists(reduxdir):
            os.makedirs(reduxdir)
    
    # README file
    if not os.path.exists('README'):
        write_readme_template()
    
    # Possibly create and add the redux scripts once the tool
    # has been created.
    
    os.chdir(rootdir)
    
    return


def mktable_helper(tablename, auto=True, rawdir="./"):
    """
    Create or append to an observation summary table.
    This function is interactive and requires input from the users.
    
    :param tablename: Filename for the table.  If it exists it will
        be extended.
    :type tablename: str
    :param auto: If True, get some of the information directly from
        the FITS headers.  [Default: True]
    :type auto: boolean
    :param rawdir: Path to raw data.  Required for auto=True.
        [Default: "./"]
    :type rawdir: str
    """
    import obstable
    import os.path
    if auto:
        from astrodata import AstroData
        
    # Create an ObsTable.  If the file already exists on disk,
    # then read it.  Otherwise, leave it empty.
    # Error handling: If the file exists but there's an read error,
    # raise, otherwise assume that you are creating a new file.
    table = obstable.ObsTable()
    table.filename = tablename
    try:
        table.read_table()
    except IOError:
        if os.path.exists(tablename):
            print "Error reading table %s\n" % tablename
            raise
        else:
            print "New table will be created."
    
    # Start the prompting the user and the data for the information
    # that needs to go in the table.
    
    user_not_done = True
    while user_not_done:
        user_inputs = {}
        if auto:
            filename_not_known = True
        
        # Get list of prompts for user or data supplied information.
        req_input_list = get_req_input_list()
        
        # Loop through record elements
        for input_request in req_input_list:
            if (not input_request['in_hdr'] or not auto):
                # if auto and this is a Science entry, get the targetname from
                # the header.  If not Science, then you need to prompt user.
                if auto and input_request['id'] == 'targetname' and \
                    user_inputs.has_key('datatype') and \
                    user_inputs['datatype'] == 'Science':
                    
                    input_value = query_header(ad, input_request['id'])
                else:
                    # prompt the user
                    input_value = raw_input(input_request['prompt'])

                user_inputs[input_request['id']] = input_value
                
                # Assume that the user has a brain.
                # Probe only the first file in 'filerange' since all the
                # files in 'filerange' should be similar.
                #
                # Once we know the name of the first MEF file, open it
                # and keep it open until we're done requesting inputs
                # (instead of opening and closing it every time).
                if auto and filename_not_known:
                    if user_inputs.has_key('rootname') and \
                       user_inputs.has_key('filerange'):
                        # parse filerange, build filename (with rawdir path)
                        filenumbers = parse_filerange(user_inputs['filerange'])
                        filename = "%sS%04d.fits" % \
                                (user_inputs['rootname'], filenumbers[0])
                        filename = os.path.join(rawdir, filename)

                        # open ad
                        ad = AstroData(filename)                        
                        filename_not_known = False
            else:
                
                # get value from header
                input_value = query_header(ad, input_request['id'])
                user_inputs[input_request['id']] = input_value
        
        if auto:
            ad.close()
                
        # Create record
        new_record = create_record(user_inputs)
        
        # Append to table
        table.add_records_to_table(new_record)
        
        # Prompt user: add another entry?
        answer = raw_input('Add another entry (y/n): ')
        user_not_done = ((answer=='y') or False)
    
    # All the info is now in the ObsTable.
    # Write the ObsTable to disk and close everything, we're done.
    table.write_table()
    table.pretty_table()
    
    return

#def mkreduxscript(tablename, targetname, band, shorttarget,
#                  rootname):
#
#    
#    return

#--------------------

def get_req_input_list():
    """
    Return a list of prompts to present to the user.  For each
    prompt, specify whether the info can be found in the header
    and assign an identifier.
    
    :rtype: list of dictionaries 
    """
    
    root_prompt = {'prompt': 'File root name (e.g. S201202012): ',
                   'in_hdr': False,
                   'id': 'rootname'}
    filerange_prompt = {'prompt': 'filerange string (e.g. 201-205): ',
                        'in_hdr': False,
                        'id': 'filerange'}
    applyto_prompt = {'prompt': 'Applies to (e.g. Science): ',
                      'in_hdr': False,
                      'id': 'applyto'}
    datatype_prompt = {'prompt': 'Type of observation (e.g. Flat): ',
                       'in_hdr': False,
                       'id': 'datatype'}
    # target means Science target, eg. a flat is associated
    # to "this" science target, hence cannot be in header.
    target_prompt = {'prompt': 'Name of science target: ',
                     'in_hdr': False,
                     'id': 'targetname'}
    band_prompt = {'prompt': 'Band: ',
                   'in_hdr': True,
                   'id': 'band'}
    grism_prompt = {'prompt': 'Grism: ',
                    'in_hdr': True,
                    'id': 'grism'}
    exptime_prompt = {'prompt': 'Exposure Time: ',
                      'in_hdr': True,
                      'id': 'exptime'}
    lnrs_prompt = {'prompt': 'LNRS: ',
                   'in_hdr': True,
                   'id': 'lnrs'}
    rdmode_prompt = {'prompt': 'Read mode (e.g. Faint, Bright): ',
                     'in_hdr': True,
                     'id': 'rdmode'}
    return [root_prompt, filerange_prompt, 
            applyto_prompt, datatype_prompt, target_prompt, band_prompt, 
            grism_prompt, exptime_prompt, lnrs_prompt,
            rdmode_prompt]

def query_header(ad, requested_input):
    """
    Returns the header value associated with the 'requested_input'
    string.  The requested_input strings are defined in get_req_input_list(),
    and they correspond to columns in the observation summary table.
    
    :param ad: AstroData object that contains the header information.
    :type ad: AstroData object
    :param requested_input: Information to retrieve from the header.  The
        valid strings correspond to the 'id' in the dictionaries returned
        by get_req_input_list().  Only the prompts with 'in_hdr'=True are
        valid.
    :type requested_intput: str
    :rtype: str
    """
    
    # warning: might not be efficient if the descriptor system is slow
    # might have to change to if-elif sequence.  (but it's kinda cool
    # looking this way.)
    return {
        'targetname' : ad.object().as_str(),
        'band'       : ad.filter_name(pretty=True).as_str(),
        'grism'      : ad.disperser(pretty=True).as_str(),
        'exptime'    : ad.exposure_time().as_float(),
        'lnrs'       : ad.phu_get_key_value('LNRS'),
        'rdmode'     : ad.read_mode(pretty=True).as_str() 
    }[requested_input]
    
def create_record(user_inputs):
    """
    Create a ObsRecord from the informations gathered from the users.
    
    :param user_inputs: Dictionary with all the values (as strings) required
        to fully populate a ObsRecord object.
    :type user_inputs: dict
    :rtype: ObsRecord object
    """
    import obstable
    
    record = obstable.ObsRecord()
    record.targetname = user_inputs['targetname']
    record.rootname = user_inputs['rootname']
    record.band = user_inputs['band']
    record.grism = user_inputs['grism']
    record.datatype = user_inputs['datatype']
    record.applyto = user_inputs['applyto']
    record.filerange = user_inputs['filerange']
    record.exptime = float(user_inputs['exptime'])
    record.lnrs = int(user_inputs['lnrs'])
    record.rdmode = user_inputs['rdmode']
    
    return record

def parse_filerange(filerange):
    """
    Parse strings like this:  
        210-214
        215
        216,217
        218-221,223-225
    and produce a list of integers corresponding to the range expressed
    in the string.
    
    :param filerange: String representing a range of integers.
    :type filerange: str
    :rtype: list of int
    """
    filenumbers = []
    ranges = filerange.split(',')
    for range_limits in ranges:
        boundaries = range_limits.split('-')
        if len(boundaries) == 1:
            filenumbers.append(int(boundaries[0]))
        elif len(boundaries) == 2:
            number = int(boundaries[0])
            while number <= int(boundaries[1]):
                filenumbers.append(number)
                number += 1
        else:
            raise RuntimeError
    
    return filenumbers

def write_readme_template():
    """
    When creating a directory structure, create also a short README
    file in which the version numbers of the DR software will be stored.
    """
    
    readme_file = open('README', 'w')
    readme_file.write("Reduced with\n")
    readme_file.write("  reduxF2LS-BELR  [hg #:sha / github sha]\n")
    readme_file.write("  gemini_iraf [version]\n")
    readme_file.write("\n")
    readme_file.write("QUICKLOOK ONLY - NOT SQ or FOR SCIENCE\n")
    readme_file.close()
    return
