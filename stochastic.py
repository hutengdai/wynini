# Globally normalize acyclic machine over log semiring
# and generate random samples

import sys
import numpy as np
from pynini import Weight

sys.path.append('..')
from wynini import config as wfst_config
from wynini.wfst import *

# Alphabet
config = {'sigma': ['a', 'b', 'c', 'd', 'e']}
wfst_config.init(config)

# Weighted acceptor
M = Wfst(wfst_config.symtable, arc_type='log')
for q in [0, 1, 2, 3, 4, 5]:
	M.add_state(q)
M.set_start(0)
M.set_final(5, Weight('log', 1.0))

w = -np.log(0.5)  # plog(1/2)

#try different weights; generate sample for a grammar
# encode an WFSA that generates sigma*
alphabet = {'a','b','c'}
grammar = {("a","b")}
# alphabet.add(wfst_config.bos)
# alphabet.add(wfst_config.eos)
phone2ix = {p: (ix+2) for (ix, p) in enumerate(alphabet)}

print(phone2ix)

M.add_arc(src=0, ilabel=wfst_config.bos, weight=Weight('log', 1.0), dest=1)
	
for symbol1 in alphabet:
	M.add_arc(src= 1, ilabel=symbol1,weight=Weight('log', w), dest = phone2ix[symbol1])
	M.add_arc(src=phone2ix[symbol1], ilabel=wfst_config.eos, weight=Weight('log', 1.0), dest=len(alphabet)+2)
	for symbol2 in alphabet:
		for constraint in grammar:
			if constraint[0] == symbol1:
				if constraint[1] == symbol2:
					M.add_arc(src=phone2ix[symbol1], ilabel=symbol2, weight=Weight('log', 0), dest=phone2ix[symbol2])

				else:
					M.add_arc(src=phone2ix[symbol1], ilabel=symbol2, weight=Weight('log', w), dest=phone2ix[symbol2])



# M.add_arc(src=1, ilabel='a', weight=Weight('log', w), dest=2)
# M.add_arc(src=1, ilabel='b', weight=Weight('log', w), dest=3)
# M.add_arc(src=2, ilabel='c', weight=Weight('log', w), dest=4)
# M.add_arc(src=2, ilabel='d', weight=Weight('log', w), dest=4)
# M.add_arc(src=3, ilabel='e', weight=Weight('log', w), dest=4)
print(M.print(acceptor=True, show_weight_one=True))
M.draw('M.dot')

# Push weights toward initial state
M_push = M.push_weights()
print(M_push.print(acceptor=True, show_weight_one=True))
M_push.draw('M_push.dot')

# Generate random sample of accepted strings
samp = M_push.randgen(npath=100, select='log_prob')
print(list(samp))
