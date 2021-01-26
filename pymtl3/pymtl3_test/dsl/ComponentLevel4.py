"""
========================================================================
ComponentLevel4.py
========================================================================
We recognize methods and method call in update blocks. At this level
we only need CalleePort that contains actual method

Author : Shunning Jiang
Date   : Dec 29, 2018
"""
from .ComponentLevel3 import ComponentLevel3
from .Connectable import CalleePort, Signal
from .ConstraintTypes import M, U


class ComponentLevel4( ComponentLevel3 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super().__new__( cls, *args, **kwargs )

    inst._dsl.M_constraints = set()

    # We don't want to get different objects everytime when we get a
    # method object from an instance. We do this by bounding the method
    # object to instance.

    # Shunning: After some profiling I found that getting dir(xxx) is
    # really slow so we would really like to avoid redundant calls to dir.
    # For example the previous code looks like this, which is REALLY bad.
    #
    # for name in dir(cls):
    #   if name in dir(ComponentLevel4)
    #
    # This means dir(ComponentLevel4) is called unnecessarily a huge
    # number of times.
    # Update: we should use cls.__dict__ to get all added methods!

    for name in cls.__dict__:
      if name[0] != '_': # filter private variables
        field = getattr( inst, name )
        if callable( field ):
          setattr( inst, name, field )

    return inst

  # Override
  def _collect_vars( s, m ):
    super()._collect_vars( m )
    if isinstance( m, ComponentLevel4 ):
      s._dsl.all_M_constraints |= m._dsl.M_constraints

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  # Override
  def add_constraints( s, *args ):
    super().add_constraints( *args )

    # add M-U, U-M, M-M constraints
    for (x0, x1, is_equal) in args:

      if   isinstance( x0, M ):
        assert isinstance( x1, (M, U) )
        s._dsl.M_constraints.add( (x0.func, x1.func, is_equal) )

      elif isinstance( x1, M ):
        assert isinstance( x0, U )
        s._dsl.M_constraints.add( (x0.func, x1.func, is_equal) )

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def _elaborate_declare_vars( s ):
    super()._elaborate_declare_vars()
    s._dsl.all_M_constraints = set()
