# Configuration
Arbiter's policy and penalty configurations are stored as objects in its database. To configure policies, use the forms on on Arbiter's web-server.. This provides a basic CRUD interface for configuration as well as a way to view graphs for usage data.

## Configuration on Web
Before begining this step, ensure web-server is started. If it is not, run `python3 manage.py runserver 0.0.0.0:8000` with your desired IP+port. Now that that is done, make sure you created an admin user for Arbiter's admin portal. If you have not, run `python3 manage.py createsuperuser` and give it the username/passcode when prompted.

Now that everything is set up, navigate to the site on (`localhost:8000/` if run locally). Here you can create your Base and Usage Policies. 
Here you can configure Arbiter's models. 

## Data Models
Arbiter relies on the following models: 
- Limits
- Policies (Base and Usage)
- Violations
- Targets

Violations and targets are created automatically by the core evaluation process. Limits are configured as part of the policy creation. 

### Limits
Limits represent a value for the systemd properties `CPUQuotaPerSecUSec` and `MemoryMax` that can be applied to a user slice. These are created when policies are configured. 

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
- CPU Limit: The limit in cores to apply to users when this policy is violated.
- Memory Limit: The limit in GiB to apply to users when this policy is violated.
- Lookback: The length of time in which Arbiter will look at a users usage to determine if they are in violation. 
- Duration: The length of time the user will have the limits when this policy is violated.
- Grace Period: The length of time after a users violation expires until they can be in violation of this policy again.
- CPU Threshold: The average number of cores a user must use during the lookback window to be in violation.
- Memory Threshold: The average number of GiB a user must use during the lookback window to be in violation.
