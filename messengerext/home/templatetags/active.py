from django import template


def get_match_routes(match):
    if len(match.namespaces) == 0:
        return match.url_name

    routes = []
    for namespace in match.namespaces:
        routes.append(namespace+":"+match.url_name)
    return routes


def route_equals(a, b):
    if a == b:
        return True

    if a.endswith("*"):
        pattern = a[:-1]
        return b.startswith(pattern)

    return False


class IfActiveNode(template.Node):
    def __init__(self, nodelist, route):
        self.nodelist = nodelist
        self.route = route

    def render(self, context):
        if ":" in self.route:
            namespace, name = self.route.split(":")
            if name == "*":
                for ns in context.request.resolver_match.namespaces:
                    if ns == namespace:
                        return self.nodelist.render(context)

        for route in get_match_routes(context.request.resolver_match):
            if route_equals(self.route, route):
                return self.nodelist.render(context)

        return ""


def ifactive(parser, token):
    nodelist = parser.parse(('endifactive',))
    parser.delete_first_token()

    try:
        tag, route = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag required one argument" % token.contents.split()[0])

    return IfActiveNode(nodelist, route.strip('"\''))

register = template.Library()
register.tag('ifactive', ifactive)
