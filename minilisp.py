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
TYPE_LAMBDA = 6

class CompilerInternals(object):
    def __init__(self, env, builder, function, module):
        self.env = env
        self.builder = builder
        self.function = function
        self.module = module

lint = llvm.core.Type.int()
fvp = llvm.core.Type.pointer(lint) # "Fake void*"
function_pointer_t = [
llvm.core.Type.pointer(llvm.core.Type.function(fvp, [])),
llvm.core.Type.pointer(llvm.core.Type.function(fvp, [fvp])),
llvm.core.Type.pointer(llvm.core.Type.function(fvp, [fvp, fvp])),
llvm.core.Type.pointer(llvm.core.Type.function(fvp, [fvp, fvp, fvp]))
]

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


def gifb(abox, ci):
    g = ci.module.get_function_named("get_int_from_box")
    return (ci.builder.call(g, [abox]), TYPE_INT)


def cons_val(val, point_to, ci):
    cv = ci.module.get_function_named("cons")
    return (ci.builder.call(cv, [val, point_to]), TYPE_CONS)


def box_val(val, vtype, ci):
    assert vtype != TYPE_BOX # Don't box boxes
    bv = ci.module.get_function_named("box_val")
    vt = llvm.core.Constant.int(lint, vtype)
    return (ci.builder.call(bv, [val, vt]), TYPE_BOX)


def head_list(alist, ci):
    head = ci.module.get_function_named("head")
    return (ci.builder.call(head, [alist]), TYPE_BOX) # FIXME_t


def tail_list(alist, ci):
    tail = ci.module.get_function_named("tail")
    return (ci.builder.call(tail, [alist]), TYPE_CONS)


def make_lambda(fp, num_args, ci):
    ml = ci.module.get_function_named("make_lambda")
    return (ci.builder.call(ml, [fp, num_args]), TYPE_LAMBDA)


def cg_set_variable(vname, vval, ci):
    entry = ci.function.get_entry_basic_block()
    builder = llvm.core.Builder.new(entry)
    builder.position_at_beginning(entry)
    ci.env[vname] = builder.alloca(fvp, vname)
    # Setting a variable doesn't return a usable value in Scheme
    return (ci.builder.store(vval, ci.env[vname]), TYPE_NONE)


def cg_function(fname, fargs, fbody, ci):
        funcvars = []
        for a in fargs:
            funcvars.append(fvp)
        func_type = llvm.core.Type.function(fvp, funcvars)
        new_func = ci.module.add_function(func_type, fname)
        f_env = copy.copy(ci.env)
        bb = new_func.append_basic_block("entry")
        func_builder = llvm.core.Builder.new(bb)
        new_function_ci = CompilerInternals(f_env, func_builder, new_func, ci.module)
        for i in range(len(fargs)):
            new_func.args[i].name = fargs[i]
            cg_set_variable(fargs[i], new_func.args[i], new_function_ci)
        body_val, bt = codegen(fbody, new_function_ci)
        # CG'ing a function doesn't intrinsically return a value
        return (func_builder.ret(body_val), TYPE_NONE) 


def codegen_boxed(aparse, ci):
    if aparse[0] == 'box':
        val, vtype = codegen(aparse[1], ci)
        assert vtype != TYPE_BOX # don't box boxes
        return box_val(val, vtype, ci)

    elif aparse[0] == 'gifb':
        gboxed, gtype = codegen(aparse[1], ci)
        assert gtype == TYPE_BOX
        return gifb(gboxed, ci)
    elif aparse[0] == 'add_boxed': # another semi-unlispy exercise
        if len(aparse) != 3:
            raise RuntimeError("Wrong number of arguments to add_boxed")
        v1 = codegen(aparse[1], ci)[0]
        v2 = codegen(aparse[2], ci)[0]
        
        callee = ci.module.get_function_named('add_boxed')
        return (ci.builder.call(callee, [v1, v2], 'add_boxed'), TYPE_INT)

    
def codegen(aparse, ci):
    if aparse in ["'()", "()", "nil", "'nil"]:
        return (llvm.core.Constant.null(llvm.core.Type.pointer(lint)), TYPE_NIL)
    if is_atom(aparse):
        if is_integer(aparse):
            return box_val(llvm.core.Constant.int(lint, aparse), TYPE_INT, ci)
        elif is_variable(aparse):
            return (ci.builder.load(ci.env[aparse]), TYPE_BOX) # FIXME_t
        else:
            raise ValueError("unhandled atom")

    elif aparse[0] in ['box', 'add_boxed', 'gifb']:
        return codegen_boxed(aparse, ci)
    elif aparse[0] == 'cons':
        val = codegen(aparse[1], ci)
        assert val[1] == TYPE_BOX
        onto = codegen(aparse[2], ci)
        # TODO/FIXME: afaik, TYPE_BOX isn't actually for cons, but dotted pairs...
        assert onto[1] == TYPE_CONS or onto[1] == TYPE_NIL or onto[1] == TYPE_BOX
        return cons_val(val[0], onto[0], ci)
    elif aparse[0] == 'head':
        thelist, ltype = codegen(aparse[1], ci)
        return head_list(thelist, ci)
    elif aparse[0] == 'tail':
        thelist, ltype = codegen(aparse[1], ci)
        return tail_list(thelist, ci)
    elif aparse[0] == 'let':
        env2 = copy.copy(ci.env)
        varbindings = aparse[1]
        for vb in varbindings:
            varname = vb[0]
            (varval, vvtype) = codegen(vb[1], ci)
            new_env_ci = CompilerInternals(env2, ci.builder, ci.function, ci.module)
            cg_set_variable(varname, varval, new_env_ci)
        new_let_ci = CompilerInternals(env2, ci.builder, ci.function, ci.module)
        return codegen(aparse[2], new_let_ci)
    elif aparse[0] == 'set!':
        varname = aparse[1]
        (val, valtype) = codegen(aparse[2], ci)
        if not ci.env.has_key(varname):
            ci.env[varname] = ci.builder.alloca(fvp, varname)
        ci.builder.store(val, ci.env[varname])
        return (None, TYPE_NONE)
    # http://www.llvmpy.org/llvmpy-doc/0.9/doc/kaleidoscope/PythonLangImpl3.html
    # heavily influenced the 'if' code.
    elif aparse[0] == 'if':
        (condition, cvtype) = codegen(aparse[1], ci)
        iftrue = aparse[2]
        iffalse = aparse[3]

        then_block = ci.function.append_basic_block('then')
        else_block = ci.function.append_basic_block('else')
        merge_block = ci.function.append_basic_block('ifcond')
        ci.builder.cbranch(condition, then_block, else_block)

        ci.builder.position_at_end(then_block)
        (then_value, tvtype) = codegen(iftrue, ci)
        ci.builder.branch(merge_block)

        then_block = ci.builder.basic_block
        ci.builder.position_at_end(else_block)
        (else_value, evtype) = codegen(iffalse, ci)
        ci.builder.branch(merge_block)
        
        else_block = ci.builder.basic_block
        ci.builder.position_at_end(merge_block)
        phi = ci.builder.phi(fvp, 'iftmp')
        phi.add_incoming(then_value, then_block)
        phi.add_incoming(else_value, else_block)
        return (phi, tvtype) # FIXME_t; this assumes tvtype == evtype
    elif aparse[0] == 'while': #unlispy exercise...
        condition_block = ci.function.append_basic_block('loop_header')
        loop_block = ci.function.append_basic_block('loop_body')
        after_block = ci.function.append_basic_block('after_loop')
        # Insert an explicit fallthrough from the current block to the condition_block.
        ci.builder.branch(condition_block)
        ci.builder.position_at_end(condition_block)
        (condition, cvtype) = codegen(aparse[1], ci)
        ci.builder.cbranch(condition, loop_block, after_block)
        ci.builder.position_at_end(loop_block)
        (body, bvtype) = codegen(aparse[2], ci)
        ci.builder.branch(condition_block)
        ci.builder.position_at_end(after_block)
        return (None, TYPE_NONE)
    elif aparse[0] == 'begin':
        ret = None
        rvtype = None
        for stmt in aparse[1:]:
            (ret, rvtype) = codegen(stmt, ci)
        return (ret, rvtype)
    elif aparse[0] == 'define':
        if is_atom(aparse[1]): # It's a variable definition
            varval, vtype = codegen(aparse[2], ci)
            return cg_set_variable(aparse[1], varval, ci)
        # Otherwise, it's a function definition
        fname = aparse[1][0]
        args = aparse[1][1:]
        body = aparse[2]
        return cg_function(fname, args, body, ci)
    elif aparse[0] == 'lambda':
        fname = gen_lambda_name(ci.module)
        args = aparse[1]
        body = aparse[2]
        cg_function(fname, args, body, ci)
        f = lookup_module(fname, ci.module)
        f_desc_reg = ci.builder.alloca(fvp, "a register to point to the function")
        ci.builder.store(f, f_desc_reg)
        num_args = llvm.core.Constant.int(lint, len(args))
        return make_lambda(f_desc_reg, num_args, ci)
    elif lookup_icmp(aparse[0]): # It's an integer comparison
        icmp_cmp = lookup_icmp(aparse[0])
        args = []
        for a in aparse[1:]:
            arg, argtype = codegen(a, ci)
            args.append(norm_to_int(arg, argtype, ci))
        cmpval = llvm.core.Constant.int(llvm.core.Type.int(1), 1) # true
        for i in range(len(args) - 1):
            curval = ci.builder.icmp(icmp_cmp, args[i], args[i+1], 'cmptmp')
            cmpval = ci.builder.and_(cmpval, curval)
        return (cmpval, TYPE_CMP)
    elif lookup_math(aparse[0]): 
        op = lookup_math(aparse[0])
        args = []
        for a in aparse[1:]:
            arg, argtype = codegen(a, ci)
            args.append(norm_to_int(arg, argtype, ci))
        res = lookup_math_id(op)
        # Subtraction is special. (- 3) = -3; (- 5 1) = 4.
        if op == 'sub' and len(args) > 1:
            res = getattr(ci.builder, op)(args[0], args[1], "intmathop")
            args = args[2:]
        for i in range(len(args)):
            res = getattr(ci.builder, op)(res, args[i], "intmathop")
        return box_val(res, TYPE_INT, ci)
    elif lookup_module(aparse[0], ci.module):
        f = lookup_module(aparse[0], ci.module)
        args = []
        for a in aparse[1:]:
            v, t = codegen(a, ci)
            args.append(v)
        return (ci.builder.call(f, args), TYPE_BOX)
    elif ci.env.has_key(aparse[0]):
        lambda_reg = ci.env[aparse[0]]
        args = []
        for a in aparse[1:]:
            val, vtype = codegen(a, ci)
            args.append(val)
        lambda_info = ci.builder.load(lambda_reg)
        lgf = ci.module.get_function_named("lambda_get_fp")
        raw_fp = ci.builder.call(lgf, [lambda_info])
        f_proto = function_pointer_t[len(args)]
        real_fp = ci.builder.bitcast(raw_fp, f_proto, "function pointer")
        return (ci.builder.call(real_fp, args), TYPE_BOX)
    else:
        raise ValueError("Unhandled: %s" % aparse[0])

        
# Temporary transition function
def norm_to_int(val, vtype, ci):
    normed = val
    if vtype == TYPE_BOX:
        normed, newt = gifb(val, ci)
        assert newt == TYPE_INT
    else:
        assert vtype == TYPE_INT
    return normed


# +/- 0 is the same number; so is * 1.
def lookup_math_id(op):
    print "op is %s" % op
    if op in ['add', 'sub']:
        return llvm.core.Constant.int(lint, 0)
    return llvm.core.Constant.int(lint, 1)


def compile_line(aparse):
    llvm.core.load_library_permanently("./lisp_runtime.so.0.0.1")
    lisp_module = llvm.core.Module.new("minilisp")
    add_runtime_functions(lisp_module)
    func_type = llvm.core.Type.function(lint, [])
    f = lisp_module.add_function(func_type, "builtin_toplevelf")
    bb = f.append_basic_block("entry")
    cbuilder = llvm.core.Builder.new(bb)
    ci = CompilerInternals({}, cbuilder, f, lisp_module)
    (codeval, codetype) = codegen(aparse, ci)
    cbuilder.ret(codeval)
    print >> sys.stderr, "module: %s" % lisp_module
    print >> sys.stderr, "function: %s" % f
    return lisp_module, f


def execute(module, llvmfunc):
    ee = llvm.ee.ExecutionEngine.new(module)
    retval = ee.run_function(llvmfunc, [])
    print >> sys.stderr, "retval is %s" % retval.as_int()
    return retval


def add_runtime_functions(to_module):
    to_module.add_function(llvm.core.Type.function(lint, [fvp, fvp]), "add_boxed")
    to_module.add_function(llvm.core.Type.function(fvp, [lint, lint]), "box_val")
    to_module.add_function(llvm.core.Type.function(fvp, [fvp, fvp]), "cons")
    to_module.add_function(llvm.core.Type.function(lint, [fvp]), "get_int_from_box")
    to_module.add_function(llvm.core.Type.function(fvp, [fvp]), "head")
    to_module.add_function(llvm.core.Type.function(fvp, [fvp]), "tail")
    to_module.add_function(llvm.core.Type.function(fvp, [llvm.core.Type.pointer(fvp), lint]), "make_lambda")
    to_module.add_function(llvm.core.Type.function(lint, [fvp]), "lambda_num_args")
    to_module.add_function(llvm.core.Type.function(fvp, [fvp]), "lambda_get_fp")


def lookup_icmp(cmp_op):
    lc = llvm.core
    cmp_ops = {'<':lc.ICMP_SLT, '=':lc.ICMP_EQ, '>':lc.ICMP_SGT,
        '!=':lc.ICMP_NE, '<=':lc.ICMP_SLE, '>=':lc.ICMP_SGE}
    if cmp_ops.has_key(cmp_op):
        return cmp_ops[cmp_op]
    return None


def lookup_math(afunc):
    funcs = {'+':'add', '*':'mul', '-':'sub'} # TODO: add more
    if afunc in funcs:
        return funcs[afunc]
    return None

def lookup_module(afunc, in_module):
    try:
        return in_module.get_function_named(afunc)
    except llvm.LLVMException:
        return None


# LLVM functions need to be named. Generate names for anonymous functions
def gen_lambda_name(in_module):
    template = "__lambda%s"
    num = random.randint(10000, 2000000000)
    fname = template % num
    # Make sure it's not already used
    try:
        in_module.get_function_named(fname)
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
