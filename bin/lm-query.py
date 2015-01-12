#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# authors: Kristy James, Tuur Leeuwenberg and Jonathan Poitz
# Script that reads probabilities from an ARPA file and returns probabilities for words and sentences, à la KenLM

'''Note: the ordering of the keys in the probability dictionaries goes: word,
order, history, probability, the keys in the self.gramcounts dictionary are integers'''

import sys, re
from collections import defaultdict
import argparse

class Languagemodel:
    '''Language Model object as read from an ARPA file, with words and history in dictionaries by:  word,
    n-gram-order, history'''

    def __init__(self, af):
        '''Construct a language model from given ARPA file'''
        self.probabilities = defaultdict(lambda: defaultdict(dict))  # probabilities listed in first col in ARPA file
        self.backoff = defaultdict(lambda: defaultdict(dict))  # probabilities listed in last col in ARPA file
        self.gramcounts = {}  # count of how many 1-grams, 2-grams etc
        self.seenwords = set()  # set of seen words, anything else gets <UNK> at testing
        with open(af, 'r') as a:
            while True:
                global line
                line = a.readline()
                # if "place ." in line:
                # print(line)
                # print(line)
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
                        if len([x for x in line.strip().split('\t') if x != '']) == 3:
                            # if (foo[-1].startswith('-') and foo[-1][-1].isnumeric()) or foo[-1] == "0":  # handles
                            # situation
                            # with BO
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
    matched_order = order
    # found
    if mylm.probabilities[curr_word][order].get(curr_history, False) == False:
        order -= 1
        matched_order -= 1
        if len(curr_history) == 1:
            try:
                log_prob = mylm.probabilities[curr_word][order][()] + mylm.backoff[curr_history[0]][order][()]
            except:
                log_prob = mylm.probabilities[curr_word][order][()]
        else:
            try:
                # this statement makes sure the correct order match is updated
                log_prob_bo = mylm.backoff[curr_history[-1]][order][curr_history[:-1]]
                matched_order, prob_aux = log_prob_calc(curr_word, order, curr_history[1:])
                log_prob = log_prob_bo + prob_aux
            except:
                matched_order, log_prob = log_prob_calc(curr_word, order, curr_history[1:])
    # the fake.arpa holds -100 as dummy value for log(0), however some implementations use -99. accounting for both
    elif mylm.probabilities[curr_word][order][curr_history] == -100.0 or mylm.probabilities[curr_word][order][
        curr_history] == -99.0:
        log_prob = 0.0
    else:
        log_prob = mylm.probabilities[curr_word][order][curr_history]
    # print(curr_word, order, curr_history, log_prob)
    return matched_order, log_prob


def main():
    '''Get files from standardinput'''
    parser = argparse.ArgumentParser(description="lm-query command line arguments",
                                     epilog="Please enjoy your probabilities.")
    parser.add_argument("arpafile", type=str, help="Load an ARPA language model file")
    parser.add_argument("--version", help="1.1")
    cl_args = parser.parse_args()
    arpa_file = str(cl_args.arpafile)
    print("Reading", str(arpa_file))
    input_text = ""
    if not sys.stdin.isatty():
        input_text = sys.stdin.readlines()
    else:
        print("error: No sentences provided from standard input", file=sys.stderr)
        exit(-1)
    # input_text = open(sys.argv[3], 'r')  #deprecated, now using argparser
    # ##input_text = open('text.txt', 'r')  # deprecated, now using command line

    print("Train the language model on the ARPA file and get global information")
    global mylm
    mylm = Languagemodel(arpa_file)
    all_words = []
    all_probs = 0.0
    all_oov = 0
    all_probs_wo_oov = 0
    order = 0
    curr_history = []
    for line in input_text:
        # resetting sum and oov variables to 0 for each line
        probs_sum, oov = 0, 0
        line = line.strip('\r\n')
        line = "<s> {} </s>".format(line)
        # print("Now considering sentence:", line)
        words = line.split(' ')
        real_words = words
        # print('seenwords:', "." in mylm.seenwords)
        # print("realwords:", "." in real_words)
        words = ["<unk>" if word not in mylm.seenwords else word for word in words]
        # print("words:", "." in words)

        '''For each word, find the optimal history, and output the first column's probability for this existing
        history'''
        for i in range(len(words)):
            all_history, curr_word = words[:i], words[i]
            # print (all_history, curr_word,'\n')
            curr_history = tuple(all_history[- min(mylm.highestorder - 1, len(
                all_history)):])  # take the longest ngram from arpa file or if too long then the longest
            # available
            order = len(curr_history) + 1

            # print the thing we search for and the dictionary entries of probabilities for debugging
            # print('word: {}, history : {}, order: {}'.format(curr_word, curr_history, order))
            # print("all probs for word",curr_word, mylm.probabilities[curr_word])

            # print("considering n-gram:", curr_word, curr_history)
            if words[i] == '<s>':
                continue
            order, log_prob = log_prob_calc(curr_word, order, curr_history)
            probs_sum += log_prob
            if curr_word == '<unk>':
                oov += 1
                # instead of printing the <unk> tag, we need to print the original word
                curr_word = real_words[i]
            else:
                # this takes care of summing up all probabilities that don't originate from an unknown word
                all_probs_wo_oov += log_prob

            # if curr_word == ".":
            print("{}=0 {} {} ".format(curr_word, order, round(log_prob, 5)), end='')
        print("Total:", round(probs_sum, 5), "OOV:", oov)
        all_words += [word for word in words if word != "<s>"]
        # sum of all log_probs
        all_probs += probs_sum
        all_oov += oov

    ppl_oov = 10 ** ((-1 * all_probs) / len(all_words))
    all_words_wo_oov = [word for word in all_words if word != "<unk>"]
    ppl_wo_oov = 10 ** ((-1 * all_probs_wo_oov) / len(all_words_wo_oov))
    print("Perplexity including OOVs:", round(ppl_oov, 3), "Perplexity excluding OOVs:", round(ppl_wo_oov, 3), "\n",
          file=sys.stderr)
    print("OOVs:", all_oov, sep="\t")
    print("Tokens:", len(all_words), sep="\t")


if __name__ == "__main__":
    main()




