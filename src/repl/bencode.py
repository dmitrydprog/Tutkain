# -*- coding: utf-8 -*-
"""
Read bencoded bytes from a buffer and turn them into Python values or turn
Python values into bencoded bytes.

Example:

    import Tutkain.src.repl.bencode as bencode

    socket = socket.sockets(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect(('localhost', 1234))
    buf = socket.makefile(mode='rwb')

    # Wait for someone to put a bencoded value onto the socket.
    #
    # For example, given:
    #
    #     b'd3:bar4:spam3:fooi42ee'

    print(bencode.read(buf))
    # => {'foo': 42, 'bar': 'spam'}

    print(bencode.write(buf, {'foo': 42, 'bar': 'spam'}))
    # => b'd3:bar4:spam3:fooi42ee'

Has complete faith in the sending end. That is, does not try to recover from
any errors.
"""


ENCODING = "utf-8"


def read_until(b, terminator):
    """Read bytes until the given terminator byte.

    Return the bytes, excluding the terminator byte."""
    bs = bytearray()
    byte = b.read(1)

    while byte != terminator:
        bs.extend(byte)
        byte = b.read(1)

    return bs


def read_list(b):
    xs = []

    while x := read(b):
        xs.append(x)

    return xs


def read_dict(b):
    d = {}

    while k := read(b):
        v = read(b)
        d[k] = v

    return d


def read_int(b):
    return int(read_until(b, b"e"))


def read(b):
    """Read bencodes values from a BufferedReader into Python values."""
    first_byte = b.read(1)

    # If the first byte is empty, the most likely reason is that the TCP server has died.
    #
    # If we don't take that into account here, our receive loop will keep flooding the system with
    # recvfrom syscalls until the parent process dies. Eventually, the parent process ends up taking
    # 100% of CPU time.
    if not first_byte or first_byte == b"e":
        return None
    elif first_byte == b"d":
        return read_dict(b)
    elif first_byte == b"l":
        return read_list(b)
    elif first_byte == b"i":
        return read_int(b)
    else:
        n = int(first_byte + read_until(b, b":"))
        return b.read(n).decode(ENCODING)


def write_int(buf, i):
    buf.write(f"i{i}e".encode(ENCODING))


def write_str(buf, s):
    length = len(s.encode(ENCODING))
    buf.write(f"{length}:{s}".encode(ENCODING))


def write_list(buf, xs):
    buf.write(b"l")

    for x in xs:
        write_value(buf, x)

    buf.write(b"e")


def write_dict(buf, d):
    buf.write(b"d")
    ks = list(d.keys())
    ks.sort()

    for k in ks:
        write_value(buf, k)
        write_value(buf, d[k])

    buf.write(b"e")


def write_value(buf, x):
    if isinstance(x, int):
        write_int(buf, x)
    elif isinstance(x, str):
        write_str(buf, x)
    elif isinstance(x, list):
        write_list(buf, x)
    elif isinstance(x, dict):
        write_dict(buf, x)
    else:
        raise ValueError(f"""Can't write {x} into bencode""")


def write(buf, x):
    """Write a Python value into BufferedReader as bencode."""
    write_value(buf, x)
    buf.flush()
