# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <phil@canary.md>
# date: 2015/06/26
# copy: (C) Copyright 2015-EOT Canary Health, Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import os
import os.path
import re
import subprocess

import six
from six.moves.urllib import parse as urlparse
import asset

#------------------------------------------------------------------------------

assetspec_cre = re.compile(r'^[a-z_][a-z0-9_]*:[^/]', re.IGNORECASE)
import_cre    = re.compile(
  r'@import\s*(?:\((?P<options>[^)]*)\))?\s*(?P<qchar>["\'])(?P<uri>.*?)(?P=qchar)\s*;')

utilprintwarning_cre = re.compile(
  r'\(node:\d+\) DeprecationWarning: util.print is deprecated. Use console.log instead.')

class LesscError(Exception): pass
class AssetError(LesscError):
  def __init__(self, cause=None, *args, **kw):
    super(AssetError, self).__init__(*args, **kw)
    self.cause = cause
class CompileError(LesscError): pass
class UnsupportedError(LesscError): pass

#------------------------------------------------------------------------------
def urijoin(base, uri):
  # todo: ugh. this is trying way too hard... perhaps abandon support
  #       for asset-specs?...
  if uri.startswith('/'):
    if base is None or base.startswith('file:///'):
      return 'file://' + uri
    if not uri.startswith('//') and assetspec_cre.match(base):
      return base.split(':', 1)[0] + ':' + uri[1:]
    return urlparse.urljoin(base, uri)
  if uri.startswith('file:///'):
    return uri
  if assetspec_cre.match(uri):
    return uri
  if base is None:
    if urlparse.urlparse(uri).scheme:
      return uri
    return 'file://' + os.path.abspath(uri)
  if not assetspec_cre.match(base):
    return urlparse.urljoin(base, uri)
  parts = base.split(':', 1)
  return parts[0] + ':' + urlparse.urljoin(parts[1], uri)

#------------------------------------------------------------------------------
def resolver(uri, base=None):
  return urijoin(base, uri)

#------------------------------------------------------------------------------
def loader(uri):
  if uri.startswith('file://'):
    # todo: what about closing this file descriptor?... let the gc do it?
    return open(uri[len('file://') : ], 'rb')
  if assetspec_cre.match(uri):
    return asset.load(uri).peek()
  raise UnsupportedError('no asset loader for URI %r' % (uri,))

#------------------------------------------------------------------------------
class Compiler(object):

  lessc_exec = 'lessc'

  #----------------------------------------------------------------------------
  def __init__(self, base_uri=None, resolver=resolver, loader=loader, *args, **kw):
    super(Compiler, self).__init__(*args, **kw)
    self.base_uri = base_uri
    self.resolver = resolver
    self.loader   = loader

  #----------------------------------------------------------------------------
  def compile_asset(self, spec):
    return self._compile(spec, asset.load(spec))

  #----------------------------------------------------------------------------
  def compile_file(self, filename):
    filename = os.path.abspath(filename)
    return self._compile('file://' + filename, open(filename, 'rb'))

  #----------------------------------------------------------------------------
  def compile_uri(self, uri):
    uri = self.resolver(uri, base=self.base_uri)
    return self._compile(uri, self.loader(uri))

  #----------------------------------------------------------------------------
  def compile(self, target):
    '''
    Compiles `target` from LESS to CSS. `target` can be one of the following:

    * A unicode string object containing the less content.

    * A binary data object containing the encoded less content (an
      attempt will be made to decode this into a unicode string).

    * A file-like object that will return the less content when read.
    '''
    if isinstance(target, six.binary_type):
      try:
        target = target.decode()
      except UnicodeDecodeError:
        try:
          target = target.decode('utf-8')
        except UnicodeDecodeError:
          raise ValueError('binary input could not be converted to unicode')
    if isinstance(target, six.string_types):
      return self._compile(None, six.StringIO(target))
    return self._compile(None, target)

  #----------------------------------------------------------------------------
  def _compile(self, uri, source):
    output = six.StringIO()
    self._preprocess(uri, source, output, dict())
    output = output.getvalue().encode('utf-8')
    output = self._less2css(output)
    return output

  #----------------------------------------------------------------------------
  def _less2css(self, data):
    proc = subprocess.Popen(
      [os.environ.get('LESSC', self.lessc_exec), '-x', '-'],
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = proc.communicate(data)
    if err and utilprintwarning_cre.match(err.strip()):
      err = None
    if err:
      raise CompileError(err)
    return output

  #----------------------------------------------------------------------------
  def _preprocess(self, uri, source, output, state):
    if 'imported' not in state:
      state['imported'] = []
    data = source.read()
    def replacer(match):
      # TODO: *** hack alert *** this is embarrassing... this should
      #       not be here. it *should* be done wherever the data
      #       stream is actually being parsed. but currently, that is
      #       in the external `lessc` node program. ugh. and this is
      #       such a simplistic, error-prone implementation. i'm so
      #       sorry. for example, it would incorrectly handle::
      #          .f { background: url("https://foo"); } @import "bar";
      #       fortunately, i expect that to be rare.
      #       unless the source is already css-minified.
      #       don't do that.
      befline = match.string[ : match.start() ].rsplit('\n', 1)[-1]
      if '//' in befline:
        return ''
      options = match.group('options') or 'once'
      options = [i.strip().lower() for i in options.split(',')]
      for opt in options:
        if opt in ('reference', 'inline', 'multiple'):
          raise UnsupportedError(
            'import option %r is not supported in python lessc' % (opt,))
      suburi = match.group('uri')
      if not os.path.splitext(suburi)[1]:
        suburi += '.less'
      if 'css' in options or ( suburi.endswith('.css') and 'less' not in options ):
        return match.string[match.start() : match.end()]
      suburi = self.resolver(suburi, base=uri)
      if suburi in state['imported']:
        return ''
      state['imported'].append(suburi)
      try:
        subsrc = self.loader(suburi)
      except (IOError, asset.NoSuchAsset) as exc:
        if 'optional' in options:
          return ''
        raise AssetError(cause=exc)
      subout = six.StringIO()
      self._preprocess(suburi, subsrc, subout, state)
      return subout.getvalue()
    data = import_cre.sub(replacer, data)
    output.write(data)


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
