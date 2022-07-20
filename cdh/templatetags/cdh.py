from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()





class TabNode(template.Node):
    def __init__(self, tab_list, name, selected=0, depth=0):
        self.tab_list = tab_list
        self.name = name
        self.selected = selected
        self.depth = depth

    def render_nav(self, num, item, context):
        active, selected = ("active", "true") if self.selected == num else ("", "false")
        nav_id = "{}_{}_{}_nav".format(self.name, self.depth, num)
        content_id = "{}_{}_{}_content".format(self.name, self.depth, num)
        return format_html(
            """
            <li class="nav-item" role="presentation">
            <button class="nav-link cdh-tab-button {}" id="{}" data-bs-toggle="tab" data-bs-target="#{}" type="button" role="tab" aria-controls="{}" aria-selected="{}">{}</button>
            </li>
            """,
            mark_safe(active),
            mark_safe(nav_id),
            mark_safe(content_id),
            mark_safe(content_id),
            mark_safe(selected),
            mark_safe(item.render(context))
        )

    def render_content(self, num, item, context):
        show, active, selected = ("show", "active", "true") if self.selected == num else ("", "", "false")
        nav_id = "{}_{}_{}_nav".format(self.name, self.depth, num)
        content_id = "{}_{}_{}_content".format(self.name, self.depth, num)        
        return format_html(
            """
            <div class="tab-pane fade {} {}" id="{}" role="tabpanel" aria-labelledby="{}">
            {}
            </div>
            """,
            mark_safe(show),
            mark_safe(active),
            mark_safe(content_id),
            mark_safe(nav_id),
            mark_safe(item.render(context))
        )

    def render_navs(self, items, context):
        return "\n".join([self.render_nav(i, nav, context) for i, nav in items])

        
    def render_contents(self, items, context):
        return "\n".join([self.render_content(i, content, context) for i, content in items])
    
    def render(self, context):
        #context["tab_depth"] = context.get("tab_depth", 0) + 1
        nav = format_html(
            """
            <ul class="nav nav-tabs cdh-nav-tabs" id="{}" role="tablist">
            {}
            </ul>
            """,
            mark_safe(self.name),
            mark_safe(self.render_navs([(i, n) for i, (n, _) in enumerate(self.tab_list)], context))
        )
        content = format_html(
            """
            <div class="tab-content" id="{}_content">
            {}
            </div>
            """,
            mark_safe(self.name),
            mark_safe(self.render_contents([(i, c) for i, (_, c) in enumerate(self.tab_list)], context))
        )
                          
        return format_html("{}\n{}", nav, content)

@register.tag("tabs")
def tabs(parser, token):
    _, name = token.split_contents()
    parser.parse(('tabnav', 'endtabs'))
    tab_list = []
    token = parser.next_token()
    while not token.contents.startswith("endtabs"):
        nav = parser.parse(("tabcontent",))
        token = parser.next_token()
        content = parser.parse(("tabnav", "endtabs",))
        token = parser.next_token()
        tab_list.append((nav, content))
    return TabNode(tab_list, name)

def vega(parser, token):
    pass
