import logging
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm, get_anonymous_user
from cdh import settings
from cdh.models import User, Slide
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group
from schedule.models.events import Event, Calendar
from primary_sources.models import PrimarySource


if settings.USE_LDAP:
    import ldap
    from ldap import modlist


logging.basicConfig(level=logging.INFO)


groups = [
    {
        "gid" : settings.CDH_LDAP_WORKSTATION_GROUP,
    },
    {
        "gid" : settings.CDH_LDAP_WORKSTATION_ADMIN_GROUP,
    },    
    {
        "gid" : settings.CDH_LDAP_WEB_GROUP,
    },
    {
        "gid" : settings.CDH_LDAP_WEB_ADMIN_GROUP,
    },
    {"gid" : "faculty"},
    {"gid" : "postdoc"},
    {"gid" : "student"},
    {"gid" : "director"},
]

users= [
    {
        "first_name" : "First",
        "last_name" : "User",            
        "email" : "user1@cdh.jhu.edu",
        "username" : "user1",
        "password" : "user",
        "superuser" : True,
        "description" : "An example user in the faculty group",
        "groups" : [settings.CDH_LDAP_WEB_GROUP, settings.CDH_LDAP_WEB_ADMIN_GROUP, "faculty"],
    },
    {
        "first_name" : "Second",
        "last_name" : "User",            
        "email" : "user2@cdh.jhu.edu",
        "username" : "user2",            
        "password" : "user",
        "description" : "An example user in the post-doctoral group",
        "groups" : [settings.CDH_LDAP_WEB_GROUP, "postdoc"],
    },
    {
        "first_name" : "Third",
        "last_name" : "User",            
        "email" : "user3@cdh.jhu.edu",
        "username" : "user3",            
        "password" : "user",
        "description" : "An example user in the student group",
        "groups" : [settings.CDH_LDAP_WEB_GROUP, "student"],
    },
]

spec = {
    Slide : [
        {
            "name" : "First example news item",
            "article" : "## Something A",
        },
        {
            "name" : "Second example news item",
            "article" : "## Something B",
        },
        {
            "name" : "Third example news item",
            "article" : "## Something C",
        },
        {
            "name" : "Fourth example news item",
            "article" : "## Something D",
        },
        {
            "name" : "Fifth example news item",
            "article" : "## Something E",
        },
        {
            "name" : "First research area",
            "article" : "# Test 1",
        },
        {
            "name" : "Second research area",
            "article" : "# Test 2",
        },
    ],
    #Calendar : [
    #    {
    #        "name" : "CDH",
    #        "slug" : "CDH",
    #    },
    #],
#     SlidePage : [
#         {
#             "name" : "index",
#             "additional_link_prompt" : "See more news from the CDH",
#             ("slides", Slide) : [
#                 {"name" : "First example news item"},
#                 {"name" : "Second example news item"},
#                 {"name" : "Third example news item"},
#                 {"name" : "Fifth example news item"},
                
#             ]
#         },
#         {
#             "name" : "research",
#             "content" : """
# ### Markdown content can go here
# """,
#             ("slides", Slide) : [
#                 {"name" : "First research area"},
#                 {"name" : "Second research area"}
#             ],
#         },

#     ],
    # Organization : [
    #     {
    #         "name" : "Alexander Grass Humanities Institute",
    #         "link" : "https://krieger.jhu.edu/humanities-institute",
    #     },
    #     {
    #         "name" : "Sheridan Library Data Services",
    #         "link" : "https://dataservices.library.jhu.edu/"
    #     },
    #     {
    #         "name" : "Center for Language and Speech Processing",
    #         "link" : "https://clsp.jhu.edu/",
    #     },
    # ],
    # Research : [
    #     {
    #         "name" : "An unsupervised neural framework for multi-modal literary and historical scholarship",
    #         "article" : "",
    #     },
    #     {
    #         "name" : "Data-driven AI models for Document Analysis in Medicine, Social Sciences, and the Humanities",
    #         "article" : "",
    #     },
    # ],
    Event : [
    ],
    # Software : [
    #     {
    #         "name" : "StarCoder",
    #         "article" : "A machine learning framework that provides an API between neural architectures and structured, semantically-annotated data.",
    #         "link" : "https://github.com/starcoder/starcoder-python",
    #     },
    # ],
    PrimarySource : [
    ]
}


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true", default=False)
        parser.add_argument("--prod", action="store_true", default=False)
    
    def handle(*args, **options):
        
        if settings.USE_LDAP and not args.prod:
            ld = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
            if ldap.get_option(ldap.OPT_X_TLS_REQUIRE_CERT) == ldap.OPT_X_TLS_DEMAND:
                if settings.AUTH_LDAP_START_TLS:
                    ld.start_tls_s()
                ld.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
            else:
                ld.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)            


            current_users = {}
            for dn, attrs in ld.search_st(settings.CDH_LDAP_GROUP_BASE, ldap.SCOPE_SUBTREE, filterstr="(&(!(objectClass=organizationalUnit))(!(objectClass=posixGroup)))"):
                if dn != settings.CDH_LDAP_ROOT_BASE:
                    if options["wipe"]:
                        ld.delete_s(dn)
                        logging.info("deleted %s", dn)
                    else:
                        current_users[attrs["uid"][0]] = (dn, attrs)
            logging.info("Current users: %s", current_users)

            current_groups = {}
            for dn, attrs in ld.search_st(settings.CDH_LDAP_GROUP_BASE, ldap.SCOPE_SUBTREE, filterstr="(objectClass=posixGroup)"):        
                if options["wipe"]:
                    ld.delete_s(dn)
                    logging.info("deleted %s", dn)
                else:
                    current_groups[attrs["cn"][0]] = (dn, attrs)
            logging.info("Current groups: %s", current_groups)

            current_ous = {}
            for dn, attrs in ld.search_st(settings.CDH_LDAP_ROOT_BASE, ldap.SCOPE_SUBTREE, filterstr="(objectClass=organizationalUnit)"):
                if options["wipe"]:
                    ld.delete_s(dn)
                    logging.info("deleted %s", dn)
                else:
                    current_ous[attrs["ou"][0]] = (dn, attrs)
            logging.info("Current ous: %s", current_ous)


            for ou in [settings.CDH_LDAP_USER_BASE, settings.CDH_LDAP_GROUP_BASE]:
                if bytes(ou, "utf-8") not in current_ous and ou.startswith("ou="):
                    item = {
                        "objectClass" : [b"organizationalUnit"],
                        "ou" : [bytes(ou, "utf-8")]
                    }
                    ld.add_s(ou, modlist.addModlist(item))
                    logging.info("added %s", ou)

            next_gid_number = max([2000] + [int(x[1]["gidNumber"][0]) for x in current_groups.values()]) + 1
            user_gid_number = current_groups.get(bytes(settings.CDH_LDAP_WEB_GROUP, "utf-8"), (None, {}))[1].get("gidNumber", [None])[0]
            for group in groups:
                if bytes(group["gid"], "utf-8") not in current_groups:
                    dn = "cn={},{}".format(group["gid"], settings.CDH_LDAP_GROUP_BASE)
                    if group["gid"] == settings.CDH_LDAP_WEB_GROUP:
                        user_gid_number = bytes(str(next_gid_number), "utf-8")
                    group = {k : bytes(v, "utf-8") if isinstance(v, str) else v for k, v in group.items()}
                    item = {
                        "objectClass" : [b"posixGroup"],
                        "gidNumber" : [bytes(str(next_gid_number), "utf-8")],
                    }            
                    next_gid_number += 1
                    ld.add_s(dn, modlist.addModlist(item))
                    logging.info("added %s", dn)

            next_uid_number = max([2000] + [int(x[1]["uidNumber"][0]) for x in current_users.values()]) + 1
            for user in users:
                if bytes(user["username"], "utf-8") not in current_users:
                    dn = "uid={},{}".format(user["username"], settings.CDH_LDAP_USER_BASE)
                    home = bytes("/home/{}".format(user["username"]), "utf-8")
                    user = {k : bytes(v, "utf-8") if isinstance(v, str) else v for k, v in user.items()}
                    uid_number = bytes(str(next_uid_number), "utf-8")
                    next_uid_number += 1
                    item = {
                        "objectClass" : [b"inetOrgPerson", b"posixAccount", b"shadowAccount"],
                        "mail" : user["email"],
                        "sn" : [user["last_name"]],
                        "givenName" : [user["first_name"]],
                        "uid" : [user["username"]],
                        "cn" : [user["username"]],
                        "uidNumber" : [uid_number],
                        "gidNumber" : [b"100"],
                        "loginShell" : [b"/bin/bash"],
                        "homeDirectory" : [home],
                        "gecos" : [user["username"]],
                    }
                    ld.add_s(dn, modlist.addModlist(item))
                    logging.info("added %s", dn)
                    ld.passwd_s(dn, None, user["password"])
                    for gname in user["groups"]:
                        dn = "cn={},{}".format(gname, settings.CDH_LDAP_GROUP_BASE)
                        old = ld.search_st(dn, ldap.SCOPE_SUBTREE, filterstr="(objectClass=posixGroup)")[0][1]
                        new = {k : v for k, v in old.items()}
                        new["memberuid"] = new.get("memberuid", []) + [user["username"]]
                        mod = ldap.modlist.modifyModlist(old, new)
                        ld.modify_s(dn, mod)
        else:
            if options["wipe"]:
                logging.info("Removing existing users and groups")                
                [u.delete() for u in User.objects.all() if u.username != "AnonymousUser"]
                Group.objects.all().delete()
            for group in groups:
                g = Group.objects.create(name=group["gid"])
                g.save()
        for user in users:
            us = User.objects.filter(username=user["username"])            
            u = us[0] if len(us) == 1 else User.objects.create(**{k : v for k, v in user.items() if k not in ["groups", "password", "superuser"]})
            if not settings.USE_LDAP:
                u.set_password(user["password"])
                for gname in user["groups"]:
                    g = Group.objects.get(name=gname)
                    u.groups.add(g)
            u.is_superuser = user.get("superuser", False)
            u.is_staff = user.get("superuser", False)
            u.save()
            assign_perm("cdh.view_user", get_anonymous_user(), u)
            assign_perm("cdh.change_user", u, u)
        user = User.objects.get(is_superuser=True)
        for et, es in spec.items():
            logging.info("Adding objects of type '%s'", et)
            if options["wipe"]:
                logging.info("First removing existing objects...")
                et.objects.all().delete()
            for e in es:
                e["created_by"] = user
                obj = et.objects.create(**{k : v[0].objects.filter(**{v[1] : v[2]})[0] if isinstance(v, tuple) else v for k, v in e.items() if k != "password" and not isinstance(v, (set, list))})
                for (field, otype), filters in [x for x in e.items() if isinstance(x[1], list)]:
                    for filt in filters:
                        other = otype.objects.get(**filt)
                        getattr(obj, field).add(other)
                for (field, otype), filters in [x for x in e.items() if isinstance(x[1], set)]:
                    pass
from wiki.models import URLPath, Article, ArticleRevision, ArticleForObject

ArticleForObject.objects.all().delete()
ArticleRevision.objects.all().delete()
Article.objects.all().delete()

root = URLPath.create_root(
    title="CDH documentation and tutorials",
    content="""
[article_list]
""",
)

root.save()
