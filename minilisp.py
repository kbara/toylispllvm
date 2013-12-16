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

import llvm
import llvm.core
import llvm.ee

prompt = ">"

Symbol = str
TYPE_NONE = 0
TYPE_INT = 1
TYPE_BOX = 2
TYPE_CONS = 3

lint = llvm.core.Type.int()

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


#def decrease_refcount(box_p, cbuilder, cfunction):
#    lint = llvm.core.Type.int()
#    mem_refp = cbuilder.gep(box_p, [llvm.core.Constant.int(lint, 2)])
#    refc = cbuilder.load(mem_refp)
#    new_refc = cbuilder.sub(refc, llvm.core.Constant.int(lint, 1))
#    cbuilder.store(new_refc, mem_refp)

#    condition_block = cfunction.append_basic_block('check_freeable')
#    free_block = cfunction.append_basic_block('free')
#    after_block = cfunction.append_basic_block('after')

#    cbuilder.branch(condition_block)
#    cbuilder.position_at_end(condition_block)
#    is_freeable = cbuilder.icmp(llvm.core.ICMP_EQ, new_refc,
#        llvm.core.Constant.int(lint, 0), 'refcmp')
#    cbuilder.cbranch(is_freeable, free_block, after_block)

#    # The reference count is zero
#    cbuilder.position_at_end(free_block)
#    cbuilder.free(box_p)
#    cbuilder.branch(after_block)
    
#    cbuilder.position_at_end(after_block) # necessary


#def box_val(val, vtype, cbuilder):
#    BOX_COMPONENTS = 3
#    lint = llvm.core.Type.int()

#    llvm_box_size = llvm.core.Constant.int(lint, BOX_COMPONENTS)
#    llvm_ref_count = llvm.core.Constant.int(lint, 1)
#    llvm_type_val = llvm.core.Constant.int(lint, vtype)
 
#    mem = cbuilder.malloc_array(lint, llvm_box_size)
#    mem_tp = cbuilder.gep(mem, [llvm.core.Constant.int(lint, 0)])
#    cbuilder.store(llvm_type_val, mem_tp)
#    mem_valp = cbuilder.gep(mem, [llvm.core.Constant.int(lint, 1)])
#    cbuilder.store(val, mem_valp)
#    mem_refp = cbuilder.gep(mem, [llvm.core.Constant.int(lint, 2)])
#    cbuilder.store(llvm_ref_count, mem_refp)

#    return (mem, TYPE_BOX)


# Value and point_to need to already be valid LLVM objects
def cons_val(val, vtype, point_to, cbuilder):
    # [Vtype, Value, Pointer, Refcount]
    CONS_COMPONENTS = 4
    lint = llvm.core.Type.int()

    llvm_cons_size = llvm.core.Constant.int(lint, CONS_COMPONENTS)
    llvm_ref_count = llvm.core.Constant.int(lint, 1)
    llvm_type_val = llvm.core.Constant.int(lint, vtype)

    mem = cbuilder.malloc_array(lint, llvm_cons_size)
    mem_tp = cbuilder.gep(mem, [llvm.core.Constant.int(lint, 0)])
    cbuilder.store(llvm_type_val, mem_tp)
    mem_valp = cbuilder.gep(mem, [llvm.core.Constant.int(lint, 1)])
    cbuilder.store(val, mem_valp)
    mem_ptrp = cbuilder.gep(mem, [llvm.core.Constant.int(lint, 2)])
    cbuilder.store(point_to, mem_ptrp)
    mem_refp = cbuilder.gep(mem, [llvm.core.Constant.int(lint, 3)])
    cbuilder.store(llvm_ref_count, mem_refp)

    return (mem, TYPE_CONS)


def box_val(val, vtype, cbuilder):
    box_val = lisp_module.get_function_named("box_val")
    vt = llvm.core.Constant.int(lint, vtype)
    return (cbuilder.call(box_val, [val, vt]), TYPE_BOX)


def codegen_boxed(aparse, env, cbuilder, cfunction):
    # [Type, Value, Refcount]
    #BOX_COMPONENTS = 3
    lint = llvm.core.Type.int()
    if aparse[0] == 'box':
        val, vtype = codegen(aparse[1], env, cbuilder, cfunction)
        return box_val(val, vtype, cbuilder)
#    elif aparse[0] == 'unbox':
#        # This -could- assert that the type is TYPE_BOX...
#        box_p = codegen(aparse[1], env, cbuilder, cfunction)[0]
#
#        mem_tp = cbuilder.gep(box_p, [llvm.core.Constant.int(lint, 0)])
#        content_type = cbuilder.load(mem_tp)
#        mem_valp = cbuilder.gep(box_p, [llvm.core.Constant.int(lint, 1)])
#        val = cbuilder.load(mem_valp)
#        decrease_refcount(box_p, cbuilder, cfunction)
#        return (val, content_type)

    elif aparse[0] == 'add_boxed': # another semi-unlispy exercise
        if len(aparse) != 3:
            raise RuntimeError("Wrong number of arguments to add_boxed")
        v1 = codegen_boxed(aparse[1], env, cbuilder, cfunction)[0]
        v2 = codegen_boxed(aparse[2], env, cbuilder, cfunction)[0]
        
        callee = lisp_module.get_function_named('add_boxed')
        return (cbuilder.call(callee, [v1, v2], 'add_boxed'), TYPE_INT)
    

def codegen(aparse, env, cbuilder, cfunction):
    lint = llvm.core.Type.int()
    if aparse in ["'()", "()", "nil", "'nil"]:
        return box_val(llvm.core.Constant.int(lint, 0), TYPE_NONE, cbuilder)
    if is_atom(aparse):
        if is_integer(aparse):
            return (llvm.core.Constant.int(llvm.core.Type.int(), aparse), TYPE_INT)
        elif is_variable(aparse):
            return (cbuilder.load(env[aparse]), TYPE_INT) # FIXME_t
        else:
            raise ValueError("unhandled atom")

    elif lookup_icmp(aparse[0]): # It's an integer comparison
        icmp_cmp = lookup_icmp(aparse[0])
        (a1, v1type) = codegen(aparse[1], env, cbuilder, cfunction)
        (a2, v2type) = codegen(aparse[2], env, cbuilder, cfunction)
        cmpval = cbuilder.icmp(icmp_cmp, a1, a2, 'cmptmp')
        return (cmpval, TYPE_INT)
    elif aparse[0] in ['box', 'unbox', 'add_boxed', 'exit']:
        return codegen_boxed(aparse, env, cbuilder, cfunction)
    elif aparse[0] == 'cons':
        val = codegen(aparse[1], env, cbuilder, cfunction)
        onto = codegen(aparse[2], env, cbuilder, cfunction)
        return cons_val(val[0], val[1], onto[0], cbuilder)
    elif aparse[0] == 'head':
        cons_p = codegen(aparse[1], env, cbuilder, cfunction)[0]

        mem_tp = cbuilder.gep(cons_p, [llvm.core.Constant.int(lint, 0)])
        content_type = cbuilder.load(mem_tp)
        mem_valp = cbuilder.gep(cons_p, [llvm.core.Constant.int(lint, 1)])
        val = cbuilder.load(mem_valp)

        return (val, content_type)
    elif aparse[0] == 'let': # this is still int-only...
        env2 = copy.copy(env)
        varbindings = aparse[1]
        for vb in varbindings:
            varname = vb[0]
            entry = cfunction.get_entry_basic_block()
            builder = llvm.core.Builder.new(entry)
            builder.position_at_beginning(entry)
            env2[varname] = builder.alloca(llvm.core.Type.int(), varname)

            (varval, vvtype) = codegen(vb[1], env, cbuilder, cfunction)
            cbuilder.store(varval, env2[varname])
        return codegen(aparse[2], env2, cbuilder, cfunction)
    elif aparse[0] == 'set!':
        varname = aparse[1]
        (val, valtype) = codegen(aparse[2], env, cbuilder, cfunction)
        if not env.has_key(varname):
            env[varname] = cbuilder.alloca(llvm.core.Type.int(), varname)
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
        phi = cbuilder.phi(llvm.core.Type.int(), 'iftmp')
        phi.add_incoming(then_value, then_block)
        phi.add_incoming(else_value, else_block)
        return (phi, TYPE_INT) # FIXME_t
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
            (ret, revtype) = codegen(stmt, env, cbuilder, cfunction)
        return (ret, rvtype)
    #elif aparse[0] == 'lambda':
    #    args = aparse[1]
    #    body = aparse[2]
    #    pass
    else: # everything else is currently a no-argument function
        op = lookup(aparse[0])
        (a1, v1type) = codegen(aparse[1], env, cbuilder, cfunction)
        (a2, v2type) = codegen(aparse[2], env, cbuilder, cfunction)
        tmp = getattr(cbuilder, op)(a1, a2, "tmpwhy")
        return (tmp, TYPE_INT) # FIXME_t
        

def compile_line(aparse):
    global lisp_module
    llvm.core.load_library_permanently("/home/me/hs/lisp/lisp_runtime.so.0.0.1")
    lisp_module = llvm.core.Module.new("minilisp")
    lint = llvm.core.Type.int()
    add_runtime_functions(lisp_module)
    func_type = llvm.core.Type.function(lint, [])
    f = lisp_module.add_function(func_type, "afunction")
    bb = f.append_basic_block("entry")
    cbuilder = llvm.core.Builder.new(bb)
    (codeval, codetype) = codegen(aparse, {}, cbuilder, f)
    cbuilder.ret(codeval)
    print >> sys.stderr, "module: %s" % lisp_module
    print >> sys.stderr, "function: %s" % f
    return lisp_module, f


def execute(module, llvmfunc):
    ee = llvm.ee.ExecutionEngine.new(module)
    lint = llvm.core.Type.int()
    retval = ee.run_function(llvmfunc, [])
    print >> sys.stderr, "retval is %s" % retval.as_int()
    return retval


def add_runtime_functions(module):
    lint = llvm.core.Type.int()
    lap = llvm.core.Type.pointer(lint) # Lies; I'm using it like void*
    lisp_module.add_function(llvm.core.Type.function(lint, [lap, lap]), "add_boxed")
    lisp_module.add_function(llvm.core.Type.function(lap, [lint, lint]), "box_val")

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
