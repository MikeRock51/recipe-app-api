'''Test Module'''

from django.test import SimpleTestCase
from app import calc

class CalcTest(SimpleTestCase):
    '''Calculator test module'''

    def test_add(self):
        '''Tests the add function'''
        res = calc.add(5, 7)

        self.assertEqual(res, 12)

    def test_subtract(self):
        '''Tests the subtract function'''
        res = calc.subtract(16, 6)

        self.assertEqual(res, 10)
