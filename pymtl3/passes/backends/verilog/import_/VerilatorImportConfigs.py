#=========================================================================
# VerilatorImportConfigs.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jul 28, 2019
"""Configuration of Verilator import pass."""

import os
import subprocess
from textwrap import fill, indent

from pymtl3.passes.errors import InvalidPassOptionValue
from pymtl3.passes.PassConfigs import BasePassConfigs, Checker
from pymtl3.passes.PlaceholderConfigs import expand


class VerilatorImportConfigs( BasePassConfigs ):

  Options = {
    # Enable verbose mode?
    "verbose" : False,

    # Enable external line trace?
    # Once enabled, the `line_trace()` method of the imported component
    # will return a string read from the external `line_trace()` function.
    # This means your Verilog module has to have a `line_trace` function
    # that provides the line trace string which has less than 512 characters.
    # Default to False
    "vl_line_trace" : False,

    # Enable all verilator coverage
    "vl_coverage" : False,

    # Enable all verilator coverage
    "vl_line_coverage" : False,

    # Enable all verilator coverage
    "vl_toggle_coverage" : False,

    # Verilator code generation options
    # These options will be passed to verilator to generate the C simulator.
    # By default, verilator is called with `--cc`.

    # --Mdir
    # Expects the path of Makefile output directory;
    # "" to use `obj_dir_<translated_top_module>`
    "vl_mk_dir" : "",

    # --assert
    # Expects a boolean value
    "vl_enable_assert" : True,

    # Verilator optimization options

    # -O0/3
    # Expects a non-negative integer
    # Currently only support 0 (disable opt) and 3 (highest effort opt)
    "vl_opt_level" : 3,

    # --unroll-count
    # Expects a non-negative integer
    # 0 to disable this option
    "vl_unroll_count" : 1000000,

    # --unroll-stmts
    # Expects a non-negative integer
    # 0 to disable this option
    "vl_unroll_stmts" : 1000000,

    # Verilator warning-related options

    # False to disable the warnings, True to enable
    "vl_W_lint" : True,
    "vl_W_style" : True,
    "vl_W_fatal" : True,

    # Un-warn all warnings in the given list; [] to disable this option
    # The given list should only include strings that appear in `Warnings`
    "vl_Wno_list" : [ 'UNOPTFLAT', 'UNSIGNED', 'WIDTH' ],

    # Verilator misc options

    # What is the inital value of signals?
    # Should be one of ['zeros', 'ones', 'rand']
    "vl_xinit" : "zeros",

    # --trace
    # Expects a boolean value
    "vl_trace" : False,

    # The output filename of Verilator VCD tracing
    # default is {component_name}.verilator1
    "vl_trace_filename" : "",

    # Passed to verilator tracing function
    "vl_trace_timescale" : "10ps",

    # `vl_trace_cycle_time`*`vl_trace_timescale` is the cycle time of the
    # PyMTL clock that appears in the generated VCD
    # With the default options, the frequency of PyMTL clock is 1GHz
    "vl_trace_cycle_time" : 100,

    # C-compilation options
    # These options will be passed to the C compiler to create a shared lib.

    # Additional flags to be passed to the C compiler.
    # By default, CC is called with `-O0 -fPIC -shared`.
    # "" to disable this option
    "c_flags" : "",

    # Additional include search path of the C compiler.
    # [] to disable this option
    "c_include_path" : [],

    # Additional C source files passed to the C compiler.
    # [] to compile verilator generated files only.
    "c_srcs" : [],

    # `LDLIBS` will be listed after the primary target file whereas
    # `LDFLAGS` will be listed before.

    # We enforce the GNU makefile implicit rule that `LDFLAGS` should only
    # include non-library linker flags such as `-L`.
    "ld_flags" : "",

    # We enforce the GNU makefile implicit rule that `LDLIBS` should only
    # include library linker flags/names such as `-lfoo`.
    "ld_libs" : "",
  }

  Checkers = {
    ("verbose", "vl_enable_assert", "vl_line_trace", "vl_W_lint", "vl_W_style",
     "vl_W_fatal", "vl_trace", "vl_coverage", "vl_line_coverage", "vl_toggle_coverage"):
      Checker( lambda v: isinstance(v, bool), "expects a boolean" ),

    ("c_flags", "ld_flags", "ld_libs", "vl_trace_filename"):
      Checker( lambda v: isinstance(v, str),  "expects a string" ),

    ("vl_opt_level", "vl_unroll_count", "vl_unroll_stmts"):
      Checker( lambda v: isinstance(v, int) and v >= 0, "expects an integer >= 0" ),

    "vl_Wno_list": Checker( lambda v: isinstance(v, list) and all(w in VerilogPlaceholderConfigs.Warnings for w in v),
                            "expects a list of warnings" ),

    "vl_xinit": Checker( lambda v: v in ['zeros', 'ones', 'rand'],
                  "vl_xinit should be one of ['zeros', 'ones', 'rand']" ),

    "vl_trace_timescale": Checker( lambda v: isinstance(v, str) and len(v) > 2 and v[-1] == 's' and \
                                    v[-2] in ['p', 'n', 'u', 'm'] and \
                                    all(c.isdigit() for c in v[:-2]),
                                    "expects a timescale string" ),

    "vl_trace_cycle_time": Checker( lambda v: isinstance(v, int) and (v % 2) == 0,
                                    "expects an integer `n` such that `n`*`vl_trace_timescale` is the cycle time" ),

    "vl_mk_dir": Checker( lambda v: isinstance(v, str), "expects a path to directory" ),

    "c_include_path": Checker( lambda v: isinstance(v, list) and all(os.path.isdir(expand(p)) for p in v),
                                "expects a list of paths to directories" ),

    "c_srcs": Checker( lambda v: isinstance(v, list) and all(os.path.isfile(expand(p)) for p in v),
                       "expects a list of paths to files" )
  }

  Warnings = [
    'ALWCOMBORDER', 'ASSIGNIN', 'ASSIGNDLY', 'BLKANDNBLK', 'BLKSEQ',
    'BLKLOOPINIT', 'BSSPACE', 'CASEINCOMPLETE', 'CASEOVERLAP',
    'CASEX', 'CASEWITHX', 'CDCRSTLOGIC', 'CLKDATA', 'CMPCONST',
    'COLONPLUS', 'COMBDLY', 'CONTASSREG', 'DECLFILENAME', 'DEFPARAM',
    'DETECTARRAY', 'ENDLABEL', 'GENCLK', 'IFDEPTH', 'IGNOREDRETURN',
    'IMPERFECTSCH', 'IMPLICIT', 'IMPORTSTAR', 'IMPURE', 'INCABSPATH',
    'INFINITELOOP', 'INITIALDLY', 'LITENDIAN', 'MODDUP', 'MULTIDRIVEN',
    'MULTITOP', 'PINCONNECTEMPTY', 'PINMISSING', 'PINNOCONNECT',
    'PROCASSWIRE', 'REALCVT', 'REDEFMACRO', 'SELRANGE', 'STMTDLY',
    'SYMRSVDWORD', 'SYNCASYNCNET', 'TASKNSVAR', 'TICKCOUNT', 'UNDRIVEN',
    'UNOPT', 'UNOPTFLAT', 'UNOPTTHREADS', 'UNPACKED', 'UNSIGNED', 'UNUSED',
    'USERINFO', 'USERWARN', 'USERERROR', 'USERFATAL', 'VARHIDDEN', 'WIDTH',
    'WIDTHCONCAT',
  ]

  PassName = 'VerilatorImportConfigs'

  #---------------------------------------------------
  # Public APIs
  #---------------------------------------------------

  def setup_configs( s, m, m_tr_namespace ):
    # VerilatorImportConfigs alone does not have the complete information about
    # the module to be imported. For example, we need to read from the placeholder
    # configuration to figure out the pickled file name and the top module name.
    # This method is meant to be called before calling other public APIs.

    s.translated_top_module = m_tr_namespace.translated_top_module
    s.translated_source_file = m_tr_namespace.translated_filename
    s.v_include = m.config_placeholder.v_include
    # s.src_file = m.config_placeholder.src_file
    s.port_map = m.config_placeholder.port_map
    s.params = m.config_placeholder.params

    if not s.vl_mk_dir:
      s.vl_mk_dir = f'obj_dir_{s.translated_top_module}'

  def get_vl_xinit_value( s ):
    if s.vl_xinit == 'zeros':
      return 0
    elif s.vl_xinit == 'ones':
      return 1
    elif s.vl_xinit == 'rand':
      return 2
    else:
      raise InvalidPassOptionValue("vl_xinit should be one of 'zeros', 'ones', or 'rand'!")

  def get_c_wrapper_path( s ):
    return f'{s.translated_top_module}_v.cpp'

  def get_py_wrapper_path( s ):
    return f'{s.translated_top_module}_v.py'

  def get_shared_lib_path( s ):
    return f'lib{s.translated_top_module}_v.so'

  #---------------------
  # Command generation
  #---------------------

  def create_vl_cmd( s ):
    top_module  = f"--top-module {s.translated_top_module}"
    src         = s.translated_source_file
    mk_dir      = f"--Mdir {s.vl_mk_dir}"
    # flist       = "" if s.is_default("v_flist") else \
    #               f"-f {s.v_flist}"
    include     = "" if not s.v_include else \
                  " ".join("-I" + path for path in s.v_include)
    en_assert   = "--assert" if s.vl_enable_assert else ""
    opt_level   = "-O3" if s.is_default( 'vl_opt_level' ) else "-O0"
    loop_unroll = "" if s.vl_unroll_count == 0 else \
                  f"--unroll-count {s.vl_unroll_count}"
    stmt_unroll = "" if s.vl_unroll_stmts == 0 else \
                  f"--unroll-stmts {s.vl_unroll_stmts}"
    trace       = "--trace" if s.vl_trace else ""
    coverage    = "--coverage" if s.vl_coverage else ""
    line_cov    = "--coverage-line" if s.vl_line_coverage else ""
    toggle_cov  = "--coverage-toggle" if s.vl_toggle_coverage else ""
    warnings    = s._create_vl_warning_cmd()

    all_opts = [
      top_module, mk_dir, include, en_assert, opt_level, loop_unroll,
      # stmt_unroll, trace, warnings, flist, src, coverage,
      stmt_unroll, trace, warnings, src, coverage,
      line_cov, toggle_cov,
    ]

    return f"verilator --cc {' '.join(opt for opt in all_opts if opt)}"

  def create_cc_cmd( s ):
    c_flags = "-O0 -fPIC -fno-gnu-unique -shared" + \
             ("" if s.is_default("c_flags") else f" {expand(s.c_flags)}")
    c_include_path = " ".join("-I"+p for p in s._get_all_includes() if p)
    out_file = s.get_shared_lib_path()
    c_src_files = " ".join(s._get_c_src_files())
    ld_flags = expand(s.ld_flags)
    ld_libs = s.ld_libs
    coverage = "-DVM_COVERAGE" if s.vl_coverage or \
                                  s.vl_line_coverage or \
                                  s.vl_toggle_coverage else ""
    return f"g++ {c_flags} {c_include_path} {ld_flags}"\
           f" -o {out_file} {c_src_files} {ld_libs} {coverage}"

  def vprint( s, msg, nspaces = 0, use_fill = False ):
    if s.verbose:
      if use_fill:
        print(indent(fill(msg), " "*nspaces))
      else:
        print(indent(msg, " "*nspaces))

  #---------------------
  # Internal helpers
  #---------------------

  def _create_vl_warning_cmd( s ):
    lint = "" if s.is_default("vl_W_lint") else "--Wno-lint"
    style = "" if s.is_default("vl_W_style") else "--Wno-style"
    fatal = "" if s.is_default("vl_W_fatal") else "--Wno-fatal"
    wno = " ".join(f"--Wno-{w}" for w in s.vl_Wno_list)
    return " ".join(w for w in [lint, style, fatal, wno] if w)

  def _get_all_includes( s ):
    includes = s.c_include_path

    # Try to obtain verilator include path either from environment variable
    # or from `pkg-config`
    vl_include_dir = os.environ.get("PYMTL_VERILATOR_INCLUDE_DIR")
    if vl_include_dir is None:
      get_dir_cmd = ["pkg-config", "--variable=includedir", "verilator"]
      try:
        vl_include_dir = \
            subprocess.check_output(get_dir_cmd, stderr = subprocess.STDOUT).strip()
        vl_include_dir = vl_include_dir.decode('ascii')
      except OSError as e:
        vl_include_dir_msg = \
"""\
Cannot locate the include directory of verilator. Please make sure either \
$PYMTL_VERILATOR_INCLUDE_DIR is set or `pkg-config` has been configured properly!
"""
        raise OSError(fill(vl_include_dir_msg)) from e

    # Add verilator include path
    s.vl_include_dir = vl_include_dir
    includes += [vl_include_dir, vl_include_dir + "/vltstd"]

    return includes

  def _get_c_src_files( s ):
    srcs = s.c_srcs
    top_module = s.translated_top_module
    vl_mk_dir = s.vl_mk_dir
    vl_class_mk = f"{vl_mk_dir}/V{top_module}_classes.mk"

    # Add C wrapper
    srcs.append(s.get_c_wrapper_path())

    # Add files listed in class makefile
    with open(vl_class_mk) as class_mk:
      srcs += s._get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_CLASSES_FAST")
      srcs += s._get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_CLASSES_SLOW")
      srcs += s._get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_SUPPORT_FAST")
      srcs += s._get_srcs_from_vl_class_mk(
          class_mk, vl_mk_dir, "VM_SUPPORT_SLOW")
      srcs += s._get_srcs_from_vl_class_mk(
          class_mk, s.vl_include_dir, "VM_GLOBAL_FAST")
      srcs += s._get_srcs_from_vl_class_mk(
          class_mk, s.vl_include_dir, "VM_GLOBAL_SLOW")

    return srcs

  def _get_srcs_from_vl_class_mk( s, mk, path, label ):
    """Return all files under `path` directory in `label` section of `mk`."""
    srcs, found = [], False
    mk.seek(0)
    for line in mk:
      if line.startswith(label):
        found = True
      elif found:
        if line.strip() == "":
          found = False
        else:
          file_name = line.strip()[:-2]
          srcs.append( path + "/" + file_name + ".cpp" )
    return srcs
