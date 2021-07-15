from collections import defaultdict

from django import template
from django.conf import settings
from django.template.base import Node, NodeList, TemplateSyntaxError, TokenType
from django.template.library import parse_bits
from django.utils.safestring import mark_safe

from django_components.component import ACTIVE_SLOT_CONTEXT_KEY, registry, local_registry
from django_components.middleware import CSS_DEPENDENCY_PLACEHOLDER, JS_DEPENDENCY_PLACEHOLDER

from ..nodes.component_import_node import ComponentImportNode
from ..nodes.component_node import ComponentNode
from ..nodes.slot_node import SlotNode

register = template.Library()

def get_components_from_registry(registry):
    """Returns a list unique components from the registry."""

    unique_component_classes = set(registry.all().values())

    components = []
    for component_class in unique_component_classes:
        components.append(component_class(component_class.__name__))

    return components


# @register.simple_tag(name="component_dependencies")
# def component_dependencies_tag():
#     """Marks location where CSS link and JS script tags should be rendered."""

#     if is_dependency_middleware_active():
#         return mark_safe(CSS_DEPENDENCY_PLACEHOLDER + JS_DEPENDENCY_PLACEHOLDER)
#     else:
#         rendered_dependencies = []
#         for component in get_components_from_registry(local_registry):
#             rendered_dependencies.append(component.render_dependencies())

#         return mark_safe("\n".join(rendered_dependencies))


@register.simple_tag(name="component_css")
def component_css_dependencies_tag():
    """Marks location where CSS link tags should be rendered."""

    if is_dependency_middleware_active():
        return mark_safe(CSS_DEPENDENCY_PLACEHOLDER)
    else:
        rendered_dependencies = []
        for component in get_components_from_registry(local_registry):
            rendered_dependencies.append(component.render_css_dependencies())

        return mark_safe("\n".join(rendered_dependencies))


@register.simple_tag(name="component_js")
def component_js_dependencies_tag():
    """Marks location where JS script tags should be rendered."""

    if is_dependency_middleware_active():
        return mark_safe(JS_DEPENDENCY_PLACEHOLDER)
    else:
        rendered_dependencies = []
        for component in get_components_from_registry(local_registry):
            rendered_dependencies.append(component.render_js_dependencies())

        return mark_safe("\n".join(rendered_dependencies))


@register.tag(name='use')
def do_use(parser, token):
    bits = token.split_contents()
    # bits, isolated_context = check_for_isolated_context_keyword(bits)
    # print(bits, isolated_context)
    components = parse_use_components(parser, bits, 'use')
    
    # LOAD STATICS HERE
    for comp in components:
        if type(comp).__name__.lower() not in local_registry.all().keys():
            local_registry.register(type(comp).__name__.lower(), comp.__class__)

    return ComponentImportNode(
        f'<!-- Using {", ".join([type(comp).__name__.lower() for comp in components])} -->',
        components, 
    )


@register.tag(name='component')
def do_component(parser, token):
    bits = token.split_contents()
    bits, isolated_context = check_for_isolated_context_keyword(bits)
    component, context_args, context_kwargs = parse_component_with_args(parser, bits, 'component')

    print(component)

    return ComponentNode(component, context_args, context_kwargs, isolated_context=isolated_context)


@register.tag("slot")
def do_slot(parser, token, component=None):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' tag takes only one argument" % bits[0])

    slot_name = bits[1].strip('"')
    nodelist = parser.parse(parse_until=["endslot"])
    parser.delete_first_token()

    return SlotNode(slot_name, nodelist, component=component)


@register.tag("component_block")
def do_component_block(parser, token):
    """
    To give the component access to the template context:
        {% component_block "name" positional_arg keyword_arg=value ... %}

    To render the component in an isolated context:
        {% component_block "name" positional_arg keyword_arg=value ... only %}

    Positional and keyword arguments can be literals or template variables.
    The component name must be a single- or double-quotes string and must
    be either the first positional argument or, if there are no positional
    arguments, passed as 'name'.
    """

    bits = token.split_contents()
    bits, isolated_context = check_for_isolated_context_keyword(bits)

    component, context_args, context_kwargs = parse_component_with_args(parser, bits, 'component_block')

    return ComponentNode(component, context_args, context_kwargs,
                         slots=[do_slot(parser, slot_token, component=component)
                                for slot_token in slot_tokens(parser)],
                         isolated_context=isolated_context)


def slot_tokens(parser):
    """Yield each 'slot' token appearing before the next 'endcomponent_block' token.

    Raises TemplateSyntaxError if there are other content tokens or if there is no endcomponent_block token."""

    def is_whitespace(token):
        return token.token_type == TokenType.TEXT and not token.contents.strip()

    def is_block_tag(token, name):
        return token.token_type == TokenType.BLOCK and token.split_contents()[0] == name

    while True:
        try:
            token = parser.next_token()
        except IndexError:
            raise TemplateSyntaxError('Unclosed component_block tag')
        if is_block_tag(token, name='endcomponent_block'):
            return
        elif is_block_tag(token, name='slot'):
            yield token
        elif not is_whitespace(token) and token.token_type != TokenType.COMMENT:
            raise TemplateSyntaxError(f'Content tokens in component blocks must be inside of slot tags: {token}')


def check_for_isolated_context_keyword(bits):
    """Return True and strip the last word if token ends with 'only' keyword."""

    if bits[-1] == 'only':
        return bits[:-1], True
    return bits, False


def parse_component_with_args(parser, bits, tag_name):
    tag_args, tag_kwargs = parse_bits(
        parser=parser,
        bits=bits,
        params=["tag_name", "name"],
        takes_context=False,
        name=tag_name,
        varargs=True,
        varkw=[],
        defaults=None,
        kwonly=[],
        kwonly_defaults=None,
    )

    assert tag_name == tag_args[0].token, "Internal error: Expected tag_name to be {}, but it was {}".format(tag_name, tag_args[0].token)
    if len(tag_args) > 1:  # At least one position arg, so take the first as the component name
        component_name = tag_args[1].token
        context_args = tag_args[2:]
        context_kwargs = tag_kwargs
    else:  # No positional args, so look for component name as keyword arg
        try:
            component_name = tag_kwargs.pop('name').token
            context_args = []
            context_kwargs = tag_kwargs
        except IndexError:
            raise TemplateSyntaxError(
                "Call the '%s' tag with a component name as the first parameter" % tag_name
            )

    if not is_wrapped_in_quotes(component_name):
        raise TemplateSyntaxError(
            "Component name '%s' should be in quotes" % component_name
        )

    trimmed_component_name = component_name[1: -1]
    component_class = local_registry.get(trimmed_component_name)
        
    component = component_class(trimmed_component_name)

    return component, context_args, context_kwargs

def parse_use_components(parser, bits, tag_name):
    tag_args, tag_kwargs = parse_bits(
        parser=parser,
        bits=bits,
        params=["tag_name", "components"],
        takes_context=False,
        name=tag_name,
        varargs=True,
        varkw=[],
        defaults=None,
        kwonly=[],
        kwonly_defaults=None,
    )

    assert tag_name == tag_args[0].token, "Internal error: Expected tag_name to be {}, but it was {}".format(
        tag_name, tag_args[0].token)
    if len(tag_args) > 1:  # At least one position arg, so take the first as the component name
        components_names = [ tag_arg.token for tag_arg in tag_args[1:] ]

        for comp_name in components_names:

            if not is_wrapped_in_quotes(comp_name):
                raise TemplateSyntaxError(
                    "Component name '%s' should be in quotes" % comp_name
                )

        components_names = [ comp.replace('\'', '') for comp in components_names ]
        # context_args = tag_args[len(components_names):]
        # context_kwargs = tag_kwargs
    else:  # No positional args, so look for component name as keyword arg
        try:
            # SANITIZING
            components_names = tag_kwargs.pop('components').token.replace('\'', '') # REMOVE single commas
            components_names = [ comp.replace(' ', '') \
                                for comp in components_names.split(',') ] # PUTTING COMMAS AND REMOVING SPACES
            # context_args = []
            # context_kwargs = tag_kwargs
        except IndexError:
            raise TemplateSyntaxError(
                "Declaring the '%s' tag imples using 'components' key with multiples args wrapped in commas and separated by a comma" % tag_name
            )

    components = []
    for comp_name in components_names:
        # trimmed_component_name = comp_name[1: -1]
        component_class = registry.get(comp_name)
        components.append(component_class(comp_name))

    return components#, context_args, context_kwargs


def safe_resolve(context_item, context):
    """Resolve FilterExpressions and Variables in context if possible.  Return other items unchanged."""

    return context_item.resolve(context) if hasattr(context_item, 'resolve') else context_item


def is_wrapped_in_quotes(s):
    return s.startswith(('"', "'")) and s[0] == s[-1]


def is_dependency_middleware_active():
    return getattr(settings, "COMPONENTS", {}).get('RENDER_DEPENDENCIES', False)
