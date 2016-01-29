Reponimous
==========

A tool for overlaying git repositories. Git submodules can sometimes be a bear to work with. For many, the workflow required is hard to grok and, moreover, doesn't really suit the needs of the project. There are a number of other tools to handle workflows like this, but these, too, did not really provide a simple interface for us to pull external sources into our artifacts.

This was originally devised for sharing `Ansible`_ playbooks, roles and libraries, but there is not reason this would not be used with other projects that just want to be able to merge source from various git repositories.

.. _`Ansible`: http://github.com/ansible/ansible

Installation
------------

.. code-block:: bash

  $ mkvirtualenv reponimous
  $ python setup.py install
  $ cp Reponimous.example Reponimous


Usage
-----

.. code-block:: bash

  $ reponimous install --path <path.to.install.directory>

or

.. code-block:: bash


  $ reponimous archive --path <path.to.archive> --name <name.of.archive>


Actions
-------

There are currently 2 actions that are supported by reponimous:

- install - creates a merged repository at the location provided by --path. All git history is preserved for pushing changes upstream.
- archive - creates a tar and gzipped merged repository at the location provided by --path. This is a shallow copy with all git history removed and is intended to be used in the creation of artifacts.
