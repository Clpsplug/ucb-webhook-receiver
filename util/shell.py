import subprocess
from sys import platform


class NotificationSound:
    """
    Constants (as class attrs) that contains sound names for terminal-notifier.
    The names are based on post-Big-Sur names. The values are pre-Big-Sur names which terminal-notifier accepts.
    """

    Boop = "Tink"
    Breeze = "Blow"
    Bubble = "Pop"
    Crystal = "Glass"
    Funky = "Funk"
    Heroine = "Hero"
    Jump = "Frog"
    Mezzo = "Basso"
    Pebble = "Bottle"
    Pluck = "Purr"
    Pong = "Morse"
    Sonar = "Ping"
    Sosumi = "Sosumi"
    Submerge = "Submarine"
    Default = "default"


class TerminalNotifier:
    should_be_no_op = False

    def __init__(self):
        raise Exception("Don't instantiate this class please.")

    @staticmethod
    def initialize():
        """
        Checks if the system can run terminal-notifier.
        You can still safely call fire_notification on incompatible systems, on which the function becomes a no-op.
        """

        if platform != "darwin":
            TerminalNotifier.should_be_no_op = True

        process = subprocess.Popen(["which", "terminal-notifier"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, _ = process.communicate()
        ret = process.returncode

        if ret is None or ret != 0:
            TerminalNotifier.should_be_no_op = True

    @staticmethod
    def fire_notification(title: str, message: str = None, sound: str = NotificationSound.Default):
        """
        Runs terminal-notifier. This function is a no-op on incompatible systems.

        :param title: Title text. If message is None or empty, this is instead printed into message section.
        :param message: Message Text.
        :param sound: str, but specify NotificationSound class attribute.
        """

        if TerminalNotifier.should_be_no_op:
            return
        command = [
            "terminal-notifier",
        ]
        if message is None or message != "":
            command.append("-title")
            command.append('"{title}"'.format(title=title))
            command.append("-message")
            command.append('"{message}"'.format(message=message))
        else:
            command.append("-message")
            command.append('"{message}"'.format(message=title))
        command.append("-sound")
        command.append('"{sound}"'.format(sound=sound))

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc.communicate()
        if proc.returncode != 0:
            raise ValueError
