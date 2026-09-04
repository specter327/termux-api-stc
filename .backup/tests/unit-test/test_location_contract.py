import pytest
import termux_api_stc.location as location

def test_location_arg_builder_defaults():
    assert location._args("gps","once")==("-p","gps","-r","once")

@pytest.mark.parametrize("provider",["gps","network","passive"])
def test_location_valid_providers(provider):
    assert location._args(provider,"once")[1]==provider

@pytest.mark.parametrize("request_kind",["once","last","updates"])
def test_location_valid_requests(request_kind):
    assert location._args("gps",request_kind)[3]==request_kind

def test_location_invalid_provider():
    with pytest.raises(ValueError):
        location._args("wifi","once")

def test_location_invalid_request():
    with pytest.raises(ValueError):
        location._args("gps","forever")
