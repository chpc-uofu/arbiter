import shutil, os
from jinja2 import Template
from importlib.resources import files

def initialize_config():
    current_path = os.getcwd()
    arbiter_conf_dir = os.path.join(current_path, "arbiter")
    os.makedirs(arbiter_conf_dir, exist_ok=True)    

    created_manage = os.path.join(arbiter_conf_dir, "manage.py")
    created_settings = os.path.join(arbiter_conf_dir, "settings.py")
    created_base = os.path.join(arbiter_conf_dir, "base.py")
    created_config = os.path.join(arbiter_conf_dir, "config.toml")

    manage_template = str(files("arbiter3.portal.config_templates").joinpath("manage.py"))
    setting_template = str(files("arbiter3.portal.config_templates").joinpath("settings.py"))
    config_template = str(files("arbiter3.portal.config_templates").joinpath("config.toml"))
    base_template = str(files("arbiter3.portal.config_templates").joinpath("base.py"))


    eval_service_template = Template(str(files("arbiter3.portal.config_templates").joinpath("arbiter-eval.service.jinja")))
    web_service_template = Template(str(files("arbiter3.portal.config_templates").joinpath("arbiter-eval.service.jinja")))

    shutil.copy(manage_template, created_manage)
    print(f"Generated {created_manage}")

    shutil.copy(setting_template, created_settings)
    print(f"Generated {created_settings}")
    
    shutil.copy(base_template, created_base)
    print(f"Generated {created_base}")

    shutil.copy(config_template, created_config)
    print(f"Generated {created_config}")




def initialize_project():
    current_path = os.getcwd()
    arbiter_conf_dir = os.path.join(current_path, "arbiter")
    os.makedirs(arbiter_conf_dir, exist_ok=True)    

    created_manage = os.path.join(arbiter_conf_dir, "manage.py")
    created_settings = os.path.join(arbiter_conf_dir, "settings.py")
    created_config = os.path.join(arbiter_conf_dir, "config.toml")
    created_base = os.path.join(arbiter_conf_dir, "base.py")
    created_wsgi = os.path.join(arbiter_conf_dir, "wsgi.py")
    created_urls = os.path.join(arbiter_conf_dir, "urls.py")

    eval_service_template = Template(str(files("arbiter3.portal.config_templates").joinpath("arbiter-eval.service.jinja")))
    web_service_template = Template(str(files("arbiter3.portal.config_templates").joinpath("arbiter-eval.service.jinja")))
    config_template = str(files("arbiter3.portal.config_templates").joinpath("config.toml"))
    

    shutil.copy(manage.__file__, created_manage)
    print(f"Generated {created_manage}")

    shutil.copy(settings.__file__, created_settings)
    print(f"Generated {created_settings}")

    shutil.copy(settings.__file__, created_base)
    print(f"Generated {created_base}")

    shutil.copy(settings.__file__, created_wsgi)
    print(f"Generated {created_wsgi}")

    shutil.copy(settings.__file__, created_wsgi)
    print(f"Generated {created_wsgi}")

    shutil.copy(config_template, created_config)
    print(f"Generated {created_config}")

    eval_service_template.render()
    web_service_template.render()