from .comment_node import CommentNode

class ComponentImportNode(CommentNode):
    def __init__(self, comment, using_components):
        self.using_components = [type(comp).__name__.lower() for comp in using_components]
        self.comment = comment

    def render(self, context):
        return self.comment