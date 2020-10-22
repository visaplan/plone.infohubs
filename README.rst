.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

.. image::
   https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
       :target: https://pycqa.github.io/isort/

=======================
visaplan.plone.infohubs
=======================

This product establishes a "mini language" for the calculation and re-use of
information in Plone_ instances during the processing of a single request,
e.g. when creating breadcrumbs; e.g., if the login state is important for the
breadcrumb for ``/foo``, that same state might be important for the
``/foo/bar`` breadcrumb as well.

It is part of the footing of the "Unitracc family" of Plone sites
which are maintained by `visaplan GmbH`_, Bochum, Germany; the mini-language
was established during the development of the now factored-out package
``visaplan.plone.breadcrumbs``.

The purpose of this package (for now) is *not* to provide new functionality
but to factor out existing functionality from our former monolithic Zope product.
Thus, it is more likely to lose functionality during further development
(as parts of it will be forked out into their own packages,
or some functionality may even become obsolete because there are better
alternatives in standard Plone components).


Features
--------

- The ``info`` dictionary holds the collected information of interest
  during processing of the request.
- The ``hub`` dictionary holds the tools which were used to get those
  information chunks.

  For some named tools, there are abbreviations available (e.g. ``pc`` for
  ``portal_catalog``), mostly for historical reasons.


Examples
--------

This add-on can be seen in action at the following sites:

- https://www.unitracc.de
- https://www.unitracc.com


Installation and usage
----------------------

Add ``visaplan.plone.infohubs`` to the requirements of your add-on.

Then, in your own code::

    from visaplan.plone.infohubs import make_hubs
    ...
        # in some function or method where you have a meaningful context:
        hub, info = make_hubs(self.context)
        someval = info['some_known_key']

While getting the information for the given key ``some_known_key``,
the used tools will be stored in the ``hub`` dictionary,
and other information found on the way will be stored in the ``info``
dictionary.


Contribute
----------

- Issue Tracker: https://github.com/visaplan/plone.infohubs/issues
- Source Code: https://github.com/visaplan/plone.infohubs


Support
-------

If you are having issues, please let us know;
please use the `issue tracker`_ mentioned above.


License
-------

The project is licensed under the GPLv2.

.. _`issue tracker`: https://github.com/visaplan/plone.infohubs/issues
.. _Plone: https://plone.org/
.. _`visaplan GmbH`: http://visaplan.com

.. vim: tw=79 cc=+1 sw=4 sts=4 si et
