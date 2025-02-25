# Updating Arbiter

## Versioning

Arbiter is released using [semantic versioning](https://semver.org/) ([major].[minor].[release]).

## Update Process for Pip Installation
1. Activate virtual environment (set up during install)
```shell
source venv/bin/activate
```
2. Upgrade arbiter package
```shell
pip install arbiter3 --upgrade
```

4. Run migrations
```shell
./arbiter.py migrate
```

5. Restart services
```shell
systemctl restart arbiter-web.service
systemctl restart arbiter-eval.service
```

## Update Process for Git Installation
1. Fetch updates from Github
```shell
git pull
```

2. Activate virtual environment (set up during install)
```shell
source venv/bin/activate
```

3. Update Arbiter and its dependencies
```shell
pip install .
```

4. Run migrations
```shell
./arbiter.py migrate
```

5. Restart services
```shell
systemctl restart arbiter-web.service
systemctl restart arbiter-eval.service
```