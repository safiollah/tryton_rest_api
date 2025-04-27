*************
Configuration
*************

The *Document Incoming Module* uses values from settings in the
``[document_incoming]`` section of the :ref:`trytond:topics-configuration`.

.. _config-document_incoming.filestore:

``filestore``
=============

The ``filestore`` defines if the incoming documents are stored in the
:ref:`FileStore <trytond:ref-filestore>`.

The default value is: ``True``

.. _config-document_incoming.store_prefix:

``store_prefix``
================

The ``store_prefix`` contains the prefix to use with the :ref:`FileStore
<trytond:ref-filestore>`.

The default value is: ``None``

.. _config-inboud_email.max_size:

``max_size``
============

The maximum size in bytes of the incoming document request (zero means no
limit).

The default value is: `trytond:config-request.max_size`
