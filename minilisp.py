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

    elif aparse[0] == '=':
        a1 = codegen(aparse[1], env, cbuilder, cfunction)
        a2 = codegen(aparse[2], env, cbuilder, cfunction)

        cmpval = cbuilder.icmp(llvm.core.ICMP_EQ, a1, a2, 'cmptmp')
        return cmpval
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
    # http://www.llvmpy.org/llvmpy-doc/0.9/doc/kaleidoscope/PythonLangImpl3.html
    # heavily influenced the 'if' code.
    elif aparse[0] == 'if':
        condition = codegen(aparse[1], env, cbuilder, cfunction)
        iftrue = aparse[2]
        iffalse = aparse[3]

        then_block = cfunction.append_basic_block('then')
        else_block = cfunction.append_basic_block('else')
        merge_block = cfunction.append_basic_block('ifcond')
        cbuilder.cbranch(condition, then_block, else_block)

        cbuilder.position_at_end(then_block)
        then_value = codegen(iftrue, env, cbuilder, cfunction)
        cbuilder.branch(merge_block)

        then_block = cbuilder.basic_block
        cbuilder.position_at_end(else_block)
        else_value = codegen(iffalse, env, cbuilder, cfunction)
        cbuilder.branch(merge_block)
        
        else_block = cbuilder.basic_block
        cbuilder.position_at_end(merge_block)
        phi = cbuilder.phi(llvm.core.Type.int(), 'iftmp')
        phi.add_incoming(then_value, then_block)
        phi.add_incoming(else_value, else_block)
        return phi
    elif aparse[0] == 'begin':
        ret = None
        for stmt in aparse[1:]:
            ret = codegen(stmt, env, cbuilder, cfunction)
        return ret
    #elif aparse[0] == 'lambda':
    #    args = aparse[1]
    #    body = aparse[2]
    #    pass
    else: # everything else is currently a no-argument function
        lint = llvm.core.Type.int()
        op = lookup(aparse[0])
        a1 = codegen(aparse[1], env, cbuilder, cfunction)
        a2 = codegen(aparse[2], env, cbuilder, cfunction)
        tmp = getattr(cbuilder, op)(a1, a2, "tmpwhy")
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
    funcs = {'+':'add', '*':'mul', '-':'sub'}
    if afunc in funcs:
        return funcs[afunc]
    else:
        raise ValueError("Undefined function %s" % afunc)

def run_code_to_int(string_code):
    return run_code(string_code).as_int()

def run_code(string_code):
    m, f = compile_line(parse(string_code))
    return execute(m, f)

def repl():
    while True:
        try:
            line = raw_input("%s " % prompt)
            print run_code_to_int(line)
        except ValueError as ve:
            print ve
            

if __name__ == '__main__':
    repl()
