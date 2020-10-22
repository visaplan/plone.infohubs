Changelog
=========


1.2.0 (unreleased)
------------------

New Features:

- info key `my_translation`: a proxy to get the appropriate language version
  for an object given by `path` or `uid`

Hard dependencies removed:

+------------------------------+----------------------------------------+
| Package                      | Depending features                     |
+==============================+========================================+
| visaplan.plone.groups_       | - ``info['group_title']``              |
|                              | - ``info['gid']`` (group id)           |
|                              | - ``info['managed_group_title']``      |
|                              | - ``info['is_member_of'](`group`)``    |
+------------------------------+----------------------------------------+
| visaplan.plone.tools_        | - ``info['session']``                  |
|                              | - ``info['gid']`` (group id)           |
+------------------------------+----------------------------------------+
| visaplan.plone.pdfexport     | - ``info['PDFCreator']``               |
+------------------------------+----------------------------------------+
| visaplan.plone.unitracctool  | - ``info['desktop_brain']``            |
|                              | - ``info['desktop_url']``              |
|                              | - ``info['bracket_default']``          |
+------------------------------+----------------------------------------+

[tobiasherp]


1.1.0 (2020-07-15)
------------------

New Features:

- info key `my_translation`: a proxy to get the appropriate language version
  for an object given by `path` or `uid`

[tobiasherp]


1.0.2 (2019-05-09)
------------------

- convenience function ``context_tuple``,
  e.g. for methods with optional ``hub`` and ``info`` arguments

- Explicitly raise TypeErrors instead of using assertions
  (``context_and_form_tuple``, ``context_tuple``)

- New info keys ``counter`` and ``counters``

[tobiasherp]


1.0.1 (2019-01-31)
------------------

- ``info['my_uid']`` uses ``plone.uuid.interfaces.IUUID`` directly
  [tobiasherp]


1.0 (2018-09-17)
-----------------

- Initial release.
  [tobiasherp]

.. _visaplan.plone.groups: https://pypi.org/project/visaplan.plone.groups
.. _visaplan.plone.tools: https://pypi.org/project/visaplan.plone.tools
