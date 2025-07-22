# Configuration
Arbiter's policy and penalty configurations are stored as objects in its database. To configure policies, use the forms on on Arbiter's web-server.. This provides a basic CRUD interface for configuration as well as a way to view graphs for usage data.

## Configuration on Web
Before beginning this step, ensure web-server is started. If it is not, run `python3 arbiter.py runserver 0.0.0.0:8000` with your desired IP+port. Now that that is done, make sure you created an admin user for Arbiter's admin portal. If you have not, run `python3 arbiter.py createsuperuser` and give it the username/passcode when prompted.

Now that everything is set up, navigate to the site on (`localhost:8000/` if run locally). Here you can create your Base and Usage Policies. 
Here you can configure Arbiter's models. 

## Loading Default Fixtures
To begin, you can start by loading a fixture for our default policy.
```shell
./arbiter.py loaddata default_policy
```
This will load a new Policy 


## Data Models
Arbiter relies on the following models: 
- Policies (Base and Usage)
- Violations
- Targets

Violations and targets are created automatically by the core evaluation process. Limits are configured as part of the policy creation. 

### Policies
Policies are the rules users can violate. Policies use a Prometheus query to determine if a user is in violation. There are two type of policies, Base and Usage.

#### Base Policies
These represent the CPU and memory limits you want to have applied to users at all times for a resource. 
- Name: A name for the policy. Must be Unique.
- Domain: Machines that this policy will apply to. Supports wildcards and conditionals, such as `node.*.site.edu` or `node1.site.edu | node2.site.edu`. 
- Description (optional): A text field that may be used to describe what the policy does. 
- CPU Limit: The default limit in cores to apply to users.
- Memory Limit: The default limit in GiB to apply to users.

#### Usage Policies
- Name: A name for the policy. Must be Unique.
- Domain: Machines that this policy will apply to. **MUST match the instance label shown in prometheus so if ports are present in the abel, as default, they might need to be in the domain regex as well**. Supports wildcards and conditionals, such as `.*\.site\.edu:2112` or `node1\.site\.edu:2112|node2\.site\.edu:2112`. See some more examples and info  [down here](#regex).
- Description (optional): A text field that may be used to describe what the policy does.
- Penalty Duration: The initial length of time the user will be in penalty when a this policy is violated.
- Repeated Offense Scalar: The value to multiply the initial penalty duration upon each subsequent violation created in the repeated offense lookback range.
- Repeated Offense Lookback: The window in which repeated violations increase the penalty duration times and upgrade the penalty constraints.
- Grace Period: How long after a violation expires to allow another to be created. 
- Lookback: The window at which to look at CPU and memory utilization violations. 
- Active: Whether or not this policy gets evaluated.
- Penalty Constraints: The actual constraints to apply to a user upon a violation, in CPU cores and memory GiB. The order in which these are added is the order in which these will be applied. Useful for creating 'harsher' violations for repeated offenses. 
- Query Process Whitelist (optional) : If this is non-empty, these processes will not be used in the violation evaluation. Format is a Prometheus regular expression, such as`sshd|squeue|ls|grep`. See some more examples and info  [down here](#regex).
- Query User Whitelist (optional) : If this is non-empty, these users will not be evaluated. Format is a Prometheus regular expression, such as `user1|user2|user3`. See some more examples and info  [down here](#regex).
- Query CPU Threshold: The average number of cores a user must use during the lookback window to be in violation. 
- Query Memory Threshold: The average number of GiB a user must use during the lookback window to be in violation.


## Regex:

Options like domain or the user/process whitelists on policies follow the regex syntax used by prometheus ([RE2](https://github.com/google/re2/wiki/syntax)), meaning `.` is a wild card, `|` represents an `or` and that `*` and `+` mean zero or more and one or more respectively. 

For example, if you wanted a domain that matched on `node1.site.edu` and `node2.site.edu` on port 2112, you could use one of the following:
- `node(1|2)\.site\.edu:2112` if you want to match on specific number nodes with similar host names
- `(node1\.site\.edu|node2\.differentsite\.edu):2112` if you want to match on multiple hosts that might have more different host names.
- `node\d+\.site\.edu` if you wanted it to match for any number node on `site.edu`.
- `(node\d+\.site\.edu|node\d+\.differentsite\.edu):2112` if you want to match on any number node on multiple sites.

> Note since you likely won't have multiple wardens on the same host with different ports, feel free to replace the `:2112` with `:\d+` to match on any port. Also if you have prometheus configured to strip ports on the labels, they will need to be removed from the regex, or made optional like `host.name(:2112)?`

If you simply want the policy to apply the policy on **all** hosts with a warden your prometheus has registered, you should use `.*` as the domain.

Similarly, for the whitelists we often use a list of process/user names seperated with `|` such as `vi|emacs|vim|nano` or `user1|user2|user3`.
> ⚠️ Note that some special characters may need to be escaped with `\`, such as if you wanted to whitelist the `g++` compiler you would need to escape the plus symbols `g\+\+`.
