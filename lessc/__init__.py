# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <phil@canary.md>
# date: 2015/06/26
# copy: (C) Copyright 2015-EOT Canary Health, Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from .compiler import Compiler

#------------------------------------------------------------------------------

_default_compiler = None

#------------------------------------------------------------------------------
def get_default_compiler():
  global _default_compiler
  if _default_compiler is None:
    _default_compiler = Compiler()
  return _default_compiler

#------------------------------------------------------------------------------
def set_default_compiler(compiler):
  global _default_compiler
  _default_compiler = compiler

#------------------------------------------------------------------------------
def get_compiler(resolver=None, loader=None):
  if resolver is None and loader is None:
    return get_default_compiler()
  return Compiler(resolver=resolver, loader=loader)

#------------------------------------------------------------------------------
def compile(target, **kw):
  return get_compiler(**kw).compile(target)

#------------------------------------------------------------------------------
def compile_file(target, **kw):
  return get_compiler(**kw).compile_file(target)

#------------------------------------------------------------------------------
def compile_asset(target, **kw):
  return get_compiler(**kw).compile_asset(target)

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
