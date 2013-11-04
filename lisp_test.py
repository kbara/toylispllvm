#!/usr/bin/env python

import unittest
import minilisp

class TestParse(unittest.TestCase):
    def testParseEmpty(self):
        assert(minilisp.parse('') == '')

    def testParseNumber(self):
        assert(minilisp.parse("3") == 3)

    def testParseExpr(self):
        assert(minilisp.parse("(+ 3 4)") == ['+', 3, 4])

    def testParseNested(self):
        assert(minilisp.parse("(+ 3 (+ 4 5))") == ['+', 3, ['+', 4, 5]])

if __name__ == '__main__':
    unittest.main()

