from django import template


class IfRoleNode(template.Node):
    def __init__(self, nodelist, role):
        self.nodelist = nodelist
        self.role = role

    def render(self, context):
        user = context.request.user
        group = context["group"]

        if group.has_role(user, self.role):
            return self.nodelist.render(context)

        return ""


def ifrole(parser, token):
    nodelist = parser.parse(('endifrole',))
    parser.delete_first_token()

    try:
        tag, route = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag required one argument" % token.contents.split()[0])

    return IfRoleNode(nodelist, route.strip('"\''))

register = template.Library()
register.tag('ifrole', ifrole)
