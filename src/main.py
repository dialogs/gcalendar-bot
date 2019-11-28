# Python Standard Library
import os
import sys
import json
import logging
import datetime
import calendar
import i18n

# Dialogs Python Bot SDK
import grpc
from dialog_api import peers_pb2
from dialog_bot_sdk import interactive_media
from dialog_bot_sdk.bot import DialogBot

from GCaluAPI import GCaluAPI


# Prevent bot from crashing
def raw_call(*args, **kwargs):
    pass


def get_quarter_range(year: int, q: int, tz: datetime.timezone = None) -> tuple:
    """
    returns (start, end) datetime of selected quarter
    :param year: year
    :param q: quarter of the year 1-4
    :param tz: timezone (datetime.timezone)
    :return: tuple(start,end) as datetime.datetime
    """
    return (datetime.datetime(year, 3 * q - 2, 1, tzinfo=tz),
            datetime.datetime(year, 3 * q, calendar.monthrange(year, 3 * q)[1], tzinfo=tz))


def get_full_month_range(year: int, month: int, tz: datetime.timezone = None) -> tuple:
    """
    returns (start, end) datetime of selected month
    :param year: year
    :param month: month
    :param tz: timezone (datetime.timezone)
    :return: tuple(start,end) as datetime.datetime
    """
    return (datetime.datetime(year, month, 1, tzinfo=tz),
            datetime.datetime(year, month, calendar.monthrange(year, month)[1], tzinfo=tz))


def get_event_list(calendar_id: str, event_limit: int = 128, start: datetime.datetime = None,
                   end: datetime.datetime = None):
    """
    returns a text representing list of all events in range (start,end) dates 1 event per line
    :param calendar_id: id of calendar
    :param event_limit: maximum number of events to output
    :param start: start date
    :param end: end time
    :return: str
    """
    fmt = "%d/%m-%H:%M"
    fmt_b = "%H:%M"
    out = ""
    for evt in API.get_following_events(calendar_id, start, event_limit, end):
        event_start = datetime.datetime.fromisoformat(
            evt["start"]["dateTime"] if "dateTime" in evt["start"] else evt["start"]["date"])
        event_end = datetime.datetime.fromisoformat(
            evt["end"]["dateTime"] if "dateTime" in evt["start"] else evt["end"]["date"])
        event_delta = event_end - event_start
        out += ">{0}->{1} => {2} {3}".format(
            event_start.strftime(fmt),
            event_end.strftime(fmt if event_delta.days > 0 else fmt_b),
            evt["summary"] if "summary" in evt else "",
            str("("+evt["description"]+")") if "description" in evt else "")
        out += "\n"
    return out


def on_msg(*params):
    for param in params:
        log.debug("onMsg -> {}".format(param))
        try:
            if param.peer.id == param.sender_uid:
                lang = get_lang(param.peer.id)
                if SETTINGS["user_id"] and param.sender_uid not in SETTINGS["user_id"]:
                    # User Not authorized
                    continue
                txt = param.message.textMessage.text.lower()
                now = datetime.datetime.now(TZONE)

                if txt.startswith(SETTINGS["command0"]):
                    events = get_event_list(SETTINGS["calendar_id"], start=now,
                                            event_limit=SETTINGS["num_events_limit"])
                    text = "{0}\n{1}".format(i18n.t(PHRASES + '.all_list', locale=lang), events)
                    bot.messaging.send_message(param.peer, text)

                elif txt == SETTINGS["command1"]:
                    bot.messaging.send_message(param.peer, i18n.t(PHRASES + '.set_month', locale=lang),
                                               months_select(lang))
                elif txt == SETTINGS["command2"]:
                    bot.messaging.send_message(param.peer, i18n.t(PHRASES + '.set_number', locale=lang),
                                               quarters_select(lang))
                else:
                    bot.messaging.send_message(param.peer,
                                               i18n.t(PHRASES + '.help', locale=lang)
                                               .format(SETTINGS["command0"],
                                                       SETTINGS["command1"],
                                                       SETTINGS["command2"]))
        except:
            log.error("Exception", exc_info=True)
            continue


def on_event(*params):
    uid = params[0].uid
    msg = bot.messaging.get_messages_by_id([params[0].mid])[0]
    peer = peers_pb2.Peer(type=peers_pb2.PEERTYPE_PRIVATE, id=uid)
    which_button = params[0].value
    if which_button in MONTHS or which_button in ["1", "2", "3", "4"]:
        send_events(peer, which_button)
    bot.messaging.update_message(msg, msg.message.textMessage.text)


def send_events(peer, target):
    lang = get_lang(peer.id)
    now = datetime.datetime.now(TZONE)
    if target.isdigit():
        start, end = get_quarter_range(now.year, int(target), TZONE)
        phrase = '.quarter_list'
    else:
        start, end = get_full_month_range(now.year, MONTHS[target], TZONE)
        phrase = '.month_list'
        target = i18n.t("{0}.{1}".format(MONTHS_I18N, target), locale=lang)
    events = get_event_list(SETTINGS["calendar_id"], start=start, end=end,
                            event_limit=SETTINGS["num_events_limit"])
    text = "{0}\n{1}".format(i18n.t(PHRASES + phrase, locale=lang).format(target), events)
    if len(events) > 0:
        bot.messaging.send_message(peer, text)
    else:
        bot.messaging.send_message(peer, i18n.t(PHRASES + '.no_events', locale=lang))


def get_lang(uid):
    user = bot.users.get_user_by_id(uid)
    locales = user.data.locales
    if not locales or locales[0] not in LANG_LIST:
        return DEFAULT_LANG
    else:
        return locales[0]


def months_select(lang):
    actions = {}
    for month, value in MONTHS.items():
        actions[month] = i18n.t("{0}.{1}".format(MONTHS_I18N, month), locale=lang)

    return [interactive_media.InteractiveMediaGroup([
            interactive_media.InteractiveMedia(
                "months",
                interactive_media.InteractiveMediaSelect(actions, i18n.t(PHRASES + '.month', locale=lang))
            )
        ]
    )]


def quarters_select(lang):
    actions = {}
    for i in range(1, 5):
        actions[str(i)] = "Q{}".format(str(i))
    return [interactive_media.InteractiveMediaGroup([
            interactive_media.InteractiveMedia(
                "quarters",
                interactive_media.InteractiveMediaSelect(actions, i18n.t(PHRASES + '.quarter', locale=lang),
                                                         i18n.t(PHRASES + '.quarter', locale=lang))
            )
        ]
    )]


if __name__ == '__main__':
    i18n.load_path.append(os.path.dirname(__file__) + '/../translations')
    PHRASES = 'phrases.phrases'
    MONTHS_I18N = 'phrases.month'
    SETTINGS_PATH = os.path.dirname(__file__) + "/settings.json"

    MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())

    if os.path.exists(SETTINGS_PATH):
        try:
            SETTINGS = json.load(open(SETTINGS_PATH))
            TZONE = datetime.datetime.strptime(SETTINGS["timezone"], "%z").tzinfo
        except:
            log.error("Can't load settings", exc_info=True)
            sys.exit(1)

        LANG_LIST = ["en", "ru"]
        try:
            DEFAULT_LANG = SETTINGS["default_lang"]
            if DEFAULT_LANG not in LANG_LIST:
                raise Exception()
        except:
            DEFAULT_LANG = "en"

        # Initialize API
        try:
            API = GCaluAPI("{0}/{1}".format(os.path.dirname(__file__), SETTINGS["credentials_file"]),
                           "{0}/{1}".format(os.path.dirname(__file__), SETTINGS["token_file"]))
        except:
            log.error("Can't initialize GoogleuAPI", exc_info=True)
            sys.exit(1)

        # Enable this flag and use this to obtain google calendar id
        if SETTINGS["show_calendars"]:
            for current_cal in API.get_calendars():
                log.info("{0} => {1}".format(current_cal["id"], current_cal["summary"]))

        try:
            bot = DialogBot.get_secure_bot(
                os.environ.get('BOT_ENDPOINT'),  # bot endpoint
                grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
                os.environ.get('BOT_TOKEN')  # bot token
            )
            bot.messaging.on_message(on_msg, on_event, raw_callback=raw_call)
        except:
            log.error("Can't initialize bot", exc_info=True)
            sys.exit(1)

    else:
        log.error("{0} not found. Create one using settings_default.json as reference.".format(SETTINGS_PATH),
                  exc_info=True)
        sys.exit(1)
