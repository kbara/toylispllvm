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



current_bb_builder = None
current_function = None

def codegen(aparse, env):
    if is_atom(aparse):
        if is_integer(aparse):
            return llvm.core.Constant.int(llvm.core.Type.int(), aparse)
        elif is_variable(aparse):
            return current_bb_builder.load(env[aparse])
        else:
            raise ValueError("unhandled atom")
    elif aparse[0] == 'let': # this is still int-only, and only one var...
        varname = aparse[1][0]
        env2 = copy.copy(env) 

        entry = current_function.get_entry_basic_block()
        builder = llvm.core.Builder.new(entry)
        builder.position_at_beginning(entry)
        env2[varname] = builder.alloca(llvm.core.Type.int(), varname)

        varval = codegen(aparse[1][1], env)
        current_bb_builder.store(varval, env2[varname])
        return codegen(aparse[2], env2)

    elif aparse[0] == 'lambda':
        args = aparse[1]
        body = aparse[2]
        pass
    else: # everything else is currently a no-argument function
        lint = llvm.core.Type.int()
        #two_arg_func = llvm.core.Type.function(lint, [lint, lint])
        op = lookup(aparse[0])
        a1 = codegen(aparse[1], env)
        a2 = codegen(aparse[2], env)
        tmp = getattr(current_bb_builder, op.__name__)(a1, a2, "tmpwhy")
        return tmp
        

def compile_line(aparse):
    lisp_module = llvm.core.Module.new("minilisp")
    lint = llvm.core.Type.int()
    func_type = llvm.core.Type.function(lint, [])
    f = lisp_module.add_function(func_type, "afunction")
    bb = f.append_basic_block("entry")
    global current_bb_builder, current_function
    current_function = f
    current_bb_builder = llvm.core.Builder.new(bb)
    current_bb_builder.ret(codegen(aparse, {}))
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
