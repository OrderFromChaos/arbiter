import re

# Idea: more transparent conversions of sections of code to functions.
# This uses regex matches alongside normal Python string parsing to grab all functions
# and variables named inside a bloc lines of code, then outputs them to stdout.

with open('Market_Requests_v5.py','r') as f:
    code = f.readlines()
    code = [line.strip() for line in code]

wordmatch = re.compile(r"\w+(\.)?(?(1)\w+|)")
stdlib = {'print','str','False','True','if','not','for','in','range'}

def preformat(line):
    # Cut out all "#"-prepended comments
    line = line.split('#')[0]
    # Cut out everything before the = sign. Add to newly_defined global var; this shouldn't show up in matches.
    line = line.split('=')
    if len(line) > 1:
        global newly_defined
        newly_defined.append(line[0].strip())
        line = line[1]
    else:
        line = line[0]
    return line

def postprocess(match_objs):
    def is_number(match):
        try:
            float(match)
        except ValueError:
            return False
        return True
    
    def is_string(match):
        string_delimiters = {('\'','\''),('"','"')}
        if (match[0],match[-1]) in string_delimiters:
            return True
        else:
            return False
    
    def in_stdlib_or_newly_defined(match):
        global stdlib
        global newly_defined
        if match in stdlib or match in newly_defined:
            return True
        else:
            return False

    new_matches = []
    for m in match_objs:
        conditions = [is_number, 
                      is_string, 
                      in_stdlib_or_newly_defined]
        all_satisfied = all([not f(m.group(0)) for f in conditions])
        if all_satisfied:
            new_matches.append(m)
    return new_matches

newly_defined = [] # Updated by preformat
lines = [126,139]
for line_num in range(lines[0]-1,lines[1]-1):
    currline = code[line_num]
    print(repr(currline))
    currline = preformat(currline)
    print(repr(currline))
    if len(currline) > 0:
        if currline[0] != '#':
            matches = [match_obj for match_obj in wordmatch.finditer(currline)]
            matches = postprocess(matches)
            strmatches = [x.group(0) for x in matches]
            print('    ', strmatches)
        else:
            print('    ',[])
    else:
        print('    ',[])
    print()