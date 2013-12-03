#!/usr/bin/env python

import unittest
import minilisp

class TestLispFunctions(unittest.TestCase):
    def testParse(self):
        self.assertEqual(3, minilisp.parse("3"))
        self.assertEqual('x', minilisp.parse("x"))
        self.assertEqual(['+', 'x', 'y'], minilisp.parse("(+ x y)"))

    def testVar(self):
        self.assertEqual(3, minilisp.run_code_to_int('3'))

    def testMath(self):
        self.assertEqual(7, minilisp.run_code_to_int('(+ 2 (- (* 5 2) 5))'))

    def testLet(self):
        self.assertEqual(9, minilisp.run_code_to_int('(let (x 1) (+ x 8))'))

    def testEquality(self):
        ret1 = 1 & minilisp.run_code_to_int('(= 3 3)')
        self.assertEqual(1, ret1)
        ret2 = 1 & minilisp.run_code_to_int('(= 3 2)')
        self.assertEqual(0, ret2)

    def testIf(self):
        self.assertEqual(4, minilisp.run_code_to_int('(if (= 1 2) 3 4)'))
        self.assertEqual(3, minilisp.run_code_to_int('(if (= 1 1) 3 4)'))
        
    def testComplexIfLet(self):
        code = '(if (= (let (x 1) x) (let (x 2) x)) (let (x 5) x) (let (x 6) x))'
        self.assertEqual(6, minilisp.run_code_to_int(code))

    def testBegin(self):
        code = '(begin (+ 3 4) (+ 7 8))'
        self.assertEqual(15, minilisp.run_code_to_int(code))

    def testSet(self):
        code = '(let (x 3) (let (y 4) (begin (set! x 5) x)))'
        self.assertEqual(5, minilisp.run_code_to_int(code))

    def testBeginAndSet(self):
        code = '(begin (set! x 3) x)'
        self.assertEqual(3, minilisp.run_code_to_int(code))

if __name__ == '__main__':
    unittest.main()

