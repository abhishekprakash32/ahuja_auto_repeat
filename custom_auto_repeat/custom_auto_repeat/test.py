import unittest
from .doctype.test_auto_repeat.test_auto_repeat import TestAutoRepeat

def run_tests():
   suite = unittest.TestSuite()
   suite.addTest(TestAutoRepeat('test_daily_frequency'))
   suite.addTest(TestAutoRepeat('test_weekly_frequency'))
   
   runner = unittest.TextTestRunner(verbosity=2)
   runner.run(suite)