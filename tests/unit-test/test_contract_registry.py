from termux_api_stc.contracts import INSPECTED_CONTRACTS
from termux_api_stc.official import OFFICIAL_COMMAND_SET


def test_inspected_contracts_are_official_commands():
    assert set(INSPECTED_CONTRACTS) <= OFFICIAL_COMMAND_SET


def test_contract_source_shas_are_full_sha1():
    assert all(len(c.source_sha) == 40 for c in INSPECTED_CONTRACTS.values())
    assert all(all(ch in "0123456789abcdef" for ch in c.source_sha) for c in INSPECTED_CONTRACTS.values())


def test_contract_binary_key_matches_value():
    assert all(name == contract.binary for name, contract in INSPECTED_CONTRACTS.items())
