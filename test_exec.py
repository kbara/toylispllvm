#!/usr/bin/env python

import unittest
import minilisp

def run_code_to_int(string_code):
    return minilisp.run_code("(gifb %s)" % string_code).as_int()

def run_unboxed_code_to_int(string_code):
    return minilisp.run_code(string_code).as_int()

class TestLispFunctions(unittest.TestCase):
    def testParse(self):
        self.assertEqual(3, minilisp.parse("3"))
        self.assertEqual('x', minilisp.parse("x"))
        self.assertEqual(['+', 'x', 'y'], minilisp.parse("(+ x y)"))

    def testVar(self):
        self.assertEqual(3, run_code_to_int('3'))

    def testMath(self):
        self.assertEqual(7, run_code_to_int('(+ 2 (- (* 5 3) 10))'))

    def testLet(self):
        self.assertEqual(9, run_code_to_int('(let ((x 1)) (+ x 8))'))

    def testEquality(self):
        ret1 = 1 & run_unboxed_code_to_int('(= 3 3)')
        self.assertEqual(1, ret1)
        ret2 = 1 & run_unboxed_code_to_int('(= 3 2)')
        self.assertEqual(0, ret2)

    def testLT(self):
        ret1 = 1 & run_unboxed_code_to_int('(< 3 3)')
        self.assertEqual(0, ret1)
        ret2 = 1 & run_unboxed_code_to_int('(< 2 3)')
        self.assertEqual(1, ret2)

    def testOtherCmp(self): 
        ret1 = 1 & run_unboxed_code_to_int('(<= 3 3)')
        self.assertEqual(1, ret1)
        ret2 = 1 & run_unboxed_code_to_int('(<= 3 4)')
        self.assertEqual(1, ret2)
        ret3 = 1 & run_unboxed_code_to_int('(<= 3 2)')
        self.assertEqual(0, ret3)
        ret4 = 1 & run_unboxed_code_to_int('(!= 2 3)')
        self.assertEqual(1, ret4)
        ret5 = 1 & run_unboxed_code_to_int('(!= 5 5)')
        self.assertEqual(0, ret5)
        ret6 = 1 & run_unboxed_code_to_int('(> 3 5)')
        self.assertEqual(0, ret6)
        ret7 = 1 & run_unboxed_code_to_int('(> 3 3)')
        self.assertEqual(0, ret7)
        ret8 = 1 & run_unboxed_code_to_int('(>= 3 3)')
        self.assertEqual(1, ret8)

    def testIf(self):
        self.assertEqual(4, run_code_to_int('(if (= 1 2) 3 4)'))
        self.assertEqual(3, run_code_to_int('(if (= 1 1) 3 4)'))
        
    def testComplexIfLet(self):
        code = '(if (= (let ((x 1)) x) (let ((x 2)) x)) (let ((x 5)) x) (let ((x 6)) x))'
        self.assertEqual(6, run_code_to_int(code))

    def testBegin(self):
        code = '(begin (+ 3 4) (+ 7 8))'
        self.assertEqual(15, run_code_to_int(code))

    def testSet(self):
        code = '(let ((x 3)) (let ((y 4)) (begin (set! x 5) x)))'
        self.assertEqual(5, run_code_to_int(code))

    def testBeginAndSet(self):
        code = '(begin (set! x 3) x)'
        self.assertEqual(3, run_code_to_int(code))

    def testWhile(self):
        code = '(let ((x 2)(y 11)) \
            (begin \
                (while (< 0 x) \
                    (begin (set! x (- x 1)) (set! y (+ y 1)))) \
            y))'
        self.assertEqual(13, run_code_to_int(code))


    def testWhileNoTimes(self):
        code = ('(let ((x 3)) (begin (while (< 3 0) (set! x 5)) x))')
        self.assertEqual(3, run_code_to_int(code))

    def testNil(self):
        minilisp.run_code('nil')

    def testCons(self):
        minilisp.run_code('(cons 3 nil)')

    def testHead(self):
        self.assertEqual(5, run_code_to_int('(head (cons 5 nil))'))

    def testAddBoxed(self):
        self.assertEqual(25, run_unboxed_code_to_int('(add_boxed 10 15)'))        

    def testLetCons(self):
        self.assertEqual(33, run_code_to_int('(let ((y (cons 33 nil))) (head y))'))

    def testConsCons(self):
        self.assertEqual(3, run_code_to_int('(let ((x (cons 3 nil)) (y (cons 4 nil))) (head (head (cons x y))))'))

    def testTail(self):
        self.assertEqual(4, run_code_to_int('(head (tail (cons 3 (cons 4 nil))))'))

    def testLambda(self):
        self.assertEqual(5, run_code_to_int('(let ((tfunc (lambda (x y) (+ x y)))) (tfunc 2 3))'))

    def testDefineVar(self):
        self.assertEqual(3, run_code_to_int('(begin (define a 3) a)'))

    def testDefineFunc(self):
        self.assertEqual(7, run_code_to_int('(begin (define (atestf y z) (+ y z)) (atestf 3 4))'))

    def testNCmp(self):
        ret1 = 1 & run_unboxed_code_to_int('(< 2)')
        self.assertEqual(1, ret1)
        ret2 = 1 & run_unboxed_code_to_int('(< 2 3 4)')
        self.assertEqual(1, ret2)
        ret3 = 1 & run_unboxed_code_to_int('(< 2 4 3)')
        self.assertEqual(0, ret3)


    def testNAdd(self):
        ret1 = run_code_to_int('(+)')
        self.assertEqual(0, ret1)
        ret2 = run_code_to_int('(+ 2)')
        self.assertEqual(2, ret2)
        ret3 = run_code_to_int('(+ 2 4 3)')
        self.assertEqual(9, ret3)

    def testNSub(self):
        ret1 = run_code_to_int('(- -4)')
        self.assertEqual(4, ret1)
        ret2 = run_code_to_int('(- 5 2)')
        self.assertEqual(3, ret2)
        ret3 = run_code_to_int('(- 10 7 1)')
        self.assertEqual(2, ret3)


if __name__ == '__main__':
    unittest.main()

