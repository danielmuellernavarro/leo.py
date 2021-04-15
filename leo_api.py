import requests
from lxml import etree
from io import StringIO
import logging
import time


logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

uri = 'http://dict.leo.org/%s%s/' # LEO uri
section_names = (
    'subst',
    'verb',
    'adjadv',
    'praep',
    'definition',
    'phrase',
    'example',
)


class Leo:
   def __init__(self, source_language='en', target_language='de', section_names=section_names, wait_between_search=20.0):
      self.sl = source_language
      self.tl = target_language
      self.section_names = section_names
      self.wait_between_search = wait_between_search
      self._first_wait = False
      # English (en)
      # French (fr)
      # Spanish (es)
      # Italian (it)
      # Chinese (ch)
      # Russian (ru)
      # German (de)
      # Portuguese (pt)
      # Polish (pl)

   def _get_text(self, elt):
      buf = StringIO()

      def _helper(_elt):
         if _elt.text is not None:
               buf.write(_elt.text)
         for child in _elt:
               _helper(child)
         if _elt.tail is not None:
               buf.write(_elt.tail)

      _helper(elt)
      return buf.getvalue()

   def _format_ret(self, ret):
      format_ret = ''
      for x in ret:
         # subst, verb, adjadv, definition, example, subst, phrase
         if x not in self.section_names:
            continue
         x[0].upper()
         format_ret += x + '\n'
         for x in ret[x]:
            sl = x[self.sl][0].upper() + x[self.sl][1:]
            tl = x[self.tl][0].upper() + x[self.tl][1:]
            format_ret += sl + '\t' + tl + '\n'
         format_ret += '\n'
      return format_ret

   def _wait(self):
      if self._first_wait:
         time.sleep(self.wait_between_search)
         self._first_wait = False
      self._first_wait = True

   def search(self, term, timeout = 10, max_results = 999):
      self._wait()

      url = uri % (self.sl, self.tl)
      resp = requests.get(url, params={'search': term}, timeout=timeout)
      ret = {}
      if resp.status_code != requests.codes.ok:
         return ret
      p = etree.HTMLParser()
      html = etree.parse(StringIO(resp.text), p)
      for section_name in self.section_names:
         section = html.find(".//div[@id='section-%s']" % section_name)
         if section is None:
            continue
         ret[section_name] = []
         results = section.findall(".//td[@lang='%s']" % (self.sl,)) # source language
         for index, r_sl in enumerate(results):
            if index >= max_results:
               break
            r_tl = r_sl.find("./../td[@lang='%s']" % (self.tl,)) # target language
            ret[section_name].append({
               self.sl: self._get_text(r_sl).strip(),
               self.tl: self._get_text(r_tl).strip(),
            })
      return self._format_ret(ret)


def main():
   sections = (
      'subst',
      'definition',
      'phrase',
      'example',
   )   
   leo = Leo(section_names=sections)
   # leo = Leo()
   result = leo.search('milk', max_results=5)
   print(result)


if __name__ == '__main__':
   main()
