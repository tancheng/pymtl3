#=========================================================================
# DynamicSchedulePass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from pymtl3.datatypes import Bits8, Bits32, bitstruct
from pymtl3.dsl import *
from pymtl3.dsl.errors import UpblkCyclicError

from ..DynamicSchedulePass import DynamicSchedulePass
from ..GenDAGPass import GenDAGPass
from ..SimpleSchedulePass import SimpleSchedulePass
from ..SimpleTickPass import SimpleTickPass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( DynamicSchedulePass() )
  A.apply( SimpleTickPass() )
  A.lock_in_simulation()
  A.eval_combinational()

  T = 0
  while T < 5:
    A.tick()
    print(A.line_trace())
    T += 1
  return A

def test_false_cyclic_dependency():

  class Top(Component):

    def construct( s ):
      s.a = Wire(int)
      s.b = Wire(int)
      s.c = Wire(int)
      s.d = Wire(int)
      s.e = Wire(int)
      s.f = Wire(int)
      s.g = Wire(int)
      s.h = Wire(int)
      s.i = Wire(int)
      s.j = Wire(int)

      @s.update
      def up1():
        s.a = 10 + s.i
        s.b = s.d + 1

      @s.update
      def up2():
        s.c = s.a + 1
        s.e = s.d + 1

      @s.update
      def up3():
        s.d = s.c + 1
        print("up3 prints out d =", s.d)

      @s.update
      def up4():
        s.f = s.d + 1

      @s.update
      def up5():
        s.g = s.c + 1
        s.h = s.j + 1
        print("up5 prints out h =", s.h)

      @s.update
      def up6():
        s.i = s.i + 1

      @s.update
      def up7():
        s.j = s.g + 1

    def done( s ):
      return True

    def line_trace( s ):
      return "a {} | b {} | c {} | d {} | e {} | f {} | g {} | h {} | i {} | j {}" \
              .format( s.a, s.b, s.c, s.d, s.e, s.f, s.g, s.h, s.i, s.j )

  _test_model( Top )

def test_combinational_loop():

  class Top(Component):

    def construct( s ):
      s.a = Wire(int)
      s.b = Wire(int)
      s.c = Wire(int)
      s.d = Wire(int)

      @s.update
      def up1():
        s.b = s.d + 1

      @s.update
      def up2():
        s.c = s.b + 1

      @s.update
      def up3():
        s.d = s.c + 1
        print("up3 prints out d =", s.d)

    def done( s ):
      return True

    def line_trace( s ):
      return "a {} | b {} | c {} | d {}" \
              .format( s.a, s.b, s.c, s.d )

  try:
    _test_model( Top )
  except Exception as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown Exception.")

def test_very_deep_dag():

  class Inner(Component):
    def construct( s ):
      s.in_ = InPort(int)
      s.out = OutPort(int)

      @s.update
      def up():
        s.out = s.in_ + 1

    def done( s ):
      return True

    def line_trace( s ):
      return "{} > {}".format( s.a, s.b, s.c, s.d )

  class Top(Component):
    def construct( s, N=2000 ):
      s.inners = [ Inner() for i in range(N) ]
      for i in range(N-1):
        s.inners[i].out //= s.inners[i+1].in_

    def done( s ):
      return True
    def line_trace( s ):
      return ""

  _test_model( Top )

def test_sequential_break_loop():

  class Top(Component):

    def construct( s ):
      s.b = Wire( Bits32 )
      s.c = Wire( Bits32 )

      @s.update
      def up1():
        s.b = s.c + 1

      @s.update_ff
      def up2():
        if s.reset:
          s.c <<= 0
        else:
          s.c <<= s.b + 1

    def done( s ):
      return True

    def line_trace( s ):
      return "b {} | c {}" \
              .format( s.b, s.c )

  A = _test_model( Top )
  assert A.c > 5, "Is the sequential behavior actually captured?"

def test_connect_slice_int():

  class Top( Component ):
    def construct( s ):
      from pymtl3.datatypes import Bits8, Bits32
      s.y = OutPort( Bits8 )
      s.x = Wire( Bits32 )

      s.y //= s.x[0:8]
      @s.update
      def sx():
        s.x = 10 # Except

  try:
    _test_model( Top )
  except TypeError as e:
    assert str(e).startswith( "'int' object is not subscriptable" )
    return
  raise Exception("Should've thrown TypeError: 'int' object is not subscriptable")

def test_const_connect_nested_struct_signal_to_struct():

  @bitstruct
  class SomeMsg1:
    a: Bits8
    b: Bits32

  @bitstruct
  class SomeMsg2:
    a: SomeMsg1
    b: Bits32

  class Top( Component ):
    def construct( s ):
      s.out = OutPort(SomeMsg2)
      connect( s.out, SomeMsg2(SomeMsg1(1,2),3) )

  x = Top()
  x.elaborate()
  x.apply( GenDAGPass() )
  x.apply( DynamicSchedulePass() )
  x.apply( SimpleTickPass() )
  x.lock_in_simulation()
  x.tick()
  assert x.out == SomeMsg2(SomeMsg1(1,2),3)

def test_const_connect_cannot_handle_same_name_nested_struct():

  class A:
    @bitstruct
    class SomeMsg1:
      a: Bits8
      b: Bits32

  class B:
    @bitstruct
    class SomeMsg1:
      c: Bits8
      d: Bits32

  @bitstruct
  class SomeMsg2:
    a: A.SomeMsg1
    b: B.SomeMsg1

  class Top( Component ):
    def construct( s ):
      s.out = OutPort(SomeMsg2)
      connect( s.out, SomeMsg2(A.SomeMsg1(1,2),B.SomeMsg1(3,4)) )

  x = Top()
  x.elaborate()
  try:
    x.apply( GenDAGPass() )
  except AssertionError as e:
    print(e)
    assert str(e) == "Cannot handle two subfields with the same struct name but different structs"
    return
  raise Exception("Should've thrown AssertionError")
