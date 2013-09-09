# -*- coding: utf-8 -*-

"""
module providing support for the base handler

Created: Aug, 2013
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'


from abc import abstractmethod
from dagr.web.helpers.templates import MakoHandler
from dagr.helpers.debug import Log
from dagr.db.session import SessionManager
from importlib import import_module

class HandlerException(Exception):
  """
  Exception base for handler exceptions
  """
  def __init__(self, message):
    Exception.__init__(self, message)

class HandlerBase(object):
  """
  Base class for handlers
  """
  def __init__(self):
    self.mako = MakoHandler.getInstance()
    self.logger = Log.getLogger(self.__class__.__name__)
    self.__sessionHandler = SessionManager.getInstance()

  @abstractmethod
  def populateAttributes(self, params, obj, definition, user):
    """
    Creates the attributes

    :param params: The parameters
    :type params: Dictionary
    :param obj: The object the attributes belongs to
    :type obj: BASE object
    :param definition: Attribute definition
    :type definition: AttributeDefinition
    :param user: The user creating the attribute
    :type user: User

    :returns: List of Attributes or a single Attribute
    """
    raise HandlerException(('populateAttributes '
                            + 'not defined for {0} and parameters '
                            + ' {1}, {2}, {3}, {4}').format(
                                                    self.__class__.__name__,
                                                    params,
                                                    obj,
                                                    definition,
                                                    user
                                                    ))

  @abstractmethod
  def render(self, enabled, attribute=None):
    """
    Generates the HTML for displaying the attribute

    :param enabled: If the view should be enabled
    :type enabled: Boolean
    :param attribute: The attribute to be displayed
    :type attribute: Attribute

    :returns: generated HTML
    """
    raise HandlerException(('render not defined'
                            + ' for {0} with parameter {1} and{2}')
                           .format(self.__class__.__name__,
                                   enabled,
                                   attribute))

  @abstractmethod
  def convertToAttributeValue(self, value):
    """
    Convert the attribute to a single value, to be used to form a generic
    attribute

    :param value:
    :type value: Object
    """
    raise HandlerException(('convert not '
                            + 'defined for {0} with parameter {1}').format(
                                                    self.__class__.__name__,
                                                    value))
  @abstractmethod
  def getAttributesNameList(self):
    """
    Returns a list of attributes required for the handling
    """
    return HandlerException('{0}.getAttributesNameList is not defined'.format(
                                                    self.__class__.__name__))


  def getTemplate(self, name):
    """Returns the template

    :param name: The name of the template (can also be a path)
    :type name: String

    :returns: Template
    """
    return self.mako.getTemplate(name)

  def brokerFactory(self, clazz):
    """
    Instantiates a broker.

    Note: In short sets up the broker in a correct manner with all the
    required settings

    :param clazz: The BrokerClass to be instantiated
    :type clazz: Extension of brokerbase

    :returns: Instance of a broker
    """
    return self.__sessionHandler.brokerFactory(clazz)

  def getLogger(self):
    """
    Returns the logger

    :returns: Logger
    """
    return Log.getLogger(self.__class__.__name__)

  @staticmethod
  def getHandler(definition):
    """
    Returns the handler instance of the given definition

    :param definition: The definition
    :type definition: AttributeDefinition

    :returns: Instance extending HandlerBase
    """
    # GethandlerClass
    temp = definition.handlerName.rsplit('.', 1)
    module = import_module('.' + temp[0], 'ce1sus.web.helpers.handlers')
    clazz = getattr(module, temp[1])
    # instantiate
    handler = clazz()
    # check if handler base is implemented
    if not isinstance(handler, HandlerBase):
      raise HandlerException(('{0} does not implement '
                              + 'HandlerBase').format(definition.handlerName))
    return handler