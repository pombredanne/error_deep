# Copyright 2017 Dhvani Patel

import sqlite3
from check_pypy_syntax import checkPyPySyntax
from compile_error import CompileError
import tokenize
import token
import StringIO
import keyword
from Token import Token
import json
#from pprint import pprint
import numpy as np
from mutate_insert import insertMut
from mutate_deletion import deleteMut
from mutate_token_insert import insertTokMutS
from mutate_token_delete import deleteTokMutS
from mutate_token_sub import subTokMutS
import sys
import cPickle
from scipy import sparse

# NUM TOTAL: 462 563
# ACTUAl: 462 540
# ACTUAL: 925 080, BATCH = 60, GOOD = 30, BAD = 30 (I, D, S -> 10)
# Iterations: 15 418
# Unused samples = 23 
# ONE HOT = 88
# OUT = 105 (2 + 2 + 3 + 10 + 88)
# 10 = WINDOW SIZE
WINDOW_SIZE = 10
BATCH_SIZE = 66
NUM_BITS_OUTPUT = 102
global all_tokens
new_tokens_ins = []
new_tokens_del = []
new_tokens_sub = []
global indexed_tokens
data = None

#Declaring Global Constants
YES_TOKEN = 0b10
NO_TOKEN = 0b01
INSERTION = 0b001
DELETION = 0b010
SUBSTITUTION = 0b100
YES_ERROR = 0b00
NO_ERROR = 0b01

START_TOKEN = '<s>'
END_TOKEN = '</s>'

def one_hot_a(indexed_tokens):
	print indexed_tokens
	print len(indexed_tokens)
	one_hot = []
	nb_classes = 88
	one_hot_targets = np.eye(nb_classes)[indexed_tokens]
	one_hot = one_hot_targets.tolist()
	#print "fort"
	#bruhTemp = one_hot[:]
	for x in range(len(one_hot)):
		#one_hot[x].astype(int)
		[int(i) for i in one_hot[x]]
	#one_hot.astype(int)
	#print type(one_hot[0][0])
	return one_hot

def one_hot(indexed_tokens):
	return indexed_tokens
	

def set_from_json(all_tokens, flag):
	#print "OMG"
	with open('vocabulary.json') as data_file:    
    		data = json.load(data_file)
		#pprint(data)
	#print len(data["indexes"])
	#print "DHADHA"

	tempT = all_tokens[:]
	for token in tempT:
		if len(token.value) > 0:
			if token.value[0] == '#':
				all_tokens.remove(token)
				#print "no way"

	for token in all_tokens:
		if token.value == "\\r\\n":
			token.value = "NEWLINE"
		toCompare = token.value
		#print token.type
		#print "Broke..."
		#print token.line
		global indexed_tokens
		if len(toCompare) > 0:
			indexed_tokens.append(data["indexes"].index(toCompare))
	for r in range(9):
		indexed_tokens.insert(r, data["indexes"].index(START_TOKEN))
		indexed_tokens.append(data["indexes"].index(END_TOKEN))
		
	#print indexed_tokens
	return one_hot(indexed_tokens)

def set_from_json_nonarr(token, flag):
	#print "OMG"
	with open('vocabulary.json') as data_file:    
    		data = json.load(data_file)
		#pprint(data)
	#print len(data["indexes"])
	#print "dhadha"
	toCompare = token.value
	#print token.type
	#print "Broke..."
	#print token.line
	if len(toCompare) > 0:
		ind_token_nonarr = data["indexes"].index(toCompare)
	#print indexed_tokens
	return ind_token_nonarr

def open_closed_tokens(token):
    """
    'Flattens' Python into tokens based on whether the token is open or
    closed.
    """

    # List of token names that whose text should be used verbatim as the type.
    VERBATIM_CLASSES = {
        "AMPER", "AMPEREQUAL", "ASYNC", "AT", "ATEQUAL", "AWAIT", "CIRCUMFLEX",
        "CIRCUMFLEXEQUAL", "COLON", "COMMA", "DOT", "DOUBLESLASH",
        "DOUBLESLASHEQUAL", "DOUBLESTAR", "DOUBLESTAREQUAL", "ELLIPSIS",
        "EQEQUAL", "EQUAL", "GREATER", "GREATEREQUAL", "LBRACE", "LEFTSHIFT",
        "LEFTSHIFTEQUAL", "LESS", "LESSEQUAL", "LPAR", "LSQB", "MINEQUAL",
        "MINUS", "NOTEQUAL", "OP", "PERCENT", "PERCENTEQUAL", "PLUS", "PLUSEQUAL",
        "RARROW", "RBRACE", "RIGHTSHIFT", "RIGHTSHIFTEQUAL", "RPAR", "RSQB",
        "SEMI", "SLASH", "SLASHEQUAL", "STAR", "STAREQUAL", "TILDE", "VBAR",
        "VBAREQUAL"
    }
 
    OTHER = { "NEWLINE", "INDENT", "DEDENT"}
    CHECK = {"None", "True", "False"}

    if token.type == 'NAME':
        # Special case for NAMES, because they can also be keywords.
        if keyword.iskeyword(token.value):
            return token.value
	elif token.value in CHECK:
	    return token.value
        else:
            return '<IDENTIFIER>'
    elif token.type in VERBATIM_CLASSES:
        # These tokens should be mapped verbatim to their names.
        assert ' ' not in token.value
        return token.value
    elif token.type in {'NUMBER', 'STRING'}:
        # These tokens should be abstracted.
        # Use the <ANGLE-BRACKET> notation to signify these classes.        
	return "<" + token.type.upper() + ">"
    elif token.type in OTHER:
        return token.type
    else:
        # Use these token's name verbatim.
       # assert token.type in {
        #    'NEWLINE', 'INDENT', 'DEDENT',
        #    'ENDMARKER', 'ENCODING', 'COMMENT', 'NL', 'ERRORTOKEN'
        #}
	
        return token.value
	
def vocabularize_tokens(every_token, flag):
    if flag == False:
   	 EXTRANEOUS_TOKENS = {
             # Always occurs as the first token: internally indicates the file
             # ecoding, but is irrelelvant once the stream is already tokenized
            'ENCODING',
	
            # Always occurs as the last token.
            'ENDMARKER',

            # Insignificant newline; not to be confused with NEWLINE
            'NL',
	
            # Discard comments
            'COMMENT',

            # Represents a tokenization error. This should never appear for
            # syntatically correct files.
            'ERRORTOKEN',
        }
    elif flag == True:
        EXTRANEOUS_TOKENS = {
             # Always occurs as the first token: internally indicates the file
             # ecoding, but is irrelelvant once the stream is already tokenized
            'ENCODING',
	
            # Always occurs as the last token.
            'ENDMARKER',

            # Discard comments
            'COMMENT',

            # Represents a tokenization error. This should never appear for
            # syntatically correct files.
            'ERRORTOKEN',
        }
    

    
    all_tokens_iter = every_token[:]
    for Token in all_tokens_iter:

       	vocab_entry = open_closed_tokens(Token)
	Token.value = vocab_entry
        if Token.type in EXTRANEOUS_TOKENS:
		every_token.remove(Token)
	if flag == True:
		if Token.value == "\\n":
			every_token.remove(Token)
			#if Token.type == "NL":
			#print "Gotch u"
   
    #for Token in every_token:
    #print Token.value
    return set_from_json(every_token, flag)
 	
def getRid(every_token, flag):
    if flag == False:
   	 EXTRANEOUS_TOKENS = {
             # Always occurs as the first token: internally indicates the file
             # ecoding, but is irrelelvant once the stream is already tokenized
            'ENCODING',
	
            # Always occurs as the last token.
            'ENDMARKER',

            # Insignificant newline; not to be confused with NEWLINE
            'NL',
	
            # Discard comments
            'COMMENT',

            # Represents a tokenization error. This should never appear for
            # syntatically correct files.
            'ERRORTOKEN',
        }
    elif flag == True:
        EXTRANEOUS_TOKENS = {
             # Always occurs as the first token: internally indicates the file
             # ecoding, but is irrelelvant once the stream is already tokenized
            'ENCODING',
	
            # Always occurs as the last token.
            'ENDMARKER',

            # Discard comments
            'COMMENT',

            # Represents a tokenization error. This should never appear for
            # syntatically correct files.
            'ERRORTOKEN',
        }

    all_tokens_iter = every_token[:]
    for Token in all_tokens_iter:
	#print tokenize.tok_name[Token[0]]
        if tokenize.tok_name[Token[0]] in EXTRANEOUS_TOKENS:
		every_token.remove(Token)
	if flag == True:
		if Token[1] == "\\n":
			every_token.remove(Token)
			#if Token.type == "NL":
			#print "Gotch u"
    return every_token

# Create list of tokens
def handle_token(type, token, (srow, scol), (erow, ecol), line):
    if repr(token)[:2] == 'u\'':
	val = repr(token)[2:len(repr(token))-1]
    else:
        val = repr(token)[1:len(repr(token))-1]
    send = Token(tokenize.tok_name[type], val, srow, scol, erow, ecol, line)
    global all_tokens
    all_tokens.append(send)
    #print "%d,%d-%d,%d:\t%s\t%s" % \
    #    (srow, scol, erow, ecol, tokenize.tok_name[type], repr(token))


def perform(curr):
	sqlite_file = "/home/dhvani/python-sources.sqlite3"
	conn = sqlite3.connect(sqlite_file)
	c = conn.cursor()
	#print "Success Connection to database..."
	c.execute("SELECT source FROM source_file INNER JOIN eligible_source ON source_file.hash = eligible_source.hash")
	#print "Executed SELECT..."
	#print "Fetching all rows..."
	all_rows = c.fetchmany(size=2600)
	conn.close() # Close the connection to SQL
	#for curr in range(2):
	#print all_rows[curr][0]
	if True:
		
		#curr = 13
		#print all_rows[curr][0]
		#print "Got Em..."
		#print "Running PyPy test..."
		#print curr
		toTest = checkPyPySyntax(all_rows[curr][0])
		#print "DONE"
		#print "CURRENT: "
		#	print curr
		if toTest == None:
			#print "here"
			global all_tokens
			all_tokens = []
			global indexed_tokens
			indexed_tokens = []
			tokenStream = tokenize.tokenize(StringIO.StringIO(all_rows[curr][0]).readline, handle_token)
			#print "RAW"
			#print len(all_tokens)
			allGood = []
			global all_tokens
			allGood = all_tokens[:]
			print len(allGood)
			#print "come on"
			#print len(all_tokens)
			#print len(allGood)
			one_hot_good = vocabularize_tokens(all_tokens, False)
			#one_hot_good_out = []
			#for x in range(len(all_tokens)+(WINDOW_SIZE-1)+(WINDOW_SIZE-1)):
				#toAdd = []
				#toAdd = [0] * NUM_BITS_OUTPUT
				#toAdd[0] = 0
				#toAdd[1] = 1 # FIRST BIT (01) - INDICATE NO ERROR (1 because rest are 0 and so add up to 1)
				#toAdd = [1]
			#one_hot_good_out.append(1)
			

			#print "DHVANI"
			#print len(one_hot_good)
			#print len(allGood)
			#print len(all_tokens)
		
			raw_tokens = tokenize.generate_tokens(StringIO.StringIO(all_rows[curr][0]).readline)		
			source_code = str(all_rows[curr][0])
			
			#MUTATIONS PER TOKEN

			# INSERT

			#global all_tokens
			#all_tokens = []
			global indexed_tokens
			indexed_tokens = []
			#print "RAW"		
			#print len(all_tokens)
			#passToks = all_tokens[:]
			#print len(passToks)
			#print "come
			global all_tokens
			print "dhadha"
			#print len(all_tokens)
			#print len(allGood)
			passBall = allGood[:]
			new_i_text, NO_TOKEN, INSERTION, out_tokens_loc, chosenTrueLineInds, insToks = insertTokMutS(raw_tokens, passBall, source_code)

			while isinstance(new_i_text, int):
				new_i_text, NO_TOKEN, INSERTION, out_tokens_loc, chosenTrueLineInds, insToks = insertTokMutS(NO_TOKEN, out_tokens_loc, INSERTION)
				if isinstance(new_i_text, str):
					break
			print "here"
			new_tokens_ins = allGood[:]
			#print "BOL BOL BOL"			
			#print len(new_tokens_ins)
			temp = insToks[:]
			for insTok in temp:
				if insTok.type == "NL":
					insToks[insToks.index(insTok)].type = "NEWLINE"
			
			temp2 = chosenTrueLineInds[:]
			for chosenTrueLineInd in temp2:
				vocab_entry = open_closed_tokens(chosenTrueLineInd)
				chosenTrueLineInds[chosenTrueLineInds.index(chosenTrueLineInd)].value = vocab_entry
				#print vocab_entry
			#print "OK ------------------------------"
			#print len(new_tokens_ins)
			#print len(chosenTrueLineInds)
			#print len(all_tokens)
			bruhInd = 0
			for wow in range(len(chosenTrueLineInds)):
				bruhInd = -1
				iterInd = 0
				chosenTrueLineInd = chosenTrueLineInds[wow]
				insTok = insToks[wow]
				#print len(all_tokens)
				for a in allGood:
					if a == chosenTrueLineInd:
						bruhInd = iterInd
					iterInd = iterInd + 1
				#print bruhInd + 1
				#print bruhInd
				#print "gotchu"
				if bruhInd != -1:
					#print bruhInd
					#print "gotchu"
					new_tokens_ins.insert(bruhInd+1, insTok)
			#print "START DEBUG"
			#print insTok.value
			#print len(new_tokens_ins)
			#print new_tokens_ins[bruhInd+1].value
			
			one_hot_bad_ins = vocabularize_tokens(new_tokens_ins, True)
			#print one_hot_bad_ins[bruhInd+1+WINDOW_SIZE-1]
			#print "DONE DEBUG"
		
			#print len(new_tokens_ins)
			#print len(one_hot_bad_ins)
			
			#if(bruhInd+1 < len(new_tokens_ins)):
				
				
			
			#print "NEXT STEP...C"
			#passInsErrorInd = (bruhInd+1)+(WINDOW_SIZE-1) 
			
			#one_hot_bad_ins_out = []
			#trueErrorInd = (bruhInd+1)+(WINDOW_SIZE-1) 
		
			# INSERT OUT_PUT

			#iterNum = len(new_tokens_ins)+(WINDOW_SIZE-1)+(WINDOW_SIZE-1)
			#print "divide"
			#print trueErrorInd
			#print iterNum
			'''
			for x in range(iterNum):
				#if x <= trueErrorInd <= (x+trueErrorInd):
				#if x <= trueErrorInd <= x+(WINDOW_SIZE-1):
				if True:
					# DIFF - ACTUAL ERROR
					#print x
					#toAdd = []
					#toAdd = [0] * NUM_BITS_OUTPUT
					#toAdd[0] = 1 # FIRST BIT (10) - INDICATE ERROR 
					#toAdd[1] = 0
					#if NO_TOKEN != None:
					#	toAdd[2] = 0
					#	toAdd[3] = 1
					#if INSERTION != None:
					#	toAdd[4] = 0
					#	toAdd[5] = 0
					#	toAdd[6] = 1
					#toAdd[7] = 1
					toAdd = [0,3,6,7]
					one_hot_bad_ins_out.append(toAdd)
				else:
					toAdd = []
					toAdd = [0] * NUM_BITS_OUTPUT
					toAdd[0] = 1
					toAdd[1] = 0 # FIRST BIT (01) - INDICATE NO ERROR (1 because rest are 0 and so add up to 1)
					one_hot_bad_ins_out.append(toAdd)
			'''
			#print "Morning"	
			#print len(new_tokens_ins)
			#print len(one_hot_bad_ins_out)
			#print one_hot_bad_ins_out[trueErrorInd]

			

			# DELETE
			raw_tokens = tokenize.generate_tokens(StringIO.StringIO(all_rows[curr][0]).readline)	
			#global all_tokens
			#all_tokens = []
			global indexed_tokens
			indexed_tokens = []
			#print type(raw_tokens)
			#print type(source_code)
			passBall = allGood[:]
			new_d_text, YES_TOKEN, DELETION, chosens, fixToks = deleteTokMutS(raw_tokens,passBall, source_code)

			while isinstance(new_d_text, int):
				new_d_text, YES_TOKEN, DELETION, chosens, fixToks = deleteTokMutS(YES_TOKEN, DELETION)
				if isinstance(new_d_text, str):
					break
			

			print "NEXT STEP..."
			
			new_tokens_del = allGood[:]

			tempFix = fixToks[:]
			for send in tempFix:
				vocab_entry = open_closed_tokens(send)
				fixToks[fixToks.index(send)].value = vocab_entry
		
			#print "len"
			#print len(allGood)
			#print len(fixToks)
			#print len(new_tokens_del)
			removeInds = []
			for wow in range(len(chosens)):
				bruhInd = -1
				iterInd = 0
				send = fixToks[wow]	
				#print send.value
				for a in allGood:
					if a == send:
						bruhInd = iterInd
					iterInd = iterInd + 1
				#print bruhInd
				#print "CHECK"
				#print len(new_tokens_del)
				removeInds.append(bruhInd)
				#del new_tokens_del[bruhInd]	
				#print len(new_tokens_del)
				#print "DEL ROR"
			for r in reversed(removeInds):
				del new_tokens_del[r]
			#print len(new_tokens_del)

			one_hot_bad_del = vocabularize_tokens(new_tokens_del, True)
			
			#one_hot_bad_del_out = []
			#trueErrorInd = (bruhInd)+(WINDOW_SIZE-1)
 
			# DELETE OUT_PUT
			#iterNum = len(new_tokens_del)+(WINDOW_SIZE-1)+(WINDOW_SIZE-1)
			#print "divide"
			#print len(send)
			#print trueErrorInd
			#print iterNum
			#print "delete"
			#print send.type
			#print send.value
			#oneH_ind_deleted = set_from_json_nonarr(send, True)
			#print oneH_ind_deleted
			#print "rad"
			'''
			for x in range(iterNum):
				#if x <= trueErrorInd <= (x+trueErrorInd):
				if True:
					# DIFF - ACTUAL ERROR
					#print x
					#toAdd = []
					#toAdd = [0] * NUM_BITS_OUTPUT
					#toAdd[0] = 1 # FIRST BIT (10) - INDICATE ERROR 
					#toAdd[1] = 0
					#if YES_TOKEN != None:
					#	toAdd[2] = 1
					#	toAdd[3] = 0
					#if DELETION != None:
					#	toAdd[4] = 0
					#	toAdd[5] = 1
					#	toAdd[6] = 0
					#toAdd[7] = 1
					#toAdd[17] = 1
					toAdd = [0,2,5,7,17]
					one_hot_bad_del_out.append(toAdd)
				else:
					toAdd = []
					toAdd = [0] * NUM_BITS_OUTPUT
					toAdd[0] = 0
					toAdd[1] = 1 # FIRST BIT (01) - INDICATE NO ERROR (1 because rest are 0 and so add up to 1)
					one_hot_bad_del_out.append(toAdd)
			'''
			#print "Morning"	
			#print len(allGood)
			#print len(one_hot_bad_del_out)
			#print one_hot_bad_del_out[trueErrorInd]
		
			# SUB
			raw_tokens = tokenize.generate_tokens(StringIO.StringIO(all_rows[curr][0]).readline)	
			#global all_tokens
			#all_tokens = []
			global indexed_tokens
			indexed_tokens = []
			#print type(raw_tokens)
			passBall = allGood[:]
			new_s_text, YES_TOKEN, SUBSTITUTION, chosensS, fixToksS, insToksS = subTokMutS(raw_tokens, passBall, source_code)

			while isinstance(new_s_text, int):
				new_s_text, YES_TOKEN, SUBSTITUTION, chosensS, fixToksS, insToksS = subTokMutS(YES_TOKEN, SUBSTITUTION)
				if isinstance(new_s_text, str):
					break
			
			#print "NEXT STEP..."

			# SUB DELETE

			new_tokens_sub = allGood[:]

			temp = insToksS[:]
			for insTok in temp:
				if insTok.type == "NL":
					insToks[insToksS.index(insTok)].type = "NEWLINE"

			
			tempFix = fixToksS[:]
			for send in tempFix:
				vocab_entry = open_closed_tokens(send)
				fixToksS[fixToksS.index(send)].value = vocab_entry

			removeInds = []
			for wow in range(len(chosensS)):
				bruhInd = -1
				iterInd = 0
				send = fixToksS[wow]	
				#print send.value
				for a in allGood:
					if a == send:
						bruhInd = iterInd
					iterInd = iterInd + 1
				#print bruhInd
				#print "CHECK"
				#print len(new_tokens_del)
				removeInds.append(bruhInd)
				#del new_tokens_del[bruhInd]	
				#print len(new_tokens_del)
				#print "DEL ROR"
		
			# SUB INSERT
			#print len(removeInds)
			#print len(insToksS)
			comeIter = len(insToksS)-1
			for r in reversed(removeInds):
				del new_tokens_sub[r]
				#print insToksS[comeIter].value
				new_tokens_sub.insert(r, insToksS[comeIter])
				comeIter -= 1
			#for x in new_tokens_sub:
				#print x.value
			#print len(new_tokens_del)
		

			#print insTokS.type
			#print insTokS.value
			#print "LUNCH"


			one_hot_bad_sub = vocabularize_tokens(new_tokens_sub, True)

			#one_hot_bad_sub_out = []
			#trueErrorInd = (bruhInd)+(WINDOW_SIZE-1) 
			# SUB OUT_PUT
			#iterNum = len(new_tokens_sub)+(WINDOW_SIZE-1)+(WINDOW_SIZE-1)
			#print "divide"
			#print len(send)
			#print trueErrorInd
			#print iterNum
			#print "sub"
			#print sendS.type
			#print sendS.value
			#oneH_sub_switch = set_from_json_nonarr(sendS, True)
			#print oneH_sub_switch
			#print "rad"

			'''
			for x in range(iterNum):
				#if x <= trueErrorInd <= (x+trueErrorInd):
				#if x <= trueErrorInd <= x+(WINDOW_SIZE-1):
				if True:
					# DIFF - ACTUAL ERROR
					#print x
					#toAdd = []
					#toAdd = [0] * NUM_BITS_OUTPUT
					#toAdd[0] = 1 # FIRST BIT (10) - INDICATE ERROR 
					#toAdd[1] = 0
					
					#toAdd[2] = 1
					#toAdd[3] = 0
					
					#toAdd[4] = 1
					#toAdd[5] = 0
					#toAdd[6] = 0

					#toAdd[7] = 1
					#toAdd[17] = 1
					toAdd = [0,2,4,7,17]
					one_hot_bad_sub_out.append(toAdd)
				else:
					toAdd = []
					toAdd = [0] * NUM_BITS_OUTPUT
					toAdd[0] = 0
					toAdd[1] = 1 # FIRST BIT (01) - INDICATE NO ERROR (1 because rest are 0 and so add up to 1)
					one_hot_bad_sub_out.append(toAdd)

			'''
			#print "Morning"	
			#print len(allGood)
			#print len(all_tokens)
			#print len(one_hot_bad_sub_out)
			#print one_hot_bad_sub_out[trueErrorInd]
	

			# MUTATIONS PER CHARACTER
			# insertMut(source_code)
			#deleteMut(source_code])
			
			#print "LEN"
			#print one_hot_good[0]
			#print one_hot_bad[0]
			
			#print "----------INPUT-------------"

			#print len(one_hot_good)
			#print len(one_hot_bad_ins)
			#print len(one_hot_bad_del)
			#print len(one_hot_bad_sub)

			#print "----------OUTPUT-------------"

			#print len(one_hot_good_out)
			#print len(one_hot_bad_ins_out)
			#print len(one_hot_bad_del_out)
			#print len(one_hot_bad_sub_out)

			#print curr
		
				
			#one_hot_all = np.concatenate((one_hot_good, one_hot_bad), axis=0)

			#print "SUCCESS"
			
			#sizes = [len(one_hot_good), len(one_hot_bad_ins),len(one_hot_bad_del),len(one_hot_bad_sub)]
			#minSize = int(min(float(siz) for siz in sizes)) # min of a generator
			#return minSize
			
			#toPassGood = []
			#print len(one_hot_good)
			#for good in one_hot_good:
			#	ind = good.index(1.0)
			#	toPassGood.append(ind)
			#print len(toPassGood)
			#print one_hot_bad_sub_out
			#print type(radha)	

			toPass = [one_hot_good, one_hot_bad_ins, one_hot_bad_del, one_hot_bad_sub]
			#toPass = sparse.csr_matrix(toPassMatrix)
			#print toPass
			#print type(radha)
			
			#cPickle.dump(one_hot_bad_ins, fileStore)
			#cPickle.dump(one_hot_bad_del, fileStore)
			#cPickle.dump(one_hot_bad_sub, fileStore)
			#cPickle.dump(one_hot_good_out, fileStore)
			#cPickle.dump(one_hot_bad_ins_out, fileStore)
			#cPickle.dump(one_hot_bad_del_out, fileStore)
			#cPickle.dump(one_hot_bad_sub_out, fileStore)
			#cPickle.dump(passInsErrorInd, fileStore)
			
			return toPass
			
		
			#return one_hot_good, one_hot_bad_ins, one_hot_bad_del, one_hot_bad_sub, one_hot_good_out, one_hot_bad_ins_out, one_hot_bad_del_out, one_hot_bad_sub_out,passInsErrorInd
			
		else:
			print "Try again..."
			print curr
			#print all_rows[curr][0]
			return -1


			#return 1, None, None, None, 1, None, None, None, None

def giveItems():
	allData = cPickle.load( open( "all_pre_data.txt", "rb" ) )
	#print allData[3][8]

if __name__ == '__main__':
    count = perform(1086)
    print type(radha)
	


    all_train_to_pass = []
    for x in range(1000):
	print x
	if x != -1:
		toP = perform(x)
		all_train_to_pass.append(toP)
    fileStore = open("train_pre_data.txt", 'w')
    cPickle.dump(all_train_to_pass, fileStore)
    fileStore.close()
    all_val_to_pass = []
    for x in range(1000):
	print x
	if x != -1:
		toPV = perform(x+1001)
		all_val_to_pass.append(toPV)
    fileStoreV = open("val_pre_data.txt", 'w')
    cPickle.dump(all_val_to_pass, fileStoreV)
    fileStoreV.close()
    print "FINISHED"
    #giveItems()
 
    sys.exit()
    for x in range(10):
	  print "CURR"
	  print x
	  # 36, 80, 124, 126, 177
	  if x != 36 and x != 80 and x != 124 and x != 126 and x != 177:
  		  perform(x)


