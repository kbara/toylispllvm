#!/usr/bin/env python
import operator

prompt = ">"

def strip_outer_parens(parts):
    if parts[0] == '(':
        parts = parts[1:]
    else:
        parts[0] = parts[0][1:]

    if parts[-1] == ')':
        parts = parts[:-1]
    elif parts[-1][-1] == ')':
        parts[-1] = parts[-1][:-1]
    else:
        raise ValueError("Mismatching parens: %s" % parts)
    return parts


def parse(x):
    print x
    parts = x.split()
    if not parts:
        return '' # FIXME

    if parts[0][0] != '(':
        if len(parts) > 1:
            raise ValueError("Parse error (too many parts) on %s" % x)
        if parts[0] in '0123456789':
            return float(parts[0])
        else:
            return parts[0]
    else:
        parts = strip_outer_parens(parts)
        return (map(parse, parts))
    
def applyit(afunc, args):
    return apply(afunc, args[:2]) # FIXME

def evaluate(aparse):
    if not isinstance(aparse, [].__class__):
        return aparse
    else:
        afunc = lookup(aparse[0])
        return applyit(afunc, aparse[1:])

def lookup(afunc): # FIXME
    funcs = {'+':operator.add}
    if afunc in funcs:
        return funcs[afunc]
    else:
        raise ValueError("Undefined function %s" % afunc)

def repl():
    while True:
        try:
            line = raw_input("%s " % prompt)
            print evaluate(parse(line))
        except ValueError as ve:
            print ve
            

if __name__ == '__main__':
    repl()
