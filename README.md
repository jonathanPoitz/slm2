slm2 language modelling assignment
====
version 1.2 (13 Jan 2015)

Authors
===
Kristy James, 
Tuur Leeuwenberg and
Jonathan Poitz 
at Saarland University, Germany.

This software reads a language model from an ARPA file and outputs probabilities for each word within the sentence.

These probabilities utilise the highest order ngram available from the ARPA file; if this is unseen they back off to a 
lower-order n-gram history. This is due to the implementation of modified Kneser-Ney smoothing.

Installation:
---
Fork our [git repository](https://github.com/kristyj/slm2), run the commands below in the main directory.

Usage:
---
Run from command line with the following command:
`python3 bin/lm-query.py  lm.arpa < text.txt > test.probs 2> test.pp`, where:
  
  + `lm.arpa` is a pre-generated ARPA language model file
  
  
 + `test.txt` is the text to be analysed, with each sentence on a new line (UTF8 characters accepted)
 
 
 + `test.probs` is the output file for the probabilities
 
 
 + `test.pp` is the location of any error messages.
 
On Linux systems, you should also be able to run the program without the python3 command.

Try it on some dummy files using `python3 bin/lm-query.py src/fake_2.arpa < src/text.txt > tests/test.probs 2>tests/test.pp`

Other Resources:
===
You can learn more about KenLM [here.](https://kheafield.com/code/kenlm/)

You can learn more about the ARPA format [here.](http://www.speech.sri.com/projects/srilm/manpages/ngram-format.5.html)


