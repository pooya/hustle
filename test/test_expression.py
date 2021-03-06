import unittest
from hustle.core.marble import Column
from pyebset import BitSet


class Tablet(object):
    def __init__(self, l=()):
        self.l = BitSet()
        for i in l:
            self.l.set(i)

    def iter_all(self):
        return iter(self.l)

    def bit_eq(self, col, other):
        b = BitSet()
        for i in self.l:
            if i == other:
                b.set(i)
        return b

    def bit_ne(self, col, other):
        b = BitSet()
        for i in self.l:
            if i != other:
                b.set(i)
        return b

    def bit_lt(self, col, other):
        b = BitSet()
        for i in self.l:
            if i < other:
                b.set(i)
        return b

    def bit_gt(self, col, other):
        b = BitSet()
        for i in self.l:
            if i > other:
                b.set(i)
        return b

    def bit_ge(self, col, other):
        b = BitSet()
        for i in self.l:
            if i >= other:
                b.set(i)
        return b

    def bit_le(self, col, other):
        b = BitSet()
        for i in self.l:
            if i <= other:
                b.set(i)
        return b


class TestExpr(unittest.TestCase):
    def test_expr_without_partitions(self):
        cee_vals = Tablet([1, 5, 7, 9, 12, 13, 14, 19, 27, 38])
        cee = Column('cee', None, type_indicator=1, index_indicator=1, partition=False)

        ex = (cee < 8)
        self.assertEqual(list(ex(cee_vals)), [1, 5, 7])

        ex = (cee > 7)
        self.assertEqual(list(ex(cee_vals)), [9, 12, 13, 14, 19, 27, 38])

        ex = (cee <= 7)
        self.assertEqual(list(ex(cee_vals)), [1, 5, 7])

        ex = (cee >= 7)
        self.assertEqual(list(ex(cee_vals)), [7, 9, 12, 13, 14, 19, 27, 38])

        ex = (cee == 7)
        self.assertEqual(list(ex(cee_vals)), [7])

        ex = (cee != 7)
        self.assertEqual(list(ex(cee_vals)), [1, 5, 9, 12, 13, 14, 19, 27, 38])

        # test AND
        ex = (cee > 7) & (cee < 20)
        self.assertEqual(list(ex(cee_vals)), [9, 12, 13, 14, 19])

        ex = (cee > 7) & (cee < 20) & (cee > 13)
        self.assertEqual(list(ex(cee_vals)), [14, 19])

        # test OR
        ex = (cee < 7) | (cee > 20)
        x = sorted(ex(cee_vals))
        self.assertEqual(x, [1, 5, 27, 38])

        ex = (cee == 7) | (cee == 20) | (cee == 13)
        self.assertEqual(list(ex(cee_vals)), [7, 13])

        # test NOT
        ex = ~((cee >= 7) & (cee <= 20))
        x = sorted(ex(cee_vals))
        self.assertEqual(x, [1, 5, 27, 38])

        # test NOT
        ex = ~((cee < 7) | (cee == 19))
        x = sorted(ex(cee_vals))
        self.assertEqual(x, [7, 9, 12, 13, 14, 27, 38])

    def test_expr_with_partitions(self):
        pee = Column('pee', None, type_indicator=1, index_indicator=1, partition=True)
        pee_tags = [1, 5, 7, 9, 12, 13, 14, 19, 27, 38]
        cee = Column('cee', None, type_indicator=1, index_indicator=1, partition=False)

        p_and_p = (pee < 7)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [1, 5])

        p_and_p = (pee > 7)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [9, 12, 13, 14, 19, 27, 38])

        p_and_p = (pee == 7)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [7])

        p_and_p = (pee != 7)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [1, 5, 9, 12, 13, 14, 19, 27, 38])

        p_and_p = (pee >= 7)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [7, 9, 12, 13, 14, 19, 27, 38])

        p_and_p = (pee <= 7)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [1, 5, 7])

        p_and_p = ~(pee > 7)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [1, 5, 7])

        # test pure partition combination
        p_and_p = (pee > 5) | (pee == 1)
        self.assertEqual(sorted(p_and_p.partition(pee_tags)), [1, 7, 9, 12, 13, 14, 19, 27, 38])

        p_and_p = ~((pee <= 5) | (pee > 14))
        self.assertEqual(list(p_and_p.partition(pee_tags)), [7, 9, 12, 13, 14])

        p_and_p = (pee == 5) | (pee == 99)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [5])

        p_and_p = (pee > 5) & (pee <= 14) & (pee > 12)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [13, 14])

        p_and_p = ((pee > 5) & (pee <= 14)) | (pee == 5)
        x = sorted(p_and_p.partition(pee_tags))
        self.assertEqual(x, [5, 7, 9, 12, 13, 14])

        p_and_p = ~(~(((pee > 5) & (pee <= 14))) & (pee != 5))
        x = sorted(p_and_p.partition(pee_tags))
        self.assertEqual(x, [5, 7, 9, 12, 13, 14])

        p_and_p = ~(((pee <= 5) | (pee > 14)) & (pee != 5))
        x = sorted(p_and_p.partition(pee_tags))
        self.assertEqual(x, [5, 7, 9, 12, 13, 14])

        # test combined partition/index combinations
        # p & c == p
        p_and_p = (pee > 5) & (cee <= 14)
        self.assertEqual(list(p_and_p.partition(pee_tags)), [7, 9, 12, 13, 14, 19, 27, 38])

        # p | c == universe
        p_and_p = (pee == 5) | (pee == 8) | (cee == 99)
        x = list(p_and_p.partition(pee_tags))
        self.assertEqual(x, pee_tags)

        # p | c == universe
        p_and_p = ((pee == 5) | (pee > 14)) | (cee > 12)
        self.assertEqual(list(p_and_p.partition(pee_tags)), pee_tags)

        # c & p == p ==> p | p
        p_and_p = ((pee == 5) | (pee > 14)) | ((cee > 12) & (pee == 1))
        self.assertEqual(sorted(p_and_p.partition(pee_tags)), [1, 5, 19, 27, 38])
