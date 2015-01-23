#
# Author: Pawel A.Penczek, 09/09/2006 (Pawel.A.Penczek@uth.tmc.edu)
# Copyright (c) 2000-2006 The University of Texas - Houston Medical School
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
#

from global_def import *

def ali2d_single_iter(data, numr, wr, cs, tavg, cnx, cny, \
						xrng, yrng, step, nomirror = False, mode="F", CTF=False, \
						random_method="", T=1.0, ali_params="xform.align2d", delta = 0.0):
	"""
		single iteration of 2D alignment using ormq
		if CTF = True, apply CTF to data (not to reference!)
	"""
	from utilities import combine_params2, inverse_transform2, get_params2D, set_params2D
	from alignment import ormq, ornq

	if CTF:
		from filter  import filt_ctf

	# 2D alignment using rotational ccf in polar coords and quadratic interpolation
	cimage = Util.Polar2Dm(tavg, cnx, cny, numr, mode)
	Util.Frngs(cimage, numr)
	Util.Applyws(cimage, numr, wr)

	maxrin = numr[-1]
	sx_sum = 0.0
	sy_sum = 0.0
	nope = 0
	for im in xrange(len(data)):
		if CTF:
			#Apply CTF to image
			ctf_params = data[im].get_attr("ctf")
			ima = filt_ctf(data[im], ctf_params, True)
		else:
			ima = data[im]

		alpha, sx, sy, mirror, dummy = get_params2D(data[im], ali_params)
		alpha, sx, sy, mirror        = combine_params2(alpha, sx, sy, mirror, 0.0, -cs[0], -cs[1], 0)
		alphai, sxi, syi, scalei     = inverse_transform2(alpha, sx, sy)

		# align current image to the reference
		if random_method == "SHC":
			"""
			peaks = ormq_peaks(ima, cimage, xrng, yrng, step, mode, numr, cnx+sxi, cny+syi)
			[angt, sxst, syst, mirrort, peakt, select] = sim_anneal(peaks, T, step, mode, maxrin)
			[alphan, sxn, syn, mn] = combine_params2(0.0, -sxi, -syi, 0, angt, sxst, syst, mirrort)
			data[im].set_attr_dict({"select":select, "peak":peakt})
			set_params2D(data[im], [alphan, sxn, syn, mn, 1.0], ali_params)
			"""
			#  For shc combining of shifts is problematic as the image may randomly slide away and never come back.
			#  A possibility would be to reject moves that results in too large departure from the center.
			#  On the other hand, one cannot simply do searches around the proper center all the time,
			#    as if xr is decreased, the image cannot be brought back if the established shifts are further than new range
			olo = Util.shc(ima, [cimage], xrng, yrng, step, -1.0, mode, numr, cnx+sxi, cny+syi, "c1")
			##olo = Util.shc(ima, [cimage], xrng, yrng, step, -1.0, mode, numr, cnx, cny, "c1")
			if(data[im].get_attr("previousmax")<olo[5]):
				#[angt, sxst, syst, mirrort, peakt] = ormq(ima, cimage, xrng, yrng, step, mode, numr, cnx+sxi, cny+syi, delta)
				#print  angt, sxst, syst, mirrort, peakt,olo
				angt = olo[0]
				sxst = olo[1]
				syst = olo[2]
				mirrort = int(olo[3])
				# combine parameters and set them to the header, ignore previous angle and mirror
				[alphan, sxn, syn, mn] = combine_params2(0.0, -sxi, -syi, 0, angt, sxst, syst, mirrort)
				set_params2D(data[im], [alphan, sxn, syn, mn, 1.0], ali_params)
				##set_params2D(data[im], [angt, sxst, syst, mirrort, 1.0], ali_params)
				data[im].set_attr("previousmax",olo[5])
				##mn = sxn = syn = 0
				if mn == 0: sx_sum += sxn
				##if mirrort == 0: sx_sum += sxn
				else:       sx_sum -= sxn
				sy_sum += syn
			else:
				# Did not find a better peak, but we have to set shifted parameters, as the average shifted
				set_params2D(data[im], [alpha, sx, sy, mirror, 1.0], ali_params)
				nope += 1
		else:

			if nomirror:  [angt, sxst, syst, mirrort, peakt] = ornq(ima, cimage, xrng, yrng, step, mode, numr, cnx+sxi, cny+syi)
			else:	      [angt, sxst, syst, mirrort, peakt] = ormq(ima, cimage, xrng, yrng, step, mode, numr, cnx+sxi, cny+syi, delta)
			# combine parameters and set them to the header, ignore previous angle and mirror
			[alphan, sxn, syn, mn] = combine_params2(0.0, -sxi, -syi, 0, angt, sxst, syst, mirrort)
			set_params2D(data[im], [alphan, sxn, syn, mn, 1.0], ali_params)

			if mn == 0: sx_sum += sxn
			else:       sx_sum -= sxn
			sy_sum += syn

	return sx_sum, sy_sum, nope


def ali2d_single_iter_fast(data, dimage, params, numr, wr, cs, tavg, cnx, cny, \
							xrng, yrng, step, maxrange, nomirror = False, mode="F", \
							random_method="", T=1.0, ali_params="xform.align2d", delta = 0.0):
	"""
		single iteration of 2D alignment using ormq
		if CTF = True, apply CTF to data (not to reference!)
	"""
	from utilities import combine_params2, inverse_transform2, get_params2D, set_params2D
	from alignment import ormq, ornq

	# 2D alignment using rotational ccf in polar coords and quadratic interpolation
	cimage = Util.Polar2Dm(tavg, cnx, cny, numr, mode)
	Util.Frngs(cimage, numr)
	Util.Applyws(cimage, numr, wr)

	maxrin = numr[-1]
	#sx_sum = 0
	#sy_sum = 0
	for im in xrange(len(data)):
		#alpha, sx, sy, mirror, dummy = get_params2D(data[im], ali_params)
		#alpha, sx, sy, mirror        = combine_params2(alpha, sx, sy, mirror, 0.0, -cs[0], -cs[1], 0)
		#alphai, sxi, syi, scalei     = inverse_transform2(alpha, sx, sy)
		"""
		# align current image to the reference
		if random_method == "SA":
			peaks = ormq_peaks(ima, cimage, xrng, yrng, step, mode, numr, cnx+sxi, cny+syi)
			[angt, sxst, syst, mirrort, peakt, select] = sim_anneal(peaks, T, step, mode, maxrin)
			[alphan, sxn, syn, mn] = combine_params2(0.0, -sxi, -syi, 0, angt, sxst, syst, mirrort)
			data[im].set_attr_dict({"select":select, "peak":peakt})
			set_params2D(data[im], [alphan, sxn, syn, mn, 1.0], ali_params)
		else:
			if nomirror:  [angt, sxst, syst, mirrort, peakt] = ornq(ima, cimage, xrng, yrng, step, mode, numr, cnx+sxi, cny+syi)
			else:
		"""
		[angt, sxst, syst, mirrort, peakt] = ormq_fast(dimage[im], cimage, xrng, yrng, step, params[im][1], params[im][2], maxrange, numr, mode, delta)
		# combine parameters and set them to the header, ignore previous angle and mirror
		#[alphan, sxn, syn, mn] = combine_params2(0.0, -sxi, -syi, 0, angt, sxst, syst, mirrort)
		#set_params2D(data[im], [alphan, sxn, syn, mn, 1.0], ali_params)
		params[im] = [angt, sxst, syst, mirrort]

		#if mirrort == 0: sx_sum += sxst
		#else:            sx_sum -= sxst
		#sy_sum += syst

#	return sx_sum, sy_sum


def ang_n(tot, mode, maxrin):
	"""
	  Calculate angle based on the position of the peak
	"""
	from math import fmod
	if (mode == 'f' or mode == 'F'): return fmod(((tot-1.0) / maxrin+1.0)*360.0, 360.0)
	else:                            return fmod(((tot-1.0) / maxrin+1.0)*180.0, 180.0)

# Copy of this function is implemented in C++ in Util (Util.Applyws). It works much faster than this one.
'''
def Applyws(circ, numr, wr):
	"""
	  Apply weights to FTs of rings
	"""
	nring = len(numr)/3
	maxrin = numr[len(numr)-1]
	for i in xrange(nring):
		numr3i = numr[2+i*3]
		numr2i = numr[1+i*3]-1
		w = wr[i]
		circ[numr2i] *= w
		if (numr3i == maxrin): circ[numr2i+1] *= w
		else: circ[numr2i+1] *= 0.5*w
		for j in xrange(2,numr3i):
			jc = j+numr2i
			circ[jc] *= w
'''

def crit2d(args, data):
	#print  " AMOEBA ",args
	#  data: 0 - kb,  1 - mask, 2 - nima,  3 - current ave, 4 - current image in the gridding format
	#from utilities import info
	from fundamentals import rtshgkb
	mn = data[4].get_attr('mirror')
	temp = rtshgkb(data[4], args[0], args[1], args[2], data[0])
	if  mn: temp.process_inplace("xform.mirror", {"axis":'x'})
	#temp2 = data[3] + temp/data[2]
	temp2 = Util.madn_scalar(data[3], temp, 1.0/data[2]) 
	v = temp2.cmp("dot", temp2, {"negative":0, "mask":data[1]})
	#print  " AMOEBA ",args,mn,v
	return v


def eqproj_cascaded_ccc(args, data):
	from utilities     import peak_search, amoeba
	from fundamentals  import fft, ccf, fpol
	from alignment     import twoD_fine_search
	from statistics    import ccc
	from EMAN2 import Processor

	volft   = data[0]
	kb	    = data[1]
	prj	    = data[2]
	mask2D  = data[3]
	refi    = data[4]
	shift   = data[5]
	ts      = data[6]
	#print  "Input shift ",shift
	R = Transform({"type":"spider", "phi":args[0], "theta":args[1], "psi":args[2], "tx":0.0, "ty":0.0, "tz":0.0, "mirror":0, "scale":1.0})
	refprj = volft.extract_plane(R, kb)
	refprj.fft_shuffle()
	refprj.center_origin_fft()

	if(shift[0]!=0. or shift[1]!=0.):
		filt_params = {"filter_type" : Processor.fourier_filter_types.SHIFT,
				  "x_shift" : shift[0], "y_shift" : shift[1], "z_shift" : 0.0}
		refprj = Processor.EMFourierFilter(refprj, filt_params)

	refprj.do_ift_inplace()
	MM = refprj.get_ysize()
	refprj.set_attr_dict({'npad':2})
	refprj.depad()

	if ts==0.0:
		return ccc(prj, refprj, mask2D), shift

	refprj.process_inplace("normalize.mask", {"mask":mask2D, "no_sigma":1})
	Util.mul_img(refprj, mask2D)

	product = ccf(fpol(refprj, MM, MM, 0, False), data[4])
	nx = product.get_ysize()
	sx = nx//2
	sy = sx
	# This is for debug purpose
	#if ts == -1.0:
	#	return twoD_fine_search([sx, sy], [product, kb, -ts, sx]), shift

	ts2 = 2*ts
	data2 = [product, kb, 1.1*ts2, sx]
	size_of_ccf = 2*int(ts+1.5)+1
	pk = peak_search(Util.window(product, size_of_ccf, size_of_ccf,1,0,0,0))
	# adjust pk to correspond to large ccf
	pk[0][1] = sx + pk[0][4]
	pk[0][2] = sy + pk[0][5]
	#print  " pk ",pk
	# step in amoeba should be vicinity of the peak, within one pixel or even less.
	ps = amoeba([pk[0][1], pk[0][2]], [1.1, 1.1], twoD_fine_search, 1.e-4, 1.e-4, 500, data2)
	#print  " ps ",ps,[sx,sy], data2, shift
	#print  " if ",abs(sx-ps[0][0]),abs(sy-ps[0][1]),ts2
	if(  abs(sx-ps[0][0]) >= ts2 or abs(sy-ps[0][1]) >= ts2 ):
		return  twoD_fine_search([sx,sy], data2), shift
	else:
		s2x = (sx-ps[0][0])/2 + shift[0]
		s2y = (sy-ps[0][1])/2 + shift[1]
		#print  " B ",ps[1], [s2x, s2y]
		return ps[1], [s2x, s2y]

def twoD_fine_search(args, data):
	if(abs(args[0]-data[3]) > data[2] or abs(args[1]-data[3]) > data[2]): return -1.0e22
	return data[0].get_pixel_conv7(args[0], args[1], 0.0, data[1])

def eqproj(args, data):
	from projection import prgs
	#from fundamentals import cyclic_shift
	#from utilities import info
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask,
	#  args: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy
	prj = prgs(data[0], data[1], args)

	# the idea is for the mask to "follow" the projection
	#isx = int(args[3]+100000.5)-100000 # this is a strange trick to take care of negative sx
	#isy = int(args[4]+100000.5)-100000
	#shifted_mask = cyclic_shift(data[3], isx, isy)
	#info(proj)
	#info(data[2])
	#info(proj,None,"proj")
	#info(data[2],None,"data[2")
	#info(data[3],None,"data[3")

	#info(shifted_mask,None,"shifted mask")
	#v = -proj.cmp("SqEuclidean", data[2], {"mask":shifted_mask})
	#        CURRENTLY THE DISTANCE IS cross-correlation coefficient
	#v = -prj.cmp("SqEuclidean", data[2], {"mask":data[3]})
	v = prj.cmp("ccc", data[2], {"mask":data[3], "negative":0})
	#v = proj.cmp("ccc", data[2], {"mask":shifted_mask, "negative":0})
	#print  " AMOEBA o", args, v
	return v

def eqprojDot(args, data):
	from projection import project
	from filter import filt_ctf
	phi = args[0]
	tht = args[1]
	psi = args[2]
	vol = data[0]
	img = data[1]
	s2x = data[2]
	s2y = data[3]
	msk = data[4]
	CTF = data[5]
        ou  = data[6]

	tmp = img.process( "normalize.mask", {"mask":msk, "no_sigma":0} )
	ref = project( vol, [phi,tht,psi,-s2x,-s2y], ou )
	if CTF:
		ctf = img.get_attr( "ctf" )
		ref = filt_ctf( ref, ctf )
	return ref.cmp( "dot", tmp, {"mask":msk, "negative":0} )

def eqprojEuler(args, data):
	from projection import prgs
	prj = prgs(data[0], data[1], [args[0], args[1], args[2], data[3], data[4]])
	v = prj.cmp("ccc", data[2], {"mask":data[5], "negative":0})
	return v

def symm_func(args, data):
	from utilities import sym_vol
	from fundamentals  import  rot_shift3D
	sym = sym_vol(rot_shift3D(data[0], args[0], args[1], args[2]), data[2])
	avg = sym.cmp("dot",sym,{"mask":data[1], "negative":0})
	print avg, args
	return avg

def find_symm(vol, mask, sym_gp, phi, theta, psi, scale, ftolerance, xtolerance):
	
	from utilities import amoeba, model_circle
	from alignment import symm_func
	args   = [phi, theta, psi]
	data   = [vol, mask, sym_gp]
	result = amoeba(args, scale, symm_func, ftolerance, xtolerance, 500, data)

	return result

#   Implemented in c in utli_sparx
#  Helper functions for ali2d_r
def kbt(nx,npad=2):
	# padd two times
	N=nx*npad
	# support of the window
	K=6
	alpha=1.75
	r=nx/2
	v=K/2.0/N
	return Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
     

#  AP stuff  01/18/06
    
    
def log2(n):
	""" Returns the smallest power by which 2 has to be raised to obtain
	    an integer less equal n
	"""
	m = 1
	k =-1
	while (m <= n):
		i = m
		k +=1
		m = 2*i
	return k
    
def Numrinit(first_ring, last_ring, skip=1, mode="F"):
	"""This function calculates the necessary information for the 2D 
	   polar interpolation. For each ring, three elements are recorded:
	   numr[i*3]:  Radius of this ring
	   numr[i*3+1]: Total number of samples of all inner rings+1
	   		(Or, the beginning point of this ring)
	   numr[i*3+2]: Number of samples of this ring. This number is an 
	   		FFT-friendly power of the 2.
			
	   "F" means a full circle interpolation
	   "H" means a half circle interpolation
	"""
	MAXFFT=32768
	from math import pi

	if (mode == 'f' or mode == 'F'): dpi = 2*pi
	else:                            dpi = pi
	numr = []
	lcirc = 1
	for k in xrange(first_ring, last_ring+1, skip):
		numr.append(k)
		jp = int(dpi * k+0.5)
		ip = 2**(log2(jp)+1)  # two times oversample each ring
		if (k+skip <= last_ring and jp > ip+ip//2): ip=min(MAXFFT,2*ip)
		if (k+skip  > last_ring and jp > ip+ip//5): ip=min(MAXFFT,2*ip)

		numr.append(lcirc)
		numr.append(ip)
		lcirc += ip

	return  numr
'''
def Numrinit(first_ring, last_ring, skip=1, mode="F"):
	#  This is to test equal length rings
	"""This function calculates the necessary information for the 2D 
	   polar interpolation. For each ring, three elements are recorded:
	   numr[i*3]:  Radius of this ring
	   numr[i*3+1]: Total number of samples of all inner rings+1
	   		(Or, the beginning point of this ring)
	   numr[i*3+2]: Number of samples of this ring. This number is an 
	   		FFT-friendly power of the 2.
			
	   "F" means a full circle interpolation
	   "H" means a half circle interpolation
	"""
	MAXFFT=32768
	from math import pi

	if (mode == 'f' or mode == 'F'): dpi = 2*pi
	else:                            dpi = pi
	numr = []
	lcirc = 1
	#  This is for testing equal length rings
	ip = 128
	for k in xrange(first_ring, last_ring+1, skip):
		numr.append(k)
		numr.append(lcirc)
		numr.append(ip)
		lcirc += ip		
	return  numr
'''	
def ringwe(numr, mode="F"):
	"""
	   Calculate ring weights for rotational alignment
	   The weights are r*delta(r)*delta(phi).
	"""
	from math import pi
	if (mode == 'f' or mode == 'F'):
		dpi = 2*pi
	else:
		dpi = pi
	nring = len(numr)/3
	wr=[0.0]*nring
	maxrin = float(numr[len(numr)-1])
	for i in xrange(0,nring): wr[i] = numr[i*3]*dpi/float(numr[2+i*3])*maxrin/float(numr[2+i*3])
	return wr

def ornq(image, crefim, xrng, yrng, step, mode, numr, cnx, cny):
	"""Determine shift and rotation between image and reference image (refim)
	   no mirror
		quadratic interpolation
		cnx, cny in FORTRAN convention
	"""
	from math import pi, cos, sin, radians
	from alignment import ang_n
	#from utilities import info
	#print "ORNQ"
	peak = -1.0E23
	ky = int(2*yrng/step+0.5)/2
	kx = int(2*xrng/step+0.5)/2
	
	for i in xrange(-ky, ky+1):
		iy = i*step
		for j in xrange(-kx, kx+1):
			ix = j*step
			cimage = Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
			Util.Frngs(cimage, numr)
			retvals = Util.Crosrng_e(crefim, cimage, numr, 0)
			qn = retvals["qn"]
			if qn >= peak:
				sx = -ix
				sy = -iy
				ang = ang_n(retvals["tot"], mode, numr[-1])
				peak = qn
	# mirror is returned as zero for consistency
	mirror = 0
	co =  cos(radians(ang))
	so = -sin(radians(ang))
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang, sxs, sys, mirror, peak


def ormq(image, crefim, xrng, yrng, step, mode, numr, cnx, cny, delta = 0.0):
	"""Determine shift and rotation between image and reference image (crefim)
		crefim should be as FT of polar coords with applied weights
	        consider mirror
		quadratic interpolation
		cnx, cny in FORTRAN convention
	"""
	from math import pi, cos, sin, radians
	#print "ORMQ"
	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	for i in xrange(-ky, ky+1):
		iy = i*step
		for j in xrange(-kx, kx+1):
			ix = j*step
			cimage = Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
			Util.Frngs(cimage, numr)
			# The following code it used when mirror is considered
			if delta == 0.0:
				retvals = Util.Crosrng_ms(crefim, cimage, numr)
			else:
				retvals = Util.Crosrng_ms_delta(crefim, cimage, numr, 0.0, delta)
			qn = retvals["qn"]
			qm = retvals["qm"]
			if (qn >= peak or qm >= peak):
				sx = -ix
				sy = -iy
				if (qn >= qm):
					ang = ang_n(retvals["tot"], mode, numr[-1])
					peak = qn
					mirror = 0
				else:
					ang = ang_n(retvals["tmt"], mode, numr[-1])
					peak = qm
					mirror = 1
			'''
			# The following code is used when mirror is not considered
			retvals = Util.Crosrng_e(crefim, cimage, numr, 0)
			qn = retvals["qn"]
			if qn >= peak:
		 		sx = -ix
		 		sy = -iy
		 		ang = ang_n(retvals["tot"], mode, numr[-1])
		 		peak = qn
		 		mirror = 0
			'''
	co  =  cos(radians(ang))
	so  = -sin(radians(ang))
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang, sxs, sys, mirror, peak

def ormq_fast(dimage, crefim, xrng, yrng, step, isx, isy, maxrange, numr, mode, delta = 0.0):
	"""Determine shift and rotation between image and reference image (crefim)
		crefim should be as FT of polar coords with applied weights
	        consider mirror
		quadratic interpolation
		cnx, cny in FORTRAN convention
	"""
	#from math import pi, cos, sin, radians
	#print "ORMQ_FAST"
	#maxrange = 4
	peak = -1.0E23
	#print ' isx, isy',isx, isy
	ky = int(yrng)#int(2*yrng/step+0.5)//2
	kx = int(xrng)#int(2*xrng/step+0.5)//2
	#print  ' y ',max(-ky+isy,-maxrange), min(ky+isy+1,maxrange+1)
	for j in xrange(max(-ky+isy,-maxrange), min(ky+isy+1,maxrange+1)):
		#iy = i*step
		#print  ' x ',max(-kx+isx,-maxrange), min(kx+isx+1,maxrange+1)
		for i in xrange(max(-kx+isx,-maxrange), min(kx+isx+1,maxrange+1)):
			#ix = j*step
			# The following code is used when mirror is considered
			if delta == 0.0: retvals = Util.Crosrng_ms(crefim, dimage[i+maxrange][j+maxrange], numr)
			else:            retvals = Util.Crosrng_ms_delta(crefim, dimage[i+maxrange][j+maxrange], numr, 0.0, delta)
			qn = retvals["qn"]
			qm = retvals["qm"]
			if (qn >= peak or qm >= peak):
				sx = i
				sy = j
				if (qn >= qm):
					ang = ang_n(retvals["tot"], mode, numr[-1])
					peak = qn
					mirror = 0
				else:
					ang = ang_n(retvals["tmt"], mode, numr[-1])
					peak = qm
					mirror = 1
	"""
	co =  cos(radians(ang))
	so = -sin(radians(ang))
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	"""
	if( peak < -1.0e5):
		print " ORMQ_FAST failed, most likelt due to search ranges "
		from sys import exit
		exit()
	return  ang, sx, sy, mirror, peak
			

def ormq_peaks(image, crefim, xrng, yrng, step, mode, numr, cnx, cny):
	"""
	Determine shift and rotation between image and reference image (crefim)
	crefim should be as FT of polar coords with applied weights
	consider mirror
	quadratic interpolation
	cnx, cny in FORTRAN convention
	"""
	from utilities import peak_search

	ccfs = EMData()
	ccfm = EMData()
	Util.multiref_peaks_ali2d(image, crefim, xrng, yrng, step, mode, numr, cnx, cny, ccfs, ccfm)

	peaks = peak_search(ccfs, 1000)
	for i in xrange(len(peaks)):	peaks[i].append(0)

	peakm = peak_search(ccfm, 1000)
	for i in xrange(len(peakm)):	peakm[i].append(1)
	peaks += peakm

	return peaks


'''
def process_peak_1d_pad(peaks, step, mode, numr, nx):
	from math import pi, cos, sin
	
	peak_num = len(peaks)
	maxrin = numr[-1]
	for i in xrange(peak_num):
		peaks[i][1]= ang_n(peaks[i][1]+1-nx/2, mode, maxrin)
	peaks.sort(reverse=True)
	
	return peaks

def find_position(list_a, t):
	"""
	The function determines how many elements of list_a is larger or equal than t.
	Here we assume list_a is sorted reversely.
	"""
	if list_a[0] < t:
		return 0
	elif list_a[-1] >= t:
		return len(list_a)
	else:
		K = len(list_a)
		k_min = 1
		k_max = K-1
		while k_min != k_max:
			k = (k_min+k_max)/2
			if list_a[k] < t:
				if list_a[k-1] >= t:
					k_min = k
					k_max = k
				else:
					k_max = k-1
			else:
				k_min = k+1
		return k_min


def select_major_peaks(g, max_major_peaks, min_height, dim):

	from filter import filt_gaussl
	from fundamentals import fft
	from utilities import peak_search
	
	G = fft(g)
	
	found = False
	min_fl = 0.001
	max_fl = 0.5
	
	while found == False:
		fl = (min_fl+max_fl)/2
		peakg = peak_search(fft(filt_gaussl(G, fl)), 1000)
		K = len(peakg)
		list_a = [0.0]*K
		for i in xrange(K):  list_a[i] = peakg[i][dim+1]
		k = find_position(list_a, min_height)
		if k > max_major_peaks: 
			max_fl = fl
		elif k < max_major_peaks:
			min_fl = fl
		else:
			found = True
		if max_fl - min_fl < 0.001: found = True
		 
	return peakg[0:k] 


def select_major_peaks_Gaussian_fitting(peak):

	# Generate the histogram of the angle
	ang_bin = [0]*30
	for i in xrange(len(angle)):
		#angle.append(peak[i][1])
		bin_num = int(angle[i]/12)
		ang_bin[bin_num] += 1
	ang_bin_index = []
	for i in xrange(30):
		ang_bin_index.append([ang_bin[i], i])
	ang_bin_index.sort(reverse=True)
	print ang_bin
	print ang_bin_index
	
	K = 5
	A = [0.0]*K
	mu = [0.0]*K
	sigma = [0.0]*K
	
	for k in xrange(K):
		A[k] = ang_bin_index[k][0]
		mu[k] = ang_bin_index[k][1]*12+6
		sigma[k] = 5.0
	
	print A, mu, sigma 
	
	
	return []


def ormq_peaks_major(image, crefim, xrng, yrng, step, mode, numr, cnx, cny):
	"""
	Determine shift and rotation between image and reference image (crefim)
	crefim should be as FT of polar coords with applied weights
	consider mirror
	quadratic interpolation
	cnx, cny in FORTRAN convention
	"""
	from utilities import peak_search, pad
	
	ccfs = EMData()
	ccfm = EMData()
	ccfs_compress = EMData()
	ccfm_compress = EMData()

	Util.multiref_peaks_compress_ali2d(image, crefim, xrng, yrng, step, mode, numr, cnx, cny, ccfs, ccfm, ccfs_compress, ccfm_compress)
	
	nx = ccfs.get_xsize()
	ny = ccfs.get_ysize()
	nz = ccfs.get_zsize()

	peaks = peak_search(ccfs, 1000)
	peakm = peak_search(ccfm, 1000)

	peaks = process_peak(peaks, step, mode, numr)
	peakm = process_peak(peakm, step, mode, numr)

	max_major_peaks = 5
	min_height = 0.7
	
	peaks_major = select_major_peaks(pad(ccfs_compress, nx*2), max_major_peaks, min_height, 1)
	peakm_major = select_major_peaks(pad(ccfm_compress, nx*2), max_major_peaks, min_height, 1)

	peaks_major = process_peak_1d_pad(peaks_major, step, mode, numr, nx)
	peakm_major = process_peak_1d_pad(peakm_major, step, mode, numr, nx)	

	"""
	ccfs_compress = EMData(nx, 1, 1, True)
	ccfm_compress = EMData(nx, 1, 1, True)

	for x in xrange(nx):
		slices = Util.window(ccfs, 1, ny-2, nz-2, x-nx/2, 0, 0)
		slicem = Util.window(ccfm, 1, ny-2, nz-2, x-nx/2, 0, 0)
		
		[means, dummy, dummy, dummy] = Util.infomask(slices, None, True)
		[meanm, dummy, dummy, dummy] = Util.infomask(slicem, None, True)
		
		ccfs_compress.set_value_at(x, 0, 0, means)
		ccfm_compress.set_value_at(x, 0, 0, meanm)

	peaks_major = select_major_peaks_Gaussian_fitting(peaks)
	peakm_major = select_major_peaks_Gaussian_fitting(peakm)
	
	fs = Util.window(ccfs, nx, ny-2, nz-2, 0, 0, 0)
	fm = Util.window(ccfm, nx, ny-2, nz-2, 0, 0, 0)

	dummy1, dummy2, mins, dummy3 = Util.infomask(fs, None, True)
	dummy1, dummy2, minm, dummy3 = Util.infomask(fm, None, True)

	gs = threshold_to_minval(ccfs, mins)
	gm = threshold_to_minval(ccfm, minm)

	peaks_major = select_major_peaks(gs, max_major_peaks, min_height, 3)
	peakm_major = select_major_peaks(gm, max_major_peaks, min_height, 3)
	
	peaks_major = select_major_peaks(pad(ccfs_compress, nx*2), max_major_peaks, min_height, 1)
	peakm_major = select_major_peaks(pad(ccfm_compress, nx*2), max_major_peaks, min_height, 1)
	time4 = time()
	peaks = peak_search(ccfs, 1000)
	peakm = peak_search(ccfm, 1000)
	time5 = time()
	peaks = process_peak(peaks, step, mode, numr)
	peakm = process_peak(peakm, step, mode, numr)
	peaks_major = process_peak_1d_pad(peaks_major, step, mode, numr)
	peakm_major = process_peak_1d_pad(peakm_major, step, mode, numr)	
	time6 = time()
	"""
	
	return peaks, peakm, peaks_major, peakm_major
'''


def select_k(dJe, T):
	"""
	This routine is used in simulated annealing to select a random path
	based on the weight of the each path and the temperature.
	"""
	from random import random

	K = len(dJe)

	p  = [0.0] * K
	ut = 1.0/T
	for k in xrange(K): p[k] = dJe[k]**ut

	sumq = float(sum(p))
	for k in xrange(K): p[k] /= sumq
	#print  p

	for k in xrange(1, K-1): p[k] += p[k-1]
	# the next line looks strange, but it assures that at least the lst element is selected
	p[K-1] = 2.0

	pb = random()
	select = 0

	while(p[select] < pb):  select += 1
	#select = 0
	return select

def sim_anneal(peaks, T, step, mode, maxrin):
	from random import random
	from math import pi, cos, sin

	peaks.sort(reverse=True)

	if T < 0.0:
		select = int(-T)
		ang = ang_n(peaks[select][1]+1, mode, maxrin)
		sx  = -peaks[select][6]*step
		sy  = -peaks[select][7]*step

		co =  cos(ang*pi/180.0)
		so = -sin(ang*pi/180.0)
		sxs = sx*co - sy*so
		sys = sx*so + sy*co

		mirror = peaks[select][8]
		peak   = peaks[select][0]/peaks[0][0]
	elif T == 0.0:
		select = 0
	
		ang = ang_n(peaks[select][1]+1, mode, maxrin)
		sx  = -peaks[select][6]*step
		sy  = -peaks[select][7]*step

		co =  cos(ang*pi/180.0)
		so = -sin(ang*pi/180.0)
		sxs = sx*co - sy*so
		sys = sx*so + sy*co

		mirror = peaks[select][8]
		peak   = peaks[select][0]/peaks[0][0]
	else:
		K = len(peaks)
		qt = peaks[0][0]
		p  = [0.0] * K
		ut = 1.0/T
		for k in xrange(K): p[k] = (peaks[k][0]/qt)**ut

		sumq = float(sum(p))
		cp  = [0.0] * K
		for k in xrange(K):
			p[k] /= sumq
			cp[k] = p[k]
		#print  p

		for k in xrange(1, K-1): cp[k] += cp[k-1]
		# the next line looks strange, but it assures that at least the lst element is selected
		cp[K-1] = 2.0

		pb = random()
		select = 0
		while(cp[select] < pb):  select += 1

		ang = ang_n(peaks[select][1]+1, mode, maxrin)
		sx  = -peaks[select][6]*step
		sy  = -peaks[select][7]*step

		co =  cos(ang*pi/180.0)
		so = -sin(ang*pi/180.0)
		sxs = sx*co - sy*so
		sys = sx*so + sy*co

		mirror = peaks[select][8]
		peak   = p[select]
		
	return  ang, sxs, sys, mirror, peak, select

def sim_ccf(peaks, T, step, mode, maxrin):
	from random import random
	from math import pi, cos, sin

	if T < 0.0:
		select = int(-T)
		ang = ang_n(peaks[select][1]+1, mode, maxrin)
		sx  = -peaks[select][2]*step
		sy  = -peaks[select][3]*step

		co =  cos(ang*pi/180.0)
		so = -sin(ang*pi/180.0)
		sxs = sx*co - sy*so
		sys = sx*so + sy*co

		mirror = peaks[select][4]
		peak   = peaks[select][0]/peaks[0][0]
	elif T == 0.0:
		select = 0
	
		ang = ang_n(peaks[select][1]+1, mode, maxrin)
		sx  = -peaks[select][2]*step
		sy  = -peaks[select][3]*step

		co =  cos(ang*pi/180.0)
		so = -sin(ang*pi/180.0)
		sxs = sx*co - sy*so
		sys = sx*so + sy*co

		mirror = peaks[select][4]
		peak   = peaks[select][0]/peaks[0][0]
	else:
		select = int(peaks[5])
		ang = ang_n(peaks[1]+1, mode, maxrin)
		sx  = -peaks[2]*step
		sy  = -peaks[3]*step

		co =  cos(ang*pi/180.0)
		so = -sin(ang*pi/180.0)
		sxs = sx*co - sy*so
		sys = sx*so + sy*co

		mirror = int(peaks[4])
		peak   = peaks[0]

	return  ang, sxs, sys, mirror, peak, select


def sim_anneal2(peaks, Iter, T0, F, SA_stop):
	from math import exp, pow
	from random import random

	# Determine the current temperature
	T = T0*pow(F, Iter)	

	K = len(peaks)
	p = [0.0] * K

	if T > 0.0001 and Iter < SA_stop:
	
		dJe = [0.0]*K
		for k in xrange(K):
			dJe[k] = peaks[k][0]/peaks[0][0]

		# q[k]
		q      = [0.0] * K
		arg    = [0.0] * K
		maxarg = 0
		for k in xrange(K):
			arg[k] = dJe[k] / T
			if arg[k] > maxarg: maxarg = arg[k]
		limarg = 200
		if maxarg > limarg:
			sumarg = float(sum(arg))
			for k in xrange(K): q[k] = exp(arg[k] * limarg / sumarg)
		else:
			for k in xrange(K): q[k] = exp(arg[k])

		sumq = float(sum(q))
		for k in xrange(K):
			p[k] = q[k] / sumq
	else:
		p[0] = 1.0
	
	return p


def sim_anneal3(peaks, peakm, peaks_major, peakm_major, Iter, T0, F, SA_stop):
	from math import pow, sin, sqrt, pi
	from random import random

	# Determine the current temperature
	T = T0*pow(F, Iter)
	max_peak = 5
	DEG_to_RAD = pi/180.0

	dim = 1

	if T > 0.001 and Iter < SA_stop:

		K = len(peaks_major)
		dJe = [0.0]*K
		for k in xrange(K):	dJe[k] = peaks_major[k][dim+1]
		
		select_major = select_k(dJe, T)
		
		ang_m = peaks_major[select_major][1]
		#sx_m = peaks_major[select_major][6]
		#sy_m = peaks_major[select_major][7]
		
		neighbor = []
		for i in xrange(len(peaks)):
			ang = peaks[i][1]
			#sx = peaks[i][6]
			#sy = peaks[i][7]		
			dist = 64*abs(sin((ang-ang_m)/2*DEG_to_RAD))#+sqrt((sx-sx_m)**2+(sy-sy_m)**2)
			neighbor.append([dist, i])
		neighbor.sort()

		dJe = [0.0]*max_peak
		for k in xrange(max_peak):   dJe[k] = peaks[neighbor[k][1]][4]
		select_s = neighbor[select_k(dJe, T)][1]
			
		#############################################################################################################

		K = len(peakm_major)
		dJe = [0.0]*K
		for k in xrange(K): 	dJe[k] = peakm_major[k][dim+1]

		select_major = select_k(dJe, T)
				
		ang_m = peakm_major[select_major][1]
		#sx_m = peakm_major[select_major][6]
		#sy_m = peakm_major[select_major][7]
		
		neighbor = []
		for i in xrange(len(peakm)):
			ang = peakm[i][1]
			#sx = peakm[i][6]
			#sy = peakm[i][7]		
			dist = 64*abs(sin((ang-ang_m)/2*DEG_to_RAD))#+sqrt((sx-sx_m)**2+(sy-sy_m)**2)
			neighbor.append([dist, i])
		neighbor.sort()

		dJe = [0.0]*max_peak
		for k in xrange(max_peak):   dJe[k] = peakm[neighbor[k][1]][4]
		select_m = neighbor[select_k(dJe, T)][1]

		ps = peaks[select_s][0]
		pm = peakm[select_m][0]
		pk = select_k([1.0, min(ps/pm, pm/ps)], T)
		
		if ps > pm and pk == 0 or ps < pm and pk == 1: use_mirror = 0
		else: use_mirror = 1
	else:
		select_s = 0
		select_m = 0
		ps = peaks[select_s][0]
		pm = peakm[select_m][0]
		if ps > pm:
			use_mirror = 0
		else:
			use_mirror = 1
	
	if use_mirror == 0:
		select = select_s	
		ang = peaks[select][1]
		sx  = peaks[select][6]
		sy  = peaks[select][7]
		mirror = 0
		peak = peaks[select][0]
	else:
		select = select_m
		ang = peakm[select][1]
		sx  = peakm[select][6]
		sy  = peakm[select][7]
		mirror = 1
		peak = peakm[select][0]
		
	return  ang, sx, sy, mirror, peak, select


def prep_vol_kb(vol, kb, npad=2):
	# prepare the volume
	volft = vol.copy()
	volft.divkbsinh(kb)
	volft = volft.norm_pad(False, npad)
	volft.do_fft_inplace()
	volft.center_origin_fft()
	volft.fft_shuffle()
	return  volft

def prepare_refrings( volft, kb, nz = -1, delta = 2.0, ref_a = "P", sym = "c1", numr = None, MPI=False, \
						phiEqpsi = "Minus", kbx = None, kby = None, initial_theta = None, \
						delta_theta = None, ant = -1.0):
	"""
		Generate quasi-evenly distributed reference projections converted to rings
		ant - neighborhood for local searches.  I believe the fastest way to deal with it in case of point-group symmetry
		        it to generate cushion projections within an/2 of the border of unique zone
	"""
	from projection   import prep_vol, prgs
	from applications import MPI_start_end
	from utilities    import even_angles, getfvec
	from types        import BooleanType

	# mpi communicator can be sent by the MPI parameter
	if type(MPI) is BooleanType:
		if MPI:
			from mpi import MPI_COMM_WORLD
			mpi_comm = MPI_COMM_WORLD
	else:
		mpi_comm = MPI
		MPI = True

	mode = "F"

	from types import ListType
	if(type(ref_a) is ListType):
		# if ref_a is  list, it has to be a list of projection directions, use it
		ref_angles = ref_a
	else:
		# generate list of Eulerian angles for reference projections
		#  phi, theta, psi
		if initial_theta is None:
			ref_angles = even_angles(delta, symmetry=sym, method = ref_a, phiEqpsi = phiEqpsi)
		else:
			if delta_theta is None: delta_theta = 1.0
			ref_angles = even_angles(delta, theta1 = initial_theta, theta2 = delta_theta, symmetry=sym, method = ref_a, phiEqpsi = phiEqpsi)
	wr_four  = ringwe(numr, mode)
	cnx = nz//2 + 1
	cny = nz//2 + 1
	num_ref = len(ref_angles)

	if MPI:
		from mpi import mpi_comm_rank, mpi_comm_size
		myid = mpi_comm_rank( mpi_comm )
		ncpu = mpi_comm_size( mpi_comm )
	else:
		ncpu = 1
		myid = 0
	
	ref_start, ref_end = MPI_start_end(num_ref, ncpu, myid)

	refrings = []     # list of (image objects) reference projections in Fourier representation

	sizex = numr[len(numr)-2] + numr[len(numr)-1]-1

	for i in xrange(num_ref):
		prjref = EMData()
		prjref.set_size(sizex, 1, 1)
		refrings.append(prjref)

	if kbx is None:
		for i in xrange(ref_start, ref_end):
			prjref = prgs(volft, kb, [ref_angles[i][0], ref_angles[i][1], ref_angles[i][2], 0.0, 0.0])
			cimage = Util.Polar2Dm(prjref, cnx, cny, numr, mode)  # currently set to quadratic....
			Util.Normalize_ring(cimage, numr)
			Util.Frngs(cimage, numr)
			Util.Applyws(cimage, numr, wr_four)
			refrings[i] = cimage
	else:
		for i in xrange(ref_start, ref_end):
			prjref = prgs(volft, kb, [ref_angles[i][0], ref_angles[i][1], ref_angles[i][2], 0.0, 0.0], kbx, kby)
			cimage = Util.Polar2Dm(prjref, cnx, cny, numr, mode)  # currently set to quadratic....
			Util.Normalize_ring(cimage, numr)
			Util.Frngs(cimage, numr)
			Util.Applyws(cimage, numr, wr_four)
			refrings[i] = cimage

	if MPI:
		from utilities import bcast_EMData_to_all
		for i in xrange(num_ref):
			for j in xrange(ncpu):
				ref_start, ref_end = MPI_start_end(num_ref, ncpu, j)
				if i >= ref_start and i < ref_end: rootid = j
			bcast_EMData_to_all(refrings[i], myid, rootid, comm=mpi_comm)

	for i in xrange(len(ref_angles)):
		n1,n2,n3 = getfvec(ref_angles[i][0], ref_angles[i][1])
		refrings[i].set_attr_dict( {"phi":ref_angles[i][0], "theta":ref_angles[i][1], "psi":ref_angles[i][2], "n1":n1, "n2":n2, "n3":n3} )

	return refrings

def refprojs( volft, kb, ref_angles, cnx, cny, numr, mode, wr ):
	from projection		import prgs
	from utilities		import getfvec

	ref_proj_rings = []     # list of (image objects) reference projections in Fourier representation
	for i in xrange(len(ref_angles)):
		#prjref = project(volref, [ref_angles[i][0], ref_angles[i][1], ref_angles[i][2], 0.0, 0.0], last_ring)
		prjref = prgs(volft, kb, [ref_angles[i][0], ref_angles[i][1], ref_angles[i][2], 0.0, 0.0])
		cimage = Util.Polar2Dm(prjref, cnx, cny, numr, mode)  # currently set to quadratic....
		Util.Normalize_ring(cimage, numr)
		Util.Frngs(cimage, numr)
		Util.Applyws(cimage, numr, wr)
		ref_proj_rings.append(cimage)
		n1,n2,n3 = getfvec(ref_angles[i][0], ref_angles[i][1])
		ref_proj_rings[-1].set_attr_dict( {"phi":ref_angles[i][0], "theta":ref_angles[i][1], "psi":ref_angles[i][2], "n1":n1, "n2":n2, "n3":n3} )

	return ref_proj_rings

def proj_ali_incore_chunks(data, refrings, numr, xrng, yrng, step, finfo=None):
	from utilities    import inverse_transform2
	from EMAN2 import Vec2f

	ID = data.get_attr("ID")
	if finfo:
		from utilities    import get_params_proj
		phi, theta, psi, s2x, s2y = get_params_proj(data)
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, s2x, s2y))
		finfo.flush()

	mode = "F"
	#  center is in SPIDER convention
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	cnx  = nx//2 + 1
	cny  = ny//2 + 1

	#phi, theta, psi, sxo, syo = get_params_proj(data)
	t1 = data.get_attr("xform.projection")
	dp = t1.get_params("spider")
	#[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d(data, refrings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)

	max_peak = 0
	num_refrings = len(refrings)
	for i in xrange(num_refrings):
		[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d(data, refrings[i], xrng, yrng, step, mode, numr, cnx+dp["tx"], cny+dp["ty"])
		if peak > max_peak:
 			res = [ang, sxs, sys, mirror, iref, peak]
 			max_peak = peak
	[ang, sxs, sys, mirror, iref, peak] = res
	#print ang, sxs, sys, mirror, iref, peak
	iref = int(iref)
	#[ang,sxs,sys,mirror,peak,numref] = apmq(projdata[imn], ref_proj_rings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
	#ang = (ang+360.0)%360.0
	# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
	#  What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
	angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
	if mirror:
		phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
		theta = 180.0-refrings[iref].get_attr("theta")
		psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
		s2x   = sxb - dp["tx"]
		s2y   = syb - dp["ty"]
	else:
		phi   = refrings[iref].get_attr("phi")
		theta = refrings[iref].get_attr("theta")
		psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb - dp["tx"]
		s2y   = syb - dp["ty"]
	#set_params_proj(data, [phi, theta, psi, s2x, s2y])
	t2 = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
	t2.set_trans(Vec2f(-s2x, -s2y))
	data.set_attr("xform.projection", t2)
	data.set_attr("referencenumber", iref)
	from pixel_error import max_3D_pixel_error
	pixel_error = max_3D_pixel_error(t1, t2, numr[-3])

	if finfo:
		finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f  %11.3e\n\n" %(phi, theta, psi, s2x, s2y, peak, pixel_error))
		finfo.flush()

	return peak, pixel_error

def proj_ali_incore(data, refrings, numr, xrng, yrng, step, finfo=None):
	from utilities    import inverse_transform2
	from EMAN2 import Vec2f

	ID = data.get_attr("ID")
	if finfo:
		from utilities    import get_params_proj
		phi, theta, psi, s2x, s2y = get_params_proj(data)
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, s2x, s2y))
		finfo.flush()

	mode = "F"
	#  center is in SPIDER convention
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	cnx  = nx//2 + 1
	cny  = ny//2 + 1

	#phi, theta, psi, sxo, syo = get_params_proj(data)
	t1 = data.get_attr("xform.projection")
	dp = t1.get_params("spider")
	#[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d(data, refrings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
	[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d(data, refrings, xrng, yrng, step, mode, numr, cnx+dp["tx"], cny+dp["ty"])
	#print ang, sxs, sys, mirror, iref, peak
	iref = int(iref)
	#[ang,sxs,sys,mirror,peak,numref] = apmq(projdata[imn], ref_proj_rings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
	#ang = (ang+360.0)%360.0
	# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
	#  What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
	angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
	if mirror:
		phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
		theta = 180.0-refrings[iref].get_attr("theta")
		psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
		s2x   = sxb - dp["tx"]
		s2y   = syb - dp["ty"]
	else:
		phi   = refrings[iref].get_attr("phi")
		theta = refrings[iref].get_attr("theta")
		psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb - dp["tx"]
		s2y   = syb - dp["ty"]
	#set_params_proj(data, [phi, theta, psi, s2x, s2y])
	t2 = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
	t2.set_trans(Vec2f(-s2x, -s2y))
	data.set_attr("xform.projection", t2)
	data.set_attr("referencenumber", iref)
	from pixel_error import max_3D_pixel_error
	pixel_error = max_3D_pixel_error(t1, t2, numr[-3])

	if finfo:
		finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f  %11.3e\n\n" %(phi, theta, psi, s2x, s2y, peak, pixel_error))
		finfo.flush()

	return peak, pixel_error

def proj_ali_incore_local(data, refrings, numr, xrng, yrng, step, an, finfo=None, sym='c1'):
	from utilities    import inverse_transform2
	#from utilities    import set_params_proj, get_params_proj
	from math         import cos, sin, pi, radians
	from EMAN2        import Vec2f

	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1

	ant = cos(radians(an))
	#phi, theta, psi, sxo, syo = get_params_proj(data)
	t1 = data.get_attr("xform.projection")
	dp = t1.get_params("spider")
	#print  dp["phi"], dp["theta"], dp["psi"], -dp["tx"], -dp["ty"]
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		#finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, sxo, syo))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(dp["phi"], dp["theta"], dp["psi"], -dp["tx"], -dp["ty"]))
		finfo.flush()

	#[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d_local(data, refrings, xrng, yrng, step, ant, mode, numr, cnx-sxo, cny-syo)
	[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d_local(data, refrings, xrng, yrng, step, ant, mode, numr, cnx+dp["tx"], cny+dp["ty"])
	iref=int(iref)
	#[ang,sxs,sys,mirror,peak,numref] = apmq_local(projdata[imn], ref_proj_rings, xrng, yrng, step, ant, mode, numr, cnx-sxo, cny-syo)
	#ang = (ang+360.0)%360.0
	#print  ang, sxs, sys, mirror, iref, peak
	if iref > -1:
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		# What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		isym = int(sym[1:])
		phi   = refrings[iref].get_attr("phi")
		if(isym > 1 and an > 0.0):
			qsym = 360.0/isym
			if(phi < 0.0 or phi >= qsym ):  phi = phi%qsym
		if  mirror:
			phi   = (phi+540.0)%360.0
			theta = 180.0-refrings[iref].get_attr("theta")
			psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
			s2x   = sxb - dp["tx"]
			s2y   = syb - dp["ty"]
		else:			
			theta = refrings[iref].get_attr("theta")
			psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
			s2x   = sxb - dp["tx"]
			s2y   = syb - dp["ty"]
			
			

		#set_params_proj(data, [phi, theta, psi, s2x, s2y])
		t2 = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
		t2.set_trans(Vec2f(-s2x, -s2y))
		data.set_attr("xform.projection", t2)
		from pixel_error import max_3D_pixel_error
		pixel_error = max_3D_pixel_error(t1, t2, numr[-3])
		#print phi, theta, psi, s2x, s2y, peak, pixel_error
		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f  %11.3e\n\n" %(phi, theta, psi, s2x, s2y, peak, pixel_error))
			finfo.flush()
		return peak, pixel_error
	else:
		return -1.0e23, 0.0

def proj_ali_incore_local_chunks(data, refrings, numr, xrng, yrng, step, an, finfo=None, sym='c1'):
	from utilities    import inverse_transform2
	#from utilities    import set_params_proj, get_params_proj
	from math         import cos, sin, pi, radians
	from EMAN2        import Vec2f

	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1

	ant = cos(radians(an))
	#phi, theta, psi, sxo, syo = get_params_proj(data)
	t1 = data.get_attr("xform.projection")
	dp = t1.get_params("spider")
	#print  dp["phi"], dp["theta"], dp["psi"], -dp["tx"], -dp["ty"]
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		#finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, sxo, syo))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(dp["phi"], dp["theta"], dp["psi"], -dp["tx"], -dp["ty"]))
		finfo.flush()

	#[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d_local(data, refrings, xrng, yrng, step, ant, mode, numr, cnx-sxo, cny-syo)
# 	[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d_local(data, refrings, xrng, yrng, step, ant, mode, numr, cnx+dp["tx"], cny+dp["ty"])
	
	max_peak = 0
	num_refrings = len(refrings)
	for i in xrange(num_refrings):
		[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d(data, refrings[i], xrng, yrng, step, mode, numr, cnx+dp["tx"], cny+dp["ty"])
		if peak > max_peak:
 			res = [ang, sxs, sys, mirror, iref, peak]
 			max_peak = peak
	[ang, sxs, sys, mirror, iref, peak] = res

	iref=int(iref)
	#[ang,sxs,sys,mirror,peak,numref] = apmq_local(projdata[imn], ref_proj_rings, xrng, yrng, step, ant, mode, numr, cnx-sxo, cny-syo)
	#ang = (ang+360.0)%360.0
	#print  ang, sxs, sys, mirror, iref, peak
	if iref > -1:
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		# What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		isym = int(sym[1:])
		phi   = refrings[iref].get_attr("phi")
		if(isym > 1 and an > 0.0):
			qsym = 360.0/isym
			if(phi < 0.0 or phi >= qsym ):  phi = phi%qsym
		if  mirror:
			phi   = (phi+540.0)%360.0
			theta = 180.0-refrings[iref].get_attr("theta")
			psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
			s2x   = sxb - dp["tx"]
			s2y   = syb - dp["ty"]
		else:			
			theta = refrings[iref].get_attr("theta")
			psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
			s2x   = sxb - dp["tx"]
			s2y   = syb - dp["ty"]
			
			

		#set_params_proj(data, [phi, theta, psi, s2x, s2y])
		t2 = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
		t2.set_trans(Vec2f(-s2x, -s2y))
		data.set_attr("xform.projection", t2)
		from pixel_error import max_3D_pixel_error
		pixel_error = max_3D_pixel_error(t1, t2, numr[-3])
		#print phi, theta, psi, s2x, s2y, peak, pixel_error
		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f  %11.3e\n\n" %(phi, theta, psi, s2x, s2y, peak, pixel_error))
			finfo.flush()
		return peak, pixel_error
	else:
		return -1.0e23, 0.0

def proj_ali_incore_delta(data, refrings, numr, xrng, yrng, step, start, delta, finfo=None):
	from utilities    import inverse_transform2
	from EMAN2 import Vec2f

	ID = data.get_attr("ID")
	if finfo:
		from utilities    import get_params_proj
		phi, theta, psi, s2x, s2y = get_params_proj(data)
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, s2x, s2y))
		finfo.flush()

	mode = "F"
	#  center is in SPIDER convention
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	cnx  = nx//2 + 1
	cny  = ny//2 + 1

	#phi, theta, psi, sxo, syo = get_params_proj(data)
	t1 = data.get_attr("xform.projection")
	dp = t1.get_params("spider")
	#[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d(data, refrings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
	[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d_delta(data, refrings, xrng, yrng, step, mode, numr, cnx+dp["tx"], cny+dp["ty"], start, delta)
	iref = int(iref)
	#[ang,sxs,sys,mirror,peak,numref] = apmq(projdata[imn], ref_proj_rings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
	#ang = (ang+360.0)%360.0
	# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
	#  What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
	angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
	if mirror:
		phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
		theta = 180.0-refrings[iref].get_attr("theta")
		psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
		s2x   = sxb - dp["tx"]
		s2y   = syb - dp["ty"]
	else:
		phi   = refrings[iref].get_attr("phi")
		theta = refrings[iref].get_attr("theta")
		psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb - dp["tx"]
		s2y   = syb - dp["ty"]
	#set_params_proj(data, [phi, theta, psi, s2x, s2y])
	t2 = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
	t2.set_trans(Vec2f(-s2x, -s2y))
	data.set_attr("xform.projection", t2)
	from pixel_error import max_3D_pixel_error
	pixel_error = max_3D_pixel_error(t1, t2, numr[-3])

	if finfo:
		finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f  %11.3e\n\n" %(phi, theta, psi, s2x, s2y, peak, pixel_error))
		finfo.flush()

	return peak, pixel_error

def proj_ali_incore_local_psi(data, refrings, numr, xrng, yrng, step, an, dpsi=180.0, finfo=None):
	"""
	  dpsi - how far psi can be from the original value.
	"""
	from utilities    import inverse_transform2
	#from utilities   import set_params_proj, get_params_proj
	from EMAN2 import Vec2f
	from math         import cos, sin, pi
	
	ID = data.get_attr("ID")
	if finfo:
		phi, theta, psi, s2x, s2y = get_params_proj(data)
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, s2x, s2y))
		finfo.flush()

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1

	ant = cos(an*pi/180.0)
	#phi, theta, psi, sxo, syo = get_params_proj(data)
	t1 = data.get_attr("xform.projection")
	dp = t1.get_params("spider")
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		#finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, sxo, syo))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(dp["phi"], dp["theta"], dp["psi"], -dp["tx"], -dp["ty"]))
		finfo.flush()

	#[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d_local_psi(data, refrings, xrng, yrng, step, ant, 180.0, mode, numr, cnx-sxo, cny-syo)
	[ang, sxs, sys, mirror, iref, peak] = Util.multiref_polar_ali_2d_local_psi(data, refrings, xrng, yrng, step, ant, dpsi, mode, numr, cnx+dp["tx"], cny+dp["ty"])
	iref = int(iref)
	#Util.multiref_peaks_ali(data[imn].process("normalize.mask", {"mask":mask2D, "no_sigma":1}), ref_proj_rings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo, ccfs, ccfm, nphi, ntheta)
	#[ang,sxs,sys,mirror,peak,numref] = apmq_local(projdata[imn], ref_proj_rings, xrng, yrng, step, ant, mode, numr, cnx-sxo, cny-syo)
	#ang = (ang+360.0)%360.0
	if iref > -1:
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		# What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		if  mirror:
			phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
			theta = 180.0-refrings[iref].get_attr("theta")
			psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
			s2x   = sxb - dp["tx"]
			s2y   = syb - dp["ty"]
		else:
			phi   = refrings[iref].get_attr("phi")
			theta = refrings[iref].get_attr("theta")
			psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
			s2x   = sxb - dp["tx"]
			s2y   = syb - dp["ty"]

		#set_params_proj(data, [phi, theta, psi, s2x, s2y])
		t2 = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
		t2.set_trans(Vec2f(-s2x, -s2y))
		data.set_attr("xform.projection", t2)
		from pixel_error import max_3D_pixel_error
		pixel_error = max_3D_pixel_error(t1, t2, numr[-3])
		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f  %11.3e\n\n" %(phi, theta, psi, s2x, s2y, peak, pixel_error))
			finfo.flush()
		return peak, pixel_error
	else:
		return -1.0e23, 0.0

def proj_ali_helical(data, refrings, numr, xrng, yrng, stepx, ynumber, psi_max=180.0, finfo=None):
	"""
	  psi_max - how much psi can differ from 90 or 270 degrees
	"""
	from utilities    import inverse_transform2, get_params_proj
	from math         import cos, sin, pi
	
	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1
	phi, theta, psi, tx, ty = get_params_proj(data)
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, tx, ty))
		finfo.flush()
	[ang, sxs, sys, mirror, iref, peak] = \
		Util.multiref_polar_ali_helical(data, refrings, xrng, yrng, stepx, psi_max, mode, numr, cnx-tx, cny-ty, int(ynumber))
	iref = int(iref)
	#print  " IN ", ang, sxs, sys, mirror, iref, peak
	if iref > -1:
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		# What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		if  mirror:
			phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
			theta = 180.0-refrings[iref].get_attr("theta")
			psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
		else:
			phi   = refrings[iref].get_attr("phi")
			theta = refrings[iref].get_attr("theta")
			psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb + tx
		s2y   = syb + ty

		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f\n\n" %(phi, theta, psi, s2x, s2y, peak))
			finfo.flush()
		return peak, phi, theta, psi, s2x, s2y
	else:
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0

def proj_ali_helical_local(data, refrings, numr, xrng, yrng, stepx,ynumber, an, psi_max=180.0, finfo=None, yrnglocal=-1.0):
	"""
	  psi_max - how much psi can differ from 90 or 270 degrees
	"""
	from utilities    import inverse_transform2, get_params_proj
	from math         import cos, sin, radians
	
	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1
	ant = cos(radians(an))
	phi, theta, psi, tx, ty = get_params_proj(data)
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, tx, ty))
		finfo.flush()

	[ang, sxs, sys, mirror, iref, peak] = \
		Util.multiref_polar_ali_helical_local(data, refrings, xrng, yrng, stepx, ant, psi_max, mode, numr, cnx-tx, cny-ty, int(ynumber), yrnglocal)

	iref = int(iref)

	if iref > -1:
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		# What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		if  mirror:
			phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
			theta = 180.0-refrings[iref].get_attr("theta")
			psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
		else:
			phi   = refrings[iref].get_attr("phi")
			theta = refrings[iref].get_attr("theta")
			psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb + tx
		s2y   = syb + ty

		if finfo:
			finfo.write("ref phi: %9.4f\n"%(refrings[iref].get_attr("phi")))
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f \n\n" %(phi, theta, psi, s2x, s2y, peak))
			finfo.flush()

		return peak, phi, theta, psi, s2x, s2y
	else:
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0\

def proj_ali_helical_90(data, refrings, numr, xrng, yrng, stepx, ynumber, psi_max=180.0, finfo=None):
	"""
	  psi_max - how much psi can differ from 90 or 270 degrees
	"""
	from utilities    import inverse_transform2, get_params_proj

	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1
	phi, theta, psi, tx, ty = get_params_proj(data)
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, tx, ty))
		finfo.flush()

	[ang, sxs, sys, mirror, iref, peak] = \
		Util.multiref_polar_ali_helical_90(data, refrings, xrng, yrng, stepx, psi_max, mode, numr, cnx-tx, cny-ty, int(ynumber))
	iref = int(iref)
	#print  " IN ", ang, sxs, sys, mirror, iref, peak
	if iref > -1:
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		phi   = refrings[iref].get_attr("phi")
		theta = refrings[iref].get_attr("theta")
		psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb + tx
		s2y   = syb + ty

		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f\n\n" %(phi, theta, psi, s2x, s2y, peak))
			finfo.flush()
		return peak, phi, theta, psi, s2x, s2y
	else:
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0

def proj_ali_helical_90_local(data, refrings, numr, xrng, yrng, stepx, ynumber, an, psi_max=180.0, finfo=None, yrnglocal=-1.0):
	"""
	  psi_max - how much psi can differ from 90 or 270 degrees
	"""
	from utilities    import inverse_transform2, get_params_proj
	from math         import cos, sin, radians

	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1
	ant = cos(radians(an))
	phi, theta, psi, tx, ty = get_params_proj(data)
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, tx, ty))
		finfo.flush()

	[ang, sxs, sys, mirror, iref, peak] = \
		Util.multiref_polar_ali_helical_90_local(data, refrings, xrng, yrng, stepx, ant, psi_max, mode, numr, cnx-tx, cny-ty, int(ynumber), yrnglocal)
	iref = int(iref)
	if iref > -1:
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		phi   = refrings[iref].get_attr("phi")
		theta = refrings[iref].get_attr("theta")
		psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb + tx
		s2y   = syb + ty

		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f\n\n" %(phi, theta, psi, s2x, s2y, peak))
			finfo.flush()
		return peak, phi, theta, psi, s2x, s2y
	else:
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0

#  HELICON functions
def proj_ali_helicon_local(data, refrings, numr, xrng, yrng, stepx,ynumber, an, psi_max=180.0, finfo=None, yrnglocal=-1.0):
	"""
	  psi_max - how much psi can differ from 90 or 270 degrees
	"""
	from utilities    import inverse_transform2, get_params_proj
	from math         import cos, sin, radians

	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1
	ant = cos(radians(an))
	phi, theta, psi, tx, ty = get_params_proj(data)
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, tx, ty))
		finfo.flush()

	[ang, sxs, sys, mirror, iref, peak] = \
		Util.multiref_polar_ali_helicon_local(data, refrings, xrng, yrng, stepx, ant, psi_max, mode, numr, cnx-tx, cny-ty, int(ynumber), yrnglocal)

	iref = int(iref)

	if iref > -1:
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		# What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		if  mirror:
			phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
			theta = 180.0-refrings[iref].get_attr("theta")
			psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
		else:
			phi   = refrings[iref].get_attr("phi")
			theta = refrings[iref].get_attr("theta")
			psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb + tx
		s2y   = syb + ty

		if finfo:
			finfo.write("ref phi: %9.4f\n"%(refrings[iref].get_attr("phi")))
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f \n\n" %(phi, theta, psi, s2x, s2y, peak))
			finfo.flush()

		return peak, phi, theta, psi, s2x, s2y
	else:
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0\

def proj_ali_helicon_90_local_direct(data, refrings, xrng, yrng, \
		an, psi_max=180.0, psi_step=1.0, stepx = 1.0, stepy = 1.0, finfo=None, yrnglocal=-1.0):
	"""
	  psi_max - how much psi can differ from 90 or 270 degrees
	"""
	from utilities    import compose_transform2, get_params_proj
	from alignment    import directaligridding
	from math         import cos, sin, radians

	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	#cnx  = nx//2 + 1
	#cny  = ny//2 + 1
	ant = cos(radians(an))
	phi, theta, psi, tx, ty = get_params_proj(data)
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, tx, ty))
		finfo.flush()
	#  Determine whether segment is up and down and search for psi in one orientation only.
	if psi < 180.0 :  direction = "up"
	else:             direction = "down"
	peak = -1.0e23
	iref = -1
	imn1 = sin(radians(theta))*cos(radians(phi))
	imn2 = sin(radians(theta))*sin(radians(phi))
	imn3 = cos(radians(theta))
	print '  aaaaaa  ',psi_max, psi_step, xrng, yrng, direction
	for i in xrange(len(refrings)):
		if( (refrings[i][0].get_attr("n1")*imn1 + refrings[i][0].get_attr("n2")*imn2 + refrings[i][0].get_attr("n3")*imn3)>=ant ):
			print  " Matching refring  ",i,phi, theta, psi, tx, ty
			#  directali will do fft of the input image and 180 degs rotation, if necessary.  Eventually, this would have to be pulled up.
			a, tx,ty, tp = directaligridding(data, refrings[i], psi_max, psi_step, xrng, yrng, stepx, stepy, direction)
			if(tp>peak):
				peak = tp
				iref = i
				angb = a
				sxb = tx
				syb = ty
	"""
	[ang, sxs, sys, mirror, iref, peak] = \
		Util.multiref_polar_ali_helicon_90_local(data, refrings, xrng, yrng, stepx, ant, psi_max, mode, numr, cnx-tx, cny-ty, int(ynumber), yrnglocal)
	"""
	if iref > -1:
		#angb, sxb, syb, ct = compose_transform2(0.0, sxs, sys, 1, -ang, 0.0, 0.0, 1)
		phi   = refrings[iref][0].get_attr("phi")
		theta = refrings[iref][0].get_attr("theta")
		psi   = (refrings[iref][0].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb #+ tx
		s2y   = syb #+ ty
		print   "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f" %(phi, theta, psi, s2x, s2y, peak)
		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f\n\n" %(phi, theta, psi, s2x, s2y, peak))
			finfo.flush()
		return peak, phi, theta, psi, s2x, s2y
	else:
		print  "  NO PEAK"
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0

def proj_ali_helicon_90_local_direct1(data, refrings, xrng, yrng, \
		psi_max=180.0, psi_step=1.0, stepx = 1.0, stepy = 1.0, finfo=None, yrnglocal=-1.0, direction = "both"):
	"""
	  psi_max - how much psi can differ from either 90 or 270 degrees
	"""
	from utilities    import inverse_transform2, get_params_proj
	from alignment    import directaligridding1
	from math         import cos, sin, radians
	
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	#cnx  = nx//2 + 1
	#cny  = ny//2 + 1

	phi, theta, psi, tx, ty = get_params_proj(data)

	#  directali will do fft of the input image and 180 degs rotation, if necessary.  Eventually, this would have to be pulled up.
	angb, tx,ty, tp = directaligridding1(data, kb, refrings, psi_max, psi_step, xrng, yrng, stepx, stepy, direction)

	if tp > -1.0e23:
		#angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		phi   = refrings[iref][0].get_attr("phi")
		theta = refrings[iref][0].get_attr("theta")
		psi   = (refrings[iref][0].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb #+ tx
		s2y   = syb #+ ty
		return peak, phi, theta, psi, s2x, s2y
	else:
		print  "  NO PEAK"
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0

def proj_ali_helicon_90_local(data, refrings, numr, xrng, yrng, stepx, ynumber, an, psi_max=180.0, finfo=None, yrnglocal=-1.0):
	"""
	  psi_max - how much psi can differ from 90 or 270 degrees
	"""
	from utilities    import inverse_transform2, get_params_proj
	from math         import cos, sin, pi
	
	ID = data.get_attr("ID")

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1
	ant = cos(an*pi/180.0)
	phi, theta, psi, tx, ty = get_params_proj(data)
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, tx, ty))
		finfo.flush()

	[ang, sxs, sys, mirror, iref, peak] = \
		Util.multiref_polar_ali_helicon_90_local(data, refrings, q, yrng, stepx, ant, psi_max, mode, numr, cnx-tx, cny-ty, int(ynumber), yrnglocal)
	iref = int(iref)
	if iref > -1:
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		phi   = refrings[iref].get_attr("phi")
		theta = refrings[iref].get_attr("theta")
		psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
		s2x   = sxb + tx
		s2y   = syb + ty

		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f\n\n" %(phi, theta, psi, s2x, s2y, peak))
			finfo.flush()
		return peak, phi, theta, psi, s2x, s2y
	else:
		return -1.0e23, 0.0, 0.0, 0.0, 0.0, 0.0

def ali_vol_func(params, data):
	from utilities    import model_gauss
	from fundamentals import rot_shift3D, cyclic_shift
	from morphology   import binarize
	#print  params
	#print  data[3]
	#cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale= compose_transform3(data[3][0], data[3][1], data[3][2], data[3][3], data[3][4], data[3][5], data[3][6], params[0], params[1], params[2],params[3], params[4], params[5],1.0)
	#print  cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale
	x = rot_shift3D(data[0], params[0], params[1], params[2], params[3], params[4], params[5], 1.0)

	res = -x.cmp("ccc", data[1], {"mask":data[2]})
	#print  " %9.3f %9.3f %9.3f %9.3f %9.3f %9.3f  %10.5f" %(params[0], params[1], params[2],params[3], params[4], params[5], -res)
	return res

def ali_vol_func_julio(params, data):
	from utilities    import model_gauss
	from fundamentals import rot_shift3D, cyclic_shift
	from morphology   import binarize
	#print  params
	#print  data[3]
	#cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale= compose_transform3(data[3][0], data[3][1], data[3][2], data[3][3], data[3][4], data[3][5], data[3][6], params[0], params[1], params[2],params[3], params[4], params[5],1.0)
	#print  cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale
	x = rot_shift3D(data[0], params[0], params[1], params[2], params[3], params[4], params[5], 1.0)

	if (data[3] == None):
		mask = data[2]
	elif (data[3] > 0.0):
		mask = binarize(x, data[3])
	else:
		mask = cyclic_shift(data[2], int(round(params[3],0)), int(round(params[4],0)), int(round(params[5],0)))

	if (data[5] > 1):
		from EMAN2 import rsconvolution
		gker = model_gauss(1, 7, 7, 7)
		x = rsconvolution(x, gker)
		x = Util.decimate(x, data[5], data[5], data[5])
		mask = Util.decimate(mask, data[5], data[5], data[5])

	#res = -x.cmp("ccc", data[1], {"mask":data[2]})
	res = -x.cmp(data[4], data[1], {"mask":mask, "normalize":0})
	#print  " %9.3f %9.3f %9.3f %9.3f %9.3f %9.3f  %10.5f" %(params[0], params[1], params[2],params[3], params[4], params[5], -res)
	return res

def ali_vol_func_grid(params, data):
	from fundamentals import rot_shift3D_grid, cyclic_shift
	from morphology   import binarize

	# data[0]: image output from prepi3D (segment)
	# data[5]: kb from prepi3D
	# data[2], data[3]: mask-related info
	# data[4]: similarity measure
	# data[1]: target volume, into which data[0] is being fitted
	# data[6]: wraparound option

	# params are assumed to be in the "xyz" convention, so get "spider" ones to do the rot:
	tr = Transform({"type":"xyz","xtilt":params[0],"ytilt":params[1],"ztilt":params[2], "tx":params[3], "ty":params[4], "tz":params[5]})
	qt = tr.get_params("spider")

	x = rot_shift3D_grid(data[0], qt['phi'], qt['theta'], qt['psi'], qt['tx'], qt['ty'], qt['tz'], 1.0, data[5], "background", data[6])

	if (data[3] == None):
		mask = data[2]
	elif (data[3] > 0.0):
		mask = binarize(x, data[3])
	else:
		mask = cyclic_shift(data[2], int(round(params[3],0)), int(round(params[4],0)), int(round(params[5],0)))

	res = -x.cmp(data[4], data[1], {"mask":mask, "normalize":0})
	return res

def ali_vol_func_nopsi(params, data):
	from utilities    import compose_transform3
	from fundamentals import rot_shift3D
	#print  params
	#print  data[3]
	#cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale= compose_transform3(data[3][0], data[3][1], data[3][2], data[3][3], data[3][4], data[3][5], data[3][6], params[0], params[1], params[2],params[3], params[4], params[5],1.0)
	#print  cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale
	x = rot_shift3D(data[0], params[0], params[1], 0.0, params[2], params[3], params[4], 1.0)
	#res = -x.cmp("ccc", data[1], {"mask":data[2]})
	res = -x.cmp(data[4], data[1], {"mask":data[2]})
	#print  " %9.3f %9.3f %9.3f %9.3f %9.3f  %10.5f" %(params[0], params[1], params[2],params[3], params[4], -res)
	return res

def ali_vol_func_rotate(params, data):
	from utilities    import compose_transform3
	from fundamentals import rot_shift3D
	cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale= compose_transform3(data[3][0], data[3][1], data[3][2], data[3][3], data[3][4], data[3][5], data[3][7], params[0], params[1], params[2],0.0,0.0,0.0,1.0)
	x = rot_shift3D(data[0], cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale)
	res = -x.cmp(data[4], data[1], {"mask":data[2]})
	#print  " %9.3f %9.3f %9.3f  %12.3e" %(params[0], params[1], params[2], -res)
	return res

def ali_vol_func_shift(params, data):
	from utilities    import compose_transform3
	from fundamentals import rot_shift3D
	cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale= compose_transform3(data[3][0], data[3][1], data[3][2], data[3][3], data[3][4], data[3][5], data[3][7], 0.0,0.0,0.0, params[0], params[1], params[2],1.0)
	x = rot_shift3D(data[0], cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale)
	res = -x.cmp(data[4], data[1], {"mask":data[2]})
	#print  " %9.3f %9.3f %9.3f  %12.3e" %(params[0], params[1], params[2], -res)
	return res

def ali_vol_func_scale(params, data):
	from utilities    import compose_transform3
	from fundamentals import rot_shift3D
	cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale= compose_transform3(data[3][0], data[3][1], data[3][2], data[3][3], data[3][4], data[3][5], data[3][7], params[0], params[1], params[2], params[3], params[4], params[5], params[6])
	x = rot_shift3D(data[0], cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale)
	res = -x.cmp(data[4], data[1], {"mask":data[2]})
	#print  " %9.3f %9.3f %9.3f %9.3f %9.3f %9.3f %9.3f  %12.3e" %(params[0], params[1], params[2],params[3], params[4], params[5], params[6], -res)
	return res

def ali_vol_func_only_scale(params, data):
	from utilities    import compose_transform3
	from fundamentals import rot_shift3D
	cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale= compose_transform3(data[3][0], data[3][1], data[3][2], data[3][3], data[3][4], data[3][5], data[3][7], 0.0,0.0,0.0,0.0,0.0,0.0, params[0])
	x = rot_shift3D(data[0], cphi, ctheta, cpsi, cs2x, cs2y, cs2z, cscale)
	res = -x.cmp(data[4], data[1], {"mask":data[2]})
	#print  " %9.3f  %12.3e" %(params[0], -res)
	return res

def helios_func(params, data):
	sm = data[0].helicise(data[2], params[0], params[1], data[3], data[4], data[5])
	#try other sim creteria
	q = sm.cmp("dot", sm, {"negative":0})
	#q = sm.cmp("dot", data[0], {"negative":0})# corelation  with the recon data
	#print  params,q
	return  q

def helios(vol, pixel_size, dp, dphi, section_use = 0.75, radius = 0.0, rmin = 0.0):
	from alignment    import helios_func
	from utilities    import amoeba
	nx = vol.get_xsize()
	ny = vol.get_ysize()
	nz = vol.get_zsize()
	if(radius <= 0.0):    radius = nx//2-1
	params = [dp, dphi]
	#print  " input params ",params
	data=[vol, params, pixel_size, section_use, radius, rmin]
	new_params = [dp, dphi]
	new_params = amoeba(new_params, [0.05*dp, 0.05*abs(dphi)], helios_func, 1.0e-2, 1.0e-2, 50, data)
	#print  " new params ", new_params[0], new_params[1]
	return  vol.helicise(pixel_size, new_params[0][0], new_params[0][1], section_use, radius), new_params[0][0], new_params[0][1]

def helios7(vol, pixel_size, dp, dphi, section_use = 0.75, radius = 0.0, rmin = 0.0):
	from alignment    import helios_func
	nx = vol.get_xsize()
	ny = vol.get_ysize()
	nz = vol.get_zsize()
	if(radius <= 0.0):    radius = nx//2-1
	params = [dp, dphi]
	data=[vol, params, pixel_size, section_use, radius, rmin]
	q = helios_func([dp, dphi], data)
	return q

def sub_favj(ave, data, jtot, mirror, numr):
	'''
		Subtract FT of rings from the average
	'''
	from math import pi,sin,cos
	#from utilities  import print_col
	# trig functions in radians
	pi2 = pi*2
	nring = len(numr)/3
	maxrin = numr[len(numr)-1]
	#print  "update",psi
	#print_col(ave)
	#print_col(data)
	#print numr
	if(mirror):
		# for mirrored data has to be conjugated
		for i in xrange(nring):
			numr3i = numr[2+i*3]
			np = numr[1+i*3]-1
			ave[np]   -= data[np]
			ave[np+1] -= data[np+1]*cos(pi2*(jtot-1)/2.0*numr3i/maxrin)
			for j in xrange(2, numr3i, 2):
				arg = pi2*(jtot-1)*int(j/2)/maxrin
				cs = complex(data[np + j],data[np + j +1])*complex(cos(arg),sin(arg))
				ave[np + j]    -= cs.real
				ave[np + j +1] += cs.imag
	else:
		for i in xrange(nring):
			numr3i = numr[2+i*3]
			np = numr[1+i*3]-1
			ave[np]   -= data[np]
			ave[np+1] -= data[np+1]*cos(pi2*(jtot-1)/2.0*numr3i/maxrin)
			for j in xrange(2, numr3i, 2):
				arg = pi2*(jtot-1)*int(j/2)/maxrin
				cs = complex(data[np + j],data[np + j +1])*complex(cos(arg),sin(arg))
				ave[np + j]    -= cs.real
				ave[np + j +1] -= cs.imag
	#print_col(ave)

def update_favj(ave, data, jtot, mirror, numr):
	'''
		Add FT of rings to the average
	'''
	from math import pi,sin,cos
	#from utilities  import print_col
	# trig functions in radians
	pi2 = pi*2
	nring = len(numr)/3
	maxrin = numr[len(numr)-1]
	#print  "update",psi
	#print_col(ave)
	#print_col(data)
	#print numr
	if(mirror):
		# for mirrored data has to be conjugated
		for i in xrange(nring):
			numr3i = numr[2+i*3]
			np = numr[1+i*3]-1
			ave[np]   += data[np]
			ave[np+1] += data[np+1]*cos(pi2*(jtot-1)/2.0*numr3i/maxrin)
			for j in xrange(2, numr3i, 2):
				arg = pi2*(jtot-1)*int(j/2)/maxrin
				cs = complex(data[np + j],data[np + j +1])*complex(cos(arg),sin(arg))
				ave[np + j]    += cs.real
				ave[np + j +1] -= cs.imag
	else:
		for i in xrange(nring):
			numr3i = numr[2+i*3]
			np = numr[1+i*3]-1
			ave[np]   += data[np]
			ave[np+1] += data[np+1]*cos(pi2*(jtot-1)/2.0*numr3i/maxrin)
			for j in xrange(2, numr3i, 2):
				arg = pi2*(jtot-1)*int(j/2)/maxrin
				cs = complex(data[np + j],data[np + j +1])*complex(cos(arg),sin(arg))
				ave[np + j]    += cs.real
				ave[np + j +1] += cs.imag
	#print_col(ave)

def fine_2D_refinement(data, br, mask, tavg, group = -1):
	from utilities import amoeba
	from fundamentals 	import rtshgkb, prepg

	# IMAGES ARE SQUARES!
	nx = data[0].get_xsize()
	#  center is in SPIDER convention
	cnx = int(nx/2)+1
	cny = cnx

	if(group > -1):
		nima = 0
		for im in xrange(len(data)):
			if(data[im].get_attr('ref_num') == group):  nima += 1
	else:  nima = len(data)

	# prepare KB interpolants
	kb = kbt(nx)
	# load stuff for amoeba
	stuff = []
	stuff.insert(0, kb)
	stuff.insert(1, mask)
	stuff.insert(2, nima)
	#stuff.insert(3,tave)  # current average
	#stuff.insert(4,data)  # current image in the gridding format
	weights = [br]*3 # weights define initial bracketing, so one would have to figure how to set them correctly

	for im in xrange(len(data)):
		if(group > -1):
			if(data[im].get_attr('ref_num') != group):  continue
		# subtract current image from the average
		alpha  = data[im].get_attr('alpha')
		sx     = data[im].get_attr('sx')
		sy     = data[im].get_attr('sy')
		mirror = data[im].get_attr('mirror')
		ddata  = prepg(data[im], kb)
		ddata.set_attr_dict({'alpha': alpha, 'sx':sx, 'sy':sy, 'mirror': mirror})
		temp   = rtshgkb(ddata, alpha, sx, sy, kb)
		if  mirror: temp.process_inplace("xform.mirror", {"axis":'x'})
		#  Subtract current image from the average
		refim = Util.madn_scalar(tavg, temp, -1.0/float(nima)) 
		stuff.append(refim)  # curent ave-1
		stuff.append(ddata)  # curent image
		# perform amoeba alignment
		params = [alpha, sx, sy]
		outparams =  amoeba(params, weights, crit2d, 1.e-4, 1.e-4, 500, stuff)
		del stuff[3]
		del stuff[3]
		# set parameters to the header
		data[im].set_attr_dict({'alpha':outparams[0][0], 'sx':outparams[0][1], 'sy':outparams[0][2],'mirror': mirror})
		# update the average
		temp = rtshgkb(ddata, outparams[0][0], outparams[0][1], outparams[0][2], kb)
		if  mirror: temp.process_inplace("xform.mirror",{"axis":'x'})
		#check whether the criterion actually increased
		# add current image to the average
		tavg = Util.madn_scalar(refim, temp, 1.0/float(nima))
		#print  im,tave.cmp("dot", tave, {"negative":0,"mask":mask}),params,outparams[0],outparams[2]
		#tave,tvar = ave_var_series_g(data,kb)
		#print  " Criterium on the fly ", tave.cmp("dot", tave, {"negative":0,"mask":mask})


def align2d(image, refim, xrng=0, yrng=0, step=1, first_ring=1, last_ring=0, rstep=1, mode = "F"):
	"""  Determine shift and rotation between image and reference image
	     quadratic interpolation
	     Output: ang, sxs, sys, mirror, peak
	"""
	#from utilities import print_col
	from alignment import Numrinit, ringwe
	step = float(step)
	nx = refim.get_xsize()
	ny = refim.get_ysize()
	MAX_XRNG = nx/2
	MAX_YRNG=ny/2
	if xrng >= MAX_XRNG:
		ERROR('Translation search range in x is at most %d'%MAX_XRNG, "align2d ", 1)
	if yrng >= MAX_YRNG:
		ERROR('Translation search range in y is at most %d'%MAX_YRNG, "align2d ", 1)
	if(last_ring == 0):  last_ring = nx/2-2-int(max(xrng,yrng))
	# center in SPIDER convention
	cnx = nx//2+1
	cny = ny//2+1
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr   = ringwe(numr, mode)
	#cimage=Util.Polar2Dmi(refim, cnx, cny, numr, mode, kb)
	crefim = Util.Polar2Dm(refim, cnx, cny, numr, mode)
	#crefim = Util.Polar2D(refim, numr, mode)
	#print_col(crefim)
	Util.Frngs(crefim, numr)
	Util.Applyws(crefim, numr, wr)
	return ormq(image, crefim, xrng, yrng, step, mode, numr, cnx, cny)
	

def align2dshc(image, refim, xrng=0, yrng=0, step=1, first_ring=1, last_ring=0, rstep=1, mode = "F"):
	"""  Determine shift and rotation between image and reference image
	     quadratic interpolation
	     Output: ang, sxs, sys, mirror, peak
	"""
	#from utilities import print_col
	from alignment import Numrinit, ringwe
	step = float(step)
	nx = refim.get_xsize()
	ny = refim.get_ysize()
	MAX_XRNG = nx/2
	MAX_YRNG=ny/2
	if xrng >= MAX_XRNG:
		ERROR('Translation search range in x is at most %d'%MAX_XRNG, "align2d ", 1)
	if yrng >= MAX_YRNG:
		ERROR('Translation search range in y is at most %d'%MAX_YRNG, "align2d ", 1)
	if(last_ring == 0):  last_ring = nx/2-2-int(max(xrng,yrng))
	# center in SPIDER convention
	cnx = nx//2+1
	cny = ny//2+1
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr   = ringwe(numr, mode)
	#cimage=Util.Polar2Dmi(refim, cnx, cny, numr, mode, kb)
	crefim = Util.Polar2Dm(refim, cnx, cny, numr, mode)
	#crefim = Util.Polar2D(refim, numr, mode)
	#print_col(crefim)
	Util.Frngs(crefim, numr)
	Util.Applyws(crefim, numr, wr)
	#return ormq(image, crefim, xrng, yrng, step, mode, numr, cnx, cny)
	return   Util.shc(image, [crefim], xrng, yrng, step, -1.0, mode, numr, cnx, cny, "c1")



	
"""

#MIRROR HAS A PROBLEM
def align_new_test(image, refim, xrng=0, yrng=0):
	from fundamentals import scf, rot_shift2D, ccf
	from utilities import peak_search
	from math import radians, sin, cos
	nx = image.get_xsize()
	ou = nx//2-1

	alpha, sxs, sys, mirr, peak = align2d(scf(image), scf(refim), last_ring=ou, mode="H")
	
	nrx = 2*(xrng+1)+1
	nry = 2*(yrng+1)+1

	ccf1 = Util.window(ccf(rot_shift2D(image, alpha, 0.0, 0.0, mirr),refim),nrx,nry)
	p1 = peak_search(ccf1)
	
	ccf2 = Util.window(ccf(rot_shift2D(image, alpha+180.0, 0.0, 0.0, mirr),refim),nrx,nry)
	p2 = peak_search(ccf2)
	#print p1
	#print p2

	
	peak_val1 = p1[0][0]
	peak_val2 = p2[0][0]
	
	if peak_val1 > peak_val2:
		sxs = -p1[0][4]
		sys = -p1[0][5]
		cx = int(p1[0][1])
		cy = int(p1[0][2])
		peak = peak_val1
	else:
		alpha += 180.0
		sxs = -p2[0][4]
		sys = -p2[0][5]
		peak = peak_val2
		cx = int(p2[0][1])
		cy = int(p2[0][2])
		ccf1 = ccf2
	from utilities import model_blank
	#print cx,cy
	z = model_blank(3,3)
	for i in xrange(3):
		for j in xrange(3):
			z[i,j] = ccf1[i+cx-1,j+cy-1]
	#print  ccf1[cx,cy],z[2,2]
	XSH, YSH, PEAKV = parabl(z)
	#print sxs, sys, XSH, YSH, PEAKV, peak
	if(mirr == 1):  	sx = -sxs+XSH
	else:               sx =  sxs-XSH
	return alpha, sx, sys-YSH, mirr, PEAKV
	#return alpha, sxs, sys, mirror, peak
"""


def align_new_test(image, refim, xrng=0, yrng=0, ou = -1):
	from fundamentals import scf, rot_shift2D, ccf, mirror
	from utilities import peak_search
	from math import radians, sin, cos
	nx = image.get_xsize()
	if(ou<0):  ou = nx//2-1
	#sci = scf(image)
	scr = scf(refim)

	alpha1, sxs, sys, mirr, peak1 = align2d_no_mirror(scf(image), scr, last_ring=ou, mode="H")
	alpha2, sxs, sys, mirr, peak2 = align2d_no_mirror(scf(mirror(image)), scr, last_ring=ou, mode="H")
	
	if(peak1>peak2):
		mirr = 0
		alpha = alpha1
	else:
		mirr = 1
		alpha = -alpha2
	nrx = 2*(xrng+1)+1
	nry = 2*(yrng+1)+1

	ccf1 = Util.window(ccf(rot_shift2D(image, alpha, 0.0, 0.0, mirr),refim),nrx,nry)
	p1 = peak_search(ccf1)
	
	ccf2 = Util.window(ccf(rot_shift2D(image, alpha+180.0, 0.0, 0.0, mirr),refim),nrx,nry)
	p2 = peak_search(ccf2)
	#print p1
	#print p2

	
	peak_val1 = p1[0][0]
	peak_val2 = p2[0][0]
	
	if peak_val1 > peak_val2:
		sxs = -p1[0][4]
		sys = -p1[0][5]
		cx = int(p1[0][1])
		cy = int(p1[0][2])
		peak = peak_val1
	else:
		alpha += 180.0
		sxs = -p2[0][4]
		sys = -p2[0][5]
		peak = peak_val2
		cx = int(p2[0][1])
		cy = int(p2[0][2])
		ccf1 = ccf2
	from utilities import model_blank
	#print cx,cy
	z = model_blank(3,3)
	for i in xrange(3):
		for j in xrange(3):
			z[i,j] = ccf1[i+cx-1,j+cy-1]
	#print  ccf1[cx,cy],z[1,1]
	XSH, YSH, PEAKV = parabl(z)
	#print sxs, sys, XSH, YSH, PEAKV, peak
	if(mirr == 1):  	sx = -sxs+XSH
	else:               sx =  sxs-XSH
	return alpha, sx, sys-YSH, mirr, PEAKV
	#return alpha, sxs, sys, mirror, peak

def parabl(Z):
	#  parabolic fit to a peak, C indexing
	C1 = (26.*Z[0,0] - Z[0,1] + 2*Z[0,2] - Z[1,0] - 19.*Z[1,1] - 7.*Z[1,2] + 2.*Z[2,0] - 7.*Z[2,1] + 14.*Z[2,2])/9.

	C2 = (8.* Z[0,0] - 8.*Z[0,1] + 5.*Z[1,0] - 8.*Z[1,1] + 3.*Z[1,2] +2.*Z[2,0] - 8.*Z[2,1] + 6.*Z[2,2])/(-6.)

	C3 = (Z[0,0] - 2.*Z[0,1] + Z[0,2] + Z[1,0] -2.*Z[1,1] + Z[1,2] + Z[2,0] - 2.*Z[2,1] + Z[2,2])/6.

	C4 = (8.*Z[0,0] + 5.*Z[0,1] + 2.*Z[0,2] -8.*Z[1,0] -8.*Z[1,1] - 8.*Z[1,2] + 3.*Z[2,1] + 6.*Z[2,2])/(-6.)

	C5 = (Z[0,0] - Z[0,2] - Z[2,0] + Z[2,2])/4.

	C6 = (Z[0,0] + Z[0,1] + Z[0,2] - 2.*Z[1,0] - 2.*Z[1,1] -2.*Z[1,2] + Z[2,0] + Z[2,1] + Z[2,2])/6.

	DENOM = 4. * C3 * C6 - C5 * C5
	if(DENOM == 0.):
		return 0.0, 0.0, 0.0

	YSH   = (C4*C5 - 2.*C2*C6) / DENOM - 2.
	XSH   = (C2*C5 - 2.*C4*C3) / DENOM - 2.

	PEAKV = 4.*C1*C3*C6 - C1*C5*C5 - C2*C2*C6 + C2*C4*C5 - C4*C4*C3
	PEAKV = PEAKV / DENOM
	#print  "  in PARABL  ",XSH,YSH,Z[1,1],PEAKV

	XSH = min(max( XSH, -1.0), 1.0)
	YSH = min(max( YSH, -1.0), 1.0)

	return XSH, YSH, PEAKV
'''
def parabl(Z):
	#  Original with Fortran indexing

	C1 = (26.*Z[1,1] - Z[1,2] + 2*Z[1,3] - Z[2,1] - 19.*Z[2,2] - 7.*Z[2,3] + 2.*Z[3,1] - 7.*Z[3,2] + 14.*Z[3,3])/9.

	C2 = (8.* Z[1,1] - 8.*Z[1,2] + 5.*Z[2,1] - 8.*Z[2,2] + 3.*Z[2,3] +2.*Z[3,1] - 8.*Z[3,2] + 6.*Z[3,3])/(-6.)

	C3 = (Z[1,1] - 2.*Z[1,2] + Z[1,3] + Z[2,1] -2.*Z[2,2] + Z[2,3] + Z[3,1] - 2.*Z[3,2] + Z[3,3])/6.

	C4 = (8.*Z[1,1] + 5.*Z[1,2] + 2.*Z[1,3] -8.*Z[2,1] -8.*Z[2,2] - 8.*Z[2,3] + 3.*Z[3,2] + 6.*Z[3,3])/(-6.)

	C5 = (Z[1,1] - Z[1,3] - Z[3,1] + Z[3,3])/4.

	C6 = (Z[1,1] + Z[1,2] + Z[1,3] - 2.*Z[2,1] - 2.*Z[2,2] -2.*Z[2,3] + Z[3,1] + Z[3,2] + Z[3,3])/6.

	DENOM = 4. * C3 * C6 - C5 * C5
	if(DENOM == 0.):
		return 0.0, 0.0, 0.0

	YSH   = (C4*C5 - 2.*C2*C6) / DENOM - 2.
	XSH   = (C2*C5 - 2.*C4*C3) / DENOM - 2.

	PEAKV = 4.*C1*C3*C6 - C1*C5*C5 - C2*C2*C6 + C2*C4*C5 - C4*C4*C3
	PEAKV = PEAKV / DENOM
	#print  "  in PARABL  ",XSH,YSH,Z[2,2],PEAKV

	XSH = min(max( XSH, -1.0), 1.0)
	YSH = min(max( YSH, -1.0), 1.0)

	return XSH, YSH, PEAKV
'''

def align2d_direct2(image, refim, xrng=1, yrng=1, psimax=1, psistep=1, ou = -1):
	from fundamentals import fft, rot_shift2D, ccf, mirror
	from utilities import peak_search, model_circle, model_blank, inverse_transform2
	from math import radians, sin, cos
	
	nx = image.get_xsize()
	if(ou<0):  ou = nx//2-1
	mask = model_circle(ou,nx,nx)
	nk = int(psimax/psistep)
	nm = 2*nk+1
	nc = nk + 1
	refs = [None]*nm*2
	for i in xrange(nm):
		refs[2*i] = fft(rot_shift2D(refim, (i-nc)*psistep)*mask)
		refs[2*i+1] = fft(rot_shift2D(refim, (i-nc)*psistep+180.0)*mask)
	ims = fft(image)
	ama = -1.e23
	bang = 0.
	bsx = 0.
	bsy = 0.
	for i in xrange(1,nm*2):
		c = ccf(ims, refs[i])
		#c.write_image('rer.hdf')
		#exit()
		w = Util.window(c,2*xrng+1,2*yrng+1)
		pp =peak_search(w)[0]
		px = int(pp[4])
		py = int(pp[5])
		if( pp[0] == 1.0 and px == 0 and py == 0):
			pass #XSH, YSH, PEAKV = 0.,0.,0.
		else:
			ww = model_blank(3,3)
			ux = int(pp[1])
			uy = int(pp[2])
			for k in xrange(3):
				for l in xrange(3):
					ww[k,l] = w[k+ux-1,l+uy-1]
			XSH, YSH, PEAKV = parabl(ww)
			#print i,pp[-1],XSH, YSH,px+XSH, py+YSH, PEAKV
			if(PEAKV >ama):
				ama = PEAKV
				bsx = px+round(XSH,2)
				bsy = py+round(YSH,2)
				bang = i
	# returned parameters have to be inverted
	bang = (bang//2-nc)*psistep + 180.*(bang%2)
	print bang,bsx,bsy
	bang, bsx, bsy, i = inverse_transform2(bang, bsx, bsy)
	return bang, bsx, bsy, ama

def align2d_direct(image, refim, xrng=1, yrng=1, psimax=1, psistep=1, ou = -1):
	from fundamentals import fft, rot_shift2D, ccf
	from utilities import model_blank, model_circle, peak_search, compose_transform2, inverse_transform2
	from math import radians, sin, cos

	nx = image.get_xsize()
	if(ou<0):  ou = nx//2-1
	mask = model_circle(ou,nx,nx)
	nk = int(psimax/psistep)
	nm = 2*nk+1
	nc = nk + 1
	refs = [None]*nm
	for i in xrange(nm):
		refs[i] = fft(rot_shift2D(refim, (i-nc)*psistep)*mask)
	ims = fft(image)
	imr = fft(rot_shift2D(image, 180.0))
	ama  = -1.0e23
	bang = 0.0
	bsx  = 0.0
	bsy  = 0.0
	for i in xrange(nm):
		c = ccf(ims, refs[i])
		w = Util.window(c,2*xrng+1,2*yrng+1)
		pp =peak_search(w)[0]
		px = int(pp[4])
		py = int(pp[5])
		if( pp[0] == 1.0 and px == 0 and py == 0):
			pass #XSH, YSH, PEAKV = 0.,0.,0.
		else:
			ww = model_blank(3,3)
			ux = int(pp[1])
			uy = int(pp[2])
			for k in xrange(3):
				for l in xrange(3):
					ww[k,l] = w[k+ux-1,l+uy-1]
			XSH, YSH, PEAKV = parabl(ww)
			#print i,pp[-1],XSH, YSH,px+XSH, py+YSH, PEAKV
			if(PEAKV >ama):
				ama = PEAKV
				bsx = px+round(XSH,2)
				bsy = py+round(YSH,2)
				bang = i
				rt180 = 0.
		c = ccf(imr, refs[i])
		#c.write_image('imr.hdf')
		#exit()
		c = rot_shift2D(c,180)
		w = Util.window(c,2*xrng+1,2*yrng+1)
		pp =peak_search(w)[0]
		px = int(pp[4])
		py = int(pp[5])
		if( pp[0] == 1.0 and px == 0 and py == 0):
			pass #XSH, YSH, PEAKV = 0.,0.,0.
		else:
			ww = model_blank(3,3)
			ux = int(pp[1])
			uy = int(pp[2])
			for k in xrange(3):
				for l in xrange(3):
					ww[k,l] = w[k+ux-1,l+uy-1]
			XSH, YSH, PEAKV = parabl(ww)
			#print i,pp[-1],XSH, YSH,px+XSH, py+YSH, PEAKV
			if(PEAKV >ama):
				ama = PEAKV
				bsx = px+round(XSH,2)
				bsy = py+round(YSH,2)
				bang = i
				rt180 = 180.
	# returned parameters have to be inverted
	bang = 180-(bang//2-nc)*psistep
	print  bang, bsx, bsy,rt180
	bang, bsx, bsy, i = inverse_transform2(bang, bsx, bsy)
	return bang, bsx, bsy, ama


def align2d_no_mirror(image, refim, xrng=0, yrng=0, step=1, first_ring=1, last_ring=0, rstep=1, mode = "F"):
	"""  Determine shift and rotation between image and reference image
	     no mirror
	     quadratic interpolation
	     Output: ang, sxs, sys, mirror, peak  # Mirror==0
	"""
	#from utilities import print_col
	from alignment import Numrinit, ringwe
	step = float(step)
	nx = refim.get_xsize()
	ny = refim.get_ysize()
	MAX_XRNG = nx/2
	MAX_YRNG=ny/2
	if xrng >= MAX_XRNG:
		ERROR('Translation search range in x is at most %d'%MAX_XRNG, "align2d ", 1)
	if yrng >= MAX_YRNG:
		ERROR('Translation search range in y is at most %d'%MAX_YRNG, "align2d ", 1)
	if(last_ring == 0):  last_ring = nx/2-2-int(max(xrng,yrng))
	# center in SPIDER convention
	cnx = nx//2+1
	cny = ny//2+1
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr   = ringwe(numr, mode)
	crefim = Util.Polar2Dm(refim, cnx, cny, numr, mode)
	Util.Frngs(crefim, numr)
	Util.Applyws(crefim, numr, wr)
	return ornq(image, crefim, xrng, yrng, step, mode, numr, cnx, cny)


def align2d_peaks(image, refim, xrng=0, yrng=0, step=1, first_ring=1, last_ring=0, rstep=1, mode = "F"):
	"""  Determine shift and rotation between image and reference image
	     quadratic interpolation
	"""
	#from utilities import print_col
	from alignment import Numrinit, ringwe
	step = float(step)
	nx = refim.get_xsize()
	ny = refim.get_ysize()
	if(last_ring == 0):  last_ring = nx/2-2-int(max(xrng,yrng))
	# center in SPIDER convention
	cnx = nx//2+1
	cny = ny//2+1
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr   = ringwe(numr, mode)
	#cimage=Util.Polar2Dmi(refim, cnx, cny, numr, mode, kb)
	crefim = Util.Polar2Dm(refim, cnx, cny, numr, mode)
	#crefim = Util.Polar2D(refim, numr, mode)
	#print_col(crefim)
	Util.Frngs(crefim, numr)
	Util.Applyws(crefim, numr, wr)
	return ormq_peaks(image, crefim, xrng, yrng, step, mode, numr, cnx, cny)

def align2d_g(image, refim, xrng=0, yrng=0, step=1, first_ring=1, last_ring=0, rstep=1, mode = "F"):
	"""  Determine shift and rotation between image and reference image
	     quadratic interpolation
	"""
	from development import ormy2
	from alignment import Numrinit, ringwe
	from fundamentals import fft
	
	step = float(step)
	nx = refim.get_xsize()
	ny = refim.get_ysize()
	if(last_ring == 0):  last_ring = nx/2-2-int(max(xrng,yrng))
	# center in SPIDER convention
	cnx = int(nx/2)+1
	cny = int(ny/2)+1
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr = ringwe(numr, mode)

	N = nx*2
	K = 6
	alpha = 1.75
	r = nx/2
	v = K/2.0/N
	kb = Util.KaiserBessel(alpha, K, r, v, N)
	refi = refim.FourInterpol(N,N,1,0)  
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	q = Processor.EMFourierFilter(refi,params)
	refi = fft(q)
	crefim = Util.Polar2Dmi(refi,cnx,cny,numr,mode,kb)

	Util.Frngs(crefim, numr)
	Util.Applyws(crefim, numr, wr)
	numr = Numrinit(first_ring, last_ring, rstep, mode)

	return ormy2(image,refim,crefim,xrng,yrng,step,mode,numr,cnx,cny,"gridding")


def directali(inima, refs, psimax=1.0, psistep=1.0, xrng=1, yrng=1, updown = "both"):
	"""
	Direct 2D alignment within a predefined angular range.  If the range is large the method will be very slow.
	refs - a stack of reference images.  If a single image, the stack will be created.
	updown - one of three keywords: both, up, down, indicating which angle to consider, 0, 180, or both.
	PAP 12/20/2014
	"""
	from fundamentals import fft, rot_shift2D, ccf
	from utilities    import peak_search, model_blank, inverse_transform2, compose_transform2
	from alignment    import parabl

	nr = int(2*psimax/psistep)+1
	nc = nr//2

	try:
		wn = len(refs)
		if(wn != nr):
			ERROR("Incorrect number of reference images","directali",1)
		ref = refs
	except:
		ref = [None]*nr
		for i in xrange(nr):  ref[i] = fft(rot_shift2D(refs,(i-nc)*psistep))

	#  Have to add 1 as otherwise maximum on the edge of the window will not be found
	wnx = 2*(xrng+1) + 1
	wny = 2*(yrng+1) + 1

	if updown == "both" or updown == "up" :    ima = fft(inima)
	if updown == "both" or updown == "down" :  imm = fft(rot_shift2D(inima,180.0, interpolation_method = 'linear'))

	print " in ali  ", psimax, psistep, xrng, yrng, wnx, wny, nr,updown 
	ma1  = -1.e23
	ma2  = -1.e23
	ma3  = -1.e23
	ma4  = -1.e23
	oma2 = [-1.e23, -1.e23, -1.e23]
	oma4 = [-1.e23, -1.e23, -1.e23]
	"""
	fft(ima).write_image('ima.hdf')
	for i in xrange(nr):  fft(ref[i]).write_image('ref.hdf',i)
	from sys import exit
	exit()
	"""
	for i in xrange(nr):
		if updown == "both" or updown == "up" :
			c = ccf(ima,ref[i])
			w = Util.window(c, wnx, wny)
			pp = peak_search(w)[0]
			px = int(pp[4])
			py = int(pp[5])
			print '  peak   ',i,pp
			#  did not find a peak, find a maximum location instead
			if( pp[0] == 1.0 and px == 0 and py == 0):
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				if(PEAKV>ma2):
					ma2  = PEAKV
					oma2 = pp+[loc[0], loc[1], loc[0], loc[1], PEAKV,(i-nc)*psistep]
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				#print ["S %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma1):
					ma1 = pp[0]
					oma1 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma2):
					ma2  = PEAKV
					oma2 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
		if updown == "both" or updown == "down" :
			c = ccf(imm,ref[i])
			w = Util.window(c, wnx, wny)
			pp = peak_search(w)[0]
			px = int(pp[4])
			py = int(pp[5])
			if( pp[0] == 1.0 and px == 0 and py == 0):
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				if(PEAKV>ma4):
					ma4  = PEAKV
					oma4 = pp+[loc[0], loc[1], loc[0], loc[1], PEAKV,(i-nc)*psistep]
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				#print ["R %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma3):
					ma3 = pp[0]
					oma3 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma4):
					ma4 = PEAKV
					oma4 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]

	print "  hoho ",updown
	print "  oma2 ",oma2
	print "  oma4 ",oma4
	if( oma2[-2] > oma4[-2] ):
		"""
		print oma1
		print oma2
		print  "        %6.2f %6.2f  %6.2f"%(oma2[-1],oma2[-4],oma2[-3])
		"""
		nalpha, ntx, nty, mirror = inverse_transform2(oma2[-1],oma2[-4],oma2[-3],0)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		peak = oma2[-2]
	else:
		"""
		print oma3
		print oma4
		"""
		nalpha, ntx, nty, junk = compose_transform2(oma4[-1],oma4[-4],oma4[-3],1.0,180.,0,0,1)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		nalpha, ntx, nty, mirror = inverse_transform2(nalpha, ntx, nty,0)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		peak = oma4[-2]
	return  nalpha, ntx, nty, peak


def preparerefsgrid(refs, psimax=1.0, psistep=1.0):
	from fundamentals import prepi, fft
	from EMAN2 import Processor

	M = refs.get_xsize()
	alpha = 1.75
	K = 6
	N = M*2  # npad*image size
	r = M/2
	v = K/2.0/N
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,
	          "alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	kb = Util.KaiserBessel(alpha, K, r, v, N)

	nr = int(2*psimax/psistep)+1
	nc = nr//2

	ref = [None]*nr
	ima,kb = prepi(refs)
	from math import radians
	psisteprad = radians(psistep)
	for i in xrange(nr):
		# gridding rotation
		ref[i] = fft(ima.rot_scale_conv_new_background_twice((i-nc)*psisteprad, 0.,0., kb, 1.))

	return  ref

def directaligridding(inima, refs, psimax=1.0, psistep=1.0, xrng=1, yrng=1, stepx = 1.0, stepy = 1.0, updown = "both"):
	"""
	Direct 2D alignment within a predefined angular range.  If the range is large the method will be very slow.
	refs - a stack of reference images.  If a single image, the stack will be created.
	updown - one of three keywords: both, up, down, indicating which angle to consider, 0, 180, or both.
	PAP 12/27/2014
	"""
	#  Eventually will have to pass kb here
	from fundamentals import fft, rot_shift2D, ccf, prepi
	from utilities    import peak_search, model_blank, inverse_transform2, compose_transform2
	from alignment    import parabl
	from EMAN2 import Processor
	print  "  directaligridding  ",psimax, psistep, xrng, yrng, stepx, stepy, updown
	M = inima.get_xsize()
	alpha = 1.75
	K = 6
	N = M*2  # npad*image size
	r = M/2
	v = K/2.0/N
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,
	          "alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	kb = Util.KaiserBessel(alpha, K, r, v, N)



	nr = int(2*psimax/psistep)+1
	nc = nr//2

	try:
		wn = len(refs)
		if(wn != nr):
			ERROR("Incorrect number of reference images","directali",1)
		"""
		N = refs[0].get_ysize()  # assumed square image
		# prepare 
		#npad = 2
		#N = nx*npad
		K = 6
		alpha = 1.75
		r = nx/2
		v = K/2.0/N
		kb = Util.KaiserBessel(alpha, K, r, v, N)
		"""
		ref = refs
	except:
		ref = [None]*nr
		ima,kb = prepi(refs)
		from math import radians
		psisteprad = radians(psistep)
		for i in xrange(nr):
			# gridding rotation
			ref[i] = fft(ima.rot_scale_conv_new_background_twice((i-nc)*psisteprad, 0.,0., kb, 1.))
			"""
			ref[i] = rot_shift2D(refs,(i-nc)*psistep, interpolation_method = 'gridding')
			ref[i] = ref[i].FourInterpol(N, N, 1,0)
			#fft(ref[i]).write_image('refprep.hdf')
			"""

	#  Window for ccf sampled by gridding
	rnx   = int((xrng/stepx+0.5))
	rny   = int((yrng/stepy+0.5))
	wnx = 2*rnx + 1
	wny = 2*rny + 1
	w = model_blank( wnx, wny)
	stepxx = 2*stepx
	stepyy = 2*stepy
	nic = N//2
	wxc = wnx//2
	wyc = wny//2

	if updown == "both" or updown == "up" :
		ima = inima.FourInterpol(N, N, 1,0)
		ima = Processor.EMFourierFilter(ima,params)

	if updown == "both" or updown == "down" :
		imm = rot_shift2D(inima,180.0, interpolation_method = 'linear')
		imm = imm.FourInterpol(N, N, 1,0)
		imm = Processor.EMFourierFilter(imm, params)

	#fft(ima).write_image('imap.hdf')
	from utilities import get_params_proj
	e1 = ref[0]['phi']
	f1,e2,e3,e4,e5 = get_params_proj(inima)
	print " in ali  ", e1,f1,psimax, psistep, xrng, yrng, wnx, wny, rnx, rny, stepxx, stepyy, nr,updown 
	ma1  = -1.e23
	ma2  = -1.e23
	ma3  = -1.e23
	ma4  = -1.e23
	oma2 = [-1.e23, -1.e23, -1.e23]
	oma4 = [-1.e23, -1.e23, -1.e23]
	"""
	fft(ima).write_image('ima.hdf')
	for i in xrange(nr):  fft(ref[i]).write_image('ref.hdf',i)
	from sys import exit
	exit()
	"""
	for i in xrange(nr):
		if updown == "both" or updown == "up" :
			c = ccf(ima,ref[i])
			#c.write_image('gcc.hdf')
			#p = peak_search(window2d(c,4*xrng+1,4*yrng+1),5)
			#for q in p: print q
			for iy in xrange(-rny, rny + 1):
				for ix in xrange(-rnx, rnx + 1):
					w[ix+rnx,iy+rny] = c.get_pixel_conv7(ix*stepxx+nic, iy*stepyy+nic, 0.0, kb)

			pp = peak_search(w)[0]
			#print '  peak   ',i,pp
			#from sys import exit
			#exit()

			px = int(pp[4])
			py = int(pp[5])
			#print '  peak   ',i,pp,px*stepx,py*stepy
			#  did not find a peak, find a maximum location instead
			if( pp[0] == 1.0 and px == 0 and py == 0):
				#  No peak!
				return  0., 0., 0., -1.0e23
				"""
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				print "  Did not find a peak  :",i,loc[0]-wxc, loc[1]-wyc, PEAKV
				if(PEAKV>ma2):
						ma2  = PEAKV
						oma2 = pp+[loc[0]-wxc, loc[1]-wyc, loc[0]-wxc, loc[1]-wyc, PEAKV,(i-nc)*psistep]
				"""
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				print ["S %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma1):
					ma1 = pp[0]
					oma1 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma2):
					ma2  = PEAKV
					oma2 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
		if updown == "both" or updown == "down" :
			c = ccf(imm,ref[i])
			for iy in xrange(-rny, rny + 1):
				for ix in xrange(-rnx, rnx + 1):
					w[ix+rnx,iy+rny] = c.get_pixel_conv7(ix*stepxx+nic, iy*stepyy+nic, 0.0, kb)
			pp = peak_search(w)[0]
			px = int(pp[4])
			py = int(pp[5])
			if( pp[0] == 1.0 and px == 0 and py == 0):
				#  No peak!
				return  0., 0., 0., -1.0e23
				"""
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				if(PEAKV>ma4):
					ma4  = PEAKV
					oma4 = pp+[loc[0], loc[1], loc[0], loc[1], PEAKV,(i-nc)*psistep]
				"""
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				print ["R %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma3):
					ma3 = pp[0]
					oma3 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma4):
					ma4 = PEAKV
					oma4 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]

	#print "  hoho ",updown
	#print "  oma2 ",oma2
	#print "  oma4 ",oma4
	if( oma2[-2] > oma4[-2] ):
		"""
		print oma1
		print oma2
		print  "        %6.2f %6.2f  %6.2f"%(oma2[-1],oma2[-4],oma2[-3])
		"""
		nalpha, ntx, nty, mirror = inverse_transform2(oma2[-1],oma2[-4]*stepx,oma2[-3]*stepy,0)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		peak = oma2[-2]
	else:
		"""
		print oma3
		print oma4
		"""
		nalpha, ntx, nty, junk = compose_transform2(oma4[-1],oma4[-4]*stepx,oma4[-3]*stepy,1.0,180.,0,0,1)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		nalpha, ntx, nty, mirror = inverse_transform2(nalpha, ntx, nty,0)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		peak = oma4[-2]
	return  nalpha, ntx, nty, peak


def directaligridding1(inima, kb, ref, psimax=1.0, psistep=1.0, xrng=1, yrng=1, stepx = 1.0, stepy = 1.0, updown = "both"):
	"""
	Direct 2D alignment within a predefined angular range.  If the range is large the method will be very slow.
	ref - a stack of reference images. 
	updown - one of three keywords: both, up, down, indicating which angle to consider, 0, 180, or both.
	PAP 01/01/2015
	"""

	from fundamentals import fft, rot_shift2D, ccf, prepi
	from utilities    import peak_search, model_blank, inverse_transform2, compose_transform2
	from alignment    import parabl
	from EMAN2 import Processor
	#print  "  directaligridding1  ",psimax, psistep, xrng, yrng, stepx, stepy, updown

	"""
	M = inima.get_xsize()
	alpha = 1.75
	K = 6
	N = M*2  # npad*image size
	r = M/2
	v = K/2.0/N
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,
	          "alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	kb = Util.KaiserBessel(alpha, K, r, v, N)
	"""


	nr = int(2*psimax/psistep)+1
	nc = nr//2

	N = inima.get_ysize()  # assumed image is square, but because it is FT take y.
	#  Window for ccf sampled by gridding
	rnx   = int((xrng/stepx+0.5))
	rny   = int((yrng/stepy+0.5))
	wnx = 2*rnx + 1
	wny = 2*rny + 1
	w = model_blank( wnx, wny)
	stepxx = 2*stepx
	stepyy = 2*stepy
	nic = N//2
	wxc = wnx//2
	wyc = wny//2

	if updown == "both" or updown == "up" :
		ima = inima
		#ima = inima.FourInterpol(N, N, 1,0)
		#ima = Processor.EMFourierFilter(ima,params)

	if updown == "both" or updown == "down" :
		#  This yields rotation by 180 degrees.  There is no extra shift as the image was padded 2x, so it is even-sized, but two rows are incorrect
		imm = inima.conjg()
		#imm = rot_shift2D(inima,180.0, interpolation_method = 'linear')
		#imm = imm.FourInterpol(N, N, 1,0)
		#imm = Processor.EMFourierFilter(imm,params)

	#fft(ima).write_image('imap.hdf')

	ma1  = -1.e23
	ma2  = -1.e23
	ma3  = -1.e23
	ma4  = -1.e23
	oma2 = [-1.e23, -1.e23, -1.e23]
	oma4 = [-1.e23, -1.e23, -1.e23]
	"""
	fft(ima).write_image('ima.hdf')
	for i in xrange(nr):  fft(ref[i]).write_image('ref.hdf',i)
	from sys import exit
	exit()
	"""
	for i in xrange(nr):
		if updown == "both" or updown == "up" :
			c = ccf(ima,ref[i])
			#c.write_image('gcc.hdf')
			#p = peak_search(window2d(c,4*xrng+1,4*yrng+1),5)
			#for q in p: print q
			for iy in xrange(-rny, rny + 1):
				for ix in xrange(-rnx, rnx + 1):
					w[ix+rnx,iy+rny] = c.get_pixel_conv7(ix*stepxx+nic, iy*stepyy+nic, 0.0, kb)

			pp = peak_search(w)[0]
			#print '  peak   ',i,pp
			#from sys import exit
			#exit()

			px = int(pp[4])
			py = int(pp[5])
			#print '  peak   ',i,pp,px*stepx,py*stepy
			#  did not find a peak, find a maximum location instead
			if( pp[0] == 1.0 and px == 0 and py == 0):
				#  No peak!
				pass
				"""
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				print "  Did not find a peak  :",i,loc[0]-wxc, loc[1]-wyc, PEAKV
				if(PEAKV>ma2):
						ma2  = PEAKV
						oma2 = pp+[loc[0]-wxc, loc[1]-wyc, loc[0]-wxc, loc[1]-wyc, PEAKV,(i-nc)*psistep]
				"""
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				#print ["S %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma1):
					ma1 = pp[0]
					oma1 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma2):
					ma2  = PEAKV
					oma2 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
		if updown == "both" or updown == "down" :
			c = ccf(imm,ref[i])
			for iy in xrange(-rny, rny + 1):
				for ix in xrange(-rnx, rnx + 1):
					w[ix+rnx,iy+rny] = c.get_pixel_conv7(ix*stepxx+nic, iy*stepyy+nic, 0.0, kb)
			pp = peak_search(w)[0]
			px = int(pp[4])
			py = int(pp[5])
			if( pp[0] == 1.0 and px == 0 and py == 0):
				#  No peak!
				pass
				"""
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				if(PEAKV>ma4):
					ma4  = PEAKV
					oma4 = pp+[loc[0], loc[1], loc[0], loc[1], PEAKV,(i-nc)*psistep]
				"""
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				#print ["R %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma3):
					ma3 = pp[0]
					oma3 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma4):
					ma4 = PEAKV
					oma4 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]

	if( oma2[-2] > oma4[-2] ):
		peak = oma2[-2]
		if( peak == -1.0e23 ):  return  0.0, 0.0, 0.0, peak
	
		"""
		print oma1
		print oma2
		print  "        %6.2f %6.2f  %6.2f"%(oma2[-1],oma2[-4],oma2[-3])
		"""
		#  The inversion would be needed for 2D alignment.  For 3D, the proper way is to return straight results.
		#nalpha, ntx, nty, mirror = inverse_transform2(oma2[-1], oma2[-4]*stepx, oma2[-3]*stepy, 0)
		nalpha = oma2[-1]
		ntx    = oma2[-4]*stepx
		nty    = oma2[-3]*stepy
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
	else:
		peak = oma4[-2]
		if( peak == -1.0e23 ):  return  0.0, 0.0, 0.0, peak
		#  This is still strange as why I would have to invert here but not for 90 degs.  PAP  01/09/2014
		#print oma3
		#print oma4

		nalpha, ntx, nty, junk = compose_transform2(-oma4[-1],oma4[-4]*stepx,oma4[-3]*stepy,1.0,180.,0,0,1)
		#nalpha = oma4[-1] + 180.0
		#ntx    = oma4[-4]*stepx
		#nty    = oma4[-3]*stepy
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		nalpha, ntx, nty, mirror = inverse_transform2(nalpha, ntx, nty, 0)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
	return  nalpha, ntx, nty, peak


def directaligriddingconstrained(inima, kb, ref, psimax=1.0, psistep=1.0, xrng=1, yrng=1, \
			stepx = 1.0, stepy = 1.0, psiref = 0., txref = 0., tyref = 0., updown = "up"):
	"""
	Direct 2D alignment within a predefined angular range.  If the range is large the method will be very slow.
	ref - a stack of reference images. 
	updown - one of two keywords:  up, down, indicating which angle to consider, 0, or 180.
	
	Usage of constrains:  Search is around the previous parameters (psiref, txref, tyref), 
	                      but only within ranges specified by (psimax, xrng, yrng).
	
	PAP 01/16/2015
	"""

	from fundamentals import fft, rot_shift2D, ccf, prepi
	from utilities    import peak_search, model_blank, inverse_transform2, compose_transform2
	from alignment    import parabl
	from EMAN2 import Processor
	#print  "  directaligridding1  ",psimax, psistep, xrng, yrng, stepx, stepy, updown
	#print  "IN         %6.2f %6.2f  %6.2f"%(psiref, txref, tyref)

	"""
	M = inima.get_xsize()
	alpha = 1.75
	K = 6
	N = M*2  # npad*image size
	r = M/2
	v = K/2.0/N
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,
	          "alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	kb = Util.KaiserBessel(alpha, K, r, v, N)
	"""


	nr = int(2*psimax/psistep)+1
	nc = nr//2
	if updown == "up" :  reduced_psiref = psiref -  90.0
	else:                reduced_psiref = psiref - 180.0
	#  Limit psi search to within psimax range
	bnr = max(int(round(reduced_psiref/psistep))+nc,0)
	enr = min(int(round(reduced_psiref/psistep))+nc+1,nr)

	N = inima.get_ysize()  # assumed image is square, but because it is FT take y.
	#  Window for ccf sampled by gridding
	#   We quietly assume the search range for translations is always much less than the ccf size,
	#     so instead of restricting anything, we will just window out ccf around previous shift locations
	rnx   = int(round(xrng/stepx))
	rny   = int(round(yrng/stepy))
	wnx = 2*rnx + 1
	wny = 2*rny + 1
	w = model_blank( wnx, wny)
	stepxx = 2*stepx
	stepyy = 2*stepy
	nicx = N//2 - 2*txref #  here one would have to add or subtract the old value.
	nicy = N//2 - 2*tyref
	wxc = wnx//2
	wyc = wny//2

	if updown == "up" :
		ima = inima
		#ima = inima.FourInterpol(N, N, 1,0)
		#ima = Processor.EMFourierFilter(ima,params)

	if updown == "down" :
		#  This yields rotation by 180 degrees.  There is no extra shift as the image was padded 2x, so it is even-sized, but two rows are incorrect
		imm = inima.conjg()
		#imm = rot_shift2D(inima,180.0, interpolation_method = 'linear')
		#imm = imm.FourInterpol(N, N, 1,0)
		#imm = Processor.EMFourierFilter(imm,params)

	#fft(ima).write_image('imap.hdf')

	ma1  = -1.e23
	ma2  = -1.e23
	ma3  = -1.e23
	ma4  = -1.e23
	oma2 = [-1.e23, -1.e23, -1.e23]
	oma4 = [-1.e23, -1.e23, -1.e23]
	"""
	fft(ima).write_image('ima.hdf')
	for i in xrange(nr):  fft(ref[i]).write_image('ref.hdf',i)
	from sys import exit
	exit()
	"""
	for i in xrange(bnr, enr, 1):
		if updown == "up" :
			c = ccf(ima,ref[i])
			#c.write_image('gcc.hdf')
			#p = peak_search(window2d(c,4*xrng+1,4*yrng+1),5)
			#for q in p: print q
			for iy in xrange(-rny, rny + 1):
				for ix in xrange(-rnx, rnx + 1):
					w[ix+rnx,iy+rny] = c.get_pixel_conv7(ix*stepxx+nicx, iy*stepyy+nicy, 0.0, kb)

			pp = peak_search(w)[0]
			#print '  peak   ',i,pp
			#from sys import exit
			#exit()

			px = int(pp[4])
			py = int(pp[5])
			#print '  peak   ',i,pp,px*stepx,py*stepy
			#  did not find a peak, find a maximum location instead
			if( pp[0] == 1.0 and px == 0 and py == 0):
				#  No peak!
				pass
				"""
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				print "  Did not find a peak  :",i,loc[0]-wxc, loc[1]-wyc, PEAKV
				if(PEAKV>ma2):
						ma2  = PEAKV
						oma2 = pp+[loc[0]-wxc, loc[1]-wyc, loc[0]-wxc, loc[1]-wyc, PEAKV,(i-nc)*psistep]
				"""
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				#print ["S %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma1):
					ma1 = pp[0]
					oma1 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma2):
					ma2  = PEAKV
					oma2 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
		if updown == "down" :
			c = ccf(imm,ref[i])
			for iy in xrange(-rny, rny + 1):
				for ix in xrange(-rnx, rnx + 1):
					w[ix+rnx,iy+rny] = c.get_pixel_conv7(ix*stepxx+nicx, iy*stepyy+nicy, 0.0, kb)
			pp = peak_search(w)[0]
			px = int(pp[4])
			py = int(pp[5])
			if( pp[0] == 1.0 and px == 0 and py == 0):
				#  No peak!
				pass
				"""
				loc = w.calc_max_location()
				PEAKV = w.get_value_at(loc[0],loc[1])
				if(PEAKV>ma4):
					ma4  = PEAKV
					oma4 = pp+[loc[0], loc[1], loc[0], loc[1], PEAKV,(i-nc)*psistep]
				"""
			else:
				ww = model_blank(3,3)
				px = int(pp[1])
				py = int(pp[2])
				for k in xrange(3):
					for l in xrange(3):
						ww[k,l] = w[k+px-1,l+py-1]
				XSH, YSH, PEAKV = parabl(ww)
				#print ["R %10.1f"%pp[k] for k in xrange(len(pp))]," %6.2f %6.2f  %6.2f %6.2f %12.2f  %4.1f"%(XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep)
				"""
				if(pp[0]>ma3):
					ma3 = pp[0]
					oma3 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]
				"""
				if(PEAKV>ma4):
					ma4 = PEAKV
					oma4 = pp+[XSH, YSH,int(pp[4])+XSH, int(pp[5])+YSH, PEAKV,(i-nc)*psistep]

	if( oma2[-2] > oma4[-2] ):
		peak = oma2[-2]
		if( peak == -1.0e23 ):  return  0.0, 0.0, 0.0, peak
	
		"""
		print oma1
		print oma2
		print  "        %6.2f %6.2f  %6.2f"%(oma2[-1],oma2[-4],oma2[-3])
		"""
		#  The inversion would be needed for 2D alignment.  For 3D, the proper way is to return straight results.
		#nalpha, ntx, nty, mirror = inverse_transform2(oma2[-1], oma2[-4]*stepx, oma2[-3]*stepy, 0)
		nalpha = oma2[-1]
		ntx    = oma2[-4]*stepx - txref
		nty    = oma2[-3]*stepy - tyref
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
	else:
		peak = oma4[-2]
		if( peak == -1.0e23 ):  return  0.0, 0.0, 0.0, peak
		#  This is still strange as why I would have to invert here but not for 90 degs.  PAP  01/09/2014
		#print oma3
		#print oma4

		nalpha, ntx, nty, junk = compose_transform2(-oma4[-1], oma4[-4]*stepx - txref,oma4[-3]*stepy - tyref,1.0,180.,0,0,1)
		#nalpha = oma4[-1] + 180.0
		#ntx    = oma4[-4]*stepx
		#nty    = oma4[-3]*stepy
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
		nalpha, ntx, nty, mirror = inverse_transform2(nalpha, ntx, nty, 0)
		#print  "        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
	#print  "OUT        %6.2f %6.2f  %6.2f"%(nalpha, ntx, nty)
	return  nalpha, ntx, nty, peak


def ali_nvol(v, mask):
	from alignment    import alivol_mask_getref, alivol_mask
	from statistics   import ave_var
	from utilities    import set_params3D, get_params3D ,compose_transform3

	from fundamentals import rot_shift3D
	ocrit = 1.0e20
	gogo = True
	niter = 0
	for l in xrange(len(v)):  set_params3D( v[l],   (0.0,0.0,0.0,0.0,0.0,0.0,0,1.0))
	while(gogo):
	        ave,var = ave_var(v)
	        p = Util.infomask(var, mask, True)
	        crit = p[1]
	        if((crit-ocrit)/(crit+ocrit)/2.0 > -1.0e-2 or niter > 10):  gogo = False
	        niter += 1
	        ocrit = crit
	        ref = alivol_mask_getref(ave, mask)
	        for l in xrange(len(v)):
				ophi,otht,opsi,os3x,os3y,os3z,dum, dum = get_params3D(v[l])
				vor = rot_shift3D(v[l], ophi,otht,opsi,os3x,os3y,os3z )
				phi,tht,psi,s3x,s3y,s3z = alivol_mask(vor, ref, mask)
				phi,tht,psi,s3x,s3y,s3z,scale = compose_transform3(phi,tht,psi,s3x,s3y,s3z,1.0,ophi,otht,opsi,os3x,os3y,os3z,1.0)
				set_params3D(v[l],  (phi,tht,psi,s3x,s3y,s3z,0,1.0))
				#print "final align3d params: %9.4f %9.4f %9.4f %9.4f %9.4f %9.4f" % (phi,tht,psi,s3x,s3y,s3z)
	for l in xrange(len(v)):
		ophi,otht,opsi,os3x,os3y,os3z,dum,dum = get_params3D(v[l])
		print  l,ophi,otht,opsi,os3x,os3y,os3z
		v[l] = rot_shift3D( v[l], ophi,otht,opsi,os3x,os3y,os3z )
		v[l].del_attr("xform.align3d")
	return v

def alivol_mask_getref( v, mask ):
	from utilities import set_params3D
	v50S_ref = v.copy()
	v50S_ref *= mask
	cnt = v50S_ref.phase_cog()
	set_params3D( v50S_ref, (0.0,0.0,0.0,-cnt[0],-cnt[1],-cnt[2],0,1.0) )
	return v50S_ref

def alivol_mask( v, vref, mask ):
	from utilities    import set_params3D, get_params3D,compose_transform3
	from applications import ali_vol_shift, ali_vol_rotate
	v50S_i = v.copy()
	v50S_i *= mask
	cnt = v50S_i.phase_cog()
	set_params3D( v50S_i,   (0.0,0.0,0.0,-cnt[0],-cnt[1],-cnt[2],0,1.0) )

	v50S_i = ali_vol_shift( v50S_i, vref, 1.0 )
	v50S_i = ali_vol_rotate(v50S_i, vref, 5.0 )
	v50S_i = ali_vol_shift( v50S_i, vref, 0.5 )
	v50S_i = ali_vol_rotate(v50S_i, vref, 1.0 )
	phi,tht,psi,s3x,s3y,s3z,mirror,scale = get_params3D( v50S_i )
	dun,dum,dum,cnx,cny,cnz,mirror,scale = get_params3D( vref )
	phi,tht,psi,s3x,s3y,s3z,scale = compose_transform3(phi,tht,psi,s3x,s3y,s3z,1.0,0.0,0.0,0.0,-cnx,-cny,-cnz,1.0)
	return phi,tht,psi,s3x,s3y,s3z

def ali_mvol(v, mask):
	from alignment    import alivol_m
	from statistics   import ave_var
	from utilities    import set_params3D, get_params3D ,compose_transform3

	from fundamentals import rot_shift3D
	ocrit = 1.0e20
	gogo = True
	niter = 0
	for l in xrange(len(v)):  set_params3D( v[l],   (0.0,0.0,0.0,0.0,0.0,0.0,0,1.0))
	while(gogo):
	        ave,var = ave_var(v)
	        set_params3D( ave,   (0.0,0.0,0.0,0.0,0.0,0.0,0,1.0))
	        p = Util.infomask(var, mask, True)
	        crit = p[1]
	        if((crit-ocrit)/(crit+ocrit)/2.0 > -1.0e-2 or niter > 10):  gogo = False
	        niter += 1
	        ocrit = crit
	        ave *= mask
	        for l in xrange(len(v)):
				ophi,otht,opsi,os3x,os3y,os3z,dum, dum = get_params3D(v[l])
				vor = rot_shift3D(v[l], ophi,otht,opsi,os3x,os3y,os3z )
				phi,tht,psi,s3x,s3y,s3z = alivol_m(vor, ave, mask)
				phi,tht,psi,s3x,s3y,s3z,scale = compose_transform3(phi,tht,psi,s3x,s3y,s3z,1.0,ophi,otht,opsi,os3x,os3y,os3z,1.0)
				set_params3D(v[l],  (phi,tht,psi,s3x,s3y,s3z,0,1.0))
				#print "final align3d params: %9.4f %9.4f %9.4f %9.4f %9.4f %9.4f" % (phi,tht,psi,s3x,s3y,s3z)
	for l in xrange(len(v)):
		ophi,otht,opsi,os3x,os3y,os3z,dum,dum = get_params3D(v[l])
		print  i,ophi,otht,opsi,os3x,os3y,os3z
		v[l] = rot_shift3D( v[l], ophi,otht,opsi,os3x,os3y,os3z )
		v[l].del_attr("xform.align3d")
	return v

def alivol_m( v, vref, mask ):
	from utilities    import set_params3D, get_params3D,compose_transform3
	from applications import ali_vol_shift, ali_vol_rotate
	vola = v.copy()
	vola *= mask
	set_params3D( vola,   (0.0,0.0,0.0,0.0,0.0,0.0,0,1.0) )

	vola = ali_vol_shift( vola, vref, 1.0 )
	vola = ali_vol_rotate(vola, vref, 5.0 )
	vola = ali_vol_shift( vola, vref, 0.5 )
	vola = ali_vol_rotate(vola, vref, 1.0 )
	phi,tht,psi,s3x,s3y,s3z,mirror,scale = get_params3D( vola )
	return phi,tht,psi,s3x,s3y,s3z


# =================== SHC

def shc(data, refrings, numr, xrng, yrng, step, an = -1.0, sym = "c1", finfo=None):
	from utilities    import inverse_transform2
	from math         import cos, sin, pi, degrees, radians
	from EMAN2 import Vec2f

	ID = data.get_attr("ID")

	number_of_checked_refs = 0

	mode = "F"
	nx   = data.get_xsize()
	ny   = data.get_ysize()
	#  center is in SPIDER convention
	cnx  = nx//2 + 1
	cny  = ny//2 + 1

	if( an>= 0.0):  ant = cos(radians(an))
	else:           ant = -1.0
	#phi, theta, psi, sxo, syo = get_params_proj(data)
	t1 = data.get_attr("xform.projection")
	#dp = t1.get_params("spider")
	if finfo:
		finfo.write("Image id: %6d\n"%(ID))
		#finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(phi, theta, psi, sxo, syo))
		finfo.write("Old parameters: %9.4f %9.4f %9.4f %9.4f %9.4f\n"%(dp["phi"], dp["theta"], dp["psi"], -dp["tx"], -dp["ty"]))
		finfo.flush()

	previousmax = data.get_attr("previousmax")
	[ang, sxs, sys, mirror, iref, peak, checked_refs] = Util.shc(data, refrings, xrng, yrng, step, ant, mode, numr, cnx, cny, sym)  #+dp["tx"], cny+dp["ty"])
	iref=int(iref)
	number_of_checked_refs += int(checked_refs)
	#[ang,sxs,sys,mirror,peak,numref] = apmq_local(projdata[imn], ref_proj_rings, xrng, yrng, step, ant, mode, numr, cnx-sxo, cny-syo)
	#ang = (ang+360.0)%360.0

	if peak <= previousmax:
		return -1.0e23, 0.0, number_of_checked_refs, -1
		"""
		# there is no better solutions - if the current position is free, we don't change anything
		last_phi = dp["phi"]
		last_theta = dp["theta"]
		found_current_location = False
		for ir in xrange(len(refrings)):
			r = refrings[ir]
			if abs(last_phi - r.get_attr("phi")) < 0.1 and abs(last_theta - r.get_attr("theta")) < 0.1:
				found_current_location = True
				break
		if found_current_location:
			return -1.0e23, 0.0, number_of_checked_refs, ir
		"""
	else:
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		# What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = inverse_transform2(ang, sxs, sys, 0)
		if  mirror:
			phi   = (refrings[iref].get_attr("phi")+540.0)%360.0
			theta = 180.0-refrings[iref].get_attr("theta")
			psi   = (540.0-refrings[iref].get_attr("psi")+angb)%360.0
			s2x   = sxb #- dp["tx"]
			s2y   = syb #- dp["ty"]
		else:
			phi   = refrings[iref].get_attr("phi")
			theta = refrings[iref].get_attr("theta")
			psi   = (refrings[iref].get_attr("psi")+angb+360.0)%360.0
			s2x   = sxb #- dp["tx"]
			s2y   = syb #- dp["ty"]

		#set_params_proj(data, [phi, theta, psi, s2x, s2y])
		t2 = Transform({"type":"spider","phi":phi,"theta":theta,"psi":psi})
		t2.set_trans(Vec2f(-s2x, -s2y))
		data.set_attr("xform.projection", t2)
		data.set_attr("previousmax", peak)
		from pixel_error import max_3D_pixel_error
		pixel_error = max_3D_pixel_error(t1, t2, numr[-3])
		if finfo:
			finfo.write( "New parameters: %9.4f %9.4f %9.4f %9.4f %9.4f %10.5f  %11.3e\n\n" %(phi, theta, psi, s2x, s2y, peak, pixel_error))
			finfo.flush()
		return peak, pixel_error, number_of_checked_refs, iref
