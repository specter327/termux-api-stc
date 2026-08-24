"""Wrapper de `termux-sms-list` y `termux-sms-send`."""
from typing import List, Optional, Union
from .core import run


def inbox(limit: Optional[int] = None, offset: Optional[int] = None,
          from_number: Optional[str] = None, msg_type: Optional[str] = None):
    """
    Wraps `termux-sms-list [-l limit] [-o offset] [-f from] [-t type]`.
    Devuelve una lista de dicts con los mensajes SMS.
    """
    args = []
    if limit is not None:
        args += ["-l", str(limit)]
    if offset is not None:
        args += ["-o", str(offset)]
    if from_number is not None:
        args += ["-f", from_number]
    if msg_type is not None:
        args += ["-t", msg_type]
    return run("termux-sms-list", args)


def send(numbers: Union[str, List[str]], text: str, sim_slot: Optional[int] = None):
    """
    Wraps `termux-sms-send [-n numbers] [-s simslot] text`.
    :param numbers: numero de telefono, o lista de numeros
    """
    if isinstance(numbers, (list, tuple)):
        numbers = ",".join(numbers)
    args = ["-n", numbers]
    if sim_slot is not None:
        args += ["-s", str(sim_slot)]
    args.append(text)
    return run("termux-sms-send", args, parse_json=False)
