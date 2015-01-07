#! #something here
'''Script that reads probabilities from an ARPA file and returns probabilities for words and sentences, a la KenLM by
Kristy, Tuur and Jonathan'''

'''Note to Tuur: I have also changed the ordering of the keys in the probability dictionaries, so that it goes: word,
order, history, probability'''
'''I  also changed the keys in the self.gramcounts dictionary to integers'''

import sys, re
from collections import defaultdict
import math


class Languagemodel:
    '''Language Model object as read from an ARPA file, with words and history in dictionaries by:  word,
    n-gram-order, history'''

    def __init__(self, af):
        '''Construct a language model from given ARPA file'''
        self.probabilities = defaultdict(lambda: defaultdict(dict))  # probabilities listed in first col in ARPA file
        # self.probabilities = dict(dict(dict())) #probabilities listed in first col in ARPA file
        self.backoff = defaultdict(lambda: defaultdict(dict))  # probabilities listed in last col in ARPA file
        self.gramcounts = {}  # count of how many 1-grams, 2-grams etc
        self.seenwords = set()  # set of seen words, anything else gets <UNK> at testing
        with open(af, 'r') as a:
            while True:
                global line
                line = a.readline()
                if line.startswith("\\"):
                    state = line.strip("\\").rstrip('\\:\n')  # find where in arpa file, eg unigrams, end
                    if state == "end":
                        break
                        # #print("now in state", str(state)+'.')
                elif line == "\n":  # skip rest of loop because empty line
                    continue
                else:  # ARPA file reading within a state where we get information (eg /data/, /*grams/
                    if state == "data":
                        l = line.strip().split("=")
                        # print(l[0].split(' ')[1]) #this is the key in the self.gramcounts dictionary
                        if l[0].split(' ')[1].isnumeric():
                            gramorder = int(l[0].split(' ')[1])
                            self.gramcounts[gramorder] = int(l[1])  # save the ngram count in dictionary
                    elif state.endswith("grams"):
                        foo = [x for x in re.split("[ \t]", line.strip()) if x != '']  # this splits input regardless
                        # of tabs/spaces being used and removes empty strings
                        prob1 = float(foo[0])
                        if foo[-1].startswith('-') or foo[-1].startswith('0'):  # handles situation with BO probability
                            gramtext = foo[1:-1]
                            prob2 = float(foo[-1])
                        else:  # handles situations missing BO probability for highest order ngrams
                            gramtext = foo[1:]
                            prob2 = None
                        order = len(gramtext)
                        curr_word = gramtext[-1]
                        self.seenwords.add(curr_word)
                        history = tuple(gramtext[:-1])
                        # print(order, curr_word, history, prob1, ) #prob2
                        self.probabilities[curr_word][order][
                            history] = prob1  # saves only real probability into self.probabilities
                        self.backoff[curr_word][order][
                            history] = prob2  # saves backoff probability from this into self.backoff
                        '''The key error we had here was occuring partly because there is no 'history' for an n-gram,
                        this now set to None for unigrams as well as resetting to dictionary'''

        self.highestorder = max(self.gramcounts.keys())

    def __str__(self):
        self.probabilities.keys()


def log_prob_calc(curr_word, order, curr_history):
    # TODO remove unknown entries like 'bla' that are inserted in the probabilities dict with default values when not
    # found
    if mylm.probabilities[curr_word][order].get(curr_history, False) == False:
        curr_word_2 = curr_history[-1]
        curr_history_2 = curr_history[1:-1]
        order -= 1
        # TODO should i check for <= 2 or == 2?
        # ends recursion
        if order == 2 and len(curr_history) == 1:
            # TODO check if curr_history[1:-1] would not break but evaluate to []
            curr_history_2 = []
            log_prob = mylm.backoff[curr_word_2][order][curr_history_2] * mylm.probabilities[curr_word][order][
                curr_history_2]
        else:
            pass
        # TODO None check for curr_hist[1:-1] ?
        if mylm.probabilities[curr_word_2][order].get(curr_history_2, False) == False:
            log_prob = mylm.probabilities[curr_word][order][curr_history]
        else:
            # recursion
            log_prob = mylm.backoff[curr_word_2][order][curr_history_2] + log_prob_calc(curr_word, order,
                                                                                        curr_history[1:])
    # the fake.arpa holds -100 as dummy value for log(0), however some implementations use -99. accounting for both
    elif mylm.probabilities[curr_word][order][curr_history] == -100.0 or mylm.probabilities[curr_word][order][
        curr_history] == -99.0:
        log_prob = 0.0
    else:
        log_prob = mylm.probabilities[curr_word][order][curr_history]
    return log_prob


def main():
    '''Get files from standardinput'''
    arpa_file = sys.argv[1]
    print("Reading", str(arpa_file))
    # #input_text = open(sys.argv[3], 'r')  #TODO: Uncomment this when it comes from the command line,
    # currently using some testfile 'text.txt'
    input_text = open('text.txt', 'r')  # TODO: Delete this when unused

    '''Train the language model on the ARPA file and get global information'''
    global mylm
    mylm = Languagemodel(
        arpa_file)  # '''the LM now also captures the longest ngram in the arpa file as self.highestorder'''
    all_words = []
    all_probs = 0.0
    sum = 0
    oov = 0
    for line in input_text:
        # resetting sum and oov variables to 0 for each line
        sum = 0
        oov = 0
        line = "<s> {} </s>".format(line.rstrip('\n.'))
        # print("Now considering sentence:", line)
        words = line.split(
            ' ')  # TODO: Incorporate Jon's tokenizer (already lowercase from Python) on the input text to match
        # training
        # removed lower() b/c kenlm doesn't either
        real_words = words
        words = ["<unk>" if word not in mylm.seenwords else word for word in words]  # TODO:Is this the standard UNK
        # text or should we gsudo apt-get install python3rab it from the specific arpa file?

        '''For each word, find the optimal history, and output the first column's probability for this existing
        history'''
        for i in range(len(words)):
            all_history, curr_word = words[:i], words[i]
            curr_history = tuple(all_history[- min(mylm.highestorder - 1, len(
                all_history)):])  # take the longest ngram from arpa file or if too long then the longest available
            # history
            order = len(curr_history) + 1

            # print the thing we search for and the dictionary entries of probabilities for debugging
            # print('word: {}, history : {}, order: {}'.format(curr_word, curr_history, order))
            # print("all probs for word",curr_word, mylm.probabilities[curr_word])

            '''Note: There is no smoothing/backoff yet applied, and absolutely no formulas the following code merely
            prints the highest order probability available for the word'''
            # TODO: Learn about the ARPA file format and apply backoff probabilities / deal with the backoff in an
            # intelligent way

            while mylm.probabilities[curr_word][order].get(curr_history, False) == False and order > 0:
                # calculating the highest order that was found in the lm
                order -= 1
                curr_history = curr_history[1:]

            #     # go from eg bigram to unigram,
            # highestprob = mylm.probabilities[curr_word][order][curr_history]
            # print("The highest order probability (order {}) found for the word {} is {}".format(order,
            # ''.join(curr_history)+' '+curr_word, highestprob))

            log_prob = log_prob_calc(curr_word, order, curr_history)
            if log_prob == 0:
                continue
            sum += log_prob
            if curr_word == '<unk>':
                oov += 1
                # instead of printing the <unk> tag, we need to print the original word
                curr_word = real_words[i]
            
            print("{}=0 {} {} ".format(curr_word, order, log_prob), end='')
        print("Total:", sum, "OOV:", oov)

        # list of all words, needed for the computation of overall perplexity (as we need the number of tokens in the
        #  testfile)
        all_words += set([word for word in words if not( word in  ["<s>", "<unk>"])])
        # sum of all log_probs
        all_probs += sum

    # TODO find out if formula used for ppl computation is correct, does n contain the <s>/</s> tags?
    ppl_oov = 10 ** ((-1.0 * all_probs) / len(all_words))
    ppl_wo_oov = 0
    print("Perplexity including OOVs:", ppl_oov)


    '''
     backoff formula to be used:
     p(wd3|wd1,wd2)= if(trigram exists)           p_3(wd1,wd2,wd3)
                     else if(bigram w1,w2 exists) bo_wt_2(w1,w2)*p(wd3|wd2)
                     else                         p(wd3|w2)

     p(wd2|wd1)= if(bigram exists) p_2(wd1,wd2)
                 else              bo_wt_1(wd1)*p_1(wd2)

    '''

    # TODO: remove 0 probabilities from output
    # TODO: Perplexity of sentence (both including and excluding OOVs)
    #TODO: Count of OOVs
    #TODO: Count of Tokens

    #TODO: Put everything into the same format as KENLM output, including error output
    #TODO: Do all the pretty stuff like --help, --version etc, write a readme, include our names as authors
    #TODO: Put appropriate information in shebang (probably just about UTF-8

    #TODO: Put in /bin file, make a nice folder etc

    #TODO: Test against KenLM to see that it works


if __name__ == "__main__":
    main()




