from pathlib import Path
import shutil, os, sys, pwd, warnings
from jinja2 import Environment, FileSystemLoader
from arbiter3.portal import arbiter, settings
from arbiter3.scripts import config_templates


def get_username() -> str : 
    try:
        uid = os.getuid()
        return pwd.getpwuid(uid).pw_name
    except:
        warnings.warn("Unable to get current user, please update generated service file with desired user")
        return "CHANGEME"
    
def get_gunicorn_path() -> str:
    try:
        gunicorn_path = shutil.which("gunicorn")
        assert gunicorn_path
        return gunicorn_path
    except:
        path = Path(sys.executable).parent / 'gunicorn'
        warnings.warn(f"Unable to determine where gunicorn is. defaulting to '{path}'")
        return path

def initialize_config():
    interpreter_path = sys.executable
    current_path = os.getcwd()
    arbiter_conf_dir = current_path
    os.makedirs(arbiter_conf_dir, exist_ok=True)    

    # Target file destinations
    created_manage = os.path.join(arbiter_conf_dir, "arbiter.py")
    created_settings = os.path.join(arbiter_conf_dir, "settings.py")
    created_web_service = os.path.join(arbiter_conf_dir, "arbiter-web.service")
    created_eval_service = os.path.join(arbiter_conf_dir, "arbiter-eval.service")


    #using import for path here bc import lib has inconsistent output for the directory
    jinja_env = Environment(loader=FileSystemLoader(config_templates.__path__))

    # Config templates sources
    manage_template = arbiter.__file__
    setting_template = settings.__file__
    eval_service_template = jinja_env.get_template("arbiter-eval.service.jinja")
    web_service_template = jinja_env.get_template("arbiter-web.service.jinja")

    #Generate config files from source templates
    
    shutil.copy(manage_template, created_manage)
    os.chmod(created_manage, 0o744)
    print(f"Generated {created_manage}")

    shutil.copy(setting_template, created_settings)
    print(f"Generated {created_settings}")

    user = get_username()
    gunicorn_path = get_gunicorn_path()

    with open(created_eval_service, "w") as file:
        file.write(eval_service_template.render(working_dir=arbiter_conf_dir, user=user, python = interpreter_path))
        print(f"Generated {created_eval_service}")

    with open(created_web_service, "w") as file:
        file.write(web_service_template.render(working_dir=arbiter_conf_dir, user=user, gunicorn_path=gunicorn_path))
        print(f"Generated {created_web_service}")


if __name__ == "__main__":
    initialize_config()