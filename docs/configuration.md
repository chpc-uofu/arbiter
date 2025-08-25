# Configuration
Arbiter's policy and penalty configurations are stored as objects in its database. To configure policies, use the forms on on Arbiter's web-server.. This provides a basic CRUD interface for configuration as well as a way to view graphs for usage data.

## Configuration on Web
Before beginning this step, ensure web-server is started. If it is not, run `python3 arbiter.py runserver 0.0.0.0:8000` with your desired IP+port. Now that that is done, make sure you created an admin user for Arbiter's admin portal. If you have not, run `python3 arbiter.py createsuperuser` and give it the username/passcode when prompted. To add more users with less permissions see the [here](/docs/permissions.md).

Now that everything is set up, navigate to the site on (`localhost:8000/` if run locally). Here you can create your Base and Usage Policies. 
Here you can configure Arbiter's models. 

## Loading Default Fixtures
To begin, you can start by loading a fixture for our default policy.
```shell
./arbiter.py loaddata default_policy
```
This will load a new Usage Policy and Base Policy that are disabled by default and need to be activated to take effect, but can be used as a good starting point to get up and running.


## Data Models
Arbiter relies on the following models: 
- Policies (Base and Usage)
- Violations
- Targets

Violations and targets are created automatically by the core evaluation process. The usage limits are configured as part of the policy creation. 

## Policies
Policies are the rules users can violate. Policies use a Prometheus query to determine if a user is in violation. There are two type of policies, Base and Usage.

### Base Policies
These represent the CPU and memory limits you want to have applied to users at all times for a resource. The limits will be applied on first login and users will be reverted to these limits if their penalty expires.

- Name: A name for the policy. Must be Unique.

- Domain: Machines that this policy will apply to. Supports wildcards and conditionals, such as `.*\.site\.edu` or `node1\.site\.edu|node2\.site\.edu`. See some more examples and info  [here](/docs/regex.md).

- Description (optional): A text field that may be used to describe what the policy does. 

- Active: Whether or not this policy is active and is enforced.

- CPU Limit: The default limit in cores to apply to users.

- Memory Limit: The default limit in GiB to apply to users.

- User Whitelist (optional) : If this is non-empty, these users will not be evaluated. Format is a Prometheus regular expression, such as `user1|user2|user3`. See some more examples and info  [here](/docs/regex.md).


### Usage Policies
- Name: A name for the policy. Must be Unique.

- Domain: Machines that this policy will apply to. **MUST match the instance label shown in prometheus so if ports are present in the abel, as default, they might need to be in the domain regex as well**. Supports wildcards and conditionals, such as `.*\.site\.edu:2112` or `node1\.site\.edu:2112|node2\.site\.edu:2112`. See some more examples and info  [here](/docs/regex.md).

- Description (optional): A text field that may be used to describe what the policy does.

- Penalty Duration: The initial length of time the user will be in penalty when a this policy is violated.

- Repeated Offense Scalar: The value to multiply the initial penalty duration upon each subsequent violation created in the repeated offense lookback range. The duration is scaled as follows `base_duration + number_of_recent_violations * scalar`. So if set to `1.0`, the penalty duration will double the second violation and triple on the third.

- Repeated Offense Lookback: The window in which repeated violations increase the penalty duration times and upgrade the penalty constraints. Meaning that if set to 3 hours, upon violation arbiter will check how many violations this user had in the last 3 hours and scale the new penalty status duration accordingly.

- Grace Period: How long after a violation of this policy expires is the user immune to triggering another violation on this policy.

- Lookback: How far back arbiter looks at a user's usage to evaluate if the are in violation. For example, if set to 10 minutes, arbiter will look at a user's average usage over the last 10 minutes to determine if it is above the configured thresholds which triggers a violation.

    > ⚠️ Warning: Lookback should be <u> at least twice as long as your warden's scrape interval on prometheus</u>.

- Active: Whether or not this policy gets evaluated (Will watch for violations).

- Watcher Mode: If set, will not enforce limits, but will still report/email violations. Can be nice for first deploying/testing out arbiter or new policies.

- Penalty Constraints: The actual constraints to apply to a user upon a violation, in CPU cores and memory GiB. The order in which these are added is the order in which these will be applied for repeated violations. Useful for creating 'harsher' violations for repeated offenses. For example, if a user violates the same policy *x* amount of times in the *Repeated Offense Lookback*, they will receive the *x*-th tier of limits or the next highest tier if there are not *x* tiers configured. 

- Process Whitelist (optional) : A regex of process names that will not be counted as part of a user's usage. Format is a Prometheus regular expression, such as`sshd|squeue|ls|grep`. See some more examples and info  [here](/docs/regex.md).

- User Whitelist (optional) : A regex of usernames that are whitelisted (immune) from violating this policy. Format is a Prometheus regular expression, such as `user1|user2|user3`. See some more examples and info  [here](/docs/regex.md).

- CPU Threshold: The average number of cores a user must use during the lookback window to be in violation. 

- Memory Threshold: The average number of GiB a user must use during the lookback window to be in violation.
