#!/usr/bin/python3

# =============================================================================
# This script generalizes ECA to QECA with irreversible, asynchronus updating. 
# The state vector is renormalized at after each complete update since
# irreversibilities in ECA rules will not conserve probability. An update is
# complete once each state has been updated by the local update operator, which
# acts on one Moore neighborhood at a time. In otherwords, the update is
# asynchonus because the local update operator is swept across the lattice
# sequentially. 
#
# By Logan Hillberry
# =============================================================================



from itertools import product, cycle
from os.path   import isfile
from cmath     import sqrt
from math import sin, cos, pi, fabs
import copy 
import time

import numpy    as np

import fio      as io
import matrix   as mx
import states   as ss
import measures as ms

# Sweep updating ECA
# ==================
def local_update_op(R, center_op=ss.ops['X']):

    update_dict = {0 : np.eye(2), 1 : ss.ops['X'], 2 : center_op} # center_op = X is closest to classical ECA
    
    sxR = 204^R                                  # calculate swap rule s.t. 0 -> I, 1 -> sx

    sxR = np.array(mx.dec_to_bin(sxR, 2**3)[::-1])         # reverse so rule element 0 comes first
   
    '''
    op_inds = [ind for ind, val in enumerate(sxR) if val == 1]
    
    sxR[op_inds[0]] = 2
    sxR[op_inds[1]] = 2
    sxR[op_inds[2]] = 2
    sxR[op_inds[3]] = 2
    '''
    sxR[sxR>0]=2
    print(sxR) 
    op = np.zeros((2**3, 2**3), dtype=complex)

    for Rel_num, sxR_el in enumerate(sxR):      # Rel_num -> sxR_el:  000 -> 1,
        op_sub_el_list = [] 
       
        for sub_Rel_num, proj_label in enumerate(mx.dec_to_bin(Rel_num, 3)[::-1]):
            if sub_Rel_num == 1:                # sub_rel_num == 1 is center site
                op_sub_el = \
                        update_dict[sxR_el].dot(ss.ops[str(proj_label)]) 

            else:
                op_sub_el = ss.ops[str(proj_label)]  # leave neighbors alone

            op_sub_el_list.append(op_sub_el)         # make the 3-site update op

        op = op + mx.listkron(op_sub_el_list) 

    return op

def comp_basis_vec(bin_num_as_list):
    bin_num_as_str = map(str, bin_num_as_list)
    vec_list =[]
    for bin_str in bin_num_as_str:
        vec_list.append(ss.bvecs[bin_str])
    return mx.listkron(vec_list)

def general_local_update_op(R, th=pi/2.0):
    R = mx.dec_to_bin(R, 2**3)[::-1]        # reverse so rule element 0 comes first
    T = np.zeros((2**3, 2**3), dtype=complex)
    
    for d, r in  enumerate(R):     
        d_b = mx.dec_to_bin(d, 3)[::-1]
        r_b = copy.copy(d_b)
        
        if r_b[1] == r:
            thr = 0.0
        else:
            thr = th
            r_b[1] = r

        self = comp_basis_vec(d_b)
        flip = comp_basis_vec(r_b)
        
        ket = (cos(thr) * self + sin(thr) * flip)
       
        ket_bra = np.outer(ket, self)
        T = T + ket_bra
    return mx.edit_small_vals(T)

# construct generator for sweep time evolved states
# -------------------------------------------------
def time_evolve(params, tol=1E-10):
    mode = params['mode']
    R = params['R']
    IC = params['IC']
    L = params['L'] 
    tmax = params['tmax']
    center_op = mx.listdot([ss.ops[k] for k in params['center_op']])
    Tj = local_update_op(R, center_op=center_op)
    
    #Tj = np.array([[1,0,0,0],[0,0,1,0],[0,1/sqrt(2),0,1/sqrt(2)],[0,1j/sqrt(2),0,-1j/sqrt(2)]]).T
    
    state = ss.make_state(L, IC)
    state = np.kron(state, ss.bvecs['0'])

    yield state 
    
    # Sweep ECA 
    for t in np.arange(tmax):
        if mode=='sweep':
            for j in range(L):
                js = [(j-1)%(L+1), j, (j+1)%(L+1)]
                state = mx.op_on_state(Tj, js, state)

            ip = (state.conj().dot(state)).real
            
            if fabs(ip - 1.0) < tol:
                yield state
            
            else: 
                print('t = ', t, 'ip = ', ip)
                state = 1.0/sqrt(ip) * state
                yield state

    # Block ECA 
        elif mode=='block':
            for k in [0,1,2]:
                for j in range(k, L+k, 3):
                    js = [(j-1)%(L+1), j%(L+1), (j+1)%(L+1)]
                    if j==L:
                        continue
                    state = mx.op_on_state(Tj, js, state)

            ip = (state.conj().dot(state)).real
            
            if fabs(ip - 1.0) < tol:
                yield state
            
            else: 
                print('t = ', t, 'ip = ', ip)
                state = 1.0/sqrt(ip) * state
                yield state

# import/create measurement results and plot them
# -----------------------------------------------
def run_sim(params, force_rewrite = False):
    output_name = params['output_name']
    mode = params['mode']
    ic_name = io.IC_name(params['IC'])

    fname = io.file_name(output_name, 'data', io.sim_name(params), '.res' )
    if ic_name[0] == 'r' and isfile(fname) and not force_rewrite:
        fname_list = list(fname) 
        fname_list[-5] = str(eval(fname[-5])+1)
        fname = ''.join(fname_list)

    print(fname)
    if not isfile(fname) or force_rewrite:
        results = ms.simple_measure_sim(params, time_evolve(params))
        io.write_results(results, fname)
    
    print('results saved to: ', fname)



