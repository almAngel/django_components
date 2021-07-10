from django.template.base import Node, TemplateSyntaxError
from django_components.component import ACTIVE_SLOT_CONTEXT_KEY
from django.utils.safestring import mark_safe

class SlotNode(Node):
    def __init__(self, name, nodelist, component=None):
        self.name, self.nodelist, self.component = name, nodelist, component
        self.component = None
        self.parent_component = None
        self.context = None

    def __repr__(self):
        return "<Slot Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        # Thread safety: storing the context as a property of the cloned SlotNode without using
        # the render_context facility should be thread-safe, since each cloned_node
        # is only used for a single render.
        cloned_node = SlotNode(self.name, self.nodelist, self.component)
        cloned_node.parent_component = self.parent_component
        cloned_node.context = context

        with context.update({'slot': cloned_node}):
            return self.get_nodelist(context).render(context)

    def get_nodelist(self, context):
        if ACTIVE_SLOT_CONTEXT_KEY not in context:
            raise TemplateSyntaxError(f'Attempted to render SlotNode {self.name} outside of a parent Component or '
                                      'without access to context provided by its parent Component. This will not'
                                      'work properly.')

        overriding_nodelist = context[ACTIVE_SLOT_CONTEXT_KEY].get(self.name, None)
        return overriding_nodelist if overriding_nodelist is not None else self.nodelist

    def super(self):
        """Render default slot content."""
        return mark_safe(self.nodelist.render(self.context))
