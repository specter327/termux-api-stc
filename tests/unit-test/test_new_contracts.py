from __future__ import annotations

import json
from pathlib import Path

import pytest

from termux_api_stc import brightness, call_log, contacts, fingerprint, infrared, microphone
from termux_api_stc import sensor, share, sms, speech_to_text, storage, toast, wallpaper


def recorder(make, binary: str):
    make(binary, """
import json, sys
print(json.dumps({'argv': sys.argv[1:]}))
""")

def recorder_stdin(make, binary: str):
    make(binary, """
import json, sys
print(json.dumps({'argv': sys.argv[1:], 'stdin': sys.stdin.read()}))
""")


def decode(result):
    return json.loads(result.stdout.decode())


# brightness
@pytest.mark.parametrize("value,expected", [(0,"0"),(1,"1"),(128,"128"),(255,"255"),("auto","auto")])
def test_brightness_exact_argv(env_with, value, expected):
    _, make = env_with
    recorder(make, "termux-brightness")
    assert json.loads(brightness.set(value))["argv"] == [expected]

@pytest.mark.parametrize("value", [-1,256,999])
def test_brightness_rejects_out_of_range(value):
    with pytest.raises(ValueError): brightness.set(value)

def test_brightness_rejects_bool():
    with pytest.raises(TypeError): brightness.set(True)

@pytest.mark.asyncio
async def test_brightness_async_exact_argv(env_with):
    _, make = env_with; recorder(make, "termux-brightness")
    assert json.loads(await brightness.set_async(33))["argv"] == ["33"]


# call log
@pytest.mark.parametrize("limit,offset", [(10,0),(0,0),(1,2),(100,999)])
def test_call_log_exact_argv(env_with, limit, offset):
    _, make = env_with; recorder(make, "termux-call-log")
    got=decode(call_log.query(limit=limit, offset=offset))
    assert got["argv"] == ["-l",str(limit),"-o",str(offset)]

@pytest.mark.parametrize("kwargs", [{"limit":-1},{"offset":-1},{"limit":True},{"offset":True}])
def test_call_log_invalid(kwargs):
    with pytest.raises(ValueError): call_log.query(**kwargs)

@pytest.mark.asyncio
async def test_call_log_async_exact_argv(env_with):
    _,make=env_with; recorder(make,"termux-call-log")
    assert decode(await call_log.query_async(limit=3,offset=4))["argv"] == ["-l","3","-o","4"]


def test_call_log_json_parser(env_with):
    _,make=env_with; make("termux-call-log", "print('[{\"number\":\"123\"}]')")
    assert call_log.query_json()==[{"number":"123"}]


# contacts

def test_contacts_no_arguments(env_with):
    _,make=env_with; recorder(make,"termux-contact-list")
    assert decode(contacts.list_result())["argv"] == []


def test_contacts_json(env_with):
    _,make=env_with; make("termux-contact-list", "print('[{\"name\":\"A\"}]')")
    assert contacts.list_json()==[{"name":"A"}]

@pytest.mark.asyncio
async def test_contacts_async_no_arguments(env_with):
    _,make=env_with; recorder(make,"termux-contact-list")
    assert decode(await contacts.list_result_async())["argv"] == []


# infrared

def test_infrared_frequencies_no_arguments(env_with):
    _,make=env_with; recorder(make,"termux-infrared-frequencies")
    assert decode(infrared.frequencies())["argv"] == []


def test_infrared_transmit_string_pattern(env_with):
    _,make=env_with; recorder(make,"termux-infrared-transmit")
    got=decode(infrared.transmit(38000,"20,50,20,30"))
    assert got["argv"] == ["-f","38000","20,50,20,30"]


def test_infrared_transmit_sequence_pattern(env_with):
    _,make=env_with; recorder(make,"termux-infrared-transmit")
    got=decode(infrared.transmit(38000,[20,50,20,30]))
    assert got["argv"][-1] == "20,50,20,30"

@pytest.mark.parametrize("frequency", [0,-1,True])
def test_infrared_invalid_frequency(frequency):
    with pytest.raises(ValueError): infrared.transmit(frequency,"1,2")

@pytest.mark.parametrize("pattern", ["",[],[-1,2],[True,2]])
def test_infrared_invalid_pattern(pattern):
    with pytest.raises(ValueError): infrared.transmit(38000,pattern)


# sensor

def test_sensor_list_exact(env_with):
    _,make=env_with; make("termux-sensor", "print('[]')")
    assert sensor.list_available()==[]


def test_sensor_cleanup_exact(env_with):
    _,make=env_with; recorder(make,"termux-sensor")
    assert decode(sensor.cleanup())["argv"] == ["-c"]


def test_sensor_read_specific_exact(env_with):
    _,make=env_with; recorder(make,"termux-sensor")
    got=decode(sensor.read_result(sensors=["accelerometer","light"],delay_ms=200,limit=3))
    assert got["argv"] == ["-s","accelerometer,light","-d","200","-n","3"]


def test_sensor_read_all_exact(env_with):
    _,make=env_with; recorder(make,"termux-sensor")
    got=decode(sensor.read_result(all_sensors=True,limit=1))
    assert got["argv"] == ["-a","-n","1"]

@pytest.mark.parametrize("kwargs", [
    {},
    {"sensors":"a","all_sensors":True},
    {"sensors":[]},
    {"sensors":"a","delay_ms":-1},
    {"sensors":"a","limit":0},
])
def test_sensor_invalid_selection(kwargs):
    with pytest.raises(ValueError): sensor.read_result(**kwargs)

@pytest.mark.asyncio
async def test_sensor_async_exact(env_with):
    _,make=env_with; recorder(make,"termux-sensor")
    got=decode(await sensor.read_result_async(sensors="light",limit=2))
    assert got["argv"] == ["-s","light","-n","2"]


# sms
@pytest.mark.parametrize("message_type", ["all","inbox","sent","draft","outbox","failed","queued"])
def test_sms_list_message_types(env_with,message_type):
    _,make=env_with; recorder(make,"termux-sms-list")
    got=decode(sms.list_result(message_type=message_type))
    assert got["argv"] == ["-l","10","-o","0","-t",message_type]


def test_sms_list_address_conversation(env_with):
    _,make=env_with; recorder(make,"termux-sms-list")
    got=decode(sms.list_result(limit=20,offset=4,address="+5255",conversation_list=True))
    assert got["argv"] == ["-l","20","-o","4","-t","all","-f","+5255","-c"]

@pytest.mark.parametrize("kwargs", [{"limit":-1},{"offset":-1},{"message_type":"trash"}])
def test_sms_list_invalid(kwargs):
    with pytest.raises(ValueError): sms.list_result(**kwargs)


def test_sms_send_uses_stdin(env_with):
    _,make=env_with; recorder_stdin(make,"termux-sms-send")
    got=decode(sms.send(["111","222"],"hello\nworld",slot=1))
    assert got["argv"] == ["-n","111,222","-s","1"]
    assert got["stdin"] == "hello\nworld"


def test_sms_send_single_recipient(env_with):
    _,make=env_with; recorder_stdin(make,"termux-sms-send")
    got=decode(sms.send("111","x"))
    assert got["argv"] == ["-n","111"]

@pytest.mark.parametrize("recipients", ["",[]])
def test_sms_send_requires_recipient(recipients):
    with pytest.raises(ValueError): sms.send(recipients,"x")

@pytest.mark.parametrize("slot", [-1,True])
def test_sms_invalid_slot(slot):
    with pytest.raises(ValueError): sms.send("1","x",slot=slot)

@pytest.mark.asyncio
async def test_sms_send_async_stdin(env_with):
    _,make=env_with; recorder_stdin(make,"termux-sms-send")
    got=decode(await sms.send_async("1","abc"))
    assert got["stdin"] == "abc"


# toast

def test_toast_text_goes_to_stdin(env_with):
    _,make=env_with; recorder_stdin(make,"termux-toast")
    got=decode(toast.show("hello"))
    assert got == {"argv":[],"stdin":"hello"}


def test_toast_options_exact(env_with):
    _,make=env_with; recorder_stdin(make,"termux-toast")
    got=decode(toast.show("x",background="red",color="#FFFFFF",gravity="top",short=True))
    assert got["argv"] == ["-s","-c","#FFFFFF","-b","red","-g","top"]
    assert got["stdin"] == "x"

@pytest.mark.asyncio
async def test_toast_async_exact(env_with):
    _,make=env_with; recorder_stdin(make,"termux-toast")
    assert decode(await toast.show_async("x",short=True))["argv"] == ["-s"]


# speech to text

def test_speech_final_no_args(env_with):
    _,make=env_with; make("termux-speech-to-text","print('final text')")
    assert speech_to_text.transcribe().strip() == "final text"

@pytest.mark.asyncio
async def test_speech_async_no_args(env_with):
    _,make=env_with; make("termux-speech-to-text","print('final')")
    assert (await speech_to_text.transcribe_async()).strip()=="final"


# storage

def test_storage_exact_path(env_with,tmp_path):
    _,make=env_with; recorder(make,"termux-storage-get")
    path=tmp_path/"output with spaces.bin"
    got=decode(storage.get(path))
    assert got["argv"] == [str(path)]


# share

def test_share_text_stdin(env_with):
    _,make=env_with; recorder_stdin(make,"termux-share")
    got=decode(share.share_text("hello",action="send",content_type="text/plain",default_receiver=True,title="T"))
    assert got["argv"] == ["-a","send","-c","text/plain","-d","-t","T"]
    assert got["stdin"] == "hello"


def test_share_file_exact(env_with,tmp_path):
    _,make=env_with; recorder_stdin(make,"termux-share")
    p=tmp_path/"a b.txt";p.write_text("x")
    got=decode(share.share_file(p,action="view"))
    assert got["argv"] == ["-a","view",str(p)]


def test_share_invalid_action():
    with pytest.raises(ValueError): share.share_text("x",action="destroy")


def test_share_missing_file(tmp_path):
    with pytest.raises(ValueError): share.share_file(tmp_path/"missing")


# wallpaper

def test_wallpaper_file_exact(env_with,tmp_path):
    _,make=env_with; recorder(make,"termux-wallpaper")
    p=tmp_path/"wall.jpg";p.write_bytes(b"x")
    got=decode(wallpaper.from_file(p,lockscreen=True))
    assert got["argv"] == ["-l","-f",str(p)]


def test_wallpaper_url_exact(env_with):
    _,make=env_with; recorder(make,"termux-wallpaper")
    got=decode(wallpaper.from_url("https://example.test/a.jpg"))
    assert got["argv"] == ["-u","https://example.test/a.jpg"]


def test_wallpaper_missing_file(tmp_path):
    with pytest.raises(ValueError): wallpaper.from_file(tmp_path/"missing")


def test_wallpaper_empty_url():
    with pytest.raises(ValueError): wallpaper.from_url("")


# microphone

def test_microphone_default_exact(env_with):
    _,make=env_with; recorder(make,"termux-microphone-record")
    assert decode(microphone.start())["argv"] == ["-d"]


def test_microphone_full_options(env_with,tmp_path):
    _,make=env_with; recorder(make,"termux-microphone-record")
    p=tmp_path/"r.m4a"
    got=decode(microphone.start(file=p,limit_seconds=10,encoder="aac",bitrate_kbps=128,sample_rate_hz=44100,channels=2))
    assert got["argv"] == ["-f",str(p),"-l","10","-e","aac","-b","128","-r","44100","-c","2"]


def test_microphone_info_exact(env_with):
    _,make=env_with; recorder(make,"termux-microphone-record")
    assert decode(microphone.info())["argv"] == ["-i"]


def test_microphone_stop_exact(env_with):
    _,make=env_with; recorder(make,"termux-microphone-record")
    assert decode(microphone.stop())["argv"] == ["-q"]

@pytest.mark.parametrize("kwargs", [
    {"limit_seconds":-1},{"encoder":"mp3"},{"bitrate_kbps":0},{"sample_rate_hz":0},{"channels":0}
])
def test_microphone_invalid(kwargs):
    with pytest.raises(ValueError): microphone.start(**kwargs)


# fingerprint

def test_fingerprint_no_args(env_with):
    _,make=env_with; recorder(make,"termux-fingerprint")
    assert decode(fingerprint.authenticate())["argv"] == []


def test_fingerprint_all_labels(env_with):
    _,make=env_with; recorder(make,"termux-fingerprint")
    got=decode(fingerprint.authenticate(title="T",description="D",subtitle="S",cancel="C"))
    assert got["argv"] == ["-t","T","-d","D","-s","S","-c","C"]

# async parity additions
@pytest.mark.asyncio
async def test_share_text_async_exact(env_with):
    _,make=env_with; recorder_stdin(make,"termux-share")
    got=decode(await share.share_text_async("abc",action="edit",title="X"))
    assert got["argv"] == ["-a","edit","-t","X"]
    assert got["stdin"] == "abc"

@pytest.mark.asyncio
async def test_wallpaper_url_async_exact(env_with):
    _,make=env_with; recorder(make,"termux-wallpaper")
    got=decode(await wallpaper.from_url_async("https://example.test/x",lockscreen=True))
    assert got["argv"] == ["-l","-u","https://example.test/x"]

@pytest.mark.asyncio
async def test_microphone_async_default_exact(env_with):
    _,make=env_with; recorder(make,"termux-microphone-record")
    assert decode(await microphone.start_async())["argv"] == ["-d"]

@pytest.mark.asyncio
async def test_fingerprint_async_exact(env_with):
    _,make=env_with; recorder(make,"termux-fingerprint")
    got=decode(await fingerprint.authenticate_async(title="T"))
    assert got["argv"] == ["-t","T"]

@pytest.mark.asyncio
async def test_sms_list_json_async(env_with):
    _,make=env_with; make("termux-sms-list", "print('[]')")
    assert await sms.list_json_async(limit=1) == []
