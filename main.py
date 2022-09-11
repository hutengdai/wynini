from data_proc import *
from itertools import product
from pynini import Weight
import sys
sys.path.append('..')
from wynini import config as wfst_config
from wynini.wfst import *

def OEcalc(sl2_sample, sl2_possible, alphabet):
	
	# given data, constraint
	# return the violations of each constraint
	O = {i:0 for i in sl2_possible}
	n_sigma1 = {s:0 for s in alphabet}
	n_sigma2 = {s:0 for s in alphabet}

	for j in sl2_sample:
		if j in sl2_possible:
			n_sigma1[j[0]] += 1
			n_sigma2[j[1]] += 1
			for i in range(len(sl2_possible)):
			# 𝑁(𝜎1) the amount of a in first postion of sl2_sample
				if j == sl2_possible[i]:
				# count 1 for the constraint's negative constraint
					O[sl2_possible[i]] += 1
	# print(sl2_sample)
	try:
		E = {i:n_sigma1[i[0]]*n_sigma2[i[1]]/len(sl2_sample) for i in O}
		OE = {i:round(O[i]/(n_sigma1[i[0]]*n_sigma2[i[1]]/len(sl2_sample)),3) for i in O}
		return O, E, OE
	except:
		pass
	
class hypothesis_grammar():
	'''
	(1) Create a class to group functions and data for future usage
	(2) Store the grammar/automata and updated counts to the class.
	'''
	def __init__(self, alphabet, sample, edges, locality, k, tier, grammar):
		# super().__init__(alphabet,sample, edges, locality, k, tier)

	# initialize a hypothesis grammar with corresponding O/E
		self.alphabet = alphabet
		self.tier = tier
		# self.nontier = [x for x in alphabet if x not in tier]
		self.k = k
		self.edges = edges
		self.locality = locality
		self.grammar = grammar

		self.sl2_possible = [tuple(comb) for comb in product(self.tier, repeat=2)]
		for i in grammar:
			self.sl2_possible.remove(i)
		self.sl2_sample, self.sample = self.ngramize_list(sample, grammar)
		self.O = {i:0 for i in self.sl2_possible}
		# this two lines find all the bigrams in given dataset, ignoring unigrams.
		
		# self.O, self.E, self.OE = OEcalc(self.sl2_sample, self.sl2_possible, alphabet)
		# self.OE = {constraint:self.O[constraint]*len(self.sl2_possible) for constraint in self.sl2_possible}
	
	def set_grammar(self, alphabet,sample, edges, locality, k, tier, grammar):
		self.__init__(alphabet,sample, edges, locality, k, tier,grammar)

	def ngramize_list(self, sample, grammar):
		# print("sample\t"+str(sample))
		'''input sample and grammar; remove all words violating the grammar; 
		return ngram list for the rest of words'''
		# if self.locality == "sl":
		def match(str2ngram,grammar):
			violation = 0 
			for ngram in str2ngram:
				if ngram in grammar:
					# print("constraint\t"+ str(ngram))
					violation += 1
			if violation >= 1:
				return True
			else:
				return False
					
		ng_list = []
		sample_list = []
		for string in sample:
			str2ngram = ngramize_item(self.tier_image(string),k)
			# print('str2ngram\t' + str(str2ngram))
			if match(str2ngram,grammar) == False:
				ng_list += str2ngram
				sample_list += [string]
			# else:
				# print("illegal string\t" + str(string)) 
				# print("str2ngram\t" + str(str2ngram))
				# print("grammar\t" + str(grammar))
				
				# elif self.locality == "sp":
				# 	for sublist in subsequences(self.tier_image(string),k):
				# 		ng_list.append(sublist)
		# pp.pprint(sample_list)
		return ng_list, sample_list

	def tier_image(self, string):
		"""Function that returns a tier image of the input string.

		Arguments:
			string (str): string that needs to be processed.
		Returns:
			str: tier image of the input string.
		"""
		return [i for i in string if i in self.tier]

def generate_expected(alphabet,grammar,len_vector):
	process_grammar = []
	for x in grammar:
		y = ''.join(x)
		process_grammar.append(y)
		
	raw_data = []
	# only generate certain amount of string for a given string? 
	for i in range(1,max_length):
		if len_vector[i] != 0:
		# raw_data += list(sl_sats_l(lexpn(alphabet,i+1),process_grammar))
			raw_data += list(sl_sats_l(lexpn(alphabet,i+1),process_grammar))
	
	raw_data.sort()
	sample = []
	for line in raw_data:
		line = line.rstrip()
		# line = ['<s>'] + line.split(' ') + ['<e>']
		line = [char for char in line]
		sample.append(line)
	random.shuffle(sample)

	return sample

def generate_expected_wynini(alphabet,grammar,len_vector):
	# Alphabet
	alphabet = list(alphabet)
	phone2ix = {p: (ix+2) for (ix, p) in enumerate(alphabet)}

	print(phone2ix)
	config = {'sigma': alphabet}
	wfst_config.init(config)
	# # Weighted acceptor
	M = Wfst(wfst_config.symtable, arc_type='log')

	final = len(alphabet)+2
	for q in range(final+1):
		print(q)
		M.add_state(q)
	M.set_start(0)
	M.set_final(final, Weight('log', 1.0))

	w = -np.log(0.5)  # plog(1/2)
	M.add_arc(src=0, ilabel=wfst_config.bos, weight=Weight('log', 1.0), dest=1)
		
	for symbol1 in alphabet:
		M.add_arc(src= 1, ilabel=symbol1,weight=Weight('log', w), dest = phone2ix[symbol1])
		M.add_arc(src=phone2ix[symbol1], ilabel=wfst_config.eos, weight=Weight('log', 1.0), dest=len(alphabet)+2)
		for symbol2 in alphabet:
			if grammar != {}:
				for constraint in grammar:
					if constraint[0] == symbol1:
						if constraint[1] == symbol2:
							M.add_arc(src=phone2ix[symbol1], ilabel=symbol2, weight=Weight('log', 0), dest=phone2ix[symbol2])
						else:
							M.add_arc(src=phone2ix[symbol1], ilabel=symbol2, weight=Weight('log', w), dest=phone2ix[symbol2])
			else:
				M.add_arc(src=phone2ix[symbol1], ilabel=symbol2, weight=Weight('log', w), dest=phone2ix[symbol2])

	print(M.print(acceptor=True, show_weight_one=True))
	M.draw('M.dot')
	# Push weights toward initial state
	M_push = M.push_weights()
	print(M_push.print(acceptor=True, show_weight_one=True))
	M_push.draw('M_push.dot')

	# Generate random sample of accepted strings
	samp = M_push.randgen(npath=1000, select='log_prob')
	print(list(samp))

	return samp

class learner_memorize():
	'''
	(1) memorize expected strings for a given grammar 
	(2) changed for every update on grammar;
	'''
	def __init__(self, alphabet, grammar, len_vector):
		"""
		Purpose: initialize
		"""
		self.expected_strings = generate_expected(alphabet, grammar, len_vector)
		

def learner(alphabet, sample, edges, locality, k, tier, grammar, gap):
	previous_grammar = grammar

	grammar_neg = {}
	grammar_pos = {}

	# observed_grammar = hypothesis_grammar(alphabet, sample, edges, locality, k, tier, grammar)
	
	# Remove any 2-factors if it's already in the grammar. Don't worry about 
	# the dict type, i will just be key in the dictionary.
	# print("observed_O: " + str(observed_grammar.O))	
	# print("observed_E: " + str(observed_grammar.E))
	# print("observed_OE: " + str(observed_grammar.OE))

	# print("observed_last_grammar: " + str(observed_grammar.grammar))

	expected_strings = generate_expected_wynini(alphabet,grammar,len_vector)


	# idealized_grammar?
	# hypothesized_grammar = hypothesis_grammar(alphabet, expected_strings, edges, locality, k, tier, grammar)

	# print("hypothesized_O: "+ str(hypothesized_grammar.O))
	# print("hypothesized_E: "+ str(hypothesized_grammar.E))
	# print("hypothesized_OE: "+ str(hypothesized_grammar.OE))
	# # print("hypothesized_last_grammar: " + str(observed_grammar.grammar))

	# print("observed sample\n" + str(len(observed_grammar.sample)))
	# pp.pprint(observed_grammar.sample)
	# print("hypothesized sample\n"+ str(len(hypothesized_grammar.sample)))
	# pp.pprint(hypothesized_grammar.sample)
	# # print("observed_grammar: " + str(len(observed_grammar.sl2_sample)))
	# # print("hypothesized_grammar: " + str(len(hypothesized_grammar.sl2_sample)))
	
	# for x in observed_grammar.OE:
	# 	# create a dictionary just for this 2-factor
	# 	a = {x:(observed_grammar.OE[x])}

	# 	if gap == "nogap":
	# 		if observed_grammar.OE[x] == 0:
	# 			grammar = {**grammar, **a}
	# 	difference = observed_grammar.OE[x] - hypothesized_grammar.OE[x]
	# 	# print("difference\t" + str(difference))
	# 	if difference < 0:

	# 		grammar_neg = {**grammar_neg, **a}
	# 	else:
	# 		grammar_pos = {**grammar_pos, **a}

	# # add the 2factor with the lowest OE to the grammar
	# print("potential negative constraints: " + str(grammar_neg))
	
	# if grammar_neg != {}:
	# 	lowest = min(grammar_neg, key=grammar_neg.get)
	# 	grammar[lowest] = grammar_neg[lowest]

	# 	print("learned grammar: " + str(grammar))

	# 	return previous_grammar, grammar, grammar_neg

	# else:
	# 	pass

def iteration(alphabet, sample, edges, locality, k, tier, gap = "nogap"):
	print("Initialization: ")
	counter = 0
	previous_grammar = {}
	previous_grammar, grammar, grammar_neg = learner(alphabet, sample, edges, locality, k, tier, previous_grammar, gap)
	if previous_grammar != grammar:
		print(previous_grammar)
		while grammar_neg != {}:
			counter += 1
			print("\nIteration %d: " % counter)
			try:
				previous_grammar, grammar, grammar_neg = learner(alphabet, sample, edges, locality, k, tier, grammar, gap)
			except:
				break
		print("Converged at: "+ str(grammar))
	else:
		print("Converged at: "+ str(grammar))
		return grammar

if __name__ == '__main__':
	k = 2
	locality = "sl"
	edges = ['>','<']
	FeatureFile = 'data\\ToyFeatures.txt'
	TrainingFile = 'data\\ToyLearningData_noisefree.txt'
	TestingFile = 'data\\ToyTestingData.txt'
	# FeatureFile = 'data\\TurkishFeatures-tell.txt'
	# TrainingFile = 'data\\TurkishLearningData-tell.txt'
	# TestingFile = 'data\\TurkishTestingData.txt'

	sample = get_corpus_data(TrainingFile)
	alphabet, max_length, len_vector = alphabetize(sample)
	ix2phone = {ix: p for (ix, p) in enumerate(alphabet)}
	phone2ix = {p: ix for (ix, p) in enumerate(alphabet)}
	feat, feature_dict, num_feats, feature_table, feat2ix, ix2feat = process_features(FeatureFile, alphabet, ix2phone)
	vowel = [x for x in feature_dict if feature_dict[x][feat2ix['syll']] == "+"] #
	
	# change to "tier = vowel" if learning vowel harmony

	iteration(alphabet, sample, edges, locality, k, tier = alphabet, gap = "nogap")

	
	# 1. Target should be hypothesis
	# change Observed vs Hypothesis
	# 2. If there are multiple lowest  
	# 3. The ab learning data has aa as a noise. 
	# 4. Once you see a zero count, immediately add **all of them** to the grammar.
	# 5. If you have a constraint in the grammar, 
	# how does it changes the OE of the positive 2-factors in the target grammar.

	# 6. Eliminate the word violating the current grammar and calculate E
	# in the observed
	# 7.computational linguistics does is the mixture of all trades; we want a theory 
	# that explains human behavior; we also want to achieve certain technical efficiency that is 
	# as good as industrial level ml algorithms; we also want a 