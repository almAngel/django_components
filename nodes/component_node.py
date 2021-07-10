from collections import defaultdict
from django.template.base import Node, NodeList, TemplateSyntaxError, TokenType
from django.conf import settings

class ComponentNode(Node):
    class InvalidSlot:
        def super(self):
            raise TemplateSyntaxError('slot.super may only be called within a {% slot %}/{% endslot %} block.')

    def __init__(self, component, context_args, context_kwargs, slots=None, isolated_context=False):
        self.context_args = context_args or []
        self.context_kwargs = context_kwargs or {}
        self.component, self.isolated_context = component, isolated_context

        # Group slot notes by name and concatenate their nodelists
        self.component.slots = defaultdict(NodeList)
        for slot in slots or []:
            self.component.slots[slot.name].extend(slot.nodelist)
        self.should_render_dependencies = self.is_dependency_middleware_active()

    def __repr__(self):
        return "<Component Node: %s. Contents: %r>" % (self.component,
                                                       getattr(self.component.instance_template, 'nodelist', None))

    def render(self, context):
        self.component.outer_context = context.flatten()

        # Resolve FilterExpressions and Variables that were passed as args to the component, then call component's
        # context method to get values to insert into the context
        resolved_context_args = [self.safe_resolve(arg, context) for arg in self.context_args]
        resolved_context_kwargs = {key: self.safe_resolve(kwarg, context) for key, kwarg in self.context_kwargs.items()}
        component_context = self.component.context(*resolved_context_args, **resolved_context_kwargs)

        # Create a fresh context if requested
        if self.isolated_context:
            context = context.new()

        with context.update(component_context):
            rendered_component = self.component.render(context)
            if self.should_render_dependencies:
                return f'<!-- _RENDERED {self.component._component_name} -->' + rendered_component
            else:
                return rendered_component

    def is_dependency_middleware_active(self):
        return getattr(settings, "COMPONENTS", {}).get('RENDER_DEPENDENCIES', False)

    def safe_resolve(self, context_item, context):
        """Resolve FilterExpressions and Variables in context if possible.  Return other items unchanged."""
        return context_item.resolve(context) if hasattr(context_item, 'resolve') else context_item
