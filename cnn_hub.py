# Copyright 2017 Dhvani Patel

from check_pypy_syntax import checkPyPySyntax
from compile_error import CompileError
import sqlite3
import tokenize
import token
from io import StringIO
import keyword
from Token import Token
import json

global all_tokens


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
   
    #for Token in every_token:
    #print Token.value
    return every_token

# Create list of tokens
def handle_token(all_tokens):
    allReturn = []
    for tok in all_tokens:
        type = tok[0]
        token = tok[1]
        take = tok[2]
        takeT = tok[3]
        line = tok[4]
        srow = take[0]
        scol = take[1]
        erow = takeT[0]
        ecol = takeT[1]
        if repr(token)[:2] == 'u\'':
            val = repr(token)[2:len(repr(token))-1]
        else:
            val = repr(token)[1:len(repr(token))-1]
        send = Token(tokenize.tok_name[type], val, srow, scol, erow, ecol, line)
        allReturn.append(send)
        print ("%d,%d-%d,%d:\t%s\t%s" % \
            (srow, scol, erow, ecol, tokenize.tok_name[type], repr(token)))
    return allReturn

def create(numFile):

        sqlite_file = "/home/dhvani/python-sources.sqlite3"
        conn = sqlite3.connect(sqlite_file)
        c = conn.cursor()
        #print "Success Connection to database..."
        c.execute("SELECT source FROM source_file INNER JOIN eligible_source ON source_file.hash = eligible_source.hash")
        #print "Executed SELECT..."
        #print "Fetching all rows..."
        all_rows = c.fetchmany(size=2100)
        conn.close()
        toTest = checkPyPySyntax(all_rows[numFile][0])
                
        if toTest == None:
                #print all_rows[numFile][0]
                all_tokens = []
                text = (all_rows[numFile][0]).decode('utf-8')
                print (type(text))
                tokenStream = tokenize.generate_tokens(StringIO(text).readline)
                for tok in tokenStream:
                    all_tokens.append([tok.exact_type, tokenize.tok_name[tok.exact_type], tok[2], tok[3], tok[4]])
                    print (tok)
                allGood = handle_token(all_tokens[:])
                #print (allGood[21].type)
                gotWhat = vocabularize_tokens(allGood, False)
                all_text = str(all_rows[numFile][0])
                #print gotWhat[0].value
                print (len(all_tokens))
                print (len(gotWhat))

        
        
                #print all_text

                #print one_hot_good

        else:
                print ("Try again...")
                print (numFile)


if __name__ == '__main__':
    create(2)