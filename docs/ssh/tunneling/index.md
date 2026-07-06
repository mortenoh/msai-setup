# SSH Tunneling & Port Forwarding

Creating secure tunnels through SSH.

!!! warning "Forwarding is disabled by default on this build"
    The hardened sshd config on the MS-S1 MAX (drop-in `/etc/ssh/sshd_config.d/00-hardening.conf`, applied by the `ssh-hardening.yml` playbook) sets:

    ```
    AllowTcpForwarding no
    AllowAgentForwarding no
    ```

    As a result, the `-L` / `-R` / `-D` examples throughout this section will fail against the real server with:

    ```
    channel 1: open failed: administratively prohibited: open failed
    ```

    **Re-enable forwarding for a scoped case, not globally.** Rather than flipping `AllowTcpForwarding yes` in the global config, add a `Match` block in a higher-numbered drop-in that scopes the override to a single user or source network. Keep the global hardening in place.

    ```
    # /etc/ssh/sshd_config.d/10-forwarding-exception.conf
    Match User tunneluser
        AllowTcpForwarding yes
    ```

    Or scope by source address instead:

    ```
    # /etc/ssh/sshd_config.d/10-forwarding-exception.conf
    Match Address 192.168.1.0/24
        AllowTcpForwarding yes
    ```

    sshd is **first-match-wins**: the global `AllowTcpForwarding no` still applies to every connection that does not match the block. The drop-in filename sorts after `00-hardening.conf`, but note that `Match` blocks apply per-connection at evaluation time regardless of file order, so the exception only ever loosens the specific case you name. Validate with `sudo sshd -t` and reload with `sudo systemctl reload ssh` before relying on it.

## In This Section

- [Local Forwarding](local-forwarding.md) - Access remote services locally
- [Remote Forwarding](remote-forwarding.md) - Expose local services remotely
- [Dynamic Forwarding](dynamic-forwarding.md) - SOCKS proxy
- [Jump Hosts](jump-hosts.md) - Bastion servers and ProxyJump

## See Also

- [Client Configuration](../client/index.md) - SSH config for tunnels
- [Tailscale Funnel](../../tailscale/features/funnel-serve.md) - Alternative exposure method
