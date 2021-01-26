#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 27, 2019
"""Provide helper methods that might be useful to verilog passes."""

import os
import shutil
import textwrap
from collections import deque
from hashlib import blake2b

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir import get_component_ifc_rtlir
from pymtl3.passes.rtlir.util.utility import get_component_full_name


def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '
  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

def get_component_unique_name( c_rtype ):
  full_name = get_component_full_name( c_rtype )

  if len( full_name ) < 64:
    return full_name

  comp_name = c_rtype.get_name()
  param_hash = blake2b(digest_size = 8)
  param_hash.update(full_name[len(comp_name):].encode('ascii'))
  param_name = param_hash.hexdigest()
  return comp_name + "__" + param_name

  def get_string( obj ):
    """Return the string that identifies `obj`"""
    if isinstance(obj, type): return obj.__name__
    return str( obj )

def wrap( s ):
  col = shutil.get_terminal_size().columns
  return "\n".join(sum((textwrap.wrap(line, col) for line in s.split("\n")), []))

def expand( v ):
  return os.path.expanduser(os.path.expandvars(v))

def pretty_concat( *strings ):
  return ' '.join([s for s in strings if s])

def get_dir( cur_file ):
  return os.path.dirname(os.path.abspath(cur_file))+os.path.sep

def get_file_hash( file_path ):
  with open(file_path) as fd:
    hash_inst = blake2b()
    string = ''.join( fd.readlines() ).encode( 'ascii' )
    hash_inst.update(string)
    return hash_inst.hexdigest()

verilog_keyword = [
  # Verilog-1995 reserved keywords
  "always", "and", "assign", "begin", "buf", "bufif0", "bufif1", "case",
  "casex", "casez", "cmos", "deassign", "default", "defparam", "disable",
  "edge", "else", "end", "endcase", "endmodule", "endfunction", "endprimitive",
  "endspecify", "endtable", "endtask", "event", "for", "force", "forever",
  "fork", "function", "highz0", "highz1", "if", "ifnone", "initial",
  "inout", "input", "output", "integer", "join", "large", "macromodule",
  "medium", "module", "nand", "negedge", "nmos", "nor", "not", "notif0",
  "notif1", "or", "output", "parameter", "pmos", "posedge", "primitive",
  "pull0", "pull1", "pullup", "pulldown", "rcmos", "real", "realtime",
  "reg", "release", "repeat", "rnmos", "rpmos", "rtran", "rtranif0",
  "rtranif1", "scalared", "small", "specify", "specparam", "strong0",
  "strong1", "supply0", "supply1", "table", "task", "time", "tran",
  "tranif0", "tranif1", "tri", "tri0", "tri1", "triand", "trior",
  "trireg", "vectored", "wait", "wand", "weak0", "weak1", "while",
  "wire", "wor", "xnor", "xor",
  # Verilog-2001 reserved keywords
  "automatic", "cell", "config", "design", "endconfig", "endgenerate",
  "generate", "genvar", "incdir", "include", "instance", "liblist",
  "library", "localparam", "noshowcancelled", "pulsestyle_onevent",
  "pulsestyle_ondetect", "showcancelled", "signed", "unsigned", "use",
  # Verilog-2005 reserved keywords
  "uwire",
  # SystemVerilog-2005 reserved keywords
  "alias", "always_comb", "always_ff", "always_latch", "assert", "assume",
  "before", "bind", "bins", "binsof", "bit", "break", "byte", "chandle",
  "class", "clocking", "const", "constraint", "context", "continue",
  "cover", "covergroup", "coverpoint", "cross", "dist", "do", "endclass",
  "endclocking", "endgroup", "endinterface", "endpackage", "endprimitive",
  "endprogram", "endproperty", "endsequence", "enum", "expect", "export",
  "extends", "extern", "final", "first_match", "foreach", "forkjoin",
  "iff", "ignore_bins", "illegal_bins", "import", "inside", "int", "interface",
  "intersect", "join_any", "join_none", "local", "logic", "longint", "matches",
  "modport", "new", "null", "package", "packed", "priority", "program",
  "property", "protected", "pure", "rand", "randc", "randcase", "randsequence",
  "ref", "return", "sequence", "shortint", "shortreal", "solve", "static",
  "string", "struct", "super", "tagged", "this", "throughout", "timeprecision",
  "timeunit", "type", "typedef", "union", "unique", "var", "virtual", "void",
  "wait_order", "wildcard", "with", "within"
]

verilog_reserved = set( verilog_keyword )

#-----------------------------------------------------------------------
# get_rtype
#-----------------------------------------------------------------------

def get_rtype( _rtype ):
  if isinstance( _rtype, rt.Array ):
    n_dim = _rtype.get_dim_sizes()
    rtype = _rtype.get_sub_type()
  else:
    n_dim = []
    rtype = _rtype
  return n_dim, rtype

#-----------------------------------------------------------------------
# gen_mapped_ports
#-----------------------------------------------------------------------

def gen_mapped_ports( m, port_map, has_clk=True, has_reset=True ):
  """Return a list of (pname, vname, rt.Port/rt.Array ) that has all ports
  of `rtype`. This method performs SystemVerilog backend-specific name
  mangling and returns all ports that appear in the interface of component
  `rtype`. Each tuple contains a port or an array of port that has any data type
  allowed in RTLIRDataType.
  Shunning: Now we also take port_map into account. Two points to note:
  1. If a port's pname appears as a key in port_map, we need to use the
     corresponding value as vname
  2. For an n-D array of ports, we enforce the rule that assumes either no
     element is mapped in port_map, or _all_ of the elements are mapped.
  """

  def _mangle_port( pname, vname, port, n_dim ):

    # Normal port
    if not n_dim:
      return [ ( [pname], port_map[pname] if pname in port_map else vname, port ) ]

    # Handle port array. We just assume if one element of the port array
    # is mapped, we need the user to map every element in the array.
    found = tot = 0
    all_ports = []
    Q = deque( [ (pname, vname, port, n_dim ) ] )
    while Q:
      _pname, _vname, _port, _n_dim = Q.popleft()
      if not _n_dim:
        if _pname in port_map:
          found += 1
          _vname = port_map[_pname]
        all_ports.append( ( [_pname], _vname, _port ) )
      else:
        for i in range( _n_dim[0] ):
          Q.append( (f"{_pname}[{i}]", f"{_vname}__{i}", _port, _n_dim[1:]) )

    assert found == len(all_ports) or found == 0, \
        f"{pname} is an {len(n_dim)}-D array of ports with {len(all_ports)} ports in total, " \
        f" but only {found} of them is mapped. Please either map all of them or none of them."

    if not found:
      return [ ( [pname], vname, rt.Array( n_dim, port ) ) ]
    else:
      return all_ports

  def _is_ifc_mapped( pname, vname, rtype, n_dim ):
    found, tot, flatten_ports = 0, 0, []
    # pname, vname, rtype, n_dim
    Q = deque( [ (pname, vname, rtype, n_dim) ] )

    while Q:
      _pname, _vname, _rtype, _n_dim = Q.popleft()
      if _n_dim:
        for i in range(_n_dim[0]):
          Q.append((f"{_pname}[{i}]", f"{_vname}__{i}", _rtype, _n_dim[1:]))
      else:
        if isinstance( _rtype, rt.Port ):
          # Port inside the interface
          tot += 1
          if _pname in port_map:
            found += 1
            flatten_ports.append(([_pname], port_map[_pname], _rtype))
          else:
            flatten_ports.append(([_pname], _vname, _rtype))
        elif isinstance( _rtype, rt.InterfaceView ):
          # Interface (nested)
          for sub_name, sub_rtype in _rtype.get_all_properties_packed():
            sub_n_dim, sub_rtype = get_rtype( sub_rtype )
            Q.append((f"{_pname}.{sub_name}", f"{_vname}__{sub_name}", sub_rtype, sub_n_dim))
        else:
          assert False, f"{_pname} is not interface(s) or port(s)!"

    assert (found == 0) or (found == tot), \
        f"{name} is an interface that has {tot} ports in total, " \
        f" but only {found} of them is mapped. Please either map all of them or none of them."
    return (found == tot), flatten_ports

  def _gen_packed_ifc( pname, vname, ifc, n_dim ):
    packed_ifc, ret = [], []
    Q = deque( [ (pname, vname, ifc, n_dim, []) ] )
    while Q:
      _pname, _vname, _rtype, _n_dim, _prev_n_dim = Q.popleft()

      if isinstance( _rtype, rt.Port ):
        if not (_prev_n_dim + _n_dim):
          new_rtype = _rtype
        else:
          new_rtype = rt.Array(_prev_n_dim+_n_dim, _rtype)
        packed_ifc.append((_pname, _vname, new_rtype))

      elif isinstance( _rtype, rt.InterfaceView ):
        if _n_dim:
          new_prev_n_dim = _prev_n_dim + [_n_dim[0]]
          for i in range(_n_dim[0]):
            Q.append((f"{_pname}[{i}]", _vname, _rtype, _n_dim[1:], new_prev_n_dim))
        else:
          new_prev_n_dim = _prev_n_dim
          for sub_name, sub_rtype in _rtype.get_all_properties_packed():
            sub_n_dim, sub_rtype = get_rtype( sub_rtype )
            Q.append((f"{_pname}.{sub_name}", f"{_vname}__{sub_name}",
                      sub_rtype, sub_n_dim, new_prev_n_dim))
      else:
        assert False, f"{_pname} is not interface(s) or port(s)!"

    # Merge entries whose vnames are the same. The result will have a list for
    # the pnames.
    names = set()
    for _, vname, rtype in packed_ifc:
      if vname not in names:
        names.add( vname )
        ret.append(([], vname, rtype))
        for _pname, _vname, _ in packed_ifc:
          if vname == _vname:
            ret[-1][0].append(_pname)

    return ret

  def _mangle_ifc( pname, vname, ifc, n_dim ):
    is_mapped, flatten_ifc = _is_ifc_mapped( pname, vname, ifc, n_dim )
    if is_mapped:
      return flatten_ifc
    else:
      return _gen_packed_ifc( pname, vname, ifc, n_dim )

  # We start from all packed ports/interfaces, and unpack arrays if
  # it is found in a port.
  rtype = get_component_ifc_rtlir(m)
  ret = []

  for name, port in rtype.get_ports_packed():
    if not has_clk and name == 'clk':      continue
    if not has_reset and name == 'reset':  continue
    p_n_dim, p_rtype = get_rtype( port )
    ret += _mangle_port( name, name, p_rtype, p_n_dim )

  for name, ifc in rtype.get_ifc_views_packed():
    i_n_dim, i_rtype = get_rtype( ifc )
    ret += _mangle_ifc( name, name, i_rtype, i_n_dim )

  return ret
