#!/usr/bin/env python3
"""
Purpose
----
Read physio data from saved from a Siemens scanner using the PMU system and
save it as BIDS physiology recording file
Tested on a Prisma scanner running VE11C 

Usage
----
pmu2bidsphysio -i <Siemens PMU Physio file(s)> -b <BIDS file prefix>


Author
----
Pablo Velasco, NYU Center for Brain Imaging

Dates
----
2020-03-02 PJV

References
----
BIDS specification for physio signal:
https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/06-physiological-and-other-continuous-recordings.html

License
----
MIT License

Copyright (c) 2020      Pablo Velasco

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__version__ = '1.0.0'


import os
import sys
import argparse
import numpy as np
import re
import bidsphysio.bidsphysio as bp


def pmu2bids( physio_files, bids_prefix ):
    """
    Function to read a list of Siemens PMU physio files and
    save them as a BIDS physiological recording.

    Parameters
    ----------
    physio_files : list of str
        list of paths to files with a Siemens PMU recording
    bids_prefix : str
        string with the BIDS filename to save the physio signal (full path)

    Returns
    -------

    """

    # In case we are handled just a single file, make it a one-element list:
    if isinstance(physio_files, str):
        physio_files = [physio_files]
    
    # Init physiodata object to hold physio signals:
    physio = bp.physiodata()

    # Read the files from the list, extract the relevant information and
    #   add a new physiosignal to the list:
    for f in physio_files:
        physio_type, MDHTime, sampling_rate, physio_signal = readpmu( f )

        # specify label:
        if 'PULS' in physio_type:
            physio_label = 'cardiac'

        elif 'RESP' in physio_type:
            physio_label = 'respiratory'

        elif "TRIGGER" in physio_type:
            physio_label = 'trigger'

        else:
            physio_label = physio_type

        physio.append_signal(
            bp.physiosignal(
                label=physio_label,
                units='',
                samples_per_second=sampling_rate,
                t_start=MDHTime[0],
                signal=physio_signal
            )
        )

    # remove '_bold.nii(.gz)' or '_physio' if present **at the end of the bids_prefix**
    # (This is a little convoluted, but we make sure we don't delete it if
    #  it happens in the middle of the string)
    for mystr in ['.gz', '.nii', '_bold', '_physio']:
        bids_prefix = bids_prefix[:-len(mystr)] if bids_prefix.endswith(mystr) else bids_prefix
    
    # Save files:
    if 'trigger' in physio.labels():
        physio.save_to_bids_with_trigger( bids_prefix )
    else:
        physio.save_to_bids( bids_prefix )

    return


def readpmu( physio_file, softwareVersion=None ):
    """
    Function to read the physiological signal from a Siemens PMU physio file
    It would try to open the knew formats (currently, VE11C)

    Parameters
    ----------
    physio_file : str
        path to a file with a Siemens PMU recording
    softwareVersion : str or None (default)
        Siemens scanner software version
        If None (default behavior), it will try all known versions

    Returns
    -------
    physio_type : str
        type of physiological recording
    MDHTime : list
        list of two integers indicating the time in ms since last midnight.
        MDHTime[0] gives the start of the recording
        MDHTime[0] gives the end   of the recording
    sampling_rate : int
        number of samples per second
    physio_signal : list of int
        signal proper. NaN indicate points for which there was no recording
        (the scanner found a trigger in the signal)
    """

    # Check for known software versions:
    knownVersions = [ 'VE11C' ]

    if not (
            softwareVersion in knownVersions or
            softwareVersion == None
           ):
        raise "{sv} is not a known software version."

    # Define what versions we need to test:
    versionsToTest = [softwareVersion] if softwareVersion else knownVersions

    # Try to read as each of the versions to test, until we find one:
    for sv in versionsToTest:
        # try to read, if successful, it will return (the results of the call)
        # if unsuccessful, it will try the next versionToTest
        if sv == 'VE11C':
            try:
                return readVE11Cpmu( physio_file )
            except:
                print('File {f} does not seem to be a {v} file'.format(f=physio_file,v=sv))
                continue

    # if we made it this far, there was a problem:
    print('File {f} does not seem to be a Siemens PMU file'.format(f=physio_file))
    raise


def readVE11Cpmu( physio_file, forceRead=False ):
    """
    Function to read the physiological signal from a VE11C Siemens PMU physio file

    Parameters
    ----------
    physio_file : str
        path to a file with a Siemens PMU recording
    forceRead : bool
        flag indicating to read the file whether the format seems correct or not

    Returns
    -------
    physio_type : str
        type of physiological recording
    MDHTime : list
        list of two integers indicating the time in ms since last midnight.
        MDHTime[0] gives the start of the recording
        MDHTime[0] gives the end   of the recording
    sampling_rate : int
        number of samples per second
    physio_signal : list of int
        signal proper. NaN indicate points for which there was no recording
        (the scanner found a trigger in the signal)
    """

    # Read the file, splitting by lines and removing the "newline" (and any blank space)
    #   at the end of the line:
    lines = [line.rstrip() for line in open( physio_file )]

    # According to Siemens (IDEA documentation), the sampling rate is 2.5ms for all signals:
    sampling_rate = int(400)    # 1000/2.5


    # For that first line, different information regions are bound by "5002 and "6002".
    #   Find them:
    s = re.split('5002(.*?)6002', lines[0])

    # The first group contains the triggering method, gate open and close times, etc. Ignore.
    # The second group tells us the type of signal ('RESP', 'PULS', etc.)
    try:
        physio_type = re.search('LOGVERSION_([A-Z]*)', s[1]).group(1)
    except AttributeError:
        print( 'Could not find type of recording for {fName}. '
               'Setting type to "Unknown"'.format(fName=physio_file) )
        physio_type = "Unknown"

    # The third and fouth groups we ignore, and the fifth gives us the physio signal itself.
    #   (up to the entry "5003")
    raw_signal = s[4].split(' ')
    
    # Sometimes, there is an empty string ('') at the beginning of the string. Remove it:
    if raw_signal[0] == '':
        raw_signal = raw_signal[1:]

    # Convert to integers:
    raw_signal = [ int(v) for v in raw_signal ]

    # only keep up to "5003" (indicates end of signal recording):
    try:
        raw_signal = raw_signal[:raw_signal.index(5003)]
    except ValueError:
        print( "End of physio recording not found. Keeping whole data" )

    # Values "5000" and "6000" indicate "trigger on" and "trigger off", respectively, so they
    #   are not a real physio_signal value. So replace them with NaN:
    physio_signal = raw_signal
    for idx,v in enumerate(raw_signal):
        if v == 5000 or v == 6000:
            physio_signal[idx] = float('NaN')           


    # The rest of the lines have statistics about the signals, plus start and finish times.
    # Get timing:
    MPCUTime = [0,0]
    MDHTime = [0,0]
    for l in lines[1:]:     #  (don't check the first line)
        if 'MPCUTime' in l:
            ls = l.split()
            if 'LogStart' in l:
                MPCUTime[0]= int(ls[1])
            elif 'LogStop' in l:
                MPCUTime[1]= int(ls[1])
        if 'MDHTime' in l:
            ls = l.split()
            if 'LogStart' in l:
                MDHTime[0]= int(ls[1])
            elif 'LogStop' in l:
                MDHTime[1]= int(ls[1])

    return physio_type, MDHTime, sampling_rate, physio_signal


def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert Siemens physiology files to BIDS-compliant physiology recording')
    parser.add_argument('-i', '--infiles', nargs='+', required=True, help='.puls or .resp physio file(s)')
    parser.add_argument('-b', '--bidsprefix', required=True, help='Prefix of the BIDS file. It should match the _bold.nii.gz')
    args = parser.parse_args()

    # make sure output directory exists:
    odir = os.path.dirname(args.bidsprefix)
    if not os.path.exists(odir):
        os.makedirs(odir)

    pmu2bids( args.infiles, args.bidsprefix )

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()

