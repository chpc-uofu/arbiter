import pytest
import aiohttp
import multiprocessing
import paramiko
from http import HTTPStatus
from time import sleep
import asyncio

from arbiter.eval import *
from arbiter.models import Target

from testing.conf import *
import testing.fixtures 

########## HELPER FUNCTIONS ##########
def launch_ssh_process(command, user):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        TEST_ADDRESS,
        username=user,
        password=TEST_USER_PASSWORD,
        allow_agent=False,
    )
    stdin, stdout, stderr = ssh.exec_command(command)
    stdin.close()
    assert stderr.channel.recv_exit_status() == 0


async def run_apply_with_session(limits, target):
    async with aiohttp.ClientSession() as session:
        return await apply_limits(
            limits=limits,
            target=target,
            session=session,
        )


########## Begin Tests ##########
@pytest.mark.asyncio
async def test_set_property(db, target1):
    prop = {"name": "MemoryAccounting", "value": False}
    async with aiohttp.ClientSession() as session:
        status, message = await set_property(target1, session, prop)
        print(message)
        assert status == HTTPStatus.OK
        prop = {"name": "MemoryAccounting", "value": True}
        status, message = await set_property(target1, session, prop)
        assert status == HTTPStatus.OK


@pytest.mark.django_db(transaction=True)
def test_reduce_limits(
    db, many_limit_cpu, many_limit_mem, harsh_limit_cpu, harsh_limit_mem
):
    limits = many_limit_mem + many_limit_cpu
    reduced = reduce_limits(limits)
    assert len(reduced) == 2
    assert harsh_limit_cpu in reduced
    assert harsh_limit_mem in reduced


@pytest.mark.django_db(transaction=True)
def test_apply_limits(
    db, soft_limit_cpu, soft_limit_mem, unset_limit_cpu, unset_limit_mem
):
    target = Target.objects.create(unit=TEST_USER1_SLICE, host=TEST_HOST)

    successful = asyncio.run(
        run_apply_with_session([soft_limit_cpu, soft_limit_mem], target)
    )
    assert target == successful[0]
    assert soft_limit_cpu in successful[1]
    assert soft_limit_mem in successful[1]

    successful = asyncio.run(
        run_apply_with_session(limits=[unset_limit_cpu, unset_limit_mem], target=target)
    )
    assert target == successful[0]
    assert unset_limit_cpu in successful[1]
    assert unset_limit_mem in successful[1]


@pytest.mark.django_db(transaction=True)
def test_query_violations(db, short_low_harsh_policy):
    user = TEST_USER1
    comm = "stress-ng --cpu 1 --timeout 10s"
    p = multiprocessing.Process(target=launch_ssh_process, args=(comm, user))
    p.start()
    sleep(10)
    p.kill()
    violations = query_violations([short_low_harsh_policy])
    assert short_low_harsh_policy in [v.policy for v in violations]
    assert f"{user}.slice" in [v.target.unit for v in violations]


@pytest.mark.django_db(transaction=True)
def test_get_affected_hosts(db, harsh_mixed_violation):
    affected = hosts_in_domain(harsh_mixed_violation.policy.domain)
    assert TEST_HOST in affected
