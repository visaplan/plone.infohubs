# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Convenience wrappers for make_hubs usage

The functions in this module have been moved here to help solving import
deadlock problems.
"""
# Python compatibility:
from __future__ import absolute_import

from six.moves import map

# Local imports:
from . import make_hubs

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (1,  # initial version
           )
__version__ = '.'.join(map(str, VERSION))
__all__ = [
    'context_and_form_tuple',  # **kwargs --> (hub, info, context, form)
    'context_tuple',           # **kwargs --> (hub, info, context)
    ]


def context_and_form_tuple(hub=None, info=None, context=None, form=None,
                           amend=False):
    """
    Gib ein 4-Tupel zurück, das (falls übergeben oder <amend>) hub und info,
    jedenfalls aber context und form enthält.
    """
    if hub is None:
        if info is not None:
            raise TypeError('hub not given --> no info expected either')
        if form is None:
            if context is None:
                raise TypeError('no hub and no form: context needed!')
        if amend:
            hub, info = make_hubs(context)
    else:
        if info is None:
            raise TypeError('hub given --> info expected as well')
        if context is not None:
            raise TypeError('hub and info given; rejecting context')
        context = info['context']
    if form is None:
        if info is not None:
            form = info['request_var']
        else:
            form = context.REQUEST.form
    return (hub, info, context, form)


def context_tuple(hub=None, info=None, self=None,
                  **kwargs):
    """
    Für Funktionen bzw. insbesondere Methoden mit optionalen hub- und
    info-Argumenten: Gib ein 3-Tupel (hub, info, context) zurück.

    Verwendung:
        def mymethod(self, hub=None, info=None):
            hub, info, context = context_tuple(hub, info, self)

    hub, info -- entweder werden beide übergeben oder keins!
    self -- üblicherweise übergeben, um daraus den Kontext zu ermitteln, der
            dann im Attribut `context` erwartet wird.
            Achtung -- dieses Attribut ist vermutlich nicht garantiert!

    Stets benannt zu übergeben:

    context -- ein übergebener Kontext. Wenn hub und info übergeben wurden und
                strict True ist (Vorgabe), muß er identisch mit info['context']
                sein.

    strict -- Wenn False, wird ein übergebener Kontext auch dann akzeptiert
              (und im Ergebnistupel zurückgegeben), wenn er nicht identisch
              ist mit info['context'] aus einem übergebenen info-Dictionary;
              Vorgabe: True
    """
    context = kwargs.pop('context', None)
    if self is not None and context is not None:
        raise TypeError('Please specify *either* self *or* context'
                        ' (or hub and info)')
    strict = kwargs.pop('strict', True)
    if kwargs:
        raise TypeError('Unsupported argument(s): %s'
                        % (list(kwargs.keys()),
                           ))
    if hub is None:
        if info is not None:
            raise TypeError('hub not given --> no info expected either')
        if context is None:
            if self is None:
                raise TypeError('hub and info (and context) are None;'
                                ' self is needed!')
            context = self.context
        hub, info = make_hubs(context)
    else:
        if info is None:
            raise TypeError('hub given --> info expected as well')
        if context is not None:
            if strict:  # Vorgabe
                if context is not info['context']:
                    raise TypeError('Given context doesn\'t match the one '
                                    'from given info')
        else:
            context = info['context']
    return (hub, info, context)
