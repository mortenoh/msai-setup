# Ansible Concepts

The mental model. Read this first; everything else assumes you understand the terms here.

## The big idea

Ansible is **agentless declarative configuration management driven by SSH and Python**. You write a YAML document describing the **desired state** of one or more remote hosts. Ansible connects to each host over SSH, copies Python "modules" to the host, runs them with the parameters you specified, and removes them. The modules know how to make the system match the desired state, and they only act if the system isn't already in that state.

That last property — "only act if not already in state" — is **idempotency**, and it's the core of why Ansible is pleasant to use. Running the same playbook twice doesn't double-apply anything; it does nothing the second time.

## The flow, end to end

```
+-------------------+        SSH + Python        +-------------------+
|   Control node    |  -------------------->     |   Managed host    |
|   (your laptop)   |  <--------------------     |   (the MS-S1 MAX) |
+-------------------+                            +-------------------+
        |                                                 |
        | reads:                                          | runs:
        |   inventory                                     |   /tmp/ansible/<module>.py
        |   playbook                                      |     with parameters from YAML
        |   variables                                     |   reports back: changed / ok / failed
        |                                                 |
        v                                                 v
   ansible-playbook foo.yml                          (idempotent action)
```

There is **no agent** on the managed host. Ansible ships modules over SSH on every play. The downside is some startup overhead per task; the upside is "nothing to install" and "any SSH-reachable host is manageable".

## Terminology

| Term | Meaning |
|---|---|
| **Control node** | The host running `ansible-playbook`. Your Mac or laptop. Needs Python + Ansible installed. |
| **Managed host** | The host being configured. Needs SSH and Python 3 (Ubuntu has both). |
| **Inventory** | The list of managed hosts, organised into groups. Static YAML/INI or a dynamic plugin. |
| **Group** | A named subset of hosts (e.g. `lab`, `production`, `web`). Plays target groups. |
| **Play** | A block in a playbook that targets a group of hosts with a list of tasks. |
| **Playbook** | A YAML file containing one or more plays. The unit you run. |
| **Task** | A single declarative step in a play. Invokes one module with parameters. |
| **Module** | A piece of Python (or shell, etc.) that performs one kind of action — install a package, copy a file, restart a service. |
| **Handler** | A task triggered by `notify:` from another task. Runs once at end of play, even if notified multiple times. |
| **Role** | A reusable bundle of tasks + handlers + templates + defaults + files. Like a small playbook you can include from many places. |
| **Collection** | A distributable bundle of roles, modules, and plugins. Installed via `ansible-galaxy`. |
| **Variable** | A named value. Many sources and a strict precedence order ([Variables](variables.md)). |
| **Fact** | A variable Ansible automatically discovers about a managed host (OS, network, hardware) by running `setup` module. |
| **Template** | A Jinja2-templated file rendered with variables and copied to the managed host. |
| **Vault** | Encrypted YAML for secrets. |

## Idempotency, in detail

Every Ansible module is designed to compute "current state" first and then converge to "desired state" only if needed. Examples:

- `apt: name=nginx state=present` — does `dpkg -l nginx`; if installed, does nothing.
- `copy: src=foo.conf dest=/etc/foo.conf` — computes the SHA1 of source and destination; copies only if different.
- `service: name=ssh state=started` — checks systemd; starts only if not running.

Each task reports one of:

| Result | Meaning |
|---|---|
| `ok` | The system was already in the desired state. No change made. |
| `changed` | The module made a change. |
| `failed` | The module couldn't converge (e.g. `apt` couldn't find the package). |
| `skipped` | A `when:` condition or other gating caused the task not to run. |
| `unreachable` | SSH to the host failed. |

`ok` + `changed` together is "convergence happened". `failed` halts the play for that host.

This means **you can run the same playbook every hour as drift detection**: if anything reports `changed`, something on the host has drifted from declared state.

## A minimal playbook

```yaml
---
- hosts: lab                        # the play targets the 'lab' group
  become: true                       # run tasks via sudo
  tasks:
    - name: install nginx            # human-readable task name
      ansible.builtin.apt:           # module to run
        name: nginx                  # module parameter
        state: present               # desired state
        update_cache: true

    - name: ensure nginx is running
      ansible.builtin.systemd:
        name: nginx
        state: started
        enabled: true
```

Run with:

```bash
ansible-playbook -i inventory.yml minimal.yml
```

What happens:

1. Ansible reads `inventory.yml`, finds the hosts in group `lab`.
2. For each host:
   a. Opens an SSH connection (re-uses across tasks via ControlPersist).
   b. Sends the `setup` module to gather facts (unless disabled).
   c. For each task: sends the module + params, runs it, gets a result back.
3. Reports a summary: `ok=2 changed=2 failed=0 unreachable=0`.

## The Ansible loop

```
For each host in inventory (in parallel, up to forks setting):
    1. SSH connect, run `setup` module to gather facts
    2. For each play:
       For each task:
           a. Evaluate `when:` / `loop:` / `block:`
           b. Send module + params over SSH
           c. Run module on remote host
           d. Record result (ok / changed / failed / skipped)
           e. If `notify:`, queue a handler
       After all tasks, run any notified handlers in order
    3. Close SSH connection
```

Two things that aren't obvious:

- **Hosts run in parallel.** Ansible processes hosts in batches (default 5 forks). Task order within a host is strict; task order across hosts is not synchronized except at certain barriers.
- **Handlers run at end of play, not immediately.** Notifying a handler queues it; multiple notifications collapse to a single run. This makes "restart nginx if any of these N changes happen" easy.

## Modules vs ad-hoc

`ansible-playbook` runs playbooks. The `ansible` command (without `-playbook`) runs **one module against one group**:

```bash
ansible lab -m ansible.builtin.ping
ansible lab -m ansible.builtin.shell -a 'uptime'
ansible lab -m ansible.builtin.apt -a 'name=htop state=present' --become
```

Useful for poking around (`ping`, `setup`, `shell uptime`). Real work goes in playbooks.

## Where the state lives

**Nowhere persistent.** Ansible itself doesn't have a state file (no Terraform-style state.json). Every run starts fresh by querying the managed host. The "state" is the running system.

Consequences:

- Two people running the same playbook against the same host don't conflict on state; the system is the only state.
- There's no concept of "destroy what Ansible created". To remove things, write a task that removes them (`state: absent`).
- A playbook that hasn't run in months will pick up where it left off the next time you run it.

## Where Ansible isn't great

Honest about limits:

- **Provisioning** (creating VMs, cloud instances) isn't Ansible's strength. Use Terraform / Pulumi / cloud APIs / VBoxManage for that. Ansible configures things that already exist.
- **Procedural logic** (loops with side effects, intricate branching) is awkward in YAML. If a task feels like it needs a real loop with state, drop into a shell module — but mark `changed_when:` so idempotency reporting stays honest.
- **One-shot scripts** that should not be idempotent (e.g. "fire this off and forget it") fit better as plain shell scripts.

For this build: **VBoxManage (Python, via the `msai` CLI) for VM provisioning + Ansible for everything inside the VM**. The two halves of `src/msai_setup/lab/`. The hands-on walkthrough of both is [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md).

## Where to go next

- [Installation](installation.md) — install Ansible on your control node.
- [Inventory](inventory.md) — describe your hosts.
- [Playbooks](playbooks.md) — the load-bearing page; read carefully.
- [Modules](modules.md) — the modules this build uses.
