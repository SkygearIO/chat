import unittest
from ..query import Predicate

class TestPredicate(unittest.TestCase):
    def test_simple_in(self):
        p = Predicate(_id__in=["a", "b", "c"])
        self.assertListEqual(
            ["in", {"$type": "keypath", "$val": "_id"},
            ["a",  "b", "c"]]
            , p.to_dict())

    def test_simple_not(self):
        p = ~Predicate(_id__in=["a", "b", "c"])
        self.assertListEqual(['not',
            ["in", {"$type": "keypath", "$val": "_id"},
            ["a",  "b", "c"]]]
            , p.to_dict())


    def test_simple_and(self):
        p = Predicate(_id__eq="a", deleted__eq=False)
        expected = ["and", ["eq", {"$type": "keypath", "$val": "_id"}, "a"], ["eq", {"$type": "keypath", "$val": "deleted"}, False] ]
        self.assertListEqual(
            expected,
            p.to_dict()
        )
        p = Predicate(_id__eq="a")
        p = p & Predicate(deleted__eq=False)
        self.assertListEqual(expected, p.to_dict())

    def test_simple_and_three_statements(self):
        p = Predicate(time__lte="2010-07-10", time__gte="2009-01-01", deleted__ne=False)
        expected = ["and",
                   ["ne", {"$type": "keypath", "$val": "deleted"}, False],
                   ["gte", {"$type": "keypath", "$val": "time"}, "2009-01-01"],
                   ["lte", {"$type": "keypath", "$val": "time"}, "2010-07-10"]]
        self.assertListEqual(expected, p.to_dict())

    def test_simple_or(self):
        p = Predicate(_id__eq="simple", gender__eq="M", op=Predicate.OR)
        expected = ["or", ["eq", {"$type": "keypath", "$val": "_id"}, "simple"], ["eq", {"$type": "keypath", "$val": "gender"}, "M"]]
        self.assertListEqual(expected, p.to_dict())


    def test_simple_or_three_statement(self):
        p = Predicate(_id__eq="chima", gender__eq="M", type__in=["cat", "dog"] , op=Predicate.OR)
        expected = ["or", ["eq", {"$type": "keypath", "$val": "_id"}, "chima"],
                   ["eq", {"$type": "keypath", "$val": "gender"}, "M"],
                   ["in", {"$type": "keypath", "$val": "type"}, ["cat", "dog"]]]
        self.assertListEqual(expected, p.to_dict())

    def test_compound_statement_1(self):
        p = Predicate(_id__eq="chima", gender__eq="M", type__eq="dog")
        p2 = Predicate(_id__eq="fatseng", gender__eq="F", type__eq="cat")
        p3 = Predicate(_id__eq="milktea", gender__eq="NA", type__eq="frog")
        p4 = p & p2 & p3
        expected = ["and", ["eq", {"$type": "keypath", "$val": "_id"}, "chima"],
                           ["eq", {"$type": "keypath", "$val": "gender"}, "M"],
                           ["eq", {"$type": "keypath", "$val": "type"}, "dog"],
                           ["eq", {"$type": "keypath", "$val": "_id"}, "fatseng"],
                           ["eq", {"$type": "keypath", "$val": "gender"}, "F"],
                           ["eq", {"$type": "keypath", "$val": "type"}, "cat"],
                           ["eq", {"$type": "keypath", "$val": "_id"}, "milktea"],
                           ["eq", {"$type": "keypath", "$val": "gender"}, "NA"],
                           ["eq", {"$type": "keypath", "$val": "type"}, "frog"]]
        self.assertListEqual(expected, p4.to_dict())

    def test_compound_statement_2(self):
        p = Predicate(_id__eq="chima", gender__eq="M", type__eq="dog")
        p2 = Predicate(_id__eq="fatseng", gender__eq="F", type__eq="cat")
        p3 = ~Predicate(_id__eq="milktea", gender__eq="NA", type__eq="frog")
        p4 = p | p2 | p3
        expected = ["or", ["and",["eq", {"$type": "keypath", "$val": "_id"}, "chima"],
                           ["eq", {"$type": "keypath", "$val": "gender"}, "M"],
                           ["eq", {"$type": "keypath", "$val": "type"}, "dog"]],
                          ["and",["eq", {"$type": "keypath", "$val": "_id"}, "fatseng"],
                           ["eq", {"$type": "keypath", "$val": "gender"}, "F"],
                           ["eq", {"$type": "keypath", "$val": "type"}, "cat"]],
                          ["not", ["and", ["eq", {"$type": "keypath", "$val": "_id"}, "milktea"],
                           ["eq", {"$type": "keypath", "$val": "gender"}, "NA"],
                           ["eq", {"$type": "keypath", "$val": "type"}, "frog"]]]]
        self.assertListEqual(expected, p4.to_dict())

