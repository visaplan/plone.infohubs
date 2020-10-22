# -*- coding: utf-8 -*-
"""
Browser @@hubandinfo - Zugriff auf hub und info

Verwendung im Seitentemplate (tal:define):

hai hai | context/@@hubandinfo/get;
hub python:hai['hub'];
info python:hai['info'];

Achtung:
- es gibt derzeit keinerlei eingebauten Mechanismus, der dafür sorgt,
  daß das hub- und info-Objekt je Request nur einmal erzeugt wird;
  beide werden am besten weitergereicht, um in optimaler Weise von ihnen zu
  profitieren
- beide Objekte gehören zusammen; es sollten entweder beide neu erzeugt werden
  oder keins!
"""

# Python compatibility:
from __future__ import absolute_import

# Zope:
from Products.Five import BrowserView
from zope.interface import Interface, implements

# visaplan:
from visaplan.plone.infohubs import make_hubs


class IHubAndInfo(Interface):
    def get():
        """
        Erzeuge hub und info für den aktuellen Kontext und gib ein dict zurück
        """


class Browser(BrowserView):

    implements(IHubAndInfo)

    def get(self):
        """
        Erzeuge hub und info für den aktuellen Kontext und gib ein dict zurück
        """
        hub, info = make_hubs(self.context)
        return {'hub': hub,
                'info': info,
                }


# vim: ts=8 sts=4 sw=4 si et hls
