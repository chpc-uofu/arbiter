import shutil, os, sys
from jinja2 import Template, Environment, FileSystemLoader
from importlib.resources import files

def initialize_config():
    interpreter_path = sys.executable
    current_path = os.getcwd()
    config_template_dir = files("arbiter3.scripts.config_templates")
    arbiter_conf_dir = os.path.join(current_path, "arbiter") 
    os.makedirs(arbiter_conf_dir, exist_ok=True)    

    # Target file destinations
    created_manage = os.path.join(arbiter_conf_dir, "manage.py")
    created_settings = os.path.join(arbiter_conf_dir, "settings.py")
    created_base = os.path.join(arbiter_conf_dir, "base.py")
    created_config = os.path.join(arbiter_conf_dir, "config.toml")
    created_web_service = os.path.join(arbiter_conf_dir, "arbiter-web.service")
    created_eval_service = os.path.join(arbiter_conf_dir, "arbiter-eval.service")


    #for whatever reason despite outputing the same type, the config template str does not output the path unless joined with ""
    jinja_env = Environment(loader=FileSystemLoader(str(config_template_dir.joinpath(""))))

    # Config templates sources
    manage_template = str(config_template_dir.joinpath("manage.py"))
    setting_template = str(config_template_dir.joinpath("settings.py"))
    config_template = str(config_template_dir.joinpath("config.toml"))
    base_template = str(config_template_dir.joinpath("base.py"))
    eval_service_template = jinja_env.get_template("arbiter-eval.service.jinja")
    web_service_template = jinja_env.get_template("arbiter-web.service.jinja")

    #Generate config files from source templates

    shutil.copy(manage_template, created_manage)
    os.chmod(created_manage, 0o744)
    print(f"Generated {created_manage}")

    shutil.copy(setting_template, created_settings)
    print(f"Generated {created_settings}")
    
    shutil.copy(base_template, created_base)
    print(f"Generated {created_base}")

    shutil.copy(config_template, created_config)
    print(f"Generated {created_config}")

    with open(created_eval_service, "w") as file:
        file.write(eval_service_template.render(working_dir=str(arbiter_conf_dir)))
        print(f"Generated {created_eval_service}")

    with open(created_web_service, "w") as file:
        file.write(web_service_template.render(working_dir=arbiter_conf_dir))
        print(f"Generated {created_web_service}")

    