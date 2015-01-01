#! #something here
'''Script that reads probabilities from an ARPA file and returns probabilities for words and sentences, a la KenLM by Kristy, Tuur and Jonathan'''

'''Note to Tuur: I have also changed the ordering of the keys in the probability dictionaries, so that it goes: word, order, history, probability'''
'''I  also changed the keys in the self.gramcounts dictionary to integers'''
'''Note to Jonathan - Welcome! Glad to have you on the project. I hope you can decipher the code, just ask with any questions. Kristy :)'''

import sys, re
from collections import defaultdict

class Languagemodel:
    '''Language Model object as read from an ARPA file, with words and history in dictionaries by:  word, n-gram-order, history'''
    def __init__(self, af):
        '''Construct a language model from given ARPA file'''
        self.probabilities = defaultdict(lambda : defaultdict(dict)) #probabilities listed in first col in ARPA file
        self.backoff = defaultdict(lambda : defaultdict(dict)) #probabilities listed in last col in ARPA file
        self.gramcounts = {} #count of how many 1-grams, 2-grams etc
        self.seenwords = set() #set of seen words, anything else gets <UNK> at testing
        with open(af, 'r') as a:
            while True:
                global line
                line = a.readline()
                if line.startswith("\\"):
                    state = line.strip("\\").rstrip('\\:\n')  #find where in arpa file, eg unigrams, end
                    if state=="end":
                        break
                    ##print("now in state", str(state)+'.')
                elif line == "\n": #skip rest of loop because empty line
                    continue
                else: # ARPA file reading within a state where we get information (eg /data/, /*grams/
                    if state == "data":
                        l = line.strip().split("=")
                        #print(l[0].split(' ')[1]) #this is the key in the self.gramcounts dictionary
                        if l[0].split(' ')[1].isnumeric():
                            gramorder = int(l[0].split(' ')[1])
                            self.gramcounts[gramorder] = int(l[1]) #save the ngram count in dictionary
                    elif state.endswith("grams"):
                        foo = [x for x in re.split("[ \t]", line.strip()) if x!=''] #this splits input regardless of tabs/spaces being used and removes empty strings
                        prob1 = float(foo[0])
                        if foo[-1].startswith('-') or foo[-1].startswith('0'): #handles situation with BO probability
                            gramtext = foo[1:-1]
                            prob2 = float(foo[-1])
                        else:  # handles situations missing BO probability for highest order ngrams
                            gramtext = foo[1:]
                            prob2 = None
                        order = len(gramtext)
                        curr_word = gramtext[-1]
                        self.seenwords.add(curr_word)
                        history = tuple(gramtext[:-1])
                        #print(order, curr_word, history, prob1, ) #prob2
                        self.probabilities[curr_word][order][history] = prob1 #saves only real probability into self.probabilities
                        self.backoff[curr_word][order][history] = prob2 #saves backoff probability from this into self.backoff
                        '''The key error we had here was occuring partly because there is no 'history' for an n-gram, this now set to None for unigrams as well as resetting to dictionary'''

        self.highestorder = max(self.gramcounts.keys())

    def __str__(self):
        self.probabilities.keys()

def main():
    '''Get files from standardinput'''
    arpa_file = sys.argv[1]
    print("Now loading model from ",arpa_file)
    ##input_text = open(sys.argv[3], 'r')  #TODO: Uncomment this when it comes from the command line, currently using some testfile 'text.txt'
    input_text = open('text.txt', 'r')  #TODO: Delete this when unused

    '''Train the language model on the ARPA file and get global information'''
    global mylm
    mylm = Languagemodel(arpa_file)   #'''the LM now also captures the longest ngram in the arpa file as self.highestorder'''
    for line in input_text:
        line = "<s> {} </s>".format(line.lower().rstrip('\n.'))
        print("Now considering sentence:", line)
        words = line.split(' ') #TODO: Incorporate Jon's tokenizer (already lowercase from Python) on the input text to match training
        words = ["<UNK>" if word not in mylm.seenwords else word for word in words ] #TODO:Is this the standard UNK text or should we grab it from the specific arpa file?

        '''For each word, find the optimal history, and output the first column's probability for this existing history'''
        for i in range(len(words)):
            all_history, curr_word = words[:i],  words[i]
            curr_history = tuple(all_history[- min(mylm.highestorder -1 , len(all_history)):]) #take the longest ngram from arpa file or if too long then the longest available history
            order = len(curr_history) + 1

            #print the thing we search for and the dictionary entries of probabilities for debugging
            print('word: {}, history : {}, order: {}'.format(curr_word, curr_history, order))
            print("all probs for word",curr_word, mylm.probabilities[curr_word])

            '''Note: There is no smoothing/backoff yet applied, and absolutely no formulas the following code merely prints the highest order probability available for the word'''
            #TODO: Learn about the ARPA file format and apply backoff probabilities / deal with the backoff in an intelligent way

            while mylm.probabilities[curr_word][order].get(curr_history, False) == False and order > 0 : #true if entry for history doesn't exist and order allows us to back off
                order -=1; curr_history = curr_history[1:] #go from eg bigram to unigram,

            highestprob = mylm.probabilities[curr_word][order][curr_history]

            print("The highest order probability (order {}) found for the word {} is {}".format(order, ''.join(curr_history)+' '+curr_word, highestprob))

            #TODO: MOST IMPORTANT:
            '''
            Think about the backoff being applied. The ARPA files give backoff probabilities already,\
            these are stored in self.backoff but not yet used. Also there is an interpolation formula we should apply,\
             I think we should let the user have information about this. Someone needs to become an expert in this and \
             apply it properly.
             Below more trivial tasks:
            '''


            #TODO: Perplexity of sentence (both including and excluding OOVs)
            #TODO: Count of OOVs
            #TODO: Count of Tokens

            #TODO: Put everything into the same format as KENLM output, including error output
            #TODO: Do all the pretty stuff like --help, --version etc, write a readme, include our names as authors
            #TODO: Put appropriate information in shebang (probably just about UTF-8

            #TODO: Put in /bin file, make a nice folder etc

            #TODO: Test against KenLM to see that it works



if __name__=="__main__":
    main()




