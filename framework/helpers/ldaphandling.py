"""module containing interfaces classes related to LDAP"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'

from framework.helpers.config import Configuration
from framework.helpers.debug import Log
import ldap
import types

class LDAPUser(object):
  def __init__(self):
    self.uid = None
    self.mail = None
    self.password = 'EXTERNALAUTH'
    self.displayName = None

class LDAPException(Exception):
  """LDAP Error"""
  def __init__(self, message):
    Exception.__init__(self, message)

class NothingFoundException(LDAPException):
  """Invalid Error"""
  def __init__(self, message):
    LDAPException.__init__(self, message)

class InvalidCredentialsException(LDAPException):
  """Invalid Error"""
  def __init__(self, message):
    LDAPException.__init__(self, message)

class ServerErrorException(LDAPException):
  """Server Error"""
  def __init__(self, message):
    LDAPException.__init__(self, message)

class NotInitializedException(LDAPException):
  """Server Error"""
  def __init__(self, message):
    LDAPException.__init__(self, message)

class LDAPHandler(object):
  "LDAP Handler"



  instance = None
  def __init__(self, configFile):
    self.__config = Configuration(configFile, 'LDAP')

    self.__connection = None

    self.__users_dn = self.__config.get('users_dn')

    self.__tls = self.__config.get('usetls')



    LDAPHandler.instance = self

  def open(self):
    self.__connection = ldap.initialize(self.__config.get('server'))
    try:
      if self.__tls:
        self.__connection.start_tls_s()
    except ldap.LDAPError as e:
      Log.getLogger(self.__class__.__name__).fatal(e)
      raise ServerErrorException('LDAP error: ' + unicode(e))


  def isUserValid(self, uid, password):
    """
    Checks if the user is valid

    :param uid:
    :type uid: String
    :param passowrd:
    :type password: String

    :returns: Boolean
    """
    try:
      self.__bindUser(uid, password)
      return True
    except LDAPException:
      return False

  def __bindUser(self, uid, password):
    """
    Bind/authenticate with a user with appropriate rights to add objects

    :param uid:
    :type uid: String
    :param passowrd:
    :type password: String
    """
    try:
      try:
        if not (uid is None or password is None):
          self.__connection.simple_bind_s(self.__getUserDN(uid), password)
      except ldap.INVALID_CREDENTIALS:
        Log.getLogger(self.__class__.__name__
                        ).info('Username or password is invalid for {0}'.format(
                                                                          uid))
        raise InvalidCredentialsException('Username or password is invalid.')
    except ldap.LDAPError as e:
      Log.getLogger(self.__class__.__name__).fatal(e)
      raise ServerErrorException('LDAP error: {0}'.format(e))


  @staticmethod
  def __mapUser(user):
    for attributes in user:
      if isinstance(attributes, types.DictType):
        user = LDAPUser()
        for key, value in attributes.iteritems():
          if hasattr(user, key):
            # Foo to prevent ascii errors as ldap module returns strings!
            try:
              setattr(user, key, unicode(value[0]))
            except UnicodeDecodeError:
              setattr(user, key, unicode(value[0], 'utf-8', errors='replace'))

    return user

  def getAllUsers(self):
    """
    Returns the attribute value

    :param uid:
    :type uid: String
    :param attributeName:
    :type attributeName: String

    :returns: String
    """
    filter_ = '(uid=*)'

    attributes = ["uid", "displayName", "mail"]

    try:
      result = self.__connection.search_s(self.__users_dn, ldap.SCOPE_SUBTREE,
                               filter_, attributes)
      # dierft nemmen 1 sinn
      userList = list()
      for user in result:
        user = LDAPHandler.__mapUser(user)
        userList.append(user)
      if len(userList) < 1:
        raise NothingFoundException('No  users were found')
    except ldap.LDAPError as e:
      Log.getLogger(self.__class__.__name__).fatal(e)
      raise ServerErrorException('LDAP error: {0}'.format(e))
    return userList

  def getUser(self, uid):
    """
    Returns the attribute value

    :param uid:
    :type uid: String
    :param attributeName:
    :type attributeName: String

    :returns: String
    """
    filter_ = '(uid=*)'

    attributes = ["uid", "displayName", "mail"]

    try:
      result = self.__connection.search_s(self.__getUserDN(uid), ldap.SCOPE_SUBTREE,
                               filter_, attributes)
      # dierft nemmen 1 sinn
      for user in result:
        user = LDAPHandler.__mapUser(user)

    except ldap.LDAPError as e:
      Log.getLogger(self.__class__.__name__).fatal(e)
      raise ServerErrorException('LDAP error: {0}'.format(e))
    return user



  def getUserAttribute(self, uid, attributeName):
    """
    Returns the attribute value

    :param uid:
    :type uid: String
    :param attributeName:
    :type attributeName: String

    :returns: String
    """
    filter_ = '(uid=' + uid + ')'
    userdn = self.__getUserDN(uid)
    try:
      result = self.__connection.search_s(userdn, ldap.SCOPE_SUBTREE,
                               filter_, [attributeName])
    except ldap.LDAPError as e:
      Log.getLogger(self.__class__.__name__).fatal(e)
      raise ServerErrorException('LDAP error: {0}'.format(e))
    attribute = None
    # dierft nemmen 1 sinn
    for tuple in result:
      for item in tuple:
        if isinstance(item, types.DictType):
          attribute = item[attributeName][0]
    return attribute

  def __getUserDN(self, uid):
    """
    Returns the User domain name string

    :param uid:
    :type uid: String

    :returns: String
    """
    return 'uid=' + uid + ',' + self.__users_dn

  def close(self):
    """
    close the connection
    """
    try:
      self.__connection.unbind_s()
    except ldap.LDAPError as e:
      Log.getLogger(self.__class__.__name__).fatal(e)

  @classmethod
  def getInstance(cls):
    """
      Returns an instance

      :returns: LDAPHandler
    """
    if LDAPHandler.instance == None:
      raise NotInitializedException('LDAPHandler has not been initialized')
    else:
      return LDAPHandler.instance

