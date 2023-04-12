#!/usr/bin/env python3
import fire

"""
Run With: with `wolverine examples/buggy_script_2.py "return_2"`
Purpose: Fix singleton code bug in Python
"""

class SingletonClass(object):
  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(SingletonClass, cls).__new__(cls)
    return cls.instance
   
def return_2():
  """
  Always returns 2
  """
  singleton = SingletonClass()
  new_singleton = SingletonClass()
  singleton.a = 1
  new_singleton.a = 2
  return singleton.a + singleton.a  

if __name__=="__main__":
  fire.Fire()