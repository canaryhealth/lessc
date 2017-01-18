=======================
Python LESSCSS Compiler
=======================

The `lessc` Python package compiles content in LESS syntax into CSS by
first preprocessing it and then invoking the nodejs `lessc` program to
actually compile it. The preprocessing resolves imports which allows
the LESS content to come from anywhere, including the filesystem,
zipped EGG files, databases, etc. This solves one of the greatest
limitations of the nodejs lessc program which requires all of the LESS
dependencies to be actual files and imports to be non-absolute.

It is possible, but *quite* improbable, that this package turns into a
pure-Python implementation of a LESS compiler.

For more information on LESS, please see http://lesscss.org/.


Project
=======

* Homepage: https://github.com/canaryhealth/lessc
* Bugs: https://github.com/canaryhealth/lessc/issues


Installation
============

.. code:: bash

  $ npm install less
  $ export PATH="`pwd`/node_modules/.bin:$PATH"
  $ pip install lessc


Usage
=====

.. code:: python

  import lessc

  # compile a less asset in the "mypackage" python module:
  css = lessc.compile_asset('mypackage:path/to/style.less')

  # compile a less file on the filesystem
  css = lessc.compile_file('../path/to/style.less')

  # compile a less file-like object
  # (if there are any relative imports, specifying `base` is necessary)
  css = lessc.compile_file(open('../path/to/style.less'))

  # compile a less string
  # (if there are any relative imports, specifying `base` is necessary)

  less = '''
    @import "mypackage:path/to/style.less";
    // ...other less statements...
  '''

  css = lessc.compile(less)


For more import resolution control, you can specify a custom URI
resolver (which resolves a relative URI to an absolute URI) and a
custom URI loader (which loads an absolute URI), using the `resolver`
and `loader` keywords to any compile* function:

.. code:: python

  import lessc

  def resolver(uri, base=None):
    '''
    Returns the absolute URI given a base URI and a potentially
    absolute or relative URI. Note that `base` may be ``None`` when
    the initial URI is being resolved (depending on the Compiler
    configuration).
    '''
    # calculate the absolute URI...
    return absolute_uri

  def loader(uri):
    '''
    Returns a file-like object that will return the content of
    the specified URI.
    '''
    # fetch the object defined by `uri`
    return file_like_object

  css = lessc.compile_asset(uri, resolver=resolver, loader=loader)


Or you can create a custom compiler and set it as the default compiler:

.. code:: python

  import lessc

  compiler = lessc.Compiler(resolver=my_custom_resolver, loader=my_custom_loader)
  lessc.set_default_compiler(compiler)

  # this will now use `my_custom_resolver` and `my_custom_loader`
  # to compile asset `uri`
  css = lessc.compile_asset(uri)


Limitations
===========

Currently, there exist the following restrictions in what kind of
LESS syntax is used:

* Recursive imports are not supported and will be silently ignored.

* Only the following import keywords are explicitly supported:

  * ``less``
  * ``css``
  * ``once``
  * ``optional``

  The keywords ``reference``, ``inline``, and ``multiple`` are NOT
  supported. Any other keywords may or may not be supported (since
  only the above keywords were documented as of this writing,
  2015/06/26).
