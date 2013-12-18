#!/usr/bin/env python
#Minilisp: a toy lisp-to-be, with an LLVM backend
#Copyright (C) 2013 Kat

#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import copy
import sys
import random

import llvm
import llvm.core
import llvm.ee

prompt = ">"

Symbol = str
TYPE_NONE = 0
TYPE_INT = 1
TYPE_BOX = 2
TYPE_CONS = 3
TYPE_NIL = 4
TYPE_CMP = 5

lint = llvm.core.Type.int()
fvp = llvm.core.Type.pointer(lint) # "Fake void*"

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


def gifb(abox, cbuilder):
    g = lisp_module.get_function_named("get_int_from_box")
    return (cbuilder.call(g, [abox]), TYPE_INT)


def cons_val(val, point_to, cbuilder):
    cv = lisp_module.get_function_named("cons")
    return (cbuilder.call(cv, [val, point_to]), TYPE_CONS)


def box_val(val, vtype, cbuilder):
    assert vtype != TYPE_BOX # Don't box boxes
    bv = lisp_module.get_function_named("box_val")
    vt = llvm.core.Constant.int(lint, vtype)
    return (cbuilder.call(bv, [val, vt]), TYPE_BOX)


def head_list(alist, cbuilder):
    head = lisp_module.get_function_named("head")
    return (cbuilder.call(head, [alist]), TYPE_BOX) # FIXME_t


def tail_list(alist, cbuilder):
    tail = lisp_module.get_function_named("tail")
    return (cbuilder.call(tail, [alist]), TYPE_CONS)


def cg_set_variable(vname, vval, env, cbuilder, cfunction):
    entry = cfunction.get_entry_basic_block()
    builder = llvm.core.Builder.new(entry)
    builder.position_at_beginning(entry)
    env[vname] = builder.alloca(fvp, vname)
    print "env[%s] = %s" % (vname, env[vname])
    # Setting a variable doesn't return a usable value in Scheme
    return (cbuilder.store(vval, env[vname]), TYPE_NONE)


def codegen_boxed(aparse, env, cbuilder, cfunction):
    if aparse[0] == 'box':
        val, vtype = codegen(aparse[1], env, cbuilder, cfunction)
        assert vtype != TYPE_BOX # don't box boxes
        return box_val(val, vtype, cbuilder)

    elif aparse[0] == 'gifb':
        gboxed, gtype = codegen(aparse[1], env, cbuilder, cfunction)
        assert gtype == TYPE_BOX
        return gifb(gboxed, cbuilder)
    elif aparse[0] == 'add_boxed': # another semi-unlispy exercise
        if len(aparse) != 3:
            raise RuntimeError("Wrong number of arguments to add_boxed")
        v1 = codegen(aparse[1], env, cbuilder, cfunction)[0]
        v2 = codegen(aparse[2], env, cbuilder, cfunction)[0]
        
        callee = lisp_module.get_function_named('add_boxed')
        return (cbuilder.call(callee, [v1, v2], 'add_boxed'), TYPE_INT)
    

def codegen(aparse, env, cbuilder, cfunction):
    if aparse in ["'()", "()", "nil", "'nil"]:
        return (llvm.core.Constant.null(llvm.core.Type.pointer(lint)), TYPE_NIL)
    if is_atom(aparse):
        if is_integer(aparse):
            return box_val(llvm.core.Constant.int(lint, aparse), TYPE_INT, cbuilder)
        elif is_variable(aparse):
            return (cbuilder.load(env[aparse]), TYPE_BOX) # FIXME_t
        else:
            raise ValueError("unhandled atom")

    elif aparse[0] in ['box', 'add_boxed', 'gifb']:
        return codegen_boxed(aparse, env, cbuilder, cfunction)
    elif aparse[0] == 'cons':
        val = codegen(aparse[1], env, cbuilder, cfunction)
        assert val[1] == TYPE_BOX
        onto = codegen(aparse[2], env, cbuilder, cfunction)
        # TODO/FIXME: afaik, TYPE_BOX isn't actually for cons, but dotted pairs...
        assert onto[1] == TYPE_CONS or onto[1] == TYPE_NIL or onto[1] == TYPE_BOX
        return cons_val(val[0], onto[0], cbuilder)
    elif aparse[0] == 'head':
        thelist, ltype = codegen(aparse[1], env, cbuilder, cfunction)
        return head_list(thelist, cbuilder)
    elif aparse[0] == 'tail':
        thelist, ltype = codegen(aparse[1], env, cbuilder, cfunction)
        return tail_list(thelist, cbuilder)
    elif aparse[0] == 'let':
        env2 = copy.copy(env)
        varbindings = aparse[1]
        for vb in varbindings:
            varname = vb[0]
            (varval, vvtype) = codegen(vb[1], env, cbuilder, cfunction)
            cg_set_variable(varname, varval, env2, cbuilder, cfunction)
        return codegen(aparse[2], env2, cbuilder, cfunction)
    elif aparse[0] == 'set!':
        varname = aparse[1]
        (val, valtype) = codegen(aparse[2], env, cbuilder, cfunction)
        if not env.has_key(varname):
            env[varname] = cbuilder.alloca(fvp, varname)
        cbuilder.store(val, env[varname])
        return (None, TYPE_NONE)
    # http://www.llvmpy.org/llvmpy-doc/0.9/doc/kaleidoscope/PythonLangImpl3.html
    # heavily influenced the 'if' code.
    elif aparse[0] == 'if':
        (condition, cvtype) = codegen(aparse[1], env, cbuilder, cfunction)
        iftrue = aparse[2]
        iffalse = aparse[3]

        then_block = cfunction.append_basic_block('then')
        else_block = cfunction.append_basic_block('else')
        merge_block = cfunction.append_basic_block('ifcond')
        cbuilder.cbranch(condition, then_block, else_block)

        cbuilder.position_at_end(then_block)
        (then_value, tvtype) = codegen(iftrue, env, cbuilder, cfunction)
        cbuilder.branch(merge_block)

        then_block = cbuilder.basic_block
        cbuilder.position_at_end(else_block)
        (else_value, evtype) = codegen(iffalse, env, cbuilder, cfunction)
        cbuilder.branch(merge_block)
        
        else_block = cbuilder.basic_block
        cbuilder.position_at_end(merge_block)
        phi = cbuilder.phi(fvp, 'iftmp')
        phi.add_incoming(then_value, then_block)
        phi.add_incoming(else_value, else_block)
        return (phi, tvtype) # FIXME_t; this assumes tvtype == evtype
    elif aparse[0] == 'while': #unlispy exercise...
        condition_block = cfunction.append_basic_block('loop_header')
        loop_block = cfunction.append_basic_block('loop_body')
        after_block = cfunction.append_basic_block('after_loop')
        # Insert an explicit fallthrough from the current block to the condition_block.
        cbuilder.branch(condition_block)
        cbuilder.position_at_end(condition_block)
        (condition, cvtype) = codegen(aparse[1], env, cbuilder, cfunction)
        cbuilder.cbranch(condition, loop_block, after_block)
        cbuilder.position_at_end(loop_block)
        (body, bvtype) = codegen(aparse[2], env, cbuilder, cfunction)
        cbuilder.branch(condition_block)
        cbuilder.position_at_end(after_block)
        return (None, TYPE_NONE)
    elif aparse[0] == 'begin':
        ret = None
        rvtype = None
        for stmt in aparse[1:]:
            (ret, rvtype) = codegen(stmt, env, cbuilder, cfunction)
        return (ret, rvtype)
    elif aparse[0] == 'define':
        if is_atom(aparse[1]): # It's a variable definition
            varval, vtype = codegen(aparse[2], env, cbuilder, cfunction)
            return cg_set_variable(aparse[1], varval, env, cbuilder, cfunction)
        # Otherwise, it's a function definition
        fname = aparse[1][0]
        args = aparse[1][1:]
        body = aparse[2]

        funcvars = []
        for a in args:
            funcvars.append(fvp)
        func_type = llvm.core.Type.function(fvp, funcvars)
        new_func = lisp_module.add_function(func_type, fname)
        for i in range(len(args)):
            new_func.args[i].name = args[i]
            print new_func.args[i]
        bb = new_func.append_basic_block("entry")
        func_builder = llvm.core.Builder.new(bb)
        codegen(body, env, func_builder, new_func)
        return (new_func, TYPE_BOX) # TODO: check this

    elif lookup_icmp(aparse[0]): # It's an integer comparison
        icmp_cmp = lookup_icmp(aparse[0])
        (a1, v1type) = codegen(aparse[1], env, cbuilder, cfunction)
        (a2, v2type) = codegen(aparse[2], env, cbuilder, cfunction)
        a1 = norm_to_int(a1, v1type, cbuilder)
        a2 = norm_to_int(a2, v2type, cbuilder)
        cmpval = cbuilder.icmp(icmp_cmp, a1, a2, 'cmptmp')
        return (cmpval, TYPE_CMP)
    else: # everything else is currently a no-argument function
        op = lookup(aparse[0])
        (a1, v1type) = codegen(aparse[1], env, cbuilder, cfunction)
        (a2, v2type) = codegen(aparse[2], env, cbuilder, cfunction)
        a1 = norm_to_int(a1, v1type, cbuilder)
        a2 = norm_to_int(a2, v2type, cbuilder)
        mathres = getattr(cbuilder, op)(a1, a2, "intmathop")
        return box_val(mathres, TYPE_INT, cbuilder)

        
# Temporary transition function
def norm_to_int(val, vtype, cbuilder):
    normed = val
    if vtype == TYPE_BOX:
        normed, newt = gifb(val, cbuilder)
        assert newt == TYPE_INT
    else:
        assert vtype == TYPE_INT
    return normed


def compile_line(aparse):
    global lisp_module
    llvm.core.load_library_permanently("/home/me/hs/lisp/lisp_runtime.so.0.0.1")
    lisp_module = llvm.core.Module.new("minilisp")
    add_runtime_functions(lisp_module)
    func_type = llvm.core.Type.function(lint, [])
    f = lisp_module.add_function(func_type, "builtin_toplevelf")
    bb = f.append_basic_block("entry")
    cbuilder = llvm.core.Builder.new(bb)
    (codeval, codetype) = codegen(aparse, {}, cbuilder, f)
    cbuilder.ret(codeval)
    print >> sys.stderr, "module: %s" % lisp_module
    print >> sys.stderr, "function: %s" % f
    return lisp_module, f


def execute(module, llvmfunc):
    ee = llvm.ee.ExecutionEngine.new(module)
    retval = ee.run_function(llvmfunc, [])
    print >> sys.stderr, "retval is %s" % retval.as_int()
    return retval


def add_runtime_functions(module):
    lisp_module.add_function(llvm.core.Type.function(lint, [fvp, fvp]), "add_boxed")
    lisp_module.add_function(llvm.core.Type.function(fvp, [lint, lint]), "box_val")
    lisp_module.add_function(llvm.core.Type.function(fvp, [fvp, fvp]), "cons")
    lisp_module.add_function(llvm.core.Type.function(lint, [fvp]), "get_int_from_box")
    lisp_module.add_function(llvm.core.Type.function(fvp, [fvp]), "head")
    lisp_module.add_function(llvm.core.Type.function(fvp, [fvp]), "tail")


def lookup_icmp(cmp_op):
    lc = llvm.core
    cmp_ops = {'<':lc.ICMP_SLT, '=':lc.ICMP_EQ, '>':lc.ICMP_SGT,
        '!=':lc.ICMP_NE, '<=':lc.ICMP_SLE, '>=':lc.ICMP_SGE}
    if cmp_ops.has_key(cmp_op):
        return cmp_ops[cmp_op]
    return None


def lookup(afunc): # FIXME
    funcs = {'+':'add', '*':'mul', '-':'sub'}
    if afunc in funcs:
        return funcs[afunc]
    else:
        raise ValueError("Undefined function %s" % afunc)


# LLVM functions need to be named. Generate names for anonymous functions
def gen_lambda_name():
    template = "__lambda%s"
    num = random.randint(10000, 2000000000)
    fname = template % num
    # Make sure it's not already used
    try:
        lisp_module.get_function_named(fname)
    except llvm.LLVMException:
        return fname


def run_code_to_int(string_code):
    return run_code(string_code).as_int()


def run_code(string_code):
    m, f = compile_line(parse(string_code))
    return execute(m, f)


def repl():
    while True:
        try:
            print >> sys.stderr, "%s " % prompt,
            line = raw_input()
            print run_code_to_int(line)
        except ValueError as ve:
            print ve
        except EOFError:
            sys.exit(0) # Done        


if __name__ == '__main__':
    repl()
