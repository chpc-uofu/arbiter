# Configuration
Arbiter's policy and penalty configurations are stored as objects in its database. To configure policies, use the forms on on Arbiter's web-server.. This provides a basic CRUD interface for configuration as well as a way to view graphs for usage data.

## Configuration on Web
Before beginning this step, ensure web-server is started. If it is not, run `python3 arbiter.py runserver 0.0.0.0:8000` with your desired IP+port. Now that that is done, make sure you created an admin user for Arbiter's admin portal. If you have not, run `python3 arbiter.py createsuperuser` and give it the username/passcode when prompted.

Now that everything is set up, navigate to the site on (`localhost:8000/` if run locally). Here you can create your Base and Usage Policies. 
Here you can configure Arbiter's models. 

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
- Domain: Machines that this policy will apply to. Supports wildcards and conditionals, such as `node.*.site.edu` or `node1.site.edu | node2.site.edu`. 
- Description (optional): A text field that may be used to describe what the policy does.
- Penalty Duration: The initial length of time the user will be in penalty when a this policy is violated.
- Repeated Offense Scalar: The value to multiply the initial penalty duration upon each subsequent violation created in the repeateed offense lookback range.
- Repeated Offense Lookback: The window in which repeated violations increase the penalty duration times and upgrade the penalty constraints.
- Grace Period: How long after a violation expires to allow another to be created. 
- Lookback: The window at which to look at CPU and memory utilization violations. 
- Active: Whether or not this policy gets evaluated.
- Penalty Contraints: The actual constraints to apply to a user upon a violation, in CPU cores and memory GiB. The order in which these are added is the order in which these will be applied. Useful for creating 'harsher' violations for repeated offenses. 
- Query Process Whitelist (optional) : If this is non-empty, these processes will not be used in the violation evaluation. Format is a Prometheus regular expression, such as`sshd|squeue|ls|grep`
- Query User Whitelist (optional) : If this is non-empty, these users will not be evaluated. Format is a Prometheus regular expression, such as `user1|user2|user3`
- Query CPU Threshold: The average number of cores a user must use during the lookback window to be in violation.
- Query Memory Threshold: The average number of GiB a user must use during the lookback window to be in violation.
