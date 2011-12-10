# coding: utf-8                                                                                                                                                                                  
import pkg_resources
import starflyer
import pymongo
import os

from jinja2 import Environment, PackageLoader, PrefixLoader

import handlers


def setup(**kw):
    """initialize the setup"""
    config = starflyer.Configuration()
    config.register_sections('dbs')
    config.register_template_chains('main')
    config.update_settings({
        'virtual_path' : "/",
        'dbname' : "haushalt",
        'logname' : "haushalt",
        'cookie_secret' : "gcsizcscs6c87c6zw5478v8r5zt984ur",
    })
    config.update_settings(kw)

    # setup static paths
    vpath = config.settings.virtual_path
    static_file_path = pkg_resources.resource_filename(__name__, 'static')
    config.register_static_path(vpath+"/css", os.path.join(static_file_path, 'css'))
    config.register_static_path(vpath+"/js", os.path.join(static_file_path, 'js'))
    config.register_static_path(vpath+"/img", os.path.join(static_file_path, 'img'))

    # setup templates
    config.templates.main.append(PackageLoader("haushalt.web","templates"))

    # paths
    config.routes.extend([
        ('/', 'homepage', handlers.Homepage),
        ('/vorschlaege', 'proposals', handlers.Proposals),
        ('/impressum', 'impressum', handlers.Impressum),
        ('/vorschlaege/<vid>', 'proposal', handlers.Proposal),
    ])
    config.dbs.haushalt = pymongo.Connection().haushalt
    return config

