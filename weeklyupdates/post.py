import os
import datetime
from genshi.filters import HTMLSanitizer
from genshi.input import HTML, ParseError
import markdown2
import re

def _regex_from_encoded_pattern(s):
    """'foo'    -> re.compile(re.escape('foo'))
       '/foo/'  -> re.compile('foo')
       '/foo/i' -> re.compile('foo', re.I)
    """
    if s.startswith('/') and s.rfind('/') != 0:
        # Parse it: /PATTERN/FLAGS
        idx = s.rfind('/')
        pattern, flags_str = s[1:idx], s[idx+1:]
        flag_from_char = {
            "i": re.IGNORECASE,
            "l": re.LOCALE,
            "s": re.DOTALL,
            "m": re.MULTILINE,
            "u": re.UNICODE,
        }
        flags = 0
        for char in flags_str:
            try:
                flags |= flag_from_char[char]
            except KeyError:
                raise ValueError("unsupported regex flag: '%s' in '%s' "
                                 "(must be one of '%s')"
                                 % (char, s, ''.join(list(flag_from_char.keys()))))
        return re.compile(s[1:idx], flags)
    else: # not an encoded regex
        return re.compile(re.escape(s))

markdown_link_patterns_file = os.getcwd() + os.sep + "markdown_link_patterns.config"
if os.path.isfile(markdown_link_patterns_file):
    link_patterns = []
    f = open(markdown_link_patterns_file)
    try:
        for i, line in enumerate(f.readlines()):
            if not line.strip(): continue
            if line.lstrip().startswith("#"): continue
            try:
                pat, href = line.rstrip().rsplit(None, 1)
            except ValueError:
                raise MarkdownError("%s:%d: invalid link pattern line: %r"
                                        % (opts.link_patterns_file, i+1, line))
            link_patterns.append(
                (_regex_from_encoded_pattern(pat), href))
    finally:
        f.close()
else:
    link_patterns = (
        (re.compile(r'(?<!")(https?://.*?(?=[\s\]\)\|]|$))', re.I | re.MULTILINE), r'\1'),
        (re.compile(r'bug[\s:#]+(\d{3,7})\b', re.I), r'https://bugzilla.mozilla.org/show_bug.cgi?id=\1'),
    )

md = markdown2.Markdown(html4tags=True, tab_width=2,
                        extras=['link-patterns',
                                'cuddled-lists',
                                'code-friendly'],
                        link_patterns=link_patterns)

class Post(object):
    userid = None
    postdate = None
    posttime = None
    completed = None
    planned = None
    tags = None
    bugs = None

    def __init__(self, record):
        if record is not None:
            self.userid, self.postdate, self.posttime, self.completed, self.planned, self.tags = record
            self.postdate = datetime.date.fromordinal(self.postdate)
            self.posttime = datetime.datetime.fromtimestamp(self.posttime)

    def populatebugs(self, bugs):
        if bugs is not None:
            self.bugs = bugs

    def getcompleted(self):
        if self.completed is None:
            return None
        try:
            return HTML(md.convert(self.completed)) | HTMLSanitizer()
        except ParseError:
            return self.completed

    def getplanned(self):
        if self.planned is None:
            return None
        try:
            return HTML(md.convert(self.planned)) | HTMLSanitizer()
        except ParseError:
            return self.planned

    def gettags(self):
        if self.tags is None:
            return None
        try:
            return HTML(md.convert(self.tags)) | HTMLSanitizer()
        except ParseError:
            return self.tags

