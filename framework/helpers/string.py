
__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@govcert.etat.lu'
__copyright__ = 'Copyright 2013, GOVCERT Luxembourg'
__license__ = 'GPL v3+'

"""String helper module"""
import re
import cgi
from datetime import datetime

class InputException(Exception):
  def __init__(self, message):
    Exception.__init__(self, message)

def plaintext2html(text, tabstop=4):
  """
  returns the given text in HTML Code

  :param text: Text to be converted
  :type text: String
  :param tabstop: The number of indentations
  :type tabstop: Integer


  :returns: String
  """
  # reference http://djangosnippets.org/snippets/19/
  re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \\t]+)|' +
                         '(?P<lineend>\\r\\n|\\r|\\n)|(?P<protocal>(^|\\s)' +
                         '((http|ftp)://.*?))(\\s|$)', re.S | re.M | re.I)

  def replacements(string):
    """
    replacements

    :returns: String
    """
    characters = string.groupdict()
    if characters['htmlchars']:
      return cgi.escape(characters['htmlchars'])
    if characters['lineend']:
      return '<br>'
    elif characters['space']:
      t = string.group().replace('\t', '&nbsp;' * tabstop)
      t = t.replace(' ', '&nbsp;')
      return t
    elif characters['space'] == '\t':
      return ' ' * tabstop
    else:
      url = string.group('protocal')
      if url.startswith(' '):
        prefix = ' '
        url = url[1:]
      else:
        prefix = ''
        last = string.groups()[-1]
        if last in ['\n', '\r', '\r\n']:
          last = '<br>'
        return '%s<a href="%s">%s</a>%s' % (prefix, url, url, last)

  # convert to text to be compliant
  stringText = unicode(text)
  if len(stringText) > 0:
    return re.sub(re_string, replacements, stringText)
  else:
    return ''

def stringToDateTime(string):
  """
  Converts a string to a DateTime if the format is known
  """
  dateFormats = ['%Y-%m-%d',
             '%Y-%m-%d %H:%M',
             '%Y-%m-%d %H:%M:%S',
             '%Y-%m-%d - %H:%M:%S',
             '%Y-%m-%d - %H:%M',
             '%d/%m/%Y',
             '%d/%m/%Y - %H:%M',
             '%d/%m/%Y - %H:%M:%S',
             '%d/%m/%Y %H:%M',
             '%d/%m/%Y %H:%M:%S'
             ]
  # loops over the different formats and if the loop ends raise an exception
  # as no format is applicable
  dateString = unicode(string)
  for dateFormat in dateFormats:
    try:
      return datetime.strptime(dateString, dateFormat)
    except ValueError:
      pass
  raise InputException('Format of Date "{0}" is unknown'.format(string))

def isNotNull(value):
  """
  Checks if a string is not null

  :returns: Boolean
  """
  if value is None:
    return False
  string = unicode(value)
  return string and string != ''
