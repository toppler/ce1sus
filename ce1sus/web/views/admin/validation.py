# -*- coding: utf-8 -*-

"""
(Description)

Created on Feb 3, 2014
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'

from ce1sus.web.views.base import Ce1susBaseView, privileged
from ce1sus.controllers.admin.validation import ValidationController
import cherrypy
from ce1sus.web.views.common.decorators import require, require_referer
from dagr.controllers.base import ControllerException
from ce1sus.brokers.staticbroker import Status, TLPLevel, Analysis, Risk
from dagr.helpers.datumzait import DatumZait


class AdminValidationView(Ce1susBaseView):
  """index view handling all display in the index section"""
  def __init__(self, config):
    Ce1susBaseView.__init__(self, config)
    self.validation_controller = ValidationController(config)

  @require(privileged(), require_referer(('/internal')))
  @cherrypy.expose
  def index(self):
    """
    index page of the administration section

    :returns: generated HTML
    """
    return self._render_template('/admin/validation/validationBase.html')

  @require(privileged(), require_referer(('/internal')))
  @cherrypy.expose
  def unvalidated(self):
    try:
      events = self.validation_controller.get_all_unvalidated_events()
      return self._render_template('/events/recent.html',
                                   events=events,
                                   url='/admin/validation/event',
                                   tab_id='validationTabsTabContent',
                                   error=None,
                                   ext_event_id=None)
    except ControllerException as error:
      return self._render_error_page(error)

  @require(privileged(), require_referer(('/internal')))
  @cherrypy.expose
  def event(self, event_id):
    """
    renders the base page for displaying events

    :returns: generated HTML
    """
    return self._render_template('/admin/validation/eventValBase.html', event_id=event_id)

  def __render_event_details(self, template_name, event):
    """
    renders the template

    :param template_name: file string of the template
    :type template_name: String
    :param event:
    :type event: Event

    :returns: generated HTML
    """

  @require(require_referer(('/internal')))
  @cherrypy.expose
  def event_details(self, event_id):
    """
    renders the event page for displaying a single event

    :returns: generated HTML
    """
    try:
      event = self.validation_controller.get_event_by_id(event_id)
      relations = self.validation_controller.get_related_events(event)
      return self._render_template('/admin/validation/eventDetails.html',
                                   event=event,
                                   today=DatumZait.utcnow(),
                                   status_values=Status.get_definitions(),
                                   tlp_values=TLPLevel.get_definitions(),
                                   analysis_values=Analysis.get_definitions(),
                                   risk_values=Risk.get_definitions(),
                                   relations=relations)
    except ControllerException as error:
      return self._render_error_page(error)

  @require(privileged(), require_referer(('/internal')))
  @cherrypy.expose
  def event_objects(self, eventid):
    try:
      event = self.validation_controller.get_event_by_id(eventid)
      self._check_if_event_is_viewable(event)

      return self._render_template('/events/event/objects/objectsBase.html',
                                   event_id=eventid,
                                   object_list=event.objects,
                                   obj_definitions=dict(),
                                   attribute_definitions=dict(),
                                   object_id=None,
                                   owner=True)
    except ControllerException as error:
      return self._render_error_page(error)

  @require(privileged(), require_referer(('/internal')))
  @cherrypy.expose
  def flat_event_objects(self, event_id):
    try:
      event = self.validation_controller.get_event_by_id(event_id)

      flat_objects = self.validation_controller.get_flat_objects(event)
      return self._render_template('/events/event/objects/flatview.html',
                                   flat_objects=flat_objects,
                                   event_id=event_id,
                                   owner=True)
    except ControllerException as error:
      return self._render_error_page(error)

  @require(privileged(), require_referer(('/internal')))
  @cherrypy.expose
  def validate_event(self, event_id):
    try:
      event = self.validation_controller.get_event_by_id(event_id)
      user = self._get_user()
      self.validation_controller.validate_event(event, user)
      return self._return_ajax_ok()
    except ControllerException as error:
      return self._render_error_page(error)

  @require(privileged(), require_referer(('/internal')))
  @cherrypy.expose
  def delete_unvalidated_event(self, event_id):
    try:
      event = self.validation_controller.get_event_by_id(event_id)
      self.validation_controller.remove_unvalidated_event(event)
      return self._return_ajax_ok()
    except ControllerException as error:
      return self._render_error_page(error)

