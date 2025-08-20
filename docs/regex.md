## Regex:

Options like domain or the user/process whitelists on policies follow the regex syntax used by prometheus ([RE2](https://github.com/google/re2/wiki/syntax)), meaning `.` is a wild card, `|` represents an `or` and that `*` and `+` mean zero or more and one or more respectively. 

For example, if you wanted a domain that matched on `node1.site.edu` and `node2.site.edu` on port 2112, you could use one of the following:
- `node(1|2)\.site\.edu:2112` if you want to match on specific number nodes with similar host names
- `(node1\.site\.edu|node2\.differentsite\.edu):2112` if you want to match on multiple hosts that might have more different host names.
- `node\d+\.site\.edu` if you wanted it to match for any number node on `site.edu`.
- `(node\d+\.site\.edu|node\d+\.differentsite\.edu):2112` if you want to match on any number node on multiple sites.

> Note that since you likely won't have multiple wardens on the same host with different ports, feel free to replace the `:2112` with `:\d+` to match on any port. Also if you have prometheus configured to strip ports on the labels, they will need to be removed from the regex, or made optional like `host.name(:2112)?`

If you simply want the policy to apply the policy on **all** hosts with a warden your prometheus has registered, you should use `.*` as the domain.

Similarly, for the whitelists we often use a list of process/user names seperated with `|` such as `vi|emacs|vim|nano` or `user1|user2|user3`.

> ⚠️ Note that some special characters may need to be escaped with `\`, such as if you wanted to whitelist the `g++` compiler you would need to escape the plus symbols `g\+\+`.