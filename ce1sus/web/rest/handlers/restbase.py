# -*- coding: utf-8 -*-

"""
(Description)

Created on Feb 5, 2014
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'

from ce1sus.web.views.base import Ce1susBaseView
from dagr.helpers.debug import Log
import cherrypy
from ce1sus.api.dictconverter import DictConverter, DictConversionException
from ce1sus.api.common import JSONConverter, JSONException
from dagr.helpers.validator.objectvalidator import ObjectValidator
from ce1sus.web.rest.dictdbconverter import DictDBConverter, DictDBConversionException


class RestHandlerException(Exception):
  """
  Exception base for handler exceptions
  """
  pass


class RestBaseHandler(Ce1susBaseView):
  """Base class for handlers"""

  def __init__(self, config):
    Ce1susBaseView.__init__(self, config)
    self.logger = Log(config)
    self.__dictconverter = DictConverter(config)
    self.__jsonconverter = JSONConverter(config)
    self.__dict_db_converter = DictDBConverter(config)

  def create_status(self, classname=None, message=None):
    """Creates a stratus message"""
    self._get_logger().debug('Create error status with message {0}'.format(message))
    result = dict()
    result['response'] = dict()
    result['response']['errors'] = list()
    if (classname is None and message is None):
      result['response']['status'] = 'OK'
    else:
      result['response']['status'] = 'ERROR'
      result['response']['errors'].append({classname: '{0}'.format(message)})
    return result

  def _raise_fatal_error(self, error=None, msg=None):
    """generates a fatal error"""
    if error:
      self._get_logger().critical(error)
      message = error.message
    else:
      self._get_logger().critical(msg)
      message = msg
    raise cherrypy.HTTPError(418, message)

  def _raise_error(self, errorclass, error=None, msg=None):
    """generates an error"""
    if msg:
      message = msg
    else:
      if error:
        message = error.message
      else:
        self._get_logger().critical('Error message was not defined')
        raise cherrypy.HTTPError(418)
    self._get_logger().error(message)
    raise RestHandlerException('{0}: {1}'.format(errorclass, message))

  def _raise_nothing_found(self, error):
    """Raises a nothing found execption"""
    return self._raise_error('NothingFoundException', error=error)

  def _get_logger(self):
    """returns the class logger"""
    return self.logger.get_logger(self.__class__.__name__)

  def __object_to_dict(self, obj, owner, full, with_definition):
    """Converts the object to json"""

    self._get_logger().debug('Converting object to JSON with parameters {0},{1} and {2}'.format(owner,
                                                                                                full,
                                                                                                with_definition))
    try:
      rest_object = self.__dict_db_converter.convert_instance(obj, owner, full, with_definition)
      dictionary = self.__dictconverter.convert_to_dict(rest_object)
      return dictionary
    except (DictConversionException, JSONException, DictDBConversionException) as error:
      self._get_logger().critical(error)
      self._raise_error('ConversionException', error=error)

  def create_rest_obj(self, obj, owner, full, with_definition):
    return self.__object_to_dict(obj, owner, full, with_definition)

  def create_return_msg(self, dictionary):
    result = dict(dictionary.items() + self.create_status().items())
    try:
      return self.__jsonconverter.generate_json(result)
    except JSONException as error:
      self._get_logger().critical(error)
      self._raise_error('ConversionException', error=error)

  def return_object(self, obj, owner, full, with_definition):
    """ Retruns the formated return message for an object"""
    self._get_logger().debug('Returning object')
    obj_dict = self.create_rest_obj(obj, owner, full, with_definition)
    result = dict(obj_dict.items() + self.create_status().items())
    return self.create_return_msg(result)

  def get_post_object(self, action):
    """Returns the posted json to a rest object"""
    try:
      content_length = cherrypy.request.headers['Content-Length']
      raw = cherrypy.request.body.read(int(content_length))
      dictionary = self.__jsonconverter.decode_json(raw)
      user = self._get_user(False)
      rest_obj = self.__dict_db_converter.convert_to_db_object(user, dictionary, action)
      return rest_obj
    except Exception as error:
      self._get_logger().error('An error occurred by getting the post object {0}'.format(error))
      self._raise_error('UnRecoverableException',
                      msg='An unrecoverable error occurred. {0}'.format(error))

  def _raise_invalid_error(self, obj):
    error_msg = ObjectValidator.getFirstValidationError(obj)
    self._raise_error('InvalidException', msg=error_msg)
