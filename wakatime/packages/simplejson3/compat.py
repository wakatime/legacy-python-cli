"""Python 3 compatibility shims
"""
import sys
if sys.version_info[0] < 3:
    PY3 = False
    def b(s):
        return s
    def u(s):
        return str(s, 'unicode_escape')
    import io as StringIO
    StringIO = BytesIO = StringIO.StringIO
    text_type = str
    binary_type = str
    string_types = (str,)
    integer_types = (int, int)
    chr = chr
    reload_module = reload
    def fromhex(s):
        return s.decode('hex')

else:
    PY3 = True
    from imp import reload as reload_module
    import codecs
    def b(s):
        return codecs.latin_1_encode(s)[0]
    def u(s):
        return s
    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO
    text_type = str
    binary_type = bytes
    string_types = (str,)
    integer_types = (int,)

    def chr(s):
        return u(chr(s))

    def fromhex(s):
        return bytes.fromhex(s)

long_type = integer_types[-1]
