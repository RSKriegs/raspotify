#!/usr/bin/python3

# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

import subprocess
import os
import time

ASOUND_FILE_PATH = "/etc/asound.conf"
DUMMY_PATH = "/etc/foobarbaz{}".format(int(time.time()))
BACKUP_FILE_PATH = "/etc/asound.conf.bak{}".format(int(time.time()))

COMMON_FORMATS = [
    "S16_LE",
    "S16_BE",
    "S24_LE",
    "S24_BE",
    "S24_3LE",
    "S24_3BE",
    "S32_LE",
    "S32_BE",
]

COMMON_RATES = [
    8000,
    11025,
    16000,
    22050,
    44100,
    48000,
    88200,
    96000,
    176400,
    192000,
    352800,
    384000,
]


def privilege_check():
    try:
        open(DUMMY_PATH, "w").close()
        os.remove(DUMMY_PATH)
    except:
        print("Error: This script requires write privileges to /etc.")
        exit(1)


def backup_asound_conf():
    if os.path.exists(file_path):
        try:
            os.rename(ASOUND_FILE_PATH, BACKUP_FILE_PATH)
        except Exception as e:
            print("Error renaming existing {}: {}".format(ASOUND_FILE_PATH, e))
            exit(1)
        else:
            print(
                "{} already exists renaming it to {}.".format(
                    ASOUND_FILE_PATH, BACKUP_FILE_PATH
                )
            )


def revert_backup():
    try:
        os.rename(BACKUP_FILE_PATH, ASOUND_FILE_PATH)
    except:
        pass


def get_all_pcm_name():
    all_pcm_names = subprocess.run(
        ["aplay", "-L"], stdout=subprocess.PIPE
    ).stdout.decode("utf-8")

    print("Full list of ALSA PCM Names:")
    print(all_pcm_names)

    return all_pcm_names


def get_hw_pcm_names():
    hw_pcm_names = [
        n for n in get_all_pcm_name().split("\n") if n.startswith("hw:")
    ]

    if not hw_pcm_names:
        revert_backup()
        print("No available hw PCM")
        exit(1)

    elif len(hw_pcm_names) > 1:
        print("Available hw PCMs:")

        for i, pcm in enumerate(hw_pcm_names):
            print("{} - {}".format(i + 1, pcm))

    return hw_pcm_names


def choose_hw_pcm(hw_pcm_names):
    if len(hw_pcm_names) > 1:
        while True:
            try:
                choice = input("Please choose the hw PCM you wish to use: ")
                pcm = hw_pcm_names[int(choice) - 1]
            except KeyboardInterrupt:
                revert_backup()
                print("")
                exit(0)
            except:
                print("Invalid hw PCM: {}".format(choice))
                print("Enter a number from 1 - {}.".format(len(hw_pcm_names)))
                continue
            else:
                break
    else:
        pcm = hw_pcm_names[0]

        print(
            "{} is the only available hw PCM "
            "so that's what we'll use…".format(pcm)
        )

    return pcm


def get_formats_and_rates(pcm):
    r = subprocess.run(
        [
            "aplay",
            "-D{}".format(pcm),
            "--dump-hw-params",
            "/usr/share/sounds/alsa/Front_Right.wav",
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    formats = []
    rates = []

    hw_params = r.stdout.decode("utf-8") or r.stderr.decode("utf-8")

    for line in hw_params.split("\n"):
        if line.startswith("FORMAT:"):
            line = line.replace("FORMAT:", "")
            line.strip()

            for format_ in line.split(" "):
                format_.strip()
                if format_ in COMMON_FORMATS:
                    formats.append(format_)

        elif line.startswith("RATE:"):
            line = line.replace("RATE:", "")
            line = line.replace("[", "")
            line = line.replace("]", "")
            line.strip()

            for line in line.split(" "):
                try:
                    rate = int(line.strip())
                    if rate in COMMON_RATES:
                        rates.append(rate)
                except:
                    pass

    return formats, rates


def choose_format(formats):
    if len(formats) > 1:
        print("Supported Formats:")

        for i, format_ in enumerate(formats):
            print("{} - {}".format(i + 1, format_))

        print(
            "It's generally advised to choose the highest bit "
            "depth format that your device supports."
        )

        while True:
            try:
                choice = input("Please choose the desired supported format: ")
                format_ = formats[int(choice) - 1]
            except KeyboardInterrupt:
                revert_backup()
                print("")
                exit(0)
            except:
                print("Invalid format choice: {}".format(choice))
                print("Enter a number from 1 - {}.".format(len(formats)))
                continue
            else:
                break

    else:
        format_ = formats[0]

        print(
            "{} is the only supported format "
            "so that's what we'll use…".format(format_)
        )

    return format_


def choose_rate(rates):
    if len(rates) > 1:
        r_range = range(rates[0], rates[-1] + 1)

        rates = [r for r in COMMON_RATES if r in r_range]

        print("Supported Sampling Rates:")

        for i, rate in enumerate(rates):
            print("{} - {}".format(i + 1, rate))

        print(
            "Standard CD quality is 44100.\n"
            "An unnecessarily high sampling rate can lead to high CPU usage,\n"
            "degraded audio quality, and audio dropouts and glitches on "
            "low spec devices.\nUnless the music you normally listen to is a "
            "higher sampling rate,\n"
            "44100 (or as close as you can get to it) is the best choice."
        )

        while True:
            try:
                choice = input(
                    "Please choose the desired supported sampling rate: "
                )

                rate = rates[int(choice) - 1]
            except KeyboardInterrupt:
                revert_backup()
                print("")
                exit(0)
            except:
                print("Invalid sampling rate choice: {}".format(choice))
                print("Enter a number from 1 - {}.".format(len(rates)))
                continue
            else:
                break

    else:
        rate = rates[0]

        print(
            "{} is the only supported sampling rate "
            "so that's what we'll use…".format(rate)
        )

        if rate > 48000:
            print(
                "High sampling rates can lead to high CPU usage,\n"
                "degraded audio quality, and audio dropouts and "
                "glitches on low spec devices."
            )

    return rate


def pcm_to_card_device(pcm):
    card = pcm.replace("hw:CARD=", "").strip()
    [card, device] = card.split(",")
    device = device.replace("DEV=", "").strip()
    device = int(device)

    return card, device


def get_choices():
    hw_pcm_names = get_hw_pcm_names()

    while True:
        try:
            pcm = choose_hw_pcm(hw_pcm_names)
            formats, rates = get_formats_and_rates(pcm)

            if not formats or not rates:
                print(
                    "No supported formats or sampling rates were returned, "
                    "the hw PCM you chose may be busy "
                    "or not support any common formats and rates? "
                    "Make sure it's not in use and try again."
                )
                continue
            else:
                format_ = choose_format(formats)
                rate = choose_rate(rates)
                card, device = pcm_to_card_device(pcm)
                return card, device, format_, rate

        except KeyboardInterrupt:
            revert_backup()
            print("")
            exit(0)


def write_asound_conf():
    privilege_check()

    print(
        "This script will backup {0} (if it already exists) "
        "and create a new {0} based on your choices.".format(
            ASOUND_FILE_PATH
        )
    )

    try:
        choice = input("Enter OK to continue: ")

        if choice.lower() != "ok":
            exit(0)

    except KeyboardInterrupt:
        print("")
        exit(0)

    backup_asound_conf()

    card, device, format_, rate = get_choices()

    file_data = """# /etc/asound.conf

pcm.!default {{
    type plug
    slave.pcm {{
        type dmix
        ipc_key {{
            @func refer
            name defaults.pcm.ipc_key
        }}
        ipc_gid {{
            @func refer
            name defaults.pcm.ipc_gid
        }}
        ipc_perm {{
            @func refer
            name defaults.pcm.ipc_perm
        }}
        slave {{
            pcm {{
                type hw
                card {0}
                device {1}
                nonblock {{
                    @func refer
                    name defaults.pcm.nonblock
                }}
            }}
            channels 2
            rate {2}
            format {3}
        }}
        bindings {{
            0 0
            1 1
        }}
    }}
}}

ctl.!default {{
    type hw
    card {0}
}}""".format(
        card, device, rate, format_
    )

    try:
        with open(ASOUND_FILE_PATH, "w") as f:
            f.write(file_data)

    except Exception as e:
        revert_backup()
        print("Error: {}".format(e))
        exit(1)

    else:
        print(
            "Using Card: {}, Device: {}, "
            "Format: {}, and Sampling Rate: {},".format(
                card, device, format_, rate
            )
        )

        print(
            "{} was written successfully. "
            "Please verify that it is correct.".format(ASOUND_FILE_PATH)
        )


if __name__ == "__main__":
    write_asound_conf()