#!/usr/bin/env python3
import fire

"""
Run With: with `python wolverine.py examples/buggy_script_2.py`
Purpose: Fix singleton code bug in Python
"""

class SingletonClass(object):
    def __new__(cls):
        cls.instance = super(SingletonClass, cls).__new__(cls)
        return cls.instance

def check_singleton_works():
    """
    check that singleton pattern is working
    """
    singleton = SingletonClass()
    new_singleton = SingletonClass()
    singleton.a = 1
    new_singleton.a = 2
    should_be_4 = (singleton.a + new_singleton.a)
    assert should_be_4 == 4

if __name__=="__main__":
    fire.Fire(check_singleton_works)

