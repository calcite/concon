"""
.. module:: UCA_lib.descriptor_parser
   :platform: Unix, Windows
   :synopsis: Parser of descriptor syntax rules (see README.markdown)
.. moduleauthor:: Josef Nevrly

"""

import re
from collections import OrderedDict

COMMAND_PATTERN = re.compile(r'^\{([LCSA])\}(.*)$')
EXPANSION_PATTERN = re.compile(r'^=(.*)$')
LIST_ARGS_PATTERN = re.compile(r'\s*(\d+):(.*?)(;|$)')
NOTE_ARG_PATTERN = re.compile(r'\s*N:(.*?)(;|$)')
SLIDER_ARG_PATTERN = re.compile(r'\s*(.*?);\s*step:\s*([-+]?\d*\.\d+|\d+)')
NOTE_INDEX = 'N'

# Checkbox string expansions (used only for config files)
OPPOSITE_STRINGS = {
    'enabled': 'disabled',
}

DEFAULT_NEGATOR = 'not'


def parse_list_command(arguments):
    """
    Process LIST definition command.
    :param arguments:    List command arguments
    
    :return: tuple of list options
    """
    res = OrderedDict(
        [(int(argument.group(1)), argument.group(2)) for argument in
         LIST_ARGS_PATTERN.finditer(arguments)])
    note = NOTE_ARG_PATTERN.search(arguments)
    if note:
        res[NOTE_INDEX] = note.group(1)
    return res


def parse_checkbox_command(arguments):
    """
    Process Checkbox definition command.
    
    :param arguments:    Checkbox arguments.
    
    :return:    checkbox argument string (basically the same thing)
    """
    return arguments.strip()


def parse_slider_command(arguments):
    """
    Process Slider definition command.
    
    :param arguments:    Slider arguments.
    
    :return: Tuple with slider arguments (description, step)
    """
    args = SLIDER_ARG_PATTERN.search(arguments)
    return args.groups()


def parse_arrowbox_command(arguments):
    # NOTE - edit COMMAND_PARSERS if you want to use this
    pass


COMMAND_PARSERS = {
    'L': parse_list_command,
    'C': parse_checkbox_command,
    'S': parse_slider_command,
    'A': parse_slider_command,
}


def list_command_to_str(arguments):
    """
    Convert arguments for list command into comment string for config file.
    
    :param arguments:    list of options
    
    :return: Formatted string for config file.
    """
    # remove Note option
    note_str = arguments.pop(NOTE_INDEX, None)

    options_str = 'Options: ' + '; '.join(
        ['{0}: {1}'.format(key, option) for key, option in arguments.items()])

    if note_str:
        return "{0}; {1}".format(options_str, note_str)
    else:
        return options_str


def checkbox_command_to_str(arguments):
    """
    Convert arguments for checkbox command into comment string for config file.
    It also tries to find some reasonable names for the opposite option.
    
    :param arguments:    checkbox arguments
    
    :return: Formatted string for config file.
    """
    checked_value = arguments
    unchecked_value = OPPOSITE_STRINGS.get(arguments.lower(),
                                           '{0} {1}'.format(DEFAULT_NEGATOR,
                                                            arguments))
    return "Options: 0 - {0}, 1 - {1}".format(unchecked_value, checked_value)


# TODO: Finish this
def slider_command_to_str(arguments):
    """
    Convert arguments for slider and arrowbox command into comment string 
    for config file.
    
    :param arguments:    slider arguments
    
    :return: Formatted string for config file.
    """
    return '; '.join(arguments)


COMMAND_STRING_CONVERTORS = {
    'L': list_command_to_str,
    'C': checkbox_command_to_str,
    'S': slider_command_to_str,
    'A': slider_command_to_str,
}


def expand_command(descriptor):
    """
    Expands the = command string into full command string using Python eval.
    
    :param descriptor:    descriptor string.
    
    :return: Expanded descriptor string
    """
    res = EXPANSION_PATTERN.match(descriptor)
    if res:
        return eval(res.group(1))
    else:
        return descriptor


def parse_command(descriptor):
    """
    Parse the syntax for descriptor commands.
    
    :param descriptor:    descriptor string.
    
    :return: Tuple of (command code, arguments)
    """
    res = COMMAND_PATTERN.match(expand_command(descriptor))
    result_tuple = ()
    if res:
        command = res.group(1)
        command_args = res.group(2)
        result_tuple = (command, COMMAND_PARSERS[command](command_args))
    return result_tuple


def command_to_str(command, arguments):
    """
    Convert parsed descriptor command to a readable text representation.
    
    :param command:    ['L','C','S','A'] - see the uniprot documentation.
    :param arguments:    arguments object (usually tuple or string)
    
    :return: Formatted string with textual representation.
    """
    return COMMAND_STRING_CONVERTORS[command](arguments)


def process_descriptor_for_configfile(descriptor):
    """
    Process descriptors (which may include the descriptor commands) 
    and convert them to a readable form.
    
    :param descriptor:    descriptor string
    
    :return:    Formatted string for configfile comment.
    """
    res = parse_command(descriptor)
    if res:
        return command_to_str(*res)
    else:
        return descriptor
