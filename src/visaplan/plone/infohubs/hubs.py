# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Unterstützung zum Sammeln von kontextbezogenen Informationen

Verwendung:
    hub, info = make_hubs(self.context)
"""

# Python compatibility:
from __future__ import absolute_import, print_function

from six import string_types as six_string_types
from six.moves import map
from six.moves._thread import get_ident

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (1,  # initial version
           5,  # info['uid2path']
           )
__version__ = '.'.join(map(str, VERSION))
__all__ = [
    'make_hubs',               # context  --> (hub, info)
    # moved to .hubs2:
    # 'context_and_form_tuple',  **kwargs --> (hub, info, context, form)
    # 'context_tuple',           **kwargs --> (hub, info, context)
    ]

# Setup tools:
import pkg_resources

# Standard library:
from collections import Counter, defaultdict
from time import strftime

# Zope:
from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName
from zope.component import getAdapter as getComponentAdapter

# Plone:
from plone.uuid.interfaces import IUUID

# visaplan:
from visaplan.tools.classes import (
    PrefixingMap,
    Proxy,
    UniqueStack,
    WriteProtected,
    make_width_getter,
    )
from visaplan.tools.minifuncs import gimme_False, makeBool

# Local imports:
from .utils import (
    attribute_factory,
    false_by_default,
    gimme_0,
    gimme_1,
    make_toolDetector,
    sorted_nonempty_item_tuples,
    )

# Logging / Debugging:
from pdb import set_trace
from visaplan.tools.debug import pp

try:
    # Zope:
    from zope.component.hooks import getSite
except ImportError:  # zope.app.component ist veraltet ...
    # Zope:
    from zope.app.component.hooks import getSite

try:
    # Zope:
    from Globals import DevelopmentMode
except ImportError:
    # Hotfix for Zope 4; how to properly replace this?
    DevelopmentMode = False

try:
    pkg_resources.get_distribution('visaplan.plone.tools')
except pkg_resources.DistributionNotFound:
    HAS_VISAPLAN_TOOLS = False
else:
    HAS_VISAPLAN_TOOLS = True
    # Logging / Debugging:
    from visaplan.plone.tools.log import getLogSupport
    logger, debug_active, DEBUG = getLogSupport()
    logger.info('We have visaplan.plone.tools!')
    # visaplan:
    from visaplan.plone.tools.context import (
        get_published_templateid,
        getMessenger,
        make_brainGetter,
        make_pathByUIDGetter,
        make_timeformatter,
        make_translator,
        parent_brains,
        parents,
        )

try:
    pkg_resources.get_distribution('visaplan.zope.reldb')
except pkg_resources.DistributionNotFound:
    HAS_VISAPLAN_RELDB = False
    try:
        pkg_resources.get_distribution('visaplan.plone.sqlwrapper')
    except pkg_resources.DistributionNotFound:
        HAS_VISAPLAN_SQLWRAPPER = False
    else:
        HAS_VISAPLAN_SQLWRAPPER = True
        # visaplan:
        from visaplan.plone.sqlwrapper import SQLWrapper

else:
    HAS_VISAPLAN_RELDB = True
    HAS_VISAPLAN_SQLWRAPPER = False
    # visaplan:
    from visaplan.zope.reldb.legacy import SQLWrapper


# ------------------------------------------------------ [ Daten ... [
TIMESTAMP_FN = '%Y-%m-%d_%H%M%S'  # Timestamp-Format für Dateinamen
SESSIONKEY_DESKTOPGROUPS = 'unitracc_desktop_groups'
# ------------------------------------------------------ ] ... Daten ]


# --------------------------------------- [ Tools- und Info-Hubs ... [
NAMED_ADAPTERS = {
    # abbreviations for getToolByName:
    'acl':      'acl_users',
    'ctr':      'content_type_registry',
    'mr':       'mimetype_registry',
    'pa':       'portal_actions',
    'pc':       'portal_catalog',
    'pg':       'portal_groups',
    'pl':       'portal_languages',
    'pm':       'portal_membership',
    'pr':       'portal_registration',
    'pt':       'portal_types',
    'ptr':      'portal_transforms',
    'puc':      'portal_user_catalog',
    'pu':       'plone_utils',
    'pw':       'portal_workflow',
    'rc':       'reference_catalog',
    }
looksLikeATool = make_toolDetector(known=NAMED_ADAPTERS.values(),
                                   prefixes=['plone_', 'portal_'],
                                   suffixes=['_catalog', '_registry', '_tool'],
                                   nodashes=True)
if HAS_VISAPLAN_TOOLS:
    NAMED_ADAPTERS.update({
        'getbrain':         make_brainGetter,
        'message':          getMessenger,
        'totime':           make_timeformatter,
        'translate':        make_translator,
        'uid2path':         make_pathByUIDGetter,      # see as well info['uid2path']
        # the following 'hub' keys will contain data:
        'templateid':       get_published_templateid,  # see as well info['view_template_id']
        'parents':          parents,                   # context.REQUEST['PARENTS']
        'aqparents':        parent_brains,             # from catalog

        # (tool, method) tuples; will perhaps be removed:
        'portal':           ('portal_url', 'getPortalObject'),
        # no substitutes yet:
        'renderzpt':        None,
        'securitymanager':  None,
        'uid2url':          None,
        'rawbyname':        None,
        })

if HAS_VISAPLAN_RELDB or HAS_VISAPLAN_SQLWRAPPER:
    NAMED_ADAPTERS.update({
        'sqlwrapper':       SQLWrapper,
        })


def get_tool(context, name):
    return getToolByName(context, name)


def getAdapter(context, name):
    return getComponentAdapter(context, name=name)


def getBrowser(context, name):
    return context.restrictedTraverse('@@' + name, None)


def getView(context, name):
    return context.restrictedTraverse(name)


def make_hubs(context, debug=False):
    """
    Erzeuge die beiden (speziellen) dict-Objekte 'hub' und 'info',
    die bestimmte Informationen puffern, die für den aktuellen Kontext nur
    einmal ermittelt werden müssen.

    Diese beiden dict-Objekte werden bei Verwendung nur gelesen;
    die jeweiligen Werte werden bei Bedarf automatisch ermittelt.

    Der Nutzen ist vielfältig:
    - Der Code wird kompakter, weil nicht ständig durch context.getAdapter
      etc. aufgebläht
    - Optimierungen können zentral erfolgen, z. B. Ablösung von Adaptern,
      die lediglich getToolByName-Aufrufe verpacken
    - einmal ermittelte Informationen können zur weiteren Verwendung im
      selben Request weitergereicht werden
    """

    class ToolsHub(dict):
        """
        Ein dict, das Browser, Adapter, "Tools" und Views vorhält.
        Der Kontext wird beim Aufruf von make_hubs übergeben.

        Es gibt keine unterschiedlichen Namensräume für Browser, Adapter und
        Views; soweit es diese Klasse betrifft, reichen folgende Regeln:

        1. Adapter werden als selten angenommen und sind namentlich
           aufgeführt.
        2. Methoden sind noch seltener; sie sind Attribute eines der Fälle 1
           oder 5. Abweichende Methodennamen können definiert werden.
        3. Endet die Bezeichnung auf 'view', oder enthält sie Bindestriche,
           handelt es sich um eine View.
        4. Beginnt die Bezeichnung mit 'portal_', ist es ein "Tool",
           zu beschaffen mit getToolByName.
        5. Was übrigbleibt, muß ein Browser sein.
        """

        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                if debug:
                    print('*** key=%(key)r:' % locals())
                    set_trace()
                contextonly = 0
                if key in NAMED_ADAPTERS:
                    val = NAMED_ADAPTERS[key]
                    if val is None:
                        method = getAdapter
                    elif isinstance(val, six_string_types):
                        method = get_tool
                    elif isinstance(val, tuple):
                        raise ValueError('hub[%(key)r]: tuple values %(val)s'
                                         ' not (yet?) supported'
                                         % locals())
                    else:
                        method = val
                        contextonly = True
                elif key.endswith('view') or '-' in key:
                    method = getView
                elif looksLikeATool(key):
                    method = get_tool
                else:
                    method = getBrowser

                args = [context]
                if not contextonly:
                    args.append(key)
                val = method(*args)

                dict.__setitem__(self, key, val)
                return dict.__getitem__(self, key)

    hub = ToolsHub(context)

    def get_uid():
        return IUUID(context, None)

    def get_structure_number():
        if info['isBook']:
            structurenumber = hub['structurenumber']
            if structurenumber is not None:
                my_uid = info['my_uid']
                return structurenumber.get(my_uid)
            return 0
        else:
            return None

    def detect_book():
        book = hub['book']
        if book is None:
            return None
        return bool(book.isBook(info['context_as_brain']))

    def detect_presentation():
        p = hub['presentation']
        if p is None:
            return None
        # gibt stets einen bool-Wert zurück:
        return p.isPresentation(info['my_uid'])

    def detect_structual():
        structuretype = hub['structuretype']
        if structuretype is None:
            return None
        return bool(structuretype.getStructureFolderAsBrain(
                                            info['context_as_brain']))

    def detect_bracket_default():
        # visaplan:
        from visaplan.plone.unitracctool.unitraccfeature.browser import (
            FEATURESINFO,
            )
        return FEATURESINFO['bracket_default']

    def get_audit_mode():
        return makeBool(info['request_var'].get('audit-mode', 'true'))

    def get_request():
        return context.REQUEST

    def get_response():
        return info['request'].RESPONSE

    # für Breadcrumbs:
    def get_form():
        return info['request'].form

    def detect_logged_in():
        pm = hub['portal_membership']
        return not pm.isAnonymousUser()

    def detect_user_object():
        # Das User-Objekt des angemeldeten Users, oder None
        pm = hub['portal_membership']
        if pm.isAnonymousUser():
            return None
        return pm.getAuthenticatedMember()

    def detect_author_object():
        loggedin_id = info['user_id']
        if loggedin_id is not None:
            return hub['author'].getByUserId(loggedin_id)

    def detect_user_id():
        o = info['user_object']
        if o is not None:
            return o.getId()
        return None

    def detect_user_email():
        o = info['author_object']
        if o is not None:
            return o.getEmail()
        return None

    def detect_cooperating_groups():
        # Zusammenarbeitende Gruppen am Unitracc-Objekt im Kontext
        if info['portal_type'] == 'Folder':
            return []
        try:
            return context.getUnitraccGroups() or []
        except Exception as e:
            pp([('context:', context),
                ('info:', 'cooperating_groups'),
                ('error:', e),
                ])
            return []

    def detect_group_id():
        # gid: für Schreibtischfunktionalität verwendet
        # Es wird die "effektive" Gruppen-ID zurückgegeben, die ggf. den
        # Sitzungsdaten entnommen wird
        groups_raw = info['session'][SESSIONKEY_DESKTOPGROUPS]
        groups_stack = UniqueStack(groups_raw or [])
        try:
            gid = info['request_var']['gid']
        except KeyError:
            # gid nicht angegeben --> Sitzungsdaten befragen
            coop_groups = list(info['cooperating_groups'])
            if info['portal_type'] == 'Folder':
                try:
                    return coop_groups.pop()
                except IndexError:
                    # noch keine Gruppenangabe gespeichert:
                    return None
            # Objekte mit potentieller Zusammenarbeit:
            for gid in reversed(groups_stack):
                if gid is None or gid == 'None':
                    return None  # PEP 20.2
                if gid in coop_groups:
                    if info['is_member_of'](gid):
                        return gid
                    try:
                        coop_groups.remove(gid)
                    except ValueError:
                        pass
            # Hier den persönlichen Schreibtisch präferieren
            if info['is_mine']:
                return None
            # unverbrauchte Gruppen aus der Zusammenarbeit:
            for gid in coop_groups:
                if info['is_member_of'](gid):
                    return gid
            # kann eigentlich nicht sein; das Objekt dürfte nicht zugänglich
            # sein!
            return 'ERROR'
        else:
            # gid wurde angegeben --> in die Sitzungsdaten schreiben
            if gid == 'None' or not gid:
                gid = None
            groups_stack.append(gid)
            if groups_stack != groups_raw:
                info['session'][SESSIONKEY_DESKTOPGROUPS] = groups_stack
            return gid

    def managed_group_id():
        # group_id: im Management-Interface verwendet.
        # Die Abweichung ist nützlich bei der Generierung von Breadcrumbs!
        gid = info['request_var'].get('group_id')
        if gid == 'None':
            return None
        return gid or None

    def mirror_group_id():
        return info['gid']

    def detect_group_title():
        # gid: für Schreibtischfunktionalität verwendet
        # visaplan:
        from visaplan.plone.groups.groupsharing.browser import (
            groupinfo_factory,
            )
        if not info['gid']:
            return None
        return groupinfo_factory(context, 1, 1
                                 )(info['gid']
                                   )['group_title']

    def managed_group_title():
        # group_id: im Management-Interface verwendet.
        # Die Abweichung ist nützlich bei der Generierung von Breadcrumbs!
        # visaplan:
        from visaplan.plone.groups.groupsharing.browser import (
            groupinfo_factory,
            )
        if not info['group_id']:
            return None
        return groupinfo_factory(context, 1, 1
                                 )(info['group_id']
                                   )['group_title']

    def detect_export_profile_id():
        return info['request_var'].get('pid')

    def detect_export_profile():
        pid = info['export_profile_id']
        if pid:
            return hub['export'].getRawProfile(pid)

    def detect_export_profile_title():
        # Titel des Exportprofils
        pid = info['export_profile_id']
        if pid:
            return hub['export'].getProfileTitle(pid)

    def detect_template_id():
        return hub['templateid']()

    def get_is_view_template():
        return hub['plone_context_state'].is_view_template()

    def get_view_template_id():
        return hub['plone_context_state'].view_template_id()

    def get_view_url():
        return hub['plone_context_state'].view_url()

    def detect_path():
        return context.absolute_url_path()

    def detect_portal_url():
        return hub['portal']().absolute_url()

    def detect_portal_object():
        return hub['plone_portal_state'].portal()

    def detect_temp_folder():
        return info['portal_object'].temp

    def get_portal_and_site():
        p = info['portal_object']
        s = info['site_object']
        same = p is s
        pp(portal=p, site=s, identisch=same)
        return same

    def detect_portal_id():
        return info['portal_object'].getId()

    # nicht der Typ des Portals, sondern der portal_type des Kontexts:
    def detect_portal_type():
        return context.portal_type

    def detect_context_url():
        return context.absolute_url()

    def detect_context_title():
        return context.Title()

    def detect_desktop_brain():
        # visaplan:
        from visaplan.plone.unitracctool.unitraccfeature.utils import (
            MYUNITRACC_UID,
            )
        return hub['getbrain'](MYUNITRACC_UID)

    def detect_desktop_url():
        return info['desktop_brain'].getURL()

    def detect_has_uid():
        try:
            context.UID()
            return True
        except (KeyError, AttributeError) as e:
            print('detect_has_uid:', e)
            return False

    def requested_uid():
        return info['request_var'].get('uid') or None

    def detect_context_brain():
        try:
            uid = info['my_uid']
            if uid:
                return hub['getbrain'](uid)
        except AttributeError:
            return None

    def make_tooltip_divs():
        return makeBool(info['request_var'].get('tooltip_divs', 'yes'))

    def make_permission_proxy():
        pm = hub['portal_membership']
        cp = pm.checkPermission

        def f(perm):
            return cp(perm, context)
        set_trace()
        return Proxy(f)

    def check_permission():

        # noch völlig ohne Gewähr!
        # für beliebige Berechtigungen kam 1 zurück!
        def cp(perm):
            set_trace()
            if not info['has_perm'][perm]:
                raise Unauthorized
        return cp

    def make_timestamp_fn():
        # ein für den gesamten Request konstanter Zeitstempel,
        # geeignet für die Verwendung in Dateinamen
        return strftime(TIMESTAMP_FN)

    def detect_current_language():
        return hub['plone_portal_state'].language()

    def get_session_proxy():
        # visaplan:
        from visaplan.plone.tools.context import make_SessionDataProxy
        return make_SessionDataProxy(context)

    def get_is_member_of():  # gibt eine Funktion zurück
        # visaplan:
        from visaplan.plone.groups.groupsharing.browser import (
            is_member_of__factory,
            )
        if info['user_id'] is None:
            return gimme_False  # wg. Unterstützung von Argumenten
        return is_member_of__factory(context, info['user_id'])

    def get_is_mine():
        if info['user_id'] is None:  # Anonymous
            return False
        if info['portal_type'] == 'Folder':
            # auf dem Schreibtisch: kein Objekt ausgewählt
            return False
        return info['user_id'] == info['context_owner']

    def make_pdfCreator():
        # erzeuge einen PDFCreator, der seinerseits den PDFreactor kapselt;
        # lade die Lizenzdaten, und
        # füge Cookies hinzu
        # visaplan:
        from visaplan.plone.pdfexport.creator import PDFCreator
        creator = PDFCreator({'context': context,
                              'cookie': info['request'].cookies,
                              })
        creator.set_key()
        creator.setCookies()
        return creator

    def detect_context_owner():
        return context.Creator()

    def get_devmode():
        return DevelopmentMode

    def named_width():
        """
        info['named_width']['image_mini'] --> 240
        """
        return PrefixingMap(make_width_getter(info['named_sizes']))

    def named_sizes():
        popr = hub['portal_properties']
        impr = popr.imaging_properties
        alls = impr.allowed_sizes
        dic = {}
        for line in alls.split('\n'):
            key, size = line.strip().split()
            dim = list(map(int, size.split(':')))
            dic[key] = dim
        return dic

    def uid2brain_dict():
        rootfunc = hub['portal_catalog']._catalog

        def func(uid):
            # gibt gegenwärtig -- wie der Adapter getbrain -- bei
            # Mehrdeutigkeit den ersten Treffer, im Mißerfolgsfall None zurück
            brains = rootfunc(UID=uid)
            for brain in brains:
                return brain
        return Proxy(func)

    def uid2fullpath_dict():
        braindict = info['uid2brain']

        def func(uid):
            try:
                brain = braindict[uid]
            except KeyError:
                return None
            else:
                return brain.getPath()
        return Proxy(func)

    def uid2path_dict():
        braindict = info['uid2brain']

        def func(uid):
            try:
                brain = braindict[uid]
            except KeyError:
                return None
            else:
                loclist = brain.getPath().split('/')
                del loclist[1]
                return '/'.join(loclist)
        return Proxy(func)

    def uid2url_dict():
        catalog = hub['portal_catalog']
        unrestrictedSearchResults = catalog.unrestrictedSearchResults

        def func(uuid):
            res = unrestrictedSearchResults(UID=uuid)
            if res:
                url = res[0].getURL()
                pp(uuid=uuid, res=res, url=url)
                return url
        return Proxy(func)

    def dict_of_counters():
        return defaultdict(Counter)

    def get_translated():
        lang = info['current_lang']

        def func(tuples):
            o = None
            specs = 0
            for key, val in tuples:
                if key == 'path':
                    if val and val.startswith('/'):
                        val = val.lstrip('/')
                    if val:
                        specs += 1
                        try:
                            o = info['portal_object'].restrictedTraverse(val)
                        except (AttributeError, KeyError) as e:
                            print('E: path %(val)r not found!' % locals())
                            print(str(e))
                elif key == 'uid':
                    if val:
                        specs += 1
                        brain = info['uid2brain'][val]
                        if brain is not None:
                            o = brain.getObject()
                            if val == 'c27542ed513d0e6094bc2795087d8335':
                                debug = 1
                if o is not None:
                    break

            if o is None:
                if not specs:
                    dic = dict(tuples)
                    raise ValueError('%(dic)s lacks both path and uid!'
                                     % locals())
                return o

            if lang is not None:
                try:
                    o_lang = o.Language
                except AttributeError as e:
                    print("E: %(o)r lacks a 'Language' attribute" % locals())
                    o_lang = None
                if callable(o_lang):
                    o_lang = o_lang()
                if o_lang and o_lang != lang:
                    if hasattr(o, 'getTranslations'):
                        try:
                            tra_dic = o.getTranslations()
                        except AttributeError as e:
                            # error in Products.LinguaPlone.I18NBaseObject:
                            # .getTranslationBackReferences sometimes yields
                            # browsers rather than content objects ...
                            print('E: %(e)r' % locals())
                            try:
                                can_o = o.getCanonical()
                            except Exception as e:
                                print('E: %(e)r' % locals())
                            else:
                                o = can_o
                        else:
                            tra_liz = tra_dic.get(lang, [])
                            if tra_liz:
                                o = tra_liz[0]
                            else:
                                # the object has a non-empty language,
                                # and we don't have a matching translation!
                                o = None
            return o

        return Proxy(func, normalize=sorted_nonempty_item_tuples)

    FUNCMAP = {  # Objektinformationen:
               'my_uid': get_uid,
               'context_as_brain': detect_context_brain,
               'is_mine': get_is_mine,
               'cooperating_groups': detect_cooperating_groups,
               # nicht des Portals, sondern der portal_type des Kontexts:
               'portal_type': detect_portal_type,
               'context_url': detect_context_url,
               'context_title': detect_context_title,
               'context_owner': detect_context_owner,

               'st_num': get_structure_number,
               'isBook': detect_book,
               'isPresentation': detect_presentation,
               'isStructual': detect_structual,
               'bracket_default': detect_bracket_default,
               'request': get_request,
               'request_var': get_form,
               'response': get_response,
               'audit-mode': get_audit_mode,
               # UID auflösen:
               'uid2brain': uid2brain_dict,
               'uid2url': uid2url_dict,
               'uid2fullpath': uid2fullpath_dict,
               'uid2path': uid2path_dict,
               # ... in Dict:
               'my_translation': get_translated,
               # 'get_translation': get_translation_getter,
               # für Breadcrumbs:
               'gid': detect_group_id,
               'group_id': managed_group_id,
               'group_title': detect_group_title,
               'managed_group_title': managed_group_title,
               'template_id': detect_template_id,
               'portal_url': detect_portal_url,
               'portal_object': detect_portal_object,
               'temp_folder': detect_temp_folder,
               'site_object': getSite,  # noch experimentell
               'portal_and_site_objects': get_portal_and_site,
               'portal_id': detect_portal_id,
               'desktop_brain': detect_desktop_brain,
               'desktop_url': detect_desktop_url,
               'has_uid': detect_has_uid,
               'uid': requested_uid,
               'skip_desktop_crumbs': false_by_default,
               'personal_desktop_done': false_by_default,
               'group_desktop_done': false_by_default,
               'management_center_done': false_by_default,
               # Methoden von @@plone_context_state:
               'is_view_template': get_is_view_template,
               'view_url': get_view_url,
               'view_template_id': get_view_template_id,
               'view_template_done': false_by_default,
               # Exportprofil:
               'export_profile_id': detect_export_profile_id,
               'export_profile': detect_export_profile,
               'export_profile_title': detect_export_profile_title,
               # für Druckausgabe von Bildern:
               # - im Normalfall: die angegebene Größenstufe nehmen
               'image-size-steps': gimme_0,
               # - Skalierungsfaktor für Pixelbreite bzw. -höhe
               'image-print-factor': gimme_1,
               # für Entwicklungsunterstützung:
               '_nesting_depth': gimme_0,
               '_context_printed': false_by_default,
               # Tooltips erstmal nur auf Anforderung:
               '_make_tooltip_divs': make_tooltip_divs,
               'has_perm': make_permission_proxy,
               # 'checked_permission': check_permission,
               # für ../browser/export/petrify.py:
               'thread_ident': get_ident,
               'timestamp_fn': make_timestamp_fn,
               'path': detect_path,
               'current_lang': detect_current_language,
               'session': get_session_proxy,
               # Benutzerinformationen:
               'user_object': detect_user_object,
               'user_id': detect_user_id,
               'is_member_of': get_is_member_of,
               'logged_in': detect_logged_in,
               # Benutzer- bzw. Autorenprofil:
               'author_object': detect_author_object,
               'user_email': detect_user_email,
               # PDF-Generierung:
               'PDFCreator': make_pdfCreator,  # --> pdf/creator.py
               # Bilder-Abmessungen:
               'named_width': named_width,
               'named_sizes': named_sizes,
               # sonstiges:
               'devmode': get_devmode,
               'print_px_factor': gimme_1,
               'counter': Counter,
               'counters': dict_of_counters,
               }

    class InfoHub(dict):
        """
        Puffere bestimmte Informationen über den Kontext
        """

        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                if key in FUNCMAP:
                    val = FUNCMAP[key]()
                else:
                    raise
                dict.__setitem__(self, key, val)
                return dict.__getitem__(self, key)

    info = InfoHub()
    # Z. B. zum Andocken von .restrictedTraverse:
    info['context'] = context
    return hub, info
# --------------------------------------- ] ... Tools- und Info-Hubs ]

