# Updating Arbiter

## Versioning

Arbiter is released using [semantic versioning](https://semver.org/) ([major].[minor].[release]).

## Update Process
1. Fetch updates from Github
```shell
git pull
```

2. Activate virtual enviroment (set up during install)
```shell
source venv/bin/activate
```

5. Update Arbiter and its dependencies
```shell
pip install .
```

4. Run migrations
```shell
./manage.py migrate
```

5. Restart services
```shell
systemctl restart arbiter-web.service
systemctl restart arbiter-eval.service
```