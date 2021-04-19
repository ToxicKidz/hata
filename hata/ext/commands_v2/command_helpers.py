from re import compile as re_compile, escape as re_escape, M as re_multi_line, S as re_dotall, I as re_ignore_case, \
    match as re_match
from functools import partial as partial_func

from ...backend.utils import FunctionType
from ...backend.analyzer import CallableAnalyzer

from .utils import raw_name_to_display

SUB_COMMAND_NAME_RP = re_compile('([a-zA-Z0-9_\-]+)\S*')
COMMAND_NAME_RP = re_compile('[ \t\\n]*([^ \t\\n]*)[ \t\\n]*', re_multi_line|re_dotall)

async def run_checks(checks, command_context):
    """
    Runs the checks.
    
    This function is coroutine.
    
    Parameters
    ----------
    checks : `generator`
        A generator yielding checks.
    command_context : ``CommandContext``
        The respective command's context.
    
    Returns
    -------
    failed : `None` or ``CheckBase``
        The failed check if any.
    """
    for check in checks:
        if not await check(command_context):
            return check
    
    return None


async def handle_exception(error_handlers, command_context, exception):
    """
    Handles an exception raised meanwhile processing a command.
    
    This function is a coroutine.
    
    Parameters
    ----------
    error_handlers : `generator`
        A generator yielding error checks.
    command_context : ``CommandContext``
        The respective command context.
    exception : ``BaseException``
        The occurred exception.
    """
    for error_handler in error_handlers:
        result = await error_handler(command_context, exception)
        if isinstance(result, int) and result:
            break
    else:
        client = command_context.client
        await client.events.error(client, '_handle_exception', exception)


def get_sub_command_trace(command, content, index):
    """
    Gets the sub command trace and command function for the given command.
    
    Parameters
    ----------
    command : ``Command``
        The respective command.
    content : `str`
        A message's content to parse.
    index : `int`
        The starting index from where the content should be parsed from.
    
    Returns
    -------
    sub_command_trace : `None` or `tuple` of ``CommandCategory``
        Trace to the actual command.
    command_function : ``CommandFunction`` or `None`
        The command function, which should be called.
    index : `int`
        The index till the command's parameters may start from.
    """
    sub_commands = command._sub_commands
    if (sub_commands is not None):
        trace = []
        end = index
        while True:
            if end == len(content):
                break
            
            parsed = SUB_COMMAND_NAME_RP.match(content, end)
            if (parsed is None):
                break
            
            end = parsed.end()
            part = parsed.group(1)
            name = raw_name_to_display(part)
            
            try:
                sub_command = sub_commands[name]
            except KeyError:
                break
            
            trace.append((end, sub_command))
            
            sub_commands = sub_command._sub_commands
            if sub_commands is None:
                break
            
            continue
        
        while trace:
            end, sub_command = trace[-1]
            command_function = sub_command._command
            if (command_function is not None):
                return tuple(trace_element[1] for trace_element in trace), command_function, end
            
            del trace[-1]
            continue
    
    return None, command.command_function, index


def default_precheck(client, message):
    """
    Default check used by the command processor. Filters out every message what's author is a bot account and the
    channels where the client cannot send messages.
    
    Parameters
    ----------
    client : ``Client``
        The client who received the respective message.
    message : ``Message``
        The received message.
    
    Returns
    -------
    should_process : `bool`
    """
    if message.author.is_bot:
        return False
    
    if not message.channel.cached_permissions_for(client).can_send_messages:
        return False
    
    return True


def test_precheck(precheck):
    """
    Tests whether the given precheck accepts the expected amount of parameters.
    
    Parameters
    ----------
    precheck : `callable`
        A function, which decides whether a received message should be processed.
        
        The following parameters are passed to it:
        
        +-----------+---------------+
        | Name      | Type          |
        +===========+===============+
        | client    | ``Client``    |
        +-----------+---------------+
        | message   | ``Message``   |
        +-----------+---------------+
        
        Should return the following parameters:
        
        +-------------------+-----------+
        | Name              | Type      |
        +===================+===========+
        | should_process    | `bool`    |
        +-------------------+-----------+
    
    Raises
    ------
    TypeError
        - If `precheck` accepts bad amount of arguments.
        - If `precheck` is async.
    """
    analyzer = CallableAnalyzer(precheck)
    if analyzer.is_async():
        raise TypeError('`precheck` should not be given as `async` function.')
    
    min_, max_ = analyzer.get_non_reserved_positional_argument_range()
    if min_ > 2:
        raise TypeError(f'`precheck` should accept `2` arguments, meanwhile the given callable expects at '
            f'least `{min_!r}`, got `{precheck!r}`.')
    
    if min_ != 2:
        if max_ < 2:
            if not analyzer.accepts_args():
                raise TypeError(f'`precheck` should accept `2` arguments, meanwhile the given callable expects '
                    f'up to `{max_!r}`, got `{precheck!r}`.')


def test_error_handler(error_handler):
    """
    Tests whether the given precheck accepts the expected amount of parameters.
    
    Parameters
    ----------
    error_handler : `callable`
        A function, which handles an error and returns whether handled it.
        
        The following parameters are passed to it:
        
        +-------------------+-----------------------+
        | Name              | Type                  |
        +===================+=======================+
        | command_context   | ``CommandContext``    |
        +-------------------+-----------------------+
        | exception         | `BaseException`       |
        +-------------------+-----------------------+
        
        Should return the following parameters:
        
        +-------------------+-----------+
        | Name              | Type      |
        +===================+===========+
        | handled           | `bool`    |
        +-------------------+-----------+
    
    Raises
    ------
    TypeError
        - If `error_handler` accepts bad amount of arguments.
        - If `error_handler` is not async.
    """
    analyzer = CallableAnalyzer(error_handler)
    if not analyzer.is_async():
        raise TypeError('`error_handler` should be given as `async` function.')
    
    min_, max_ = analyzer.get_non_reserved_positional_argument_range()
    if min_ > 2:
        raise TypeError(f'`error_handler` should accept `2` arguments, meanwhile the given callable expects at '
            f'least `{min_!r}`, got `{error_handler!r}`.')
    
    if min_ != 2:
        if max_ < 2:
            if not analyzer.accepts_args():
                raise TypeError(f'`error_handler` should accept `2` arguments, meanwhile the given callable expects '
                    f'up to `{max_!r}`, got `{error_handler!r}`.')


def test_name_rule(rule, rule_name, nullable):
    """
    Tests the given name rule and raises if it do not passes any requirements.
    
    Parameters
    ----------
    rule : `None` or `function`
        The rule to test.
        
        A name rule should accept the following parameters:
        
        +-------+-------------------+
        | Name  | Type              |
        +=======+===================+
        | name  | `None` or `str`   |
        +-------+-------------------+
        
        Should return the following ones:
        
        +-------+-------------------+
        | Name  | Type              |
        +=======+===================+
        | name  | `str`             |
        +-------+-------------------+
    
    rule_name : `str`
        The name of the given rule.
    nullable : `bool`
        Whether `rule` should handle `None` input as well.
    
    Raises
    ------
    TypeError
        - If `rule` is not `None` or `function` instance.
        - If `rule` is `async` `function`.
        - If `rule` accepts bad amount of arguments.
        - If `rule` raised exception when `str` was passed to it.
        - If `rule` did not return `str`, when passing `str` to it.
        - If `nullable` is given as `True` and `rule` raised exception when `None` was passed to it.
        - If `nullable` is given as `True` and `rule` did not return `str`, when passing `None` to it.
    """
    if rule is None:
        return
    
    rule_type = rule.__class__
    if (rule_type is not FunctionType):
        raise TypeError(f'`{rule_name}` should have been given as `{FunctionType.__name__}`, got '
            f'{rule_type.__name__}.')
    
    analyzed = CallableAnalyzer(rule)
    if analyzed.is_async():
        raise TypeError(f'`{rule_name}` should have been given as an non async function, got {rule!r}.')
    
    non_reserved_positional_argument_count = analyzed.get_non_reserved_positional_argument_count()
    if non_reserved_positional_argument_count != 1:
        raise TypeError(f'`{rule_name}` should accept `1` non reserved positional arguments, meanwhile it expects '
            f'{non_reserved_positional_argument_count}.')
    
    if analyzed.accepts_args():
        raise TypeError(f'`{rule_name}` should accept not expect args, meanwhile it does.')
    
    if analyzed.accepts_kwargs():
        raise TypeError(f'`{rule_name}` should accept not expect kwargs, meanwhile it does.')
    
    non_default_keyword_only_argument_count = analyzed.get_non_default_keyword_only_argument_count()
    if non_default_keyword_only_argument_count:
        raise TypeError(f'`{rule_name}` should accept `0` keyword only arguments, meanwhile it expects '
            f'{non_default_keyword_only_argument_count}.')
    
    try:
        result = rule('test-this-name')
    except BaseException as err:
        raise TypeError(f'Got unexpected exception meanwhile testing the given {rule_name}: {rule!r}.') from err
    
    if (type(result) is not str):
        raise TypeError(f'{rule_name}: {rule!r} did not return `str` instance, meanwhile testing it, got '
            f'{result.__class__.__name__}')
    
    if not nullable:
        return
        
    try:
        result = rule(None)
    except BaseException as err:
        raise TypeError(f'Got unexpected exception meanwhile testing the given {rule_name}: {rule!r}.') from err
    
    if (type(result) is not str):
        raise TypeError(f'{rule_name}: {rule!r} did not return `str` instance, meanwhile testing it, got '
            f'{result.__class__.__name__}')


def validate_category_or_command_name(name):
    """
    Validates the given category name.
    
    Parameters
    ----------
    name : `str`
        The name of a category or command.
    
    Returns
    -------
    name : `str`
        The validated name.
    
    Raises
    ------
    TypeError
        If `name` was not given as `str` instance.
    ValueError
        If `name`'s length is out of range [1:128] characters.
    """
    name_type = type(name)
    if name_type is str:
        pass
    elif issubclass(name_type, str):
        name = str(name)
    else:
        raise TypeError(f'Category and command names can be given as `str` instance, got {name_type.__name__}.')
    
    name_length = len(name)
    if (name_length < 1) or (name_length > 128):
        raise ValueError(f'`Category and command name length can be in range [0:128], got {name_length};{name!r}.')
    
    return name


async def prefix_wrapper_async_callable(prefix_factory, re_flags, message):
    """
    Function to execute asynchronous callable prefix.
    
    This function is a coroutine.
    
    Parameters
    ----------
    prefix_factory : `async-callable`
        Async callable returning the prefix.
    re_flags : `int`
        Regex matching flags.
    message : ``Message``
        The received message to parse the prefix from.
    
    Returns
    -------
    prefix : `str` or `None`
        The prefix used by the user. Returned as `None` of parsing failed.
    end : `int`
        The start of the content after the prefix. Returned as `-1` if parsing failed.
    """
    prefix = await prefix_factory(message)
    if isinstance(prefix, str):
        escaped_prefix = re_escape(prefix)
    else:
        escaped_prefix = '|'.join(re_escape(prefix_part) for prefix_part in prefix)
    
    content = message.content
    parsed = re_match(escaped_prefix, content, re_flags)
    if parsed is None:
        prefix = None
        end = -1
    else:
        prefix = parsed.group(0)
        end = parsed.end()
    
    return prefix, end


async def prefix_wrapper_sync_callable(prefix_factory, re_flags, message):
    """
    Function to execute not asynchronous callable prefix.
    
    Parameters
    ----------
    prefix_factory : `async-callable`
        Async callable returning the prefix.
    re_flags : `int`
        Regex matching flags.
    message : ``Message``
        The received message to parse the prefix from.
    
    Returns
    -------
    prefix : `str` or `None`
        The prefix used by the user. Returned as `None` of parsing failed.
    end : `int`
        The start of the content after the prefix. Returned as `-1` if parsing failed.
    """
    prefix = prefix_factory(message)
    if isinstance(prefix, str):
        escaped_prefix = re_escape(prefix)
    else:
        escaped_prefix = '|'.join(re_escape(prefix_part) for prefix_part in prefix)
    
    content = message.content
    parsed = re_match(escaped_prefix, content, re_flags)
    if parsed is None:
        prefix = None
        end = -1
    else:
        prefix = parsed.group(0)
        end = parsed.end()
    
    return prefix, end

async def prefix_wrapper_regex(re_pattern, message):
    """
    Function to execute asynchronous callable prefix.
    
    This function is a coroutine.
    
    Parameters
    ----------
    re_pattern : `async-callable`
        Async callable returning the prefix.
    message : ``Message``
        The received message to parse the prefix from.
    
    Returns
    -------
    prefix : `str` or `None`
        The prefix used by the user. Returned as `None` of parsing failed.
    end : `int`
        The start of the content after the prefix. Returned as `-1` if parsing failed.
    """
    content = message.content
    parsed = re_pattern(content)
    if parsed is None:
        prefix = None
        end = -1
    else:
        prefix = parsed.group(0)
        end = parsed.end()
    
    return prefix, end


def validate_prefix(prefix, ignore_prefix_case):
    """
    Validates whether the given prefix is correct.
    
    prefix :  `str`, `tuple` of `str`, `callable`
        Prefix of the command processor.
        
        Can be given as a normal `callable` or as an `async-callable` as well, which should accept `1` parameter:
        
        +-------------------+---------------+
        | Name              | Type          |
        +===================+===============+
        | message           | ``Message``   |
        +-------------------+---------------+
        
        And return the following value:
        
        +-------------------+---------------------------+
        | Name              | Type                      |
        +===================+===========================+
        | prefix            | `str`, `tuple` of `str`   |
        +-------------------+---------------------------+
    
    Returns
    -------
    prefix : `Any`
        Async callable prefix.
    """
    if ignore_prefix_case:
        re_flags = re_ignore_case
    else:
        re_flags = 0
    
    re_flags |= re_multi_line|re_dotall
    
    if callable(prefix):
        analyzed = CallableAnalyzer(prefix)
        non_reserved_positional_argument_count = analyzed.get_non_reserved_positional_argument_count()
        if non_reserved_positional_argument_count != 1:
            raise TypeError(f'Callable `prefix` should accept `1` non reserved positional parameter, meanwhile it '
                f'accepts: `{non_reserved_positional_argument_count}`.')
        
        if analyzed.is_async():
            prefix_wrapper = prefix_wrapper_async_callable
        else:
            prefix_wrapper = prefix_wrapper_sync_callable
            
        return partial_func(prefix_wrapper, prefix, re_flags)
    
    else:
        if isinstance(prefix, str):
            escaped_prefix = re_escape(prefix)
        else:
            escaped_prefix = '|'.join(re_escape(prefix_part) for prefix_part in prefix)
        
        compiled_prefix = re_compile(escaped_prefix, re_flags)
        
        return partial_func(prefix_wrapper_regex, compiled_prefix)
