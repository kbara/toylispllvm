#!/usr/bin/env python
import operator
import llvm
import llvm.core
import llvm.ee

prompt = ">"

Symbol = str

def parse(x):
    tokens = (tokenize(x))
    if tokens:
        return read_from(tokens)
    else:
        return []

def tokenize(x):
    return x.replace('(', ' ( ').replace(')', ' ) ').split()

def read_from(tokens):
    print tokens
    if len(tokens) == 0:
        raise SyntaxError("Unexpected EOF (read_from)")
    cur_token = tokens.pop(0)
    if cur_token == '(':
        out = []
        while tokens[0] != ')':
            out.append(read_from(tokens))
        tokens.pop(0)
        return out
    elif cur_token == ')':
        raise SyntaxError("Unexpected ')' (read_from)")
    else:
        print "cur_token is %s" % cur_token
        return atom(cur_token)
   
def atom(token):
    print "atomizing %s" % token
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token) 
    
def compile_and_execute(afunc, args):
    afn = afunc.__name__
    a1 = args[0]
    a2 = args[1]

    if not hasattr(compile_and_execute, 'compiled_functions'):
        compile_and_execute.compiled_functions = {}
    cf = compile_and_execute.compiled_functions

    if afn not in cf:
        (module, compiled_func) = compile(afunc, a1, a2)
        cf[afn] = (module, compiled_func)
        #print "compiled is %s" % comp_mod[0]
    else:
        print "Function cache hit!"
    executed = execute(cf[afn][0], cf[afn][1], a1, a2)
    #print "executed is %s" % executed.as_int()
    return executed


def applyit(afunc, args):
    return apply(afunc, args[:2]) # FIXME

def evaluate(aparse, compiled_funcs=None):
    if not isinstance(aparse, [].__class__):
        return aparse
    else:
        afunc = lookup(aparse[0])
        ret = compile_and_execute(afunc, aparse[1:3])

        #comp_mod = compile(afunc, aparse[1], aparse[2])
        #print "compiled is %s" % comp_mod[0]
        #executed = execute(comp_mod[0], comp_mod[1], aparse[1], aparse[2])
        print "executed is %s" % ret.as_int()
        return applyit(afunc, aparse[1:])

def execute(module, llvmfunc, arg1, arg2):
    ee = llvm.ee.ExecutionEngine.new(module)
    lint = llvm.core.Type.int()
    a1 = llvm.ee.GenericValue.int(lint, arg1)
    a2 = llvm.ee.GenericValue.int(lint, arg2)
   
    print "llvmfunc: %s" % llvmfunc
    print "a1: %s" % a1 
    retval = ee.run_function(llvmfunc, [a1, a2])
    print "retval is %s" % retval
    return retval

def compile(afunc, arg1, arg2): # FIXME; should this take the module as an arg?
    lisp_module = llvm.core.Module.new("minilispmod")
    lint = llvm.core.Type.int()
    two_arg_func = llvm.core.Type.function(lint, [lint, lint])
    
    f = lisp_module.add_function(two_arg_func, afunc.__name__)
    #print dir(f.args[0])
    f.args[0].name = 'a'
    f.args[1].name = 'b'

    bb = f.append_basic_block("entry")
    builder = llvm.core.Builder.new(bb)
    #print dir(builder)
    tmp = getattr(builder, afunc.__name__)(f.args[0], f.args[1], "tmpwhy")
    builder.ret(tmp)

    return (lisp_module, f)

def lookup(afunc): # FIXME
    funcs = {'+':operator.add, '*':operator.mul}
    if afunc in funcs:
        return funcs[afunc]
    else:
        raise ValueError("Undefined function %s" % afunc)

def repl():
    while True:
        try:
            line = raw_input("%s " % prompt)
            print evaluate(parse(line), compiled_funcs = {})
        except ValueError as ve:
            print ve
            

if __name__ == '__main__':
    repl()
