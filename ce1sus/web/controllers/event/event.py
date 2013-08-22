"""module holding all controllers needed for the event handling"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'

import copy
from framework.web.controllers.base import BaseController
import cherrypy
from framework.web.helpers.pagination import Paginator, PaginatorOptions
from datetime import datetime
from ce1sus.brokers.eventbroker import EventBroker, ObjectBroker, \
                  AttributeBroker, Event, CommentBroker, TicketBroker
from ce1sus.brokers.staticbroker import Status, TLPLevel
from ce1sus.brokers.definitionbroker import ObjectDefinitionBroker, \
                  AttributeDefinitionBroker
from ce1sus.web.helpers.protection import require
from framework.helpers.rt import RTHelper
from framework.db.broker import ValidationException, BrokerException
from framework.helpers.converters import ObjectConverter

class EventController(BaseController):
  """event controller handling all actions in the event section"""

  def __init__(self):
    BaseController.__init__(self)
    self.eventBroker = self.brokerFactory(EventBroker)
    self.objectBroker = self.brokerFactory(ObjectBroker)
    self.def_objectBroker = self.brokerFactory(ObjectDefinitionBroker)
    self.attributeBroker = self.brokerFactory(AttributeBroker)
    self.def_attributesBroker = self.brokerFactory(AttributeDefinitionBroker)
    self.commentBroker = self.brokerFactory(CommentBroker)
    self.ticketBroker = self.brokerFactory(TicketBroker)

  @require()
  @cherrypy.expose
  def view(self, eventID):
    """
    renders the base page for displaying events

    :returns: generated HTML
    """
    template = self.mako.getTemplate('/events/event/eventBase.html')
    return template.render(eventID=eventID)


  @require()
  @cherrypy.expose
  def event(self, eventID):
    """
    renders the event page for displaying a single event

    :returns: generated HTML
    """
    template = self.mako.getTemplate('/events/event/view.html')

    event = self.eventBroker.getByID(eventID)

    # right checks
    self.checkIfViewable(event.groups,
                         self.getUser().identifier == event.creator.identifier)


    cbStatusValues = Status.getDefinitions()
    cbTLPValues = TLPLevel.getDefinitions()


    objectLabels = [{'identifier':'#'},
              {'definition.name':'Type'},
              {'creator.username':'Created by'},
              {'created':'CreatedOn'}]



    paginatorOptions = PaginatorOptions('/events/recent',
                                        'eventsTabTabContent')
    paginatorOptions.addOption('TAB',
                          'VIEW',
                          '/events/event/objects/objects/{0}/'.format(eventID),
                          contentid='',
                          tabid='eventObjects{0}'.format(eventID))
    objectPaginator = Paginator(items=event.objects,
                          labelsAndProperty=objectLabels,
                          paginatorOptions=paginatorOptions)

    objectPaginator.itemsPerPage = 3

    ticketLabels = [{'identifier':'#'},
              {'ticket':'Ticket Number'},
              {'creator.username':'Created by'},
              {'created':'CreatedOn'}]

    ticketPaginator = Paginator(items=event.tickets,
                        labelsAndProperty=ticketLabels)
    ticketPaginator.showDelete = True
    ticketPaginator.itemsPerPage = 3

    eventLabels = [{'identifier':'#'},
              {'title':'Name'},
              {'creator.username':'Created by'},
              {'created':'CreatedOn'}]
    eventPaginatorOptions = PaginatorOptions('/events/recent',
                                             'eventsTabTabContent')
    eventPaginatorOptions.addOption('NEWTAB',
                                    'VIEW',
                                    '/events/event/view/',
                                    contentid='')
    eventPaginator = Paginator(items=event.events,
                          labelsAndProperty=eventLabels,
                          paginatorOptions=eventPaginatorOptions)
    eventPaginator.itemsPerPage = 3


    comments = self.commentBroker.getAllByEventID(eventID)




    return template.render(objectPaginator=objectPaginator,
                           eventPaginator=eventPaginator,
                           ticketPaginator=ticketPaginator,
                           event=event,
                           cbStatusValues=cbStatusValues,
                           cbTLPValues=cbTLPValues,
                           comments=comments,
                           rtUrl=RTHelper.getInstance().getTicketUrl())

  @require()
  @cherrypy.expose
  def editEvent(self, eventID):
    """
    renders the base page for editing a single event

    :returns: generated HTML
    """
    template = self.getTemplate('/events/event/eventModal.html')
    event = self.eventBroker.getByID(eventID)
    cbStatusValues = Status.getDefinitions()
    cbTLPValues = TLPLevel.getDefinitions()
    return template.render(errorMsg=None,
                           event=event,
                           cbStatusValues=cbStatusValues,
                           cbTLPValues=cbTLPValues)

  @require()
  @cherrypy.expose
  def modifyEvent(self, identifier=None, action=None, status=None,
                  tlp_index=None, description=None,
                  name=None, published=None,
                  first_seen=None, last_seen=None):
    """
    modifies or inserts an event with the data of the post

    :param identifier: The identifier of the event,
                       is only used in case the action is edit or remove
    :type identifier: Integer
    :param action: action which is taken (i.e. edit, insert, remove)
    :type action: String
    :param status: The identifier of the statuts
    :type status: Integer
    :param tlp_index: The identifier of the TLP level
    :type tlp_index: Integer
    :param description: The desc
    :type description: String
    :param email: The email of the user
    :type email: String



    :returns: generated HTML
    """
    event_orig = self.eventBroker.getByID(identifier)
    # right checks only if there is a change!!!!
    self.checkIfViewable(
                    event_orig.groups, self.getUser().identifier ==
                    event_orig.creator.identifier)

    errors = False
    template = self.getTemplate('/events/event/eventModal.html')

    cbStatusValues = Status.getDefinitions()
    cbTLPValues = TLPLevel.getDefinitions()
    # fill in the values
    event = Event()
    if not action == 'insert':
      # dont want to change the original in case the user cancel!
      event = copy.copy(event_orig)
    if not action == 'remove':
      event.title = name
      event.description = description
      ObjectConverter.setInteger(event, 'tlp_level_id', tlp_index)
      ObjectConverter.setInteger(event, 'status_id', status)
      ObjectConverter.setInteger(event, 'published', published)
      event.modified = datetime.now()
      ObjectConverter.setDate(event, 'first_seen', first_seen)
      ObjectConverter.setDate(event, 'last_seen', last_seen)

    try:
      if action == 'insert':
        event.created = datetime.now()
        event.creator = self.getUser()
        event.user_id = event.creator.identifier
        self.eventBroker.insert(event)
      if action == 'update':
        # get original event
        self.eventBroker.update(event)
      if action == 'remove':
        self.eventBroker.removeByID(event.identifier)

    except ValidationException:
      self.getLogger().debug('Event is invalid')
      errors = True
    except BrokerException as e:
      errorMsg = 'An unexpected error occurred: {0}'.format(e)
      self.getLogger().debug('An unexpected error occurred: {0}'.format(e))
      errors = True

    if errors:
      return template.render(errorMsg=errorMsg,
                           event=event,
                           cbStatusValues=cbStatusValues,
                           cbTLPValues=cbTLPValues)
    else:
      return self.returnAjaxOK()



