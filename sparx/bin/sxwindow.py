#!/usr/bin/env python
#
# Author: T. Durmaz 08/29/2014 (tunay.durmaz@uth.tmc.edu)
# Copyright (c) 2014 The University of Texas - Houston Medical School
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
import os, sys
import json
from optparse import OptionParser

from EMAN2 import EMData, Region, Util
from utilities import read_text_row, set_ctf
from filter import filt_gaussh
from EMAN2jsondb import *

from global_def import *
from emboxerbase import *

def main():
	progname = os.path.basename(sys.argv[0])
	usage = progname + " -c,--coord=coord  -f,--ctf=ctf_file  -m,--mic_dir=mic_dir  -i,--input_pixel=input_pixel  -o,--output_pixel=output_pixel"
	
	parser = OptionParser(usage, version=SPARXVERSION)

	parser.add_option('-c', '--coord', dest='coord', help='location where coordinates are located')
	parser.add_option('-f', '--ctf', dest='ctf_file', help='ctf information file')
	parser.add_option('-m', '--mic_dir', dest='mic_dir', help='micrograph location')
	parser.add_option('-i', '--input_pixel', dest='input_pixel', help='input pixel size', default=1)
	parser.add_option('-o', '--output_pixel', dest='output_pixel', help='output pixel size', default=1)
		
	(options, args) = parser.parse_args()	
	
	if len(args) > 1:
		print "\nusage: " + usage
		print "Please run '" + progname + " -h' for detailed options\n"
	else:		
		json_suffix='_info.json'
		fParticle_suffix = '_ptcls.hdf'
		
		for f in os.listdir(options.coord):
			if f.endswith(json_suffix):
				fName =  os.path.join(options.coord,f)
				fRoot =  f.strip(json_suffix)
				ff    = os.path.join(options.coord, fRoot + json_suffix)
		
				im = EMData(fRoot + '.hdf')
				js = js_open_dict(ff)["boxes"]
				
				x0=im.get_xsize()/2
				y0=im.get_ysize()/2				
				box_size = 64
				
				for i in range(len(js)):
					x = js[i][0]
					y = js[i][1]
					imn=Util.window(im,box_size, box_size, 1, int(x-x0),int(y-y0))
					imn.write_image(fRoot + fParticle_suffix, -1) #appending to the image stack

if __name__=='__main__':
	main()
