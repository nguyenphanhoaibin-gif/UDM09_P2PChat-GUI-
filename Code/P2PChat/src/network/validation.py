"""Input validation helpers for network parameters."""

import ipaddress

_RESERVED_IPS: frozenset[str] = frozenset({
    "0.0.0.0",          # unspecified address
    "255.255.255.255",  # limited broadcast
})


def validate_ip(ip: str) -> bool:
    """Return True if *ip* is a valid, non-reserved IPv4 address.
    Args:
        ip: String to validate.
    Returns:
        True if the address is a usable unicast IPv4 address.
    """
    if ip in _RESERVED_IPS:
        return False
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
        return False


def validate_port(port: str) -> bool:
    """Return True if *port* is a valid TCP/UDP port number string.
    Args:
        port: String representation of the port number.
    Returns:
        True if the port is in the range 1-65535.
    """
    if not port.isdigit():
        return False
    return 1 <= int(port) <= 65535
