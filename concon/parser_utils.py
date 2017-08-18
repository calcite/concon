"""
.. module:: concon.parser_utils
    :platform: Unix, Windows
    :synopsis: Utilities for convenient config file parsing.
.. moduleauthor:: Martin Stejskal <mstejskal@alps.cz>

"""
import sys

if sys.version_info[0] == 2:
    import ConfigParser as configparser
elif sys.version_info[0] == 3:
    import configparser
else:
    raise Exception("Unknown python version")


# Because in pure ConfigParser there is no option to write comments directly
# http://stackoverflow.com/questions/8533797/adding-comment-with-configparser
class ConfigParserWithComments(configparser.ConfigParser):

    def __init__(self, *args, **kwargs):
        configparser.ConfigParser.__init__(self, *args, **kwargs)

    def add_comment(self, section, comment):
        # Do not know why, but in python3 there value can not be none, but in
        # python2 can. Not optimal, but there is version switch.
        if sys.version_info[0] == 2:
            # Nice comment
            self.set(section, '; ' + comment, None)
        elif sys.version_info[0] == 3:
            # Ugly, but working comment
            self.set(section, "; " + comment, "")
        else:
            raise Exception("Unknown python version")

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            s = str("[%s]\n" % configparser.DEFAULTSECT)

            # This is python version dependent. Again :(
            if sys.version_info[0] == 2:
                fp.write(s)

                for (key, value) in self._defaults.items():
                    self._write_item(fp, key, value)
                fp.write("\n")
            elif sys.version_info[0] == 3:
                fp.write(bytes(s, 'UTF-8'))

                for (key, value) in self._defaults.items():
                    self._write_item(fp, key, value)
                fp.write(bytes("\n"), 'UTF-8')
            else:
                raise Exception("Unknown python version")

        for section in self._sections:

            if sys.version_info[0] == 2:
                s = str("[%s]\n" % section)
                fp.write(s)

                for (key, value) in self._sections[section].items():
                    self._write_item(fp, key, value)
                s = str("\n")
                fp.write(s)
            elif sys.version_info[0] == 3:
                s = str("[%s]\n" % section)
                fp.write(bytes(s, 'UTF-8'))
                for (key, value) in self._sections[section].items():
                    self._write_item(fp, key, value)
                s = str("\n")
                fp.write(bytes(s, 'UTF-8'))
            else:
                raise Exception("Unknown python version")

    def _write_item(self, fp, key, value):
        if sys.version_info[0] == 2:
            if key.startswith(';') and value is None:
                fp.write("%s\n" % (key,))
            else:
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))

        elif sys.version_info[0] == 3:
            if key.startswith(';'):  # Value is not None and can't be
                fp.write(bytes("%s\n" % (key,), 'UTF-8'))
            else:
                fp.write(
                    bytes("%s = %s\n" % (key, str(value).replace('\n', '\n\t')),
                          'UTF-8'))
        else:
            raise Exception("Unknown python version")
