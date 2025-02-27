from pathlib import Path
import shutil
import os
import sys
import pwd
import warnings
from jinja2 import Environment, FileSystemLoader
from arbiter3.portal import arbiter, settings
from arbiter3.scripts import config_templates
import arbiter3.arbiter as arbiter_app


def get_username() -> str:
    try:
        uid = os.getuid()
        return pwd.getpwuid(uid).pw_name
    except:
        warnings.warn(
            "Unable to get current user, please update generated service file with desired user")
        return "CHANGEME"


def get_gunicorn_path() -> str:
    try:
        gunicorn_path = shutil.which("gunicorn")
        assert gunicorn_path
        return gunicorn_path
    except:
        path = Path(sys.executable).parent / 'gunicorn'
        warnings.warn(
            f"Unable to determine where gunicorn is. defaulting to '{path}'")
        return path


def initialize_config():
    interpreter_path = sys.executable
    current_path = Path(os.getcwd()).resolve()
    arbiter_ref_templates_dir = Path(arbiter_app.__file__).resolve().parent / "templates" / "arbiter"

    arbiter_conf_dir = current_path
    arbiter_templates_dir = current_path / "templates"
    os.makedirs(arbiter_conf_dir, exist_ok=True)
    os.makedirs(arbiter_templates_dir, exist_ok=True)

    # Target file destinations
    created_manage = arbiter_conf_dir / "arbiter.py"
    created_settings = arbiter_conf_dir / "settings.py"
    created_web_service = arbiter_conf_dir / "arbiter-web.service"
    created_eval_service = arbiter_conf_dir / "arbiter-eval.service"

    # Created email templates
    created_email_body = arbiter_templates_dir / "email_body.html"
    created_email_subject = arbiter_templates_dir / "email_subject.html"

    # using import for path here bc import lib has inconsistent output for the directory
    jinja_env = Environment(loader=FileSystemLoader(config_templates.__path__))

    # Config templates sources
    manage_template = arbiter.__file__
    settings_template = settings.__file__
    eval_service_template = jinja_env.get_template("arbiter-eval.service.jinja")
    web_service_template = jinja_env.get_template("arbiter-web.service.jinja")
    
    # Created email templates
    email_body_template = arbiter_ref_templates_dir / "email_body.html"
    email_subject_template = arbiter_ref_templates_dir / "email_subject.html"


    # Generate config files from source templates
    shutil.copy(manage_template, created_manage)
    os.chmod(created_manage, 0o744)
    print(f"Generated {created_manage}")

    shutil.copy(settings_template, created_settings)
    print(f"Generated {created_settings}")

    user = get_username()
    gunicorn_path = get_gunicorn_path()

    with open(created_eval_service, "w") as file:
        file.write(eval_service_template.render(
            working_dir=arbiter_conf_dir, user=user, python=interpreter_path))
        print(f"Generated {created_eval_service}")

    with open(created_web_service, "w") as file:
        file.write(web_service_template.render(
            working_dir=arbiter_conf_dir, user=user, gunicorn_path=gunicorn_path))
        print(f"Generated {created_web_service}")
    
    shutil.copy(email_body_template, created_email_body)
    print(f"Generated {created_email_body}")

    shutil.copy(email_subject_template, created_email_subject)
    print(f"Generated {created_email_subject}")


if __name__ == "__main__":
    initialize_config()
