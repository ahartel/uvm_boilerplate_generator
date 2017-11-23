import os
import sys
import argparse
from uvm_file_strings import *
from makefile_strings import *

#
# Parse arguments
#
parser = argparse.ArgumentParser(description='Generate UVM boilerplate code.')
parser.add_argument('--short', dest='short', action='store',
                    help='Short name for the DUT', required=True)
parser.add_argument('--long', dest='long', action='store',
                    help='Long name of the DUT', required=True)
parser.add_argument('--target', dest='target', action='store',
                    help='Target directory', required=True)

args = parser.parse_args()
long_name = args.long
short_name = args.short
target_dir = args.target

#
# Create target directory if necessary
#
if not os.path.isdir(target_dir):
    print("Target directory {0} does not exist.".format(target_dir))
    resp = raw_input("Create it? [y to create, other to abort]")
    if resp == 'y':
        print("Creating {0}.".format(target_dir))
        os.makedirs(target_dir)
    else:
        print("Aborting")
        sys.exit(1)

templates = []
makefiles = []

gen_sv_filename = lambda key, lng: "{0}_{1}.sv".format(lng, key)
gen_make_filename = lambda key: "Makefile.{0}".format(key)
def open_file(target_dir, fname):
    filename = os.path.join(target_dir, fname)
    print "Writing file "+filename
    return open(filename, 'w')


templates.append(('tb_top', tb_string))
templates.append(('sequencer', sequencer_string))
templates.append(('driver', driver_string))
templates.append(('monitor', monitor_string))
templates.append(('agent', agent_string))
templates.append(('scoreboard', scoreboard_string))
templates.append(('env', env_string))
templates.append(('test', test_string))


makefiles.append(('ncsim', ncsim_string))
makefiles.append(('vcs', vcs_string))

#
# Generate sourcelist makefile
#
srclist_string = """
SRC = ../rtl/
SRCS = """
for key, _ in templates:
    srclist_string += gen_sv_filename(key, long_name)+""" \\
    """
makefiles.append(('srclist', srclist_string[:-6]))

#
# Write all files to disk
#
for key, val in templates:
    with open_file(target_dir, gen_sv_filename(key, long_name)) as fhndl:
        fhndl.write(val.format(long_name, short_name))

for key, val in makefiles:
    with open_file(target_dir, gen_make_filename(key)) as fhndl:
        fhndl.write(val.format(long_name, short_name))

with open_file(target_dir, 'init.sh') as fhndl:
    fhndl.write("""
export UVM_HOME=/hyperfast/home/ahartel/uvm/uvm-1.2
module load vcs/2017.03 incisiv/15.20""")

with open_file(target_dir, 'simvision.svcf') as fhndl:
    fhndl.write("""
set w [waveform new]
set id [waveform add -using $w -signals {{{0}_tb_top.clk}}]
# e.g. waveform format $id -radix {{my_mmap}}
set id [waveform add -using $w -signals {{{0}_tb_top.reset}}]
set id [waveform add -cdivider divider]
    """.format(long_name, short_name))
