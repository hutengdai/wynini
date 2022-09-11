# from scipy.stats import pearsonr, spearmanr
import numpy as np
import random
import random
import numpy as np
import pprint
import re

pp = pprint.PrettyPrinter(indent=4)
pprint.sorted = lambda x, key=None: x

def alphabetize(raw_data):
	alphabet = []
	'''write the number to the list every time you see a word with certain length'''
	m = 0
	for w in raw_data:
		if len(w) >= m:
			m = len(w)
		for phone in w:
			if phone != '':
				alphabet.append(phone)
	l = np.zeros(m)
	for w in raw_data:
		l[len(w)-1] += 1
	
	print("length vector\t" + str(l))
	# alphabet = list(set(phone for w in raw_data for phone in w))
	# max_chars = max([len(x) for x in raw_data])
	return list(set(alphabet)), m, l

def ngramize_item(string,k):
	"""This function n-gramizes a given string.
	Arguments:
		item (str): a string that needs to be ngramized.
	Returns:
		list: list of ngrams from the item.
	"""
	ng = []
	for i in range(len(string) - (k - 1)):
		ng.append(tuple(string[i : (i + k)]))
	return ng

def subsequences(string,k):
	"""Extracts k-long subsequences out of the given word.
	Arguments:
		string (str): a string that needs to be processed.
	Returns:
		list: a list of subsequences out of the string.
	"""
	if len(string) < k:
		return []

	start = list(string[: k])
	result = [start]

	previous_state = [start]
	current_state = []

	for s in string[k :]:
		for p in previous_state:
			for i in range(k):
				new = p[:i] + p[i + 1 :] + [s]
				if new not in current_state:
					current_state.append(new)
		result.extend(current_state)
		previous_state = current_state[:]
		current_state = []

	return list(set([tuple(i) for i in result]))

def process_features(file_path, inventory, ix2phone):
	inv_size = len(inventory)

	feature_dict = {}
	file = open(file_path, 'r', encoding='utf-8')
	header = file.readline()
	for line in file:
		line = line.rstrip("\n").split("\t")
		# line = line.split(',')
		if line[0] in inventory:
			feature_dict[line[0]] = [x for x in line[1:]]
			feature_dict[line[0]] += [0, 0, 0]

	num_feats = len(feature_dict[line[0]])

	feature_dict['<s>'] = [0 for x in range(num_feats-3)] + ['-', '-', '+']
	feature_dict['<p>'] = [0 for x in range(num_feats-3)] + ['+', '+', '-']
	feature_dict['<e>'] = [0 for x in range(num_feats-3)] + ['+', '-', '-']


	feat = [feat for feat in header.rstrip("\n").split("\t")]
	feat.pop(0)
	feat.extend(['<e>', '<p>', '<s>'])

	feat2ix = {f: ix for (ix, f) in enumerate(feat)}
	ix2feat = {ix: f for (ix, f) in enumerate(feat)}
	
	# print(feature_dict)
	
	feature_table = np.chararray((inv_size, num_feats))
	for i in range(inv_size):
		feature_table[i] = feature_dict[ix2phone[i]]
	return feat, feature_dict, num_feats, feature_table, feat2ix, ix2feat

def get_corpus_data(filename):
	"""
	Reads input file and coverts it to list of lists, adding word boundary
	markers.
	"""
	raw_data = []
	file = open(filename, 'r', encoding='utf-8')
	
	for line in file:
		line = line.rstrip()
		# line = ['<s>'] + line.split(' ') + ['<e>']
		line = line.split(' ')
		raw_data.append(line)
	random.shuffle(raw_data)
 
 	# ignore token frequency of strings; comment it out to see the difference :)
	b_set = set(map(tuple,raw_data))  #need to convert the inner lists to tuples so they are hashable
	raw_data = map(list,b_set) 
	return list(raw_data)

def scan(string, grammar_neg, tier):
	string = [i for i in string if i in tier] 
	# return 1 or 0 for the given testing data, sum them up 
	ng = ngramize_item(string,2)
	for i in ng:
		if i in grammar_neg:
			prob = 0.0
		else:	
			prob = 1.0
	return prob

def outJudgement(input_filename, out_filename, grammar_neg, tier):
	inp_file = open(input_filename, 'r', encoding='UTF-8')
	out_file = open(out_filename, 'w', encoding='UTF-8')

	data = []
	as_strings = []
	word_judge = {}

	for line in inp_file:
		line = line.rstrip()
		as_strings.append(line)
		line = line.split()
		judge = line.pop()
		word_judge[''.join(line)] = judge
		data.append(line)
	pp.pprint(data)
	for i, string in enumerate(data):
		curr_string = as_strings[i]
		prob = scan(string, grammar_neg, tier)
		out_file.write(curr_string + '\t' + str(prob) + "\n")

	inp_file.close()
	out_file.close()

def factor_of(u,w):
	# print("factor: " + str(u) + " word: " + str(w))

	if re.search(u,w):
		return True
	else:
		return False

def sl_sats(w,g):
	"""Whether w satisfies forbidden SL grammar g"""
	
	for v in g:
				
		if factor_of(v,w):
			return False
	return True


def sl_sats_l(l,g):
	"""Strings in l that satisfy forbidden SL grammar g"""
	return {w for w in l if sl_sats(w,g)}

def l_concat(l1,l2):
	"""Return concatenation of languages l1 and l2"""
	return {i+j for i in l1 for j in l2}

def lexpn(l,n):
	"""Return concatenation of l to self n times"""
	if n == 0:
		return {}
	elif n == 1:
		return l
	else:
		return l_concat(l,lexpn(l,n-1))

if __name__ == '__main__':
	k = 2
	locality = "sl"
	edges = ['>','<']
	# FeatureFile = 'data\\ToyFeatures.txt'
	# TrainingFile = 'data\\ToyLearningData.txt'
	FeatureFile = 'data\\TurkishFeatures-tell.txt'
	TrainingFile = 'data\\TurkishLearningData-tell.txt'
	TestingFile = 'data\\TurkishTestingData.txt'

	sample = get_corpus_data(TrainingFile)
	alphabet, max_length = process_data(sample)
	ix2phone = {ix: p for (ix, p) in enumerate(alphabet)}
	phone2ix = {p: ix for (ix, p) in enumerate(alphabet)}
	feat, feature_dict, num_feats, feature_table, feat2ix, ix2feat = process_features(FeatureFile, alphabet, ix2phone)
	vowel = [x for x in feature_dict if feature_dict[x][feat2ix['syll']] == "+" if feature_dict[x][feat2ix['long']] == "-"] #
	tier = vowel