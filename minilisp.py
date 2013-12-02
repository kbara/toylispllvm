#!/usr/bin/env python
import operator
import copy

import llvm
import llvm.core
import llvm.ee

prompt = ">"

Symbol = str

# The parser/tokenizer/read_from are stolen from Norvig's lis.py
def parse(x):
    tokens = (tokenize(x))
    if tokens:
        return read_from(tokens)
    else:
        return []


def tokenize(x):
    return x.replace('(', ' ( ').replace(')', ' ) ').split()


def read_from(tokens):
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
        return atom(cur_token)
   

def atom(token):
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token) 


def is_integer(atom):
    try:
        int(atom)
        return True
    except ValueError:
        return False


def is_atom(aparse):
    return not isinstance(aparse, [].__class__) 

def is_variable(aparse):
    return True # FIXME


def codegen(aparse, env, cbuilder, cfunction):
    if is_atom(aparse):
        if is_integer(aparse):
            return llvm.core.Constant.int(llvm.core.Type.int(), aparse)
        elif is_variable(aparse):
            return cbuilder.load(env[aparse])
        else:
            raise ValueError("unhandled atom")
    elif aparse[0] == 'let': # this is still int-only, and only one var...
        varname = aparse[1][0]
        env2 = copy.copy(env) 

        entry = cfunction.get_entry_basic_block()
        builder = llvm.core.Builder.new(entry)
        builder.position_at_beginning(entry)
        env2[varname] = builder.alloca(llvm.core.Type.int(), varname)

        varval = codegen(aparse[1][1], env, cbuilder, cfunction)
        cbuilder.store(varval, env2[varname])
        return codegen(aparse[2], env2, cbuilder, cfunction)

    #elif aparse[0] == 'lambda':
    #    args = aparse[1]
    #    body = aparse[2]
    #    pass
    else: # everything else is currently a no-argument function
        lint = llvm.core.Type.int()
        op = lookup(aparse[0])
        a1 = codegen(aparse[1], env, cbuilder, cfunction)
        a2 = codegen(aparse[2], env, cbuilder, cfunction)
        tmp = getattr(cbuilder, op.__name__)(a1, a2, "tmpwhy")
        return tmp
        

def compile_line(aparse):
    lisp_module = llvm.core.Module.new("minilisp")
    lint = llvm.core.Type.int()
    func_type = llvm.core.Type.function(lint, [])
    f = lisp_module.add_function(func_type, "afunction")
    bb = f.append_basic_block("entry")
    cbuilder = llvm.core.Builder.new(bb)
    cbuilder.ret(codegen(aparse, {}, cbuilder, f))
    print "module: %s" % lisp_module
    print "function: %s" % f
    return lisp_module, f


def execute(module, llvmfunc):
    ee = llvm.ee.ExecutionEngine.new(module)
    lint = llvm.core.Type.int()
    retval = ee.run_function(llvmfunc, [])
    print "retval is %s" % retval.as_int()
    return retval


def lookup(afunc): # FIXME
    funcs = {'+':operator.add, '*':operator.mul, '-':operator.sub}
    if afunc in funcs:
        return funcs[afunc]
    else:
        raise ValueError("Undefined function %s" % afunc)


def repl():
    while True:
        #try:
            line = raw_input("%s " % prompt)
            m, f = compile_line(parse(line))
            execute(m, f)
        #except ValueError as ve:
        #    print ve
            

if __name__ == '__main__':
    repl()
