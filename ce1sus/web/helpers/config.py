from ce1sus.helpers.config import Configuration

class WebConfig(object):

  def __init__(self, configFile):
    WebConfig.instance = self
    self.__config = Configuration(configFile, 'ce1sus')

  def get(self, identifier):
    return self.__config.get(identifier)


  @staticmethod
  def getInstance():
    if WebConfig.instance == None:
      raise IndentationError('No SessionManager present')
    return WebConfig.instance