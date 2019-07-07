# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <phil@canary.md>
# date: 2015/06/26
# copy: (C) Copyright 2015-EOT Canary Health, Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import os.path
import unittest

import six
import asset
import fso

from .compiler import Compiler, urijoin, CompileError, AssetError

#------------------------------------------------------------------------------
class TestCompiler(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_urijoin(self):
    self.assertEqual(urijoin(None, '/path/to/foo'), 'file:///path/to/foo')
    self.assertEqual(urijoin(None, 'path/to/foo'), 'file://' + os.path.abspath('path/to/foo'))
    self.assertEqual(urijoin(None, 'http://foo.com/a/b'), 'http://foo.com/a/b')
    self.assertEqual(urijoin(None, 'pkg:a/b'), 'pkg:a/b')
    self.assertEqual(urijoin('file:///a/b', '/c/d'), 'file:///c/d')
    self.assertEqual(urijoin('file:///a/b', 'c/d'), 'file:///a/c/d')
    self.assertEqual(urijoin('http://foo.com/a/b', '/c/d'), 'http://foo.com/c/d')
    self.assertEqual(urijoin('http://foo.com/a/b', 'c/d'), 'http://foo.com/a/c/d')
    self.assertEqual(urijoin('pkg:a/b', '/c/d'), 'pkg:c/d')
    self.assertEqual(urijoin('pkg:a/b', 'c/d'), 'pkg:a/c/d')
    self.assertEqual(urijoin('http://foo.com/a/b', 'file:///c/d'), 'file:///c/d')
    self.assertEqual(urijoin('file:///c/d', 'http://foo.com/a/b'), 'http://foo.com/a/b')
    self.assertEqual(urijoin('file:///c/d', 'pkg:a/b'), 'pkg:a/b')

  #----------------------------------------------------------------------------
  def test_invalid_syntax(self):
    with self.assertRaises(CompileError):
      Compiler().compile('this is not valid less.\n')

  #----------------------------------------------------------------------------
  def test_invalid_import(self):
    with self.assertRaises(AssetError):
      Compiler().compile('@import "no-such-asset";\n')

  #----------------------------------------------------------------------------
  def test_commentedOutImport_simple(self):
    with fso.push() as overlay:
      with open('black.less', 'wb') as fp:
        fp.write('.b { color: #000; }')
      with open('white.less', 'wb') as fp:
        fp.write('.w { color: #fff; }')
      self.assertEqual(
        Compiler().compile('''
          @import "black.less";
          // @import "no-such-asset";
          @import "white.less";
        '''),
        '.b{color:#000;}\n.w{color:#fff;}\n')

  #----------------------------------------------------------------------------
  def test_commentedOutImport_interleaved(self):
    with fso.push() as overlay:
      with open('black.less', 'wb') as fp:
        fp.write('.b { color: #000; }')
      with open('white.less', 'wb') as fp:
        fp.write('.w { color: #fff; }')
      self.assertEqual(
        Compiler().compile('''
          // @import "no-such-asset";
          @import "black.less";
          .r { color: #f00; } // @import "another-bad-asset"; .g { color: #0f0; }
          @import "white.less";
        '''),
        '.b{color:#000;}\n.r{color:#f00;}\n.w{color:#fff;}\n')

  #----------------------------------------------------------------------------
  def test_string(self):
    self.assertEqual(
      Compiler().compile('@color: #000; .black { color: @color; }'),
      '.black{color:#000000;}\n')

  #----------------------------------------------------------------------------
  def test_mixed_import(self):
    self.assertEqual(
      Compiler().compile('@import "lessc:res/test-03.less";'),
      asset.load('lessc:res/test-03.css').read())

  #----------------------------------------------------------------------------
  def test_asset_simple(self):
    self.assertEqual(
      Compiler().compile_asset('lessc:res/test-01.less'),
      asset.load('lessc:res/test-01.css').read())

  #----------------------------------------------------------------------------
  def test_file_relative_import(self):
    self.assertEqual(
      Compiler().compile_asset('lessc:res/test-02.less'),
      asset.load('lessc:res/test-02.css').read())

  #----------------------------------------------------------------------------
  def test_extension_defaulting(self):
    self.assertEqual(
      Compiler().compile_asset('lessc:res/test-03.less'),
      asset.load('lessc:res/test-03.css').read())

  #----------------------------------------------------------------------------
  def test_importOption_once_explicit(self):
    def resolver(uri, base=None):
      return uri
    def loader(uri):
      if uri == 'red.less':
        return six.StringIO('.red { color: red; }')
      raise NotImplementedError(uri)
    self.assertEqual(
      Compiler(resolver=resolver, loader=loader).compile('''
        @import (once) "red";
        @import (once) 'red';
      '''),
      '.red{color:red;}\n')

  #----------------------------------------------------------------------------
  def test_importOption_once_implicit(self):
    def resolver(uri, base=None):
      return uri
    def loader(uri):
      if uri == 'red.less':
        return six.StringIO('.red { color: red; }')
      raise NotImplementedError(uri)
    self.assertEqual(
      Compiler(resolver=resolver, loader=loader).compile('''
        @import "red";
        @import 'red';
      '''),
      '.red{color:red;}\n')

  #----------------------------------------------------------------------------
  def test_importOption_css_explicit(self):
    # NOTE: this is only supported by lessc >= 1.4.0
    try:
      self.assertEqual(
        Compiler().compile('@import (css) "path.ext";'),
        '@import "path.ext";\n')
    except CompileError:
      with self.assertRaises(CompileError) as cm:
        Compiler().compile('@import (css) "path.ext";')
      self.assertIn('ParseError: Syntax Error on line 1', str(cm.exception))
      raise unittest.SkipTest('lessc >= 1.4.0 required for "import (css) ..."')

  #----------------------------------------------------------------------------
  def test_importOption_css_implicit(self):
    self.assertEqual(
      Compiler().compile('@import "path.css";'),
      '@import "path.css";\n')

  #----------------------------------------------------------------------------
  def test_importOption_less(self):
    def resolver(uri, base=None):
      return uri
    def loader(uri):
      if uri == 'red.css':
        return six.StringIO('.red { color: red; }')
      raise NotImplementedError(uri)
    self.assertEqual(
      Compiler(resolver=resolver, loader=loader).compile('@import (less) "red.css";'),
      '.red{color:red;}\n')


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
