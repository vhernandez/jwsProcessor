#!/urs/bin/env python
# -*- coding: UTF8 -*-
"""
PySMOOTHING Library v 0.11
*  Copyright (C) 2005 Victor M. Hernandez Rocamora
*  Code for Savitsky-Golay filtering converted from MatLab code of 'sgolay' and
   'sgolayfilt' functions from Octave software(http://www.octave.org/), which
   are Copyright (C) 2001 Paul Kienzle.

This module is licenced under the GNU General Public License 2.0 or a later
version.
"""
#Numpy:
from numpy import array, repeat, concatenate, ones, zeros, arange, reshape, put, add, dot, take, float32
from numpy.linalg import pinv
#SciPy:
from scipy.signal.signaltools import lfilter

def mean_movement(input_data, window):
    if window%2 != 1:
        raise Exception, "'mean_movement' function needs an odd window length"
    if window > (len(input_data))+2:
        raise Exception, "'mean_movement' function: input data too short"
    input_data = list(input_data)
    output_data = []
    length = len(input_data)
    n = (window-1)/2
    input_data2 = ([input_data[0]]*n) + list(input_data)+ ([input_data[length-1]]*(n+1))
    _sum=0.0
    for i in xrange(0, window):
      _sum+=input_data2[i]
    w  = float(window)
    for i in xrange(n, n+length):
      output_data.append(_sum/window)
      _sum -= input_data2[i-n]
      _sum += input_data2[i+n+1]
    return output_data

def _mean_movement_only_python(data, m):
    if m > (2*len(data))+2:
        return data
    input_array = list(data)
    output_array = list(data)
    mean_factor = (2*m)+1
    length = len(data)
    # Process data from the middle
    for i in xrange(m, length-m):
        _sum = 0
        for j in xrange(i-m, i+m):
            _sum += input_array[j]
        output_array[i] = _sum/mean_factor
    # Process data from the beginning
    window = 1
    for i in xrange(1, m):
        _sum = 0
        for j in xrange(i-window, i+window):
            _sum += input_array[j]
        output_array[i] = _sum/((2*window)+1)
        window += 1
    output_array[0] = input_array[0]
    #Process data from the end
    window = 1
    for i in reversed(xrange(length-m, length-1)):
        _sum = 0
        for j in xrange(i-window, i+window):
            _sum += input_array[j]
        output_array[i] = _sum/((2*window)+1)
        window +=1
    output_array[length-1] = input_array[length-1]
    del input_array
    return output_array

def sgolay(p, n):
    if n%2 != 1:
        raise Exception, "'sgolay' function needs an odd filter length n"
    elif p >= n:
        raise Exception, "'sgolay' function needs filter length n larger than polynomial order p"
    k = int(n/2)
    F = zeros((n,n), float32)
    for row in range(1,k+2):
        #A = pinv( ( [(1:n)-row]'*ones(1,p+1) ) .^ ( ones(n,1)*[0:p] ) );
        left = dot( reshape(arange(1,n+1)-row, (-1,1)), ones((1,p+1)))
        right = repeat([range(0,p+1)], n, 0)
        #A = generalized_inverse( left**right )
        A = pinv( left**right )                
        #F(row,:) = A(1,:); 
        put(F.ravel(), add(arange(n),n*(row-1)), A[0])
        
    #F(k+2:n,:) = F(k:-1:1,n:-1:1);
    for fila in range(k+1, n):
        put (F.ravel(), add(arange(n),n*fila), F[n-1-fila][::-1])

    return F

def sgolayfilt(x, p, n ):
    x = array(x, float32).ravel()   
    size = len(x)
    if size < n:
        raise Exception, "'sgolayfilt': insufficient data for filter"
    ## The first k rows of F are used to filter the first k points
    ## of the data set based on the first n points of the data set.
    ## The last k rows of F are used to filter the last k points
    ## of the data set based on the last n points of the dataset.
    ## The remaining data is filtered using the central row of F.
    F = sgolay(p, n)
    k = int(n/2)
    #z = filter(F(k+1,:), 1, x);
    z = lfilter(F[k], 1, x)
    #y = [ F(1:k,:)*x(1:n,:) ; z(n:len,:) ; F(k+2:n,:)*x(len-n+1:len,:) ];    
    left = dot(take(F, arange(k),0), take(x, arange(n),0))  
    right = dot(take(F, arange(k+1,n),0), take(x, arange(size-n, size),0))
    middle = take(z, arange(n-1, size))
    return concatenate((left, middle, right))


def test1():
    ### Demo requires Matplotlib!!!! ###
    import pylab
    import random
    import math         
    import time

    def _gen_noisy_sine():
        dataset = []
        sign_vector = (-1,1)
        for i in range(360):        
            sinval = math.sin(math.radians(i))
            randint = float(random.randint(5,50))
            randsign = float(random.choice(sign_vector))
            randval = (random.random()/randint)*randsign
            dataset.append(sinval + randval)
        return dataset

    noisy_data = _gen_noisy_sine()

    TIMES = 100
    print "Testing differents algorithms, executing each one", TIMES, "times:"
    # test means movement algorithm   
    t1 = time.clock()
    for i in xrange(TIMES):
        _mean_movement_only_python(noisy_data, 25)
    t2 = time.clock()
    print "\t- Python-only Means Movement algorithm:", t2-t1, 's'
   
    t1 = time.clock()
    for i in xrange(TIMES):
        mean_movement(noisy_data, 25)
    t2 = time.clock()
    print "\t- Python-only Means Movement algorithm 2:", t2-t1, 's'
   
    t1 = time.clock()
    for i in xrange(TIMES):    
        sgolayfilt(noisy_data, 1, 25)
    t2 = time.clock()
    print "\t- Savitsky-Golay algorithm", t2-t1, 's'

    mm_denoised_data = mean_movement(noisy_data, 25)
    sg_denoised_data = sgolayfilt(noisy_data, 1, 25)
    pylab.plot(noisy_data, "r",
               mm_denoised_data, "g",
               sg_denoised_data, "b")
    pylab.legend(("Original", "Means movement", "Savitsky-Golay"))
    pylab.show()

def test2():
  import jwslib
  import sys
  results = jwslib.read_file("spc.jws")
  if results[0] == jwslib.JWS_ERROR_SUCCESS:
    header = results[1]
    channels = results[2]
  else:
    sys.exit(-1)
  channels[0] = mean_movement(channels[0], 25)
  jwslib.dump_channel_data('feo3.txt', header, channels)

def test3():
  import jwslib
  import sys
  results = jwslib.read_file("spc.jws")
  if results[0] == jwslib.JWS_ERROR_SUCCESS:
    header = results[1]
    channels = results[2]
  else:
    sys.exit(-1)
  original = channels[0]
  for i in range(5,25,2):
    channels[0] = sgolayfilt(original, 1, i)
    jwslib.dump_channel_data('spc_sg_1_%d.txt'%i, header, channels)



if __name__=="__main__":
  test1()
  
  
