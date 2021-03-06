# -*- coding: utf-8 -*-

"""
module handing the attributes pages

Created: Aug 26, 2013
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'
from ce1sus.controllers.base import Ce1susBaseController
from dagr.helpers.ldaphandling import LDAPHandler, LDAPException
from dagr.db.broker import IntegrityException, BrokerException, \
  ValidationException, DeletionException
from ce1sus.brokers.permission.userbroker import UserBroker
from ce1sus.brokers.permission.groupbroker import GroupBroker
from dagr.controllers.base import ControllerException
from ce1sus.common.mailhandler import MailHandler, MailHandlerException
from dagr.helpers.datumzait import DatumZait


# pylint: disable=R0904
class UserController(Ce1susBaseController):
  """Controller handling all the requests for users"""

  def __init__(self, config):
    Ce1susBaseController.__init__(self, config)
    self.user_broker = self.broker_factory(UserBroker)
    self.group_broker = self.broker_factory(GroupBroker)
    self.ldap_handler = LDAPHandler(config)
    self.__use_ldap = config.get('ce1sus', 'useldap', False)
    self.mail_handler = MailHandler(config)

  @property
  def use_ldap(self):
    return self.__use_ldap

  def get_all_users(self):
    try:
      return self.user_broker.get_all()
    except BrokerException as error:
      self._raise_exception(error)

  def get_user_by_id(self, user_id):
    try:
      return self.user_broker.get_by_id(user_id)
    except BrokerException as error:
      self._raise_exception(error)

  def get_cb_group_values(self):
    try:
      groups = self.group_broker.get_all()
      cb_values = dict()
      for group in groups:
        cb_values[group.name] = group.identifier
      return cb_values
    except BrokerException as error:
      self._raise_exception(error)

  def get_all_ldap_users(self):
    try:
      return self.ldap_handler.get_all_users()
    except LDAPException as error:
      self._raise_exception(error)

  def populate_user(self, identifier, username, password,
                 priv, email, action, disabled, maingroup, apikey, gpgkey, name, sirname):
    try:
      return self.user_broker.build_user(identifier, username, password,
                 priv, email, action, disabled, maingroup, apikey, gpgkey, name, sirname)
    except BrokerException as error:
      self._raise_exception(error)

  def get_ldap_user(self, identifier):
    try:
      ldap_user = self.ldap_handler.get_user(identifier)
      # map ldap user to db user
      if not ldap_user.mail:
        ldap_user = self.ldap_handler.get_user(identifier)
      user = self.populate_user(None, ldap_user.uid, 'EXTERNALAUTH',
               0, ldap_user.mail, 'insert', 0, 1, None, None, ldap_user.name, ldap_user.sir_name)
      return user
    except LDAPException as error:
      self._raise_exception(error)

  def insert_ldap_user(self, user):
    try:
      # check if user is not already existing
      existing_user = None
      try:
        existing_user = self.user_broker.getUserByUserName(user.username)
      except BrokerException:
        pass

      if existing_user is None:
        self.insert_user(user, validate=False)
        return user, True
      else:
        raise ControllerException('User with the user name ' + user.username + 'already existing.')
    except BrokerException as error:
      self._raise_exception(error)

  def insert_user(self, user, validate=True):
    try:
      self.user_broker.insert(user, validate=validate)

      if user.gpg_key:
        self.mail_handler.import_gpg_key(user.gpg_key)

      send_mail = self._get_config().get('ce1sus', 'sendmail', False)

      if send_mail:
        # send activation mail
        self.mail_handler.send_activation_mail(user)
        # activate the user directly
      else:
        user.activated = DatumZait.utcnow()
        user.activation_str = None
        self.user_broker.update(user)
      return user, True
    except ValidationException as error:
      return user, False
    except (BrokerException, MailHandlerException) as error:
      self._raise_exception(error)

  def update_user(self, user):
    try:
      self.user_broker.update(user, validate=False)
      # add it again in case of changes
      if user.gpg_key:
        self.mail_handler.import_gpg_key(user.gpg_key)
      return user, True
    except ValidationException as error:
      return user, False
    except BrokerException as error:
      self._raise_exception(error)

  def remove_user(self, user):
    try:
      self.user_broker.remove_by_id(user.identifier)
      return user, True
    except IntegrityException as error:
      raise ControllerException('Cannot delete user. The user is referenced by elements.'
                    + ' Disable this user instead.')
    except DeletionException:
      raise ControllerException('This user cannot be deleted')
    except BrokerException as error:
      self._raise_exception(error)
