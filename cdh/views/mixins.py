from cdh.models import User
from django.contrib.auth.models import Group


class PermissionsMixin(object):

    def get_context_data(self, *argv, **argd):
        ctx = {}
        if self.buttons:
            ctx["buttons"] = self.buttons
        elif self.can_create and self.request.user.username != "AnonymousUser":
            ctx["buttons"] = [
                {
                    "label" : "Create",
                    "style" : "primary",
                    "hx_swap" : "inner",
                    "hx_post" : self.request.path_info,
                    "hx_target" : "closest .cdh-accordion-collapse"
                }
            ]
        else:
            ctx["buttons"] = []
            if self.can_update and "change" in self.obj_perms:
                ctx["buttons"].append(
                    {
                        "label" : "Save",
                        "style" : "primary",
                        "hx_target" : "closest .cdh-accordion-collapse",
                        ###"hx_target" : "#{}".format(self.uid),
                        "hx_swap" : "inner",
                        "hx_post" : self.request.path_info,
                    }                    
                )
                ctx["user_permissions_options"] = [(u, [p.split("_")[0] for p in self.user_perms.get(u, [])]) for u in User.objects.all()]
                ctx["group_permissions_options"] = [(g, [p.split("_")[0] for p in self.group_perms.get(g, [])]) for g in Group.objects.all()]
                ctx["perms"] = ["delete", "view", "change"]
            if self.can_delete and "delete" in self.obj_perms:
                ctx["buttons"].append(
                    {
                        "label" : "Delete",
                        "style" : "danger",
                        "hx_confirm" : "Are you sure you want to delete this object and any others derived from it?",
                        ###"hx_target" : "#{}".format(self.uid),
                        "hx_swap" : "none",
                        "hx_delete" : self.request.path_info,
                    }
                )
        return ctx


class NestedMixin(object):

    def __init__(self, *argv, **argd):
        super(NestedMixin, self).__init__(*argv, **argd)

    def get_context_data(self, *argv, **argd):
        return {"uid" : self.request.GET.get("uid", self.request.POST.get("uid", "0"))}
