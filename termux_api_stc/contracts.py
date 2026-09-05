from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpstreamCommandContract:
    binary: str
    source_path: str
    source_sha: str
    notes: str = ""


# Contracts inspected directly from the pinned termux/termux-api-package baseline.
# These are source identities, not claims about Android runtime behavior.
INSPECTED_CONTRACTS: dict[str, UpstreamCommandContract] = {
    "termux-brightness": UpstreamCommandContract(
        "termux-brightness", "scripts/termux-brightness.in",
        "799cef57d2254c1faf6924e3aebdf9a5c4b5e8bc",
        "One positional argument: 0..255 or auto.",
    ),
    "termux-call-log": UpstreamCommandContract(
        "termux-call-log", "scripts/termux-call-log.in",
        "0d09d3aa0245643cf6c487d0f85b6fffbb2fde38",
        "-l limit, -o offset; defaults 10 and 0.",
    ),
    "termux-contact-list": UpstreamCommandContract(
        "termux-contact-list", "scripts/termux-contact-list.in",
        "90b1024a7acf4fb07d17a8c89f5c72719ab39856",
        "No command arguments.",
    ),
    "termux-infrared-frequencies": UpstreamCommandContract(
        "termux-infrared-frequencies", "scripts/termux-infrared-frequencies.in",
        "f7a494c891a79270a918e0196163efd7c7d1520f",
        "No command arguments.",
    ),
    "termux-infrared-transmit": UpstreamCommandContract(
        "termux-infrared-transmit", "scripts/termux-infrared-transmit.in",
        "81c912a66391b4bce10b3334e5bbe5b2e1d2f638",
        "Requires -f frequency and one comma-separated pattern argument.",
    ),
    "termux-sensor": UpstreamCommandContract(
        "termux-sensor", "scripts/termux-sensor.in",
        "6f29c6057d15db7cfc02b272cb3a0354c0465d94",
        "-a/-s select sensors, -l list, -c cleanup, -d delay, -n limit.",
    ),
    "termux-sms-send": UpstreamCommandContract(
        "termux-sms-send", "scripts/termux-sms-send.in",
        "8a1bd4cc09514b0eb8dc3686db535a961256b208",
        "Requires -n recipients; optional -s slot; text can be stdin.",
    ),
    "termux-sms-list": UpstreamCommandContract(
        "termux-sms-list", "scripts/termux-sms-list.in",
        "5409e870a9b682cf5a17436dedfe17037586f58d",
        "Message/conversation query CLI with documented filters and limits.",
    ),
    "termux-toast": UpstreamCommandContract(
        "termux-toast", "scripts/termux-toast.in",
        "58e8843dbe9b252dbd39398e849502b3920ba8d4",
        "-b/-c colors, -g gravity, -s short; text accepted on stdin.",
    ),
    "termux-speech-to-text": UpstreamCommandContract(
        "termux-speech-to-text", "scripts/termux-speech-to-text.in",
        "4bc7fd0f913c1714f47995ce355be1ae20c2d7cb",
        "No args for final match; -p emits progress/partial matches.",
    ),
    "termux-storage-get": UpstreamCommandContract(
        "termux-storage-get", "scripts/termux-storage-get.in",
        "86b236edcc3ccacb21e158e25b657bf45c4848e6",
        "Requires exactly one output file path.",
    ),
    "termux-share": UpstreamCommandContract(
        "termux-share", "scripts/termux-share.in",
        "90177d55344ab7373f29a65554d6db73821b5300",
        "-a edit/send/view, -c content type, -d default receiver, -t title, optional file.",
    ),
    "termux-wallpaper": UpstreamCommandContract(
        "termux-wallpaper", "scripts/termux-wallpaper.in",
        "247bc725e0dfb8ba9651f1da76bded85b0288aef",
        "Exactly one of -f file or -u URL; optional -l lockscreen.",
    ),
    "termux-microphone-record": UpstreamCommandContract(
        "termux-microphone-record", "scripts/termux-microphone-record.in",
        "2cb7b3999096cce25a5dee75b4c2820a011eebc0",
        "record options plus mutually-exclusive -i info and -q quit.",
    ),
    "termux-fingerprint": UpstreamCommandContract(
        "termux-fingerprint", "scripts/termux-fingerprint.in",
        "ecb40b8e86365e8a0c5bef953c66bf59ab1f40cd",
        "Optional title/description/subtitle/cancel strings.",
    ),
    "termux-notification-channel": UpstreamCommandContract(
        "termux-notification-channel", "scripts/termux-notification-channel.in",
        "1fa91d373b9b31884a8592d4c68b18624c663304",
        "Create with channel-id channel-name; delete with -d channel-id.",
    ),
    "termux-notification-list": UpstreamCommandContract(
        "termux-notification-list", "scripts/termux-notification-list.in",
        "20151979edd975f27585999ec24adc289bba083b",
        "No arguments; lists currently shown notifications.",
    ),
    "termux-notification-remove": UpstreamCommandContract(
        "termux-notification-remove", "scripts/termux-notification-remove.in",
        "62b1c9df6749461c4d973e4b4691f597dbd482cb",
        "Requires exactly one notification id.",
    ),
    "termux-notification": UpstreamCommandContract(
        "termux-notification", "scripts/termux-notification.in",
        "61ee10b99e2f0e896644a0efa9a7c0f58de7deb2",
        "Creates notification; content via -c/--content or stdin; rich optional metadata.",
    ),
}
