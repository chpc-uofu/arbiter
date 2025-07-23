# Permissions 

Before any new users or arbiter-admins can be added, a superuser must be created, if you followed the initial guide for configuration you likely already did this.

```shell
./arbiter.py createsuperuser
```

## Adding New Users 

Once you have your superuser, navigate to the webserver (`localhost:8000` if run locally) to `/admin` (so `localhost:8000/admin`) and login with the superuser you have created. From here go to the **`Users`** tab and click `Add User` to create a new user.


## Giving Permissions To Users

Now that the user(s) are created, you must give them some permissions in order for them to be able to view the arbiter dashboard or to be able to configure arbiter etc. Navigate to the **`Users`** tab and click on the user you want to add the permission to. From here scroll to the *user permissions* section and select the ones you wish to add.

For Arbiter's case we only use/check two permissions:
- **Arbiter Viewer** (Listed as `Arbiter|policy|Arbiter Viewer` on the admin page) - Can view everything on the dashboard including violations, policy configuration, user limits, generate usage graphs, etc. However, if the user is not also an Arbiter Administrator they may not edit anything or run commands on the dashboard. 
- **Arbiter Administrator** (Listed as `Arbiter|policy|Arbiter Administrator` on the admin page) - can change any configuration on policies, can expire violations early, can run commands on the dashboard (apply limits, run evaluate or clean history), and can delete/create policies. <u>**HOWEVER**, the user **MUST** also be an `Arbiter Viewer` to view any pages</u>. If you give this permission to a user, you should also give them the `Arbiter Viewer` permission.


