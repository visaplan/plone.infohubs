# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79

# Python compatibility:
from __future__ import absolute_import

from six import string_types as six_string_types

__all__ = [
        'make_toolDetector',  # recognize "tools names"
        'false_by_default',
        'gimme_0',
        'gimme_1',
        'attribute_factory',
        'sorted_nonempty_item_tuples',
        ]


def make_toolDetector(**kwargs):
    """
    Return a function to recognize "tool names"

    >>> kw = {
    ...     'prefixes': ['plone_', 'portal_'],
    ...     'suffixes': ['_catalog', '_registry'],
    ...     }
    >>> a_tool = make_toolDetector(**kw)

    >>> a_tool('plone_utils')
    True
    >>> a_tool('mimetype_registry')
    True

    If nodashes=True (the default), names with dashes are considered to point
    to some other object (e.g. something contentish):

    >>> a_tool('my-silly_registry')
    False

    Some important tools we don't recognize by generic prefixes and/or
    suffixes:
    >>> a_tool('acl_users')

    We support these by providing a list of known names:
    >>> kw.update(known=['acl_users', 'my-silly_registry'])
    >>> a_tool = make_toolDetector(**kw)
    >>> a_tool('acl_users')
    True
    >>> a_tool('my-silly_registry')
    True
    """
    pop = kwargs.pop

    known_names = pop('known', None)
    if known_names is None:
        known_names = []
    elif isinstance(known_names, six_string_types):
        known_names = known_names.split()
    known_names = frozenset(known_names)

    prefixes = pop('prefixes', None)
    if prefixes is None:
        prefixes = []
    elif isinstance(prefixes, six_string_types):
        prefixes = prefixes.split()
    prefixes = tuple(prefixes)

    suffixes = pop('suffixes', None)
    if suffixes is None:
        suffixes = []
    elif isinstance(suffixes, six_string_types):
        suffixes = suffixes.split()
    suffixes = tuple(suffixes)

    nodashes = pop('nodashes', True)

    def looksLikeATool(name):
        if name in known_names:
            return True
        if nodashes and '-' in name:
            return False
        startswith = name.startswith
        for prefix in prefixes:
            if startswith(prefix):
                return True
        endswith = name.endswith
        for suffix in suffixes:
            if endswith(suffix):
                return True

    return looksLikeATool


# ------------------------------------- [ kleine Hilfsfunktionen ... [
def false_by_default():
    """
    >>> false_by_default()
    False
    """
    return False


def gimme_0():
    """
    >>> gimme_0()
    0
    """
    return 0


def gimme_1():
    """
    >>> gimme_1()
    1
    """
    return 1


def attribute_factory(o):

    # einfach o.__getattr__ zu verwenden hat nicht gereicht
    # (unabhängig von override-Funktionalität)!
    def gimme_attribute(aname, override=None):
        if override:
            return getattr(o, override)
        else:
            return getattr(o, aname)
    return gimme_attribute


def sorted_nonempty_item_tuples(dic):
    """
    Dictionaries are not hashable.
    Thus, to proxy results of functions which would expect a dict argument
    (or **kwargs), we need to transform the dict to something nearly as nice.

    >>> dic = {'uid': None, 'path': '/some/where'}
    >>> tup = sorted_nonempty_item_tuples(dic)
    >>> tup
    (('path', '/some/where'),)

    The result can be converted back to a dict (which doesn't contain the
    stripped items, though):
    >>> dict(tup)
    {'path': '/some/where'}
    """
    res = []
    for key, val in dic.items():
        if val is not None:
            res.append((key, val))
    return tuple(sorted(res))
# ------------------------------------- ] ... kleine Hilfsfunktionen ]


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
