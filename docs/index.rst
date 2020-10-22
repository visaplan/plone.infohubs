=======================
visaplan.plone.infohubs
=======================

This product establishes a "mini language" for the calculation and re-use of
information from Plone instances during the processing of a single request,
e.g. when creating breadcrumbs; e.g., if the login state is important for the
breadcrumb for ``/foo``, that same state might be important for the
``/foo/bar`` breadcrumb as well.


The normal usage in Python code will look like so::

    from visaplan.plone.infohubs import make_hubs
    ...
    def some_method(self, ...):
        ...
        hub, info = make_hubs(context)
        val = info['some_magic_key']

    That "magic key" is the name of some often interesting information which is
    known to this product;  it will be calculated in a way that stores any
    intermediate result for further use.

    Both ``hub`` and ``info`` are Python dictionaries; it is possible to put
    some information there non-automagically as well.  In this case, of course,
    you should now what you are doing. Automagically populated keys of the
    ``info`` dict won't ever start with an underscore, so you should be safe if
    you add your own ``_my.product`` subdirectory.
