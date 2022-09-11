import random
import numpy as np

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
	num_feats = len(feature_dict[line[0]])

	feat = [feat for feat in header.rstrip("\n").split("\t")]
	feat.pop(0)

	feat2ix = {f: ix for (ix, f) in enumerate(feat)}
	ix2feat = {ix: f for (ix, f) in enumerate(feat)}

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

if __name__ == '__main__':

	FeatureFile = 'data\\TurkishFeatures-tell.txt'
	TrainingFile = 'data\\TurkishLearningData-tell.txt'
	sample = get_corpus_data(TrainingFile)
	alphabet = list(set(phone for w in sample for phone in w if phone != ''))

	ix2phone = {ix: p for (ix, p) in enumerate(alphabet)}
	phone2ix = {p: ix for (ix, p) in enumerate(alphabet)}
	feat, feature_dict, num_feats, feature_table, feat2ix, ix2feat = process_features(FeatureFile, alphabet, ix2phone)

	vowel = [x for x in feature_dict if feature_dict[x][feat2ix['syll']] == "+" if feature_dict[x][feat2ix['long']] == "-"]
	tier = vowel
	nontier = [x for x in alphabet if x not in tier if feature_dict[x][feat2ix['long']] == "-"]
	#generate testing data
	noncelist = [c1 + ' ' + v1 + ' ' + c2 + ' ' + v2 for c1 in nontier for c2 in nontier for v1 in tier for v2 in tier]
	# print(word)  
	nonce2000_raw = random.sample(noncelist,2000)

	nonce2000list = []

	ix_high = feat2ix['high']
	ix_back = feat2ix['back']
	ix_round = feat2ix['round']

	for w in nonce2000_raw:
		w = w.rstrip().split(' ')
		V1 = w[1] 
		V2 = w[3]


		if feature_dict[V1][ix_back] != feature_dict[V2][ix_back]:
			w.append("ungrammatical")

		elif feature_dict[V2][ix_high] == "+":
			if feature_dict[V1][ix_round] != feature_dict[V2][ix_round]:
				if "ungrammatical" not in w:
					w.append("ungrammatical")
			else:
				w.append("\tgrammatical")


		elif "ungrammatical" not in w:
			w.append("grammatical")
				
		nonce2000list.append(' '.join(w))


	write_nonce = open("nonce.txt", "w", encoding='utf8')
	for x in nonce2000list:
		write_nonce.write(x + '\n')
