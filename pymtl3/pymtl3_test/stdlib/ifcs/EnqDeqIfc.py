"""
========================================================================
EnqDeqIfc.py
========================================================================
RTL implementation of deq and enq interface.

Author: Yanghui Ou
  Date: Mar 21, 2019
"""
from pymtl3 import *

from .GetGiveIfc import GiveIfcFL, GiveIfcRTL
from .SendRecvIfc import RecvIfcFL, RecvIfcRTL

#-------------------------------------------------------------------------
# EnqIfcRTL
#-------------------------------------------------------------------------

class EnqIfcRTL( RecvIfcRTL ):
  pass

#-------------------------------------------------------------------------
# DeqIfcRTL
#-------------------------------------------------------------------------

class DeqIfcRTL( GiveIfcRTL ):
  pass

class EnqIfcFL( RecvIfcFL ):
  pass

class DeqIfcFL( GiveIfcFL ):
  pass
