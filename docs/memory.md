# Memory
The way Arbiter, or rather cgroup-warden, limits memory is a little complex due to the differing ways memory can be limited between cgroups v1 and cgroups v2 and not wanting to OOM processes. Because of that, we document how cgroup warden limits memory here in case it is relevant.

On both versions, the memory is has limits/maxes in a few capacities (physical space, swap, cache). For arbiter's purpose we only care about physical memory and swap.


## Avoiding Swap Thrashing and OOMing
When attempting to limit user's memory use lower than their current usage we ran into a few problems. The first is if we limited both of these maxes (swap and physical) below their current usage, then the user's processes would be OOM'ed which we did not want to happen as we were considered it could crash user's sessions. If instead we choose to only lower the physical max, meaning all excess usage would be swapped to disk, the user's memory use would be significantly slowed by this. However, as that requires swapping out an unknown amount of GiBs of data, it would likely cause swap thrashing.

Because of these issues, the warden never sets a user's memory max below their current usage, however, the warden will report back to arbiter that the limit was not fully set and arbiter will have it try again the next evaluation.

So in practice on violation, they will have their memory capped near its current usage, and from their the warden/arbiter will continue to greedily lower their max memory when less is used until they reach the desired max.


## Setting Swap Maxes
In cgroups v1/v2 the memory maxes are set up a bit different to each other. V1 has a max for physical memory and a combined max for `physical_usage + swap_usage`.  V2 simply has a max physical memory usage and a max swap usage. 

Because of this the warden limits these two sets of maxes a little differently. For both the physical memory is set to the desired value. As for the combined max in v1, it is set to the same value as the physical to allow the OS to swap memory to disk if needed, but not allow them more than their limit. For the separate max for swap, we set it to a configurable ratio of the value set on physical memory, by default it is 10%.