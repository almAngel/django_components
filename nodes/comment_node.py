from django.template.base import Node

class CommentNode(Node):
    def __init__(self, comment):
        self.comment = comment

    def render(self, context):
        return self.comment