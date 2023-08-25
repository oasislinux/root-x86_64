import importlib
import random
import re

from ..utils import (
    age_restricted,
    bug_reports_message,
    classproperty,
    variadic,
    write_string,
)

# These bloat the lazy_extractors, so allow them to passthrough silently
ALLOWED_CLASSMETHODS = {'extract_from_webpage', 'get_testcases', 'get_webpage_testcases'}
_WARNED = False


class LazyLoadMetaClass(type):
    def __getattr__(cls, name):
        global _WARNED
        if ('_real_class' not in cls.__dict__
                and name not in ALLOWED_CLASSMETHODS and not _WARNED):
            _WARNED = True
            write_string('WARNING: Falling back to normal extractor since lazy extractor '
                         f'{cls.__name__} does not have attribute {name}{bug_reports_message()}\n')
        return getattr(cls.real_class, name)


class LazyLoadExtractor(metaclass=LazyLoadMetaClass):
    @classproperty
    def real_class(cls):
        if '_real_class' not in cls.__dict__:
            cls._real_class = getattr(importlib.import_module(cls._module), cls.__name__)
        return cls._real_class

    def __new__(cls, *args, **kwargs):
        instance = cls.real_class.__new__(cls.real_class)
        instance.__init__(*args, **kwargs)
        return instance

    _module = None
    _ENABLED = True
    _VALID_URL = None
    _WORKING = True
    IE_DESC = None
    _NETRC_MACHINE = None
    SEARCH_KEY = None
    age_limit = 0
    _RETURN_TYPE = None

    @classmethod
    def ie_key(cls):
        """A string for getting the InfoExtractor with get_info_extractor"""
        return cls.__name__[:-2]

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        # This function must import everything it needs (except other extractors),
        # so that lazy_extractors works correctly
        return cls._match_valid_url(url) is not None

    @classmethod
    def _match_valid_url(cls, url):
        if cls._VALID_URL is False:
            return None
        # This does not use has/getattr intentionally - we want to know whether
        # we have cached the regexp for *this* class, whereas getattr would also
        # match the superclass
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = tuple(map(re.compile, variadic(cls._VALID_URL)))
        return next(filter(None, (regex.match(url) for regex in cls._VALID_URL_RE)), None)

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    @classmethod
    def get_temp_id(cls, url):
        try:
            return cls._match_id(url)
        except (IndexError, AttributeError):
            return None

    @classmethod
    def _match_id(cls, url):
        return cls._match_valid_url(url).group('id')

    @classmethod
    def description(cls, *, markdown=True, search_examples=None):
        """Description of the extractor"""
        desc = ''
        if cls._NETRC_MACHINE:
            if markdown:
                desc += f' [*{cls._NETRC_MACHINE}*](## "netrc machine")'
            else:
                desc += f' [{cls._NETRC_MACHINE}]'
        if cls.IE_DESC is False:
            desc += ' [HIDDEN]'
        elif cls.IE_DESC:
            desc += f' {cls.IE_DESC}'
        if cls.SEARCH_KEY:
            desc += f'{";" if cls.IE_DESC else ""} "{cls.SEARCH_KEY}:" prefix'
            if search_examples:
                _COUNTS = ('', '5', '10', 'all')
                desc += f' (e.g. "{cls.SEARCH_KEY}{random.choice(_COUNTS)}:{random.choice(search_examples)}")'
        if not cls.working():
            desc += ' (**Currently broken**)' if markdown else ' (Currently broken)'

        # Escape emojis. Ref: https://github.com/github/markup/issues/1153
        name = (' - **%s**' % re.sub(r':(\w+:)', ':\u200B\\g<1>', cls.IE_NAME)) if markdown else cls.IE_NAME
        return f'{name}:{desc}' if desc else name

    @classmethod
    def is_suitable(cls, age_limit):
        """Test whether the extractor is generally suitable for the given age limit"""
        return not age_restricted(cls.age_limit, age_limit)

    @classmethod
    def supports_login(cls):
        return bool(cls._NETRC_MACHINE)

    @classmethod
    def is_single_video(cls, url):
        """Returns whether the URL is of a single video, None if unknown"""
        if cls.suitable(url):
            return {'video': True, 'playlist': False}.get(cls._RETURN_TYPE)


class LazyLoadSearchExtractor(LazyLoadExtractor):
    pass


class YoutubeBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'YoutubeBaseInfoExtract'


class YoutubeIE(YoutubeBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube'
    _VALID_URL = '(?x)^\n                     (\n                         (?:https?://|//)                                    # http(s):// or protocol-independent URL\n                         (?:(?:(?:(?:\\w+\\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie|kids)?\\.com|\n                            (?:www\\.)?deturl\\.com/www\\.youtube\\.com|\n                            (?:www\\.)?pwnyoutube\\.com|\n                            (?:www\\.)?hooktube\\.com|\n                            (?:www\\.)?yourepeat\\.com|\n                            tube\\.majestyc\\.net|\n                            (?:www\\.)?redirect\\.invidious\\.io|(?:(?:www|dev)\\.)?invidio\\.us|(?:www\\.)?invidious\\.pussthecat\\.org|(?:www\\.)?invidious\\.zee\\.li|(?:www\\.)?invidious\\.ethibox\\.fr|(?:www\\.)?iv\\.ggtyler\\.dev|(?:www\\.)?inv\\.vern\\.i2p|(?:www\\.)?am74vkcrjp2d5v36lcdqgsj2m6x36tbrkhsruoegwfcizzabnfgf5zyd\\.onion|(?:www\\.)?inv\\.riverside\\.rocks|(?:www\\.)?invidious\\.silur\\.me|(?:www\\.)?inv\\.bp\\.projectsegfau\\.lt|(?:www\\.)?invidious\\.g4c3eya4clenolymqbpgwz3q3tawoxw56yhzk4vugqrl6dtu3ejvhjid\\.onion|(?:www\\.)?invidious\\.slipfox\\.xyz|(?:www\\.)?invidious\\.esmail5pdn24shtvieloeedh7ehz3nrwcdivnfhfcedl7gf4kwddhkqd\\.onion|(?:www\\.)?inv\\.vernccvbvyi5qhfzyqengccj7lkove6bjot2xhh5kajhwvidqafczrad\\.onion|(?:www\\.)?invidious\\.tiekoetter\\.com|(?:www\\.)?iv\\.odysfvr23q5wgt7i456o5t3trw2cw5dgn56vbjfbq2m7xsc5vqbqpcyd\\.onion|(?:www\\.)?invidious\\.nerdvpn\\.de|(?:www\\.)?invidious\\.weblibre\\.org|(?:www\\.)?inv\\.odyssey346\\.dev|(?:www\\.)?invidious\\.dhusch\\.de|(?:www\\.)?iv\\.melmac\\.space|(?:www\\.)?watch\\.thekitty\\.zone|(?:www\\.)?invidious\\.privacydev\\.net|(?:www\\.)?ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid\\.onion|(?:www\\.)?invidious\\.drivet\\.xyz|(?:www\\.)?vid\\.priv\\.au|(?:www\\.)?euxxcnhsynwmfidvhjf6uzptsmh4dipkmgdmcmxxuo7tunp3ad2jrwyd\\.onion|(?:www\\.)?inv\\.vern\\.cc|(?:www\\.)?invidious\\.esmailelbob\\.xyz|(?:www\\.)?invidious\\.sethforprivacy\\.com|(?:www\\.)?yt\\.oelrichsgarcia\\.de|(?:www\\.)?yt\\.artemislena\\.eu|(?:www\\.)?invidious\\.flokinet\\.to|(?:www\\.)?invidious\\.baczek\\.me|(?:www\\.)?y\\.com\\.sb|(?:www\\.)?invidious\\.epicsite\\.xyz|(?:www\\.)?invidious\\.lidarshield\\.cloud|(?:www\\.)?yt\\.funami\\.tech|(?:www\\.)?invidious\\.3o7z6yfxhbw7n3za4rss6l434kmv55cgw2vuziwuigpwegswvwzqipyd\\.onion|(?:www\\.)?osbivz6guyeahrwp2lnwyjk2xos342h4ocsxyqrlaopqjuhwn2djiiyd\\.onion|(?:www\\.)?u2cvlit75owumwpy4dj2hsmvkq7nvrclkpht7xgyye2pyoxhpmclkrad\\.onion|(?:(?:www|no)\\.)?invidiou\\.sh|(?:(?:www|fi)\\.)?invidious\\.snopyta\\.org|(?:www\\.)?invidious\\.kabi\\.tk|(?:www\\.)?invidious\\.mastodon\\.host|(?:www\\.)?invidious\\.zapashcanon\\.fr|(?:www\\.)?(?:invidious(?:-us)?|piped)\\.kavin\\.rocks|(?:www\\.)?invidious\\.tinfoil-hat\\.net|(?:www\\.)?invidious\\.himiko\\.cloud|(?:www\\.)?invidious\\.reallyancient\\.tech|(?:www\\.)?invidious\\.tube|(?:www\\.)?invidiou\\.site|(?:www\\.)?invidious\\.site|(?:www\\.)?invidious\\.xyz|(?:www\\.)?invidious\\.nixnet\\.xyz|(?:www\\.)?invidious\\.048596\\.xyz|(?:www\\.)?invidious\\.drycat\\.fr|(?:www\\.)?inv\\.skyn3t\\.in|(?:www\\.)?tube\\.poal\\.co|(?:www\\.)?tube\\.connect\\.cafe|(?:www\\.)?vid\\.wxzm\\.sx|(?:www\\.)?vid\\.mint\\.lgbt|(?:www\\.)?vid\\.puffyan\\.us|(?:www\\.)?yewtu\\.be|(?:www\\.)?yt\\.elukerio\\.org|(?:www\\.)?yt\\.lelux\\.fi|(?:www\\.)?invidious\\.ggc-project\\.de|(?:www\\.)?yt\\.maisputain\\.ovh|(?:www\\.)?ytprivate\\.com|(?:www\\.)?invidious\\.13ad\\.de|(?:www\\.)?invidious\\.toot\\.koeln|(?:www\\.)?invidious\\.fdn\\.fr|(?:www\\.)?watch\\.nettohikari\\.com|(?:www\\.)?invidious\\.namazso\\.eu|(?:www\\.)?invidious\\.silkky\\.cloud|(?:www\\.)?invidious\\.exonip\\.de|(?:www\\.)?invidious\\.riverside\\.rocks|(?:www\\.)?invidious\\.blamefran\\.net|(?:www\\.)?invidious\\.moomoo\\.de|(?:www\\.)?ytb\\.trom\\.tf|(?:www\\.)?yt\\.cyberhost\\.uk|(?:www\\.)?kgg2m7yk5aybusll\\.onion|(?:www\\.)?qklhadlycap4cnod\\.onion|(?:www\\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\\.onion|(?:www\\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\\.onion|(?:www\\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\\.onion|(?:www\\.)?invidious\\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\\.onion|(?:www\\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\\.b32\\.i2p|(?:www\\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\\.onion|(?:www\\.)?w6ijuptxiku4xpnnaetxvnkc5vqcdu7mgns2u77qefoixi63vbvnpnqd\\.onion|(?:www\\.)?kbjggqkzv65ivcqj6bumvp337z6264huv5kpkwuv6gu5yjiskvan7fad\\.onion|(?:www\\.)?grwp24hodrefzvjjuccrkw3mjq4tzhaaq32amf33dzpmuxe7ilepcmad\\.onion|(?:www\\.)?hpniueoejy4opn7bc4ftgazyqjoeqwlvh2uiku2xqku6zpoa4bf5ruid\\.onion|(?:www\\.)?piped\\.kavin\\.rocks|(?:www\\.)?piped\\.tokhmi\\.xyz|(?:www\\.)?piped\\.syncpundit\\.io|(?:www\\.)?piped\\.mha\\.fi|(?:www\\.)?watch\\.whatever\\.social|(?:www\\.)?piped\\.garudalinux\\.org|(?:www\\.)?piped\\.rivo\\.lol|(?:www\\.)?piped-libre\\.kavin\\.rocks|(?:www\\.)?yt\\.jae\\.fi|(?:www\\.)?piped\\.mint\\.lgbt|(?:www\\.)?il\\.ax|(?:www\\.)?piped\\.esmailelbob\\.xyz|(?:www\\.)?piped\\.projectsegfau\\.lt|(?:www\\.)?piped\\.privacydev\\.net|(?:www\\.)?piped\\.palveluntarjoaja\\.eu|(?:www\\.)?piped\\.smnz\\.de|(?:www\\.)?piped\\.adminforge\\.de|(?:www\\.)?watch\\.whatevertinfoil\\.de|(?:www\\.)?piped\\.qdi\\.fi|(?:www\\.)?piped\\.video|(?:www\\.)?piped\\.aeong\\.one|(?:www\\.)?piped\\.moomoo\\.me|(?:www\\.)?piped\\.chauvet\\.pro|(?:www\\.)?watch\\.leptons\\.xyz|(?:www\\.)?pd\\.vern\\.cc|(?:www\\.)?piped\\.hostux\\.net|(?:www\\.)?piped\\.lunar\\.icu|(?:www\\.)?hyperpipe\\.surge\\.sh|(?:www\\.)?hyperpipe\\.esmailelbob\\.xyz|(?:www\\.)?listen\\.whatever\\.social|(?:www\\.)?music\\.adminforge\\.de|\n                            youtube\\.googleapis\\.com)/                        # the various hostnames, with wildcard subdomains\n                         (?:.*?\\#/)?                                          # handle anchor (#/) redirect urls\n                         (?:                                                  # the various things that can precede the ID:\n                             (?:(?:v|embed|e|shorts|live)/(?!videoseries|live_stream))  # v/ or embed/ or e/ or shorts/\n                             |(?:                                             # or the v= param in all its forms\n                                 (?:(?:watch|movie)(?:_popup)?(?:\\.php)?/?)?  # preceding watch(_popup|.php) or nothing (like /?v=xxxx)\n                                 (?:\\?|\\#!?)                                  # the params delimiter ? or # or #!\n                                 (?:.*?[&;])??                                # any other preceding param (like /?s=tuff&v=xxxx or ?s=tuff&amp;v=V36LpHqtcDY)\n                                 v=\n                             )\n                         ))\n                         |(?:\n                            youtu\\.be|                                        # just youtu.be/xxxx\n                            vid\\.plus|                                        # or vid.plus/xxxx\n                            zwearz\\.com/watch|                                # or zwearz.com/watch/xxxx\n                            (?:www\\.)?redirect\\.invidious\\.io|(?:(?:www|dev)\\.)?invidio\\.us|(?:www\\.)?invidious\\.pussthecat\\.org|(?:www\\.)?invidious\\.zee\\.li|(?:www\\.)?invidious\\.ethibox\\.fr|(?:www\\.)?iv\\.ggtyler\\.dev|(?:www\\.)?inv\\.vern\\.i2p|(?:www\\.)?am74vkcrjp2d5v36lcdqgsj2m6x36tbrkhsruoegwfcizzabnfgf5zyd\\.onion|(?:www\\.)?inv\\.riverside\\.rocks|(?:www\\.)?invidious\\.silur\\.me|(?:www\\.)?inv\\.bp\\.projectsegfau\\.lt|(?:www\\.)?invidious\\.g4c3eya4clenolymqbpgwz3q3tawoxw56yhzk4vugqrl6dtu3ejvhjid\\.onion|(?:www\\.)?invidious\\.slipfox\\.xyz|(?:www\\.)?invidious\\.esmail5pdn24shtvieloeedh7ehz3nrwcdivnfhfcedl7gf4kwddhkqd\\.onion|(?:www\\.)?inv\\.vernccvbvyi5qhfzyqengccj7lkove6bjot2xhh5kajhwvidqafczrad\\.onion|(?:www\\.)?invidious\\.tiekoetter\\.com|(?:www\\.)?iv\\.odysfvr23q5wgt7i456o5t3trw2cw5dgn56vbjfbq2m7xsc5vqbqpcyd\\.onion|(?:www\\.)?invidious\\.nerdvpn\\.de|(?:www\\.)?invidious\\.weblibre\\.org|(?:www\\.)?inv\\.odyssey346\\.dev|(?:www\\.)?invidious\\.dhusch\\.de|(?:www\\.)?iv\\.melmac\\.space|(?:www\\.)?watch\\.thekitty\\.zone|(?:www\\.)?invidious\\.privacydev\\.net|(?:www\\.)?ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid\\.onion|(?:www\\.)?invidious\\.drivet\\.xyz|(?:www\\.)?vid\\.priv\\.au|(?:www\\.)?euxxcnhsynwmfidvhjf6uzptsmh4dipkmgdmcmxxuo7tunp3ad2jrwyd\\.onion|(?:www\\.)?inv\\.vern\\.cc|(?:www\\.)?invidious\\.esmailelbob\\.xyz|(?:www\\.)?invidious\\.sethforprivacy\\.com|(?:www\\.)?yt\\.oelrichsgarcia\\.de|(?:www\\.)?yt\\.artemislena\\.eu|(?:www\\.)?invidious\\.flokinet\\.to|(?:www\\.)?invidious\\.baczek\\.me|(?:www\\.)?y\\.com\\.sb|(?:www\\.)?invidious\\.epicsite\\.xyz|(?:www\\.)?invidious\\.lidarshield\\.cloud|(?:www\\.)?yt\\.funami\\.tech|(?:www\\.)?invidious\\.3o7z6yfxhbw7n3za4rss6l434kmv55cgw2vuziwuigpwegswvwzqipyd\\.onion|(?:www\\.)?osbivz6guyeahrwp2lnwyjk2xos342h4ocsxyqrlaopqjuhwn2djiiyd\\.onion|(?:www\\.)?u2cvlit75owumwpy4dj2hsmvkq7nvrclkpht7xgyye2pyoxhpmclkrad\\.onion|(?:(?:www|no)\\.)?invidiou\\.sh|(?:(?:www|fi)\\.)?invidious\\.snopyta\\.org|(?:www\\.)?invidious\\.kabi\\.tk|(?:www\\.)?invidious\\.mastodon\\.host|(?:www\\.)?invidious\\.zapashcanon\\.fr|(?:www\\.)?(?:invidious(?:-us)?|piped)\\.kavin\\.rocks|(?:www\\.)?invidious\\.tinfoil-hat\\.net|(?:www\\.)?invidious\\.himiko\\.cloud|(?:www\\.)?invidious\\.reallyancient\\.tech|(?:www\\.)?invidious\\.tube|(?:www\\.)?invidiou\\.site|(?:www\\.)?invidious\\.site|(?:www\\.)?invidious\\.xyz|(?:www\\.)?invidious\\.nixnet\\.xyz|(?:www\\.)?invidious\\.048596\\.xyz|(?:www\\.)?invidious\\.drycat\\.fr|(?:www\\.)?inv\\.skyn3t\\.in|(?:www\\.)?tube\\.poal\\.co|(?:www\\.)?tube\\.connect\\.cafe|(?:www\\.)?vid\\.wxzm\\.sx|(?:www\\.)?vid\\.mint\\.lgbt|(?:www\\.)?vid\\.puffyan\\.us|(?:www\\.)?yewtu\\.be|(?:www\\.)?yt\\.elukerio\\.org|(?:www\\.)?yt\\.lelux\\.fi|(?:www\\.)?invidious\\.ggc-project\\.de|(?:www\\.)?yt\\.maisputain\\.ovh|(?:www\\.)?ytprivate\\.com|(?:www\\.)?invidious\\.13ad\\.de|(?:www\\.)?invidious\\.toot\\.koeln|(?:www\\.)?invidious\\.fdn\\.fr|(?:www\\.)?watch\\.nettohikari\\.com|(?:www\\.)?invidious\\.namazso\\.eu|(?:www\\.)?invidious\\.silkky\\.cloud|(?:www\\.)?invidious\\.exonip\\.de|(?:www\\.)?invidious\\.riverside\\.rocks|(?:www\\.)?invidious\\.blamefran\\.net|(?:www\\.)?invidious\\.moomoo\\.de|(?:www\\.)?ytb\\.trom\\.tf|(?:www\\.)?yt\\.cyberhost\\.uk|(?:www\\.)?kgg2m7yk5aybusll\\.onion|(?:www\\.)?qklhadlycap4cnod\\.onion|(?:www\\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\\.onion|(?:www\\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\\.onion|(?:www\\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\\.onion|(?:www\\.)?invidious\\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\\.onion|(?:www\\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\\.b32\\.i2p|(?:www\\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\\.onion|(?:www\\.)?w6ijuptxiku4xpnnaetxvnkc5vqcdu7mgns2u77qefoixi63vbvnpnqd\\.onion|(?:www\\.)?kbjggqkzv65ivcqj6bumvp337z6264huv5kpkwuv6gu5yjiskvan7fad\\.onion|(?:www\\.)?grwp24hodrefzvjjuccrkw3mjq4tzhaaq32amf33dzpmuxe7ilepcmad\\.onion|(?:www\\.)?hpniueoejy4opn7bc4ftgazyqjoeqwlvh2uiku2xqku6zpoa4bf5ruid\\.onion|(?:www\\.)?piped\\.kavin\\.rocks|(?:www\\.)?piped\\.tokhmi\\.xyz|(?:www\\.)?piped\\.syncpundit\\.io|(?:www\\.)?piped\\.mha\\.fi|(?:www\\.)?watch\\.whatever\\.social|(?:www\\.)?piped\\.garudalinux\\.org|(?:www\\.)?piped\\.rivo\\.lol|(?:www\\.)?piped-libre\\.kavin\\.rocks|(?:www\\.)?yt\\.jae\\.fi|(?:www\\.)?piped\\.mint\\.lgbt|(?:www\\.)?il\\.ax|(?:www\\.)?piped\\.esmailelbob\\.xyz|(?:www\\.)?piped\\.projectsegfau\\.lt|(?:www\\.)?piped\\.privacydev\\.net|(?:www\\.)?piped\\.palveluntarjoaja\\.eu|(?:www\\.)?piped\\.smnz\\.de|(?:www\\.)?piped\\.adminforge\\.de|(?:www\\.)?watch\\.whatevertinfoil\\.de|(?:www\\.)?piped\\.qdi\\.fi|(?:www\\.)?piped\\.video|(?:www\\.)?piped\\.aeong\\.one|(?:www\\.)?piped\\.moomoo\\.me|(?:www\\.)?piped\\.chauvet\\.pro|(?:www\\.)?watch\\.leptons\\.xyz|(?:www\\.)?pd\\.vern\\.cc|(?:www\\.)?piped\\.hostux\\.net|(?:www\\.)?piped\\.lunar\\.icu|(?:www\\.)?hyperpipe\\.surge\\.sh|(?:www\\.)?hyperpipe\\.esmailelbob\\.xyz|(?:www\\.)?listen\\.whatever\\.social|(?:www\\.)?music\\.adminforge\\.de\n                         )/\n                         |(?:www\\.)?cleanvideosearch\\.com/media/action/yt/watch\\?videoId=\n                         )\n                     )?                                                       # all until now is optional -> you can pass the naked ID\n                     (?P<id>[0-9A-Za-z_-]{11})                                # here is it! the YouTube video ID\n                     (?(1).+)?                                                # if we found the ID, everything can follow\n                     (?:\\#|$)'
    IE_DESC = 'YouTube'
    age_limit = 18
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        from ..utils import parse_qs

        qs = parse_qs(url)
        if qs.get('list', [None])[0]:
            return False
        return super().suitable(url)


class YoutubeTabBaseInfoExtractor(YoutubeBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'YoutubeTabBaseInfoExtract'


class YoutubeClipIE(YoutubeTabBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:clip'
    _VALID_URL = 'https?://(?:www\\.)?youtube\\.com/clip/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class YoutubeFavouritesIE(YoutubeBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:favorites'
    _VALID_URL = ':ytfav(?:ou?rite)?s?'
    IE_DESC = 'YouTube liked videos; ":ytfav" keyword (requires cookies)'


class YoutubeNotificationsIE(YoutubeTabBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:notif'
    _VALID_URL = ':ytnotif(?:ication)?s?'
    IE_DESC = 'YouTube notifications; ":ytnotif" keyword (requires cookies)'


class YoutubeFeedsInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:feeds'


class YoutubeHistoryIE(YoutubeFeedsInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:history'
    _VALID_URL = ':ythis(?:tory)?'
    IE_DESC = 'Youtube watch history; ":ythis" keyword (requires cookies)'


class YoutubeTabIE(YoutubeTabBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:tab'
    _VALID_URL = '(?x:\n        https?://\n            (?!consent\\.)(?:\\w+\\.)?\n            (?:\n                youtube(?:kids)?\\.com|\n                (?:www\\.)?redirect\\.invidious\\.io|(?:(?:www|dev)\\.)?invidio\\.us|(?:www\\.)?invidious\\.pussthecat\\.org|(?:www\\.)?invidious\\.zee\\.li|(?:www\\.)?invidious\\.ethibox\\.fr|(?:www\\.)?iv\\.ggtyler\\.dev|(?:www\\.)?inv\\.vern\\.i2p|(?:www\\.)?am74vkcrjp2d5v36lcdqgsj2m6x36tbrkhsruoegwfcizzabnfgf5zyd\\.onion|(?:www\\.)?inv\\.riverside\\.rocks|(?:www\\.)?invidious\\.silur\\.me|(?:www\\.)?inv\\.bp\\.projectsegfau\\.lt|(?:www\\.)?invidious\\.g4c3eya4clenolymqbpgwz3q3tawoxw56yhzk4vugqrl6dtu3ejvhjid\\.onion|(?:www\\.)?invidious\\.slipfox\\.xyz|(?:www\\.)?invidious\\.esmail5pdn24shtvieloeedh7ehz3nrwcdivnfhfcedl7gf4kwddhkqd\\.onion|(?:www\\.)?inv\\.vernccvbvyi5qhfzyqengccj7lkove6bjot2xhh5kajhwvidqafczrad\\.onion|(?:www\\.)?invidious\\.tiekoetter\\.com|(?:www\\.)?iv\\.odysfvr23q5wgt7i456o5t3trw2cw5dgn56vbjfbq2m7xsc5vqbqpcyd\\.onion|(?:www\\.)?invidious\\.nerdvpn\\.de|(?:www\\.)?invidious\\.weblibre\\.org|(?:www\\.)?inv\\.odyssey346\\.dev|(?:www\\.)?invidious\\.dhusch\\.de|(?:www\\.)?iv\\.melmac\\.space|(?:www\\.)?watch\\.thekitty\\.zone|(?:www\\.)?invidious\\.privacydev\\.net|(?:www\\.)?ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid\\.onion|(?:www\\.)?invidious\\.drivet\\.xyz|(?:www\\.)?vid\\.priv\\.au|(?:www\\.)?euxxcnhsynwmfidvhjf6uzptsmh4dipkmgdmcmxxuo7tunp3ad2jrwyd\\.onion|(?:www\\.)?inv\\.vern\\.cc|(?:www\\.)?invidious\\.esmailelbob\\.xyz|(?:www\\.)?invidious\\.sethforprivacy\\.com|(?:www\\.)?yt\\.oelrichsgarcia\\.de|(?:www\\.)?yt\\.artemislena\\.eu|(?:www\\.)?invidious\\.flokinet\\.to|(?:www\\.)?invidious\\.baczek\\.me|(?:www\\.)?y\\.com\\.sb|(?:www\\.)?invidious\\.epicsite\\.xyz|(?:www\\.)?invidious\\.lidarshield\\.cloud|(?:www\\.)?yt\\.funami\\.tech|(?:www\\.)?invidious\\.3o7z6yfxhbw7n3za4rss6l434kmv55cgw2vuziwuigpwegswvwzqipyd\\.onion|(?:www\\.)?osbivz6guyeahrwp2lnwyjk2xos342h4ocsxyqrlaopqjuhwn2djiiyd\\.onion|(?:www\\.)?u2cvlit75owumwpy4dj2hsmvkq7nvrclkpht7xgyye2pyoxhpmclkrad\\.onion|(?:(?:www|no)\\.)?invidiou\\.sh|(?:(?:www|fi)\\.)?invidious\\.snopyta\\.org|(?:www\\.)?invidious\\.kabi\\.tk|(?:www\\.)?invidious\\.mastodon\\.host|(?:www\\.)?invidious\\.zapashcanon\\.fr|(?:www\\.)?(?:invidious(?:-us)?|piped)\\.kavin\\.rocks|(?:www\\.)?invidious\\.tinfoil-hat\\.net|(?:www\\.)?invidious\\.himiko\\.cloud|(?:www\\.)?invidious\\.reallyancient\\.tech|(?:www\\.)?invidious\\.tube|(?:www\\.)?invidiou\\.site|(?:www\\.)?invidious\\.site|(?:www\\.)?invidious\\.xyz|(?:www\\.)?invidious\\.nixnet\\.xyz|(?:www\\.)?invidious\\.048596\\.xyz|(?:www\\.)?invidious\\.drycat\\.fr|(?:www\\.)?inv\\.skyn3t\\.in|(?:www\\.)?tube\\.poal\\.co|(?:www\\.)?tube\\.connect\\.cafe|(?:www\\.)?vid\\.wxzm\\.sx|(?:www\\.)?vid\\.mint\\.lgbt|(?:www\\.)?vid\\.puffyan\\.us|(?:www\\.)?yewtu\\.be|(?:www\\.)?yt\\.elukerio\\.org|(?:www\\.)?yt\\.lelux\\.fi|(?:www\\.)?invidious\\.ggc-project\\.de|(?:www\\.)?yt\\.maisputain\\.ovh|(?:www\\.)?ytprivate\\.com|(?:www\\.)?invidious\\.13ad\\.de|(?:www\\.)?invidious\\.toot\\.koeln|(?:www\\.)?invidious\\.fdn\\.fr|(?:www\\.)?watch\\.nettohikari\\.com|(?:www\\.)?invidious\\.namazso\\.eu|(?:www\\.)?invidious\\.silkky\\.cloud|(?:www\\.)?invidious\\.exonip\\.de|(?:www\\.)?invidious\\.riverside\\.rocks|(?:www\\.)?invidious\\.blamefran\\.net|(?:www\\.)?invidious\\.moomoo\\.de|(?:www\\.)?ytb\\.trom\\.tf|(?:www\\.)?yt\\.cyberhost\\.uk|(?:www\\.)?kgg2m7yk5aybusll\\.onion|(?:www\\.)?qklhadlycap4cnod\\.onion|(?:www\\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\\.onion|(?:www\\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\\.onion|(?:www\\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\\.onion|(?:www\\.)?invidious\\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\\.onion|(?:www\\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\\.b32\\.i2p|(?:www\\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\\.onion|(?:www\\.)?w6ijuptxiku4xpnnaetxvnkc5vqcdu7mgns2u77qefoixi63vbvnpnqd\\.onion|(?:www\\.)?kbjggqkzv65ivcqj6bumvp337z6264huv5kpkwuv6gu5yjiskvan7fad\\.onion|(?:www\\.)?grwp24hodrefzvjjuccrkw3mjq4tzhaaq32amf33dzpmuxe7ilepcmad\\.onion|(?:www\\.)?hpniueoejy4opn7bc4ftgazyqjoeqwlvh2uiku2xqku6zpoa4bf5ruid\\.onion|(?:www\\.)?piped\\.kavin\\.rocks|(?:www\\.)?piped\\.tokhmi\\.xyz|(?:www\\.)?piped\\.syncpundit\\.io|(?:www\\.)?piped\\.mha\\.fi|(?:www\\.)?watch\\.whatever\\.social|(?:www\\.)?piped\\.garudalinux\\.org|(?:www\\.)?piped\\.rivo\\.lol|(?:www\\.)?piped-libre\\.kavin\\.rocks|(?:www\\.)?yt\\.jae\\.fi|(?:www\\.)?piped\\.mint\\.lgbt|(?:www\\.)?il\\.ax|(?:www\\.)?piped\\.esmailelbob\\.xyz|(?:www\\.)?piped\\.projectsegfau\\.lt|(?:www\\.)?piped\\.privacydev\\.net|(?:www\\.)?piped\\.palveluntarjoaja\\.eu|(?:www\\.)?piped\\.smnz\\.de|(?:www\\.)?piped\\.adminforge\\.de|(?:www\\.)?watch\\.whatevertinfoil\\.de|(?:www\\.)?piped\\.qdi\\.fi|(?:www\\.)?piped\\.video|(?:www\\.)?piped\\.aeong\\.one|(?:www\\.)?piped\\.moomoo\\.me|(?:www\\.)?piped\\.chauvet\\.pro|(?:www\\.)?watch\\.leptons\\.xyz|(?:www\\.)?pd\\.vern\\.cc|(?:www\\.)?piped\\.hostux\\.net|(?:www\\.)?piped\\.lunar\\.icu|(?:www\\.)?hyperpipe\\.surge\\.sh|(?:www\\.)?hyperpipe\\.esmailelbob\\.xyz|(?:www\\.)?listen\\.whatever\\.social|(?:www\\.)?music\\.adminforge\\.de\n            )/\n            (?:\n                (?P<channel_type>channel|c|user|browse)/|\n                (?P<not_channel>\n                    feed/|hashtag/|\n                    (?:playlist|watch)\\?.*?\\blist=\n                )|\n                (?!(?:channel|c|user|playlist|watch|w|v|embed|e|live|watch_popup|clip|shorts|movies|results|search|shared|hashtag|trending|explore|feed|feeds|browse|oembed|get_video_info|iframe_api|s/player|source|storefront|oops|index|account|t/terms|about|upload|signin|logout)\\b)  # Direct URLs\n            )\n            (?P<id>[^/?\\#&]+)\n    )'
    IE_DESC = 'YouTube Tabs'
    _RETURN_TYPE = 'any'

    @classmethod
    def suitable(cls, url):
        return False if YoutubeIE.suitable(url) else super().suitable(url)


class YoutubeLivestreamEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'YoutubeLivestreamEmbed'
    _VALID_URL = 'https?://(?:\\w+\\.)?youtube\\.com/embed/live_stream/?\\?(?:[^#]+&)?channel=(?P<id>[^&#]+)'
    IE_DESC = 'YouTube livestream embeds'


class YoutubePlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:playlist'
    _VALID_URL = '(?x)(?:\n                        (?:https?://)?\n                        (?:\\w+\\.)?\n                        (?:\n                            (?:\n                                youtube(?:kids)?\\.com|\n                                (?:www\\.)?redirect\\.invidious\\.io|(?:(?:www|dev)\\.)?invidio\\.us|(?:www\\.)?invidious\\.pussthecat\\.org|(?:www\\.)?invidious\\.zee\\.li|(?:www\\.)?invidious\\.ethibox\\.fr|(?:www\\.)?iv\\.ggtyler\\.dev|(?:www\\.)?inv\\.vern\\.i2p|(?:www\\.)?am74vkcrjp2d5v36lcdqgsj2m6x36tbrkhsruoegwfcizzabnfgf5zyd\\.onion|(?:www\\.)?inv\\.riverside\\.rocks|(?:www\\.)?invidious\\.silur\\.me|(?:www\\.)?inv\\.bp\\.projectsegfau\\.lt|(?:www\\.)?invidious\\.g4c3eya4clenolymqbpgwz3q3tawoxw56yhzk4vugqrl6dtu3ejvhjid\\.onion|(?:www\\.)?invidious\\.slipfox\\.xyz|(?:www\\.)?invidious\\.esmail5pdn24shtvieloeedh7ehz3nrwcdivnfhfcedl7gf4kwddhkqd\\.onion|(?:www\\.)?inv\\.vernccvbvyi5qhfzyqengccj7lkove6bjot2xhh5kajhwvidqafczrad\\.onion|(?:www\\.)?invidious\\.tiekoetter\\.com|(?:www\\.)?iv\\.odysfvr23q5wgt7i456o5t3trw2cw5dgn56vbjfbq2m7xsc5vqbqpcyd\\.onion|(?:www\\.)?invidious\\.nerdvpn\\.de|(?:www\\.)?invidious\\.weblibre\\.org|(?:www\\.)?inv\\.odyssey346\\.dev|(?:www\\.)?invidious\\.dhusch\\.de|(?:www\\.)?iv\\.melmac\\.space|(?:www\\.)?watch\\.thekitty\\.zone|(?:www\\.)?invidious\\.privacydev\\.net|(?:www\\.)?ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid\\.onion|(?:www\\.)?invidious\\.drivet\\.xyz|(?:www\\.)?vid\\.priv\\.au|(?:www\\.)?euxxcnhsynwmfidvhjf6uzptsmh4dipkmgdmcmxxuo7tunp3ad2jrwyd\\.onion|(?:www\\.)?inv\\.vern\\.cc|(?:www\\.)?invidious\\.esmailelbob\\.xyz|(?:www\\.)?invidious\\.sethforprivacy\\.com|(?:www\\.)?yt\\.oelrichsgarcia\\.de|(?:www\\.)?yt\\.artemislena\\.eu|(?:www\\.)?invidious\\.flokinet\\.to|(?:www\\.)?invidious\\.baczek\\.me|(?:www\\.)?y\\.com\\.sb|(?:www\\.)?invidious\\.epicsite\\.xyz|(?:www\\.)?invidious\\.lidarshield\\.cloud|(?:www\\.)?yt\\.funami\\.tech|(?:www\\.)?invidious\\.3o7z6yfxhbw7n3za4rss6l434kmv55cgw2vuziwuigpwegswvwzqipyd\\.onion|(?:www\\.)?osbivz6guyeahrwp2lnwyjk2xos342h4ocsxyqrlaopqjuhwn2djiiyd\\.onion|(?:www\\.)?u2cvlit75owumwpy4dj2hsmvkq7nvrclkpht7xgyye2pyoxhpmclkrad\\.onion|(?:(?:www|no)\\.)?invidiou\\.sh|(?:(?:www|fi)\\.)?invidious\\.snopyta\\.org|(?:www\\.)?invidious\\.kabi\\.tk|(?:www\\.)?invidious\\.mastodon\\.host|(?:www\\.)?invidious\\.zapashcanon\\.fr|(?:www\\.)?(?:invidious(?:-us)?|piped)\\.kavin\\.rocks|(?:www\\.)?invidious\\.tinfoil-hat\\.net|(?:www\\.)?invidious\\.himiko\\.cloud|(?:www\\.)?invidious\\.reallyancient\\.tech|(?:www\\.)?invidious\\.tube|(?:www\\.)?invidiou\\.site|(?:www\\.)?invidious\\.site|(?:www\\.)?invidious\\.xyz|(?:www\\.)?invidious\\.nixnet\\.xyz|(?:www\\.)?invidious\\.048596\\.xyz|(?:www\\.)?invidious\\.drycat\\.fr|(?:www\\.)?inv\\.skyn3t\\.in|(?:www\\.)?tube\\.poal\\.co|(?:www\\.)?tube\\.connect\\.cafe|(?:www\\.)?vid\\.wxzm\\.sx|(?:www\\.)?vid\\.mint\\.lgbt|(?:www\\.)?vid\\.puffyan\\.us|(?:www\\.)?yewtu\\.be|(?:www\\.)?yt\\.elukerio\\.org|(?:www\\.)?yt\\.lelux\\.fi|(?:www\\.)?invidious\\.ggc-project\\.de|(?:www\\.)?yt\\.maisputain\\.ovh|(?:www\\.)?ytprivate\\.com|(?:www\\.)?invidious\\.13ad\\.de|(?:www\\.)?invidious\\.toot\\.koeln|(?:www\\.)?invidious\\.fdn\\.fr|(?:www\\.)?watch\\.nettohikari\\.com|(?:www\\.)?invidious\\.namazso\\.eu|(?:www\\.)?invidious\\.silkky\\.cloud|(?:www\\.)?invidious\\.exonip\\.de|(?:www\\.)?invidious\\.riverside\\.rocks|(?:www\\.)?invidious\\.blamefran\\.net|(?:www\\.)?invidious\\.moomoo\\.de|(?:www\\.)?ytb\\.trom\\.tf|(?:www\\.)?yt\\.cyberhost\\.uk|(?:www\\.)?kgg2m7yk5aybusll\\.onion|(?:www\\.)?qklhadlycap4cnod\\.onion|(?:www\\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\\.onion|(?:www\\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\\.onion|(?:www\\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\\.onion|(?:www\\.)?invidious\\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\\.onion|(?:www\\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\\.b32\\.i2p|(?:www\\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\\.onion|(?:www\\.)?w6ijuptxiku4xpnnaetxvnkc5vqcdu7mgns2u77qefoixi63vbvnpnqd\\.onion|(?:www\\.)?kbjggqkzv65ivcqj6bumvp337z6264huv5kpkwuv6gu5yjiskvan7fad\\.onion|(?:www\\.)?grwp24hodrefzvjjuccrkw3mjq4tzhaaq32amf33dzpmuxe7ilepcmad\\.onion|(?:www\\.)?hpniueoejy4opn7bc4ftgazyqjoeqwlvh2uiku2xqku6zpoa4bf5ruid\\.onion|(?:www\\.)?piped\\.kavin\\.rocks|(?:www\\.)?piped\\.tokhmi\\.xyz|(?:www\\.)?piped\\.syncpundit\\.io|(?:www\\.)?piped\\.mha\\.fi|(?:www\\.)?watch\\.whatever\\.social|(?:www\\.)?piped\\.garudalinux\\.org|(?:www\\.)?piped\\.rivo\\.lol|(?:www\\.)?piped-libre\\.kavin\\.rocks|(?:www\\.)?yt\\.jae\\.fi|(?:www\\.)?piped\\.mint\\.lgbt|(?:www\\.)?il\\.ax|(?:www\\.)?piped\\.esmailelbob\\.xyz|(?:www\\.)?piped\\.projectsegfau\\.lt|(?:www\\.)?piped\\.privacydev\\.net|(?:www\\.)?piped\\.palveluntarjoaja\\.eu|(?:www\\.)?piped\\.smnz\\.de|(?:www\\.)?piped\\.adminforge\\.de|(?:www\\.)?watch\\.whatevertinfoil\\.de|(?:www\\.)?piped\\.qdi\\.fi|(?:www\\.)?piped\\.video|(?:www\\.)?piped\\.aeong\\.one|(?:www\\.)?piped\\.moomoo\\.me|(?:www\\.)?piped\\.chauvet\\.pro|(?:www\\.)?watch\\.leptons\\.xyz|(?:www\\.)?pd\\.vern\\.cc|(?:www\\.)?piped\\.hostux\\.net|(?:www\\.)?piped\\.lunar\\.icu|(?:www\\.)?hyperpipe\\.surge\\.sh|(?:www\\.)?hyperpipe\\.esmailelbob\\.xyz|(?:www\\.)?listen\\.whatever\\.social|(?:www\\.)?music\\.adminforge\\.de\n                            )\n                            /.*?\\?.*?\\blist=\n                        )?\n                        (?P<id>(?:(?:PL|LL|EC|UU|FL|RD|UL|TL|PU|OLAK5uy_)[0-9A-Za-z-_]{10,}|RDMM|WL|LL|LM))\n                     )'
    IE_DESC = 'YouTube playlists'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        if YoutubeTabIE.suitable(url):
            return False
        from ..utils import parse_qs
        qs = parse_qs(url)
        if qs.get('v', [None])[0]:
            return False
        return super().suitable(url)


class YoutubeRecommendedIE(YoutubeFeedsInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:recommended'
    _VALID_URL = 'https?://(?:www\\.)?youtube\\.com/?(?:[?#]|$)|:ytrec(?:ommended)?'
    IE_DESC = 'YouTube recommended videos; ":ytrec" keyword'


class YoutubeSearchDateIE(YoutubeTabBaseInfoExtractor, LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:search:date'
    _VALID_URL = 'ytsearchdate(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'YouTube search, newest videos first'
    SEARCH_KEY = 'ytsearchdate'
    _RETURN_TYPE = 'playlist'


class YoutubeSearchIE(YoutubeTabBaseInfoExtractor, LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:search'
    _VALID_URL = 'ytsearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'YouTube search'
    SEARCH_KEY = 'ytsearch'
    _RETURN_TYPE = 'playlist'


class YoutubeSearchURLIE(YoutubeTabBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:search_url'
    _VALID_URL = 'https?://(?:www\\.)?youtube\\.com/(?:results|search)\\?([^#]+&)?(?:search_query|q)=(?:[^&]+)(?:[&#]|$)'
    IE_DESC = 'YouTube search URLs with sorting and filter support'
    _RETURN_TYPE = 'playlist'


class YoutubeMusicSearchURLIE(YoutubeTabBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:music:search_url'
    _VALID_URL = 'https?://music\\.youtube\\.com/search\\?([^#]+&)?(?:search_query|q)=(?:[^&]+)(?:[&#]|$)'
    IE_DESC = 'YouTube music search URLs with selectable sections, e.g. #songs'
    _RETURN_TYPE = 'playlist'


class YoutubeSubscriptionsIE(YoutubeFeedsInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:subscriptions'
    _VALID_URL = ':ytsub(?:scription)?s?'
    IE_DESC = 'YouTube subscriptions feed; ":ytsubs" keyword (requires cookies)'


class YoutubeTruncatedIDIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:truncated_id'
    _VALID_URL = 'https?://(?:www\\.)?youtube\\.com/watch\\?v=(?P<id>[0-9A-Za-z_-]{1,10})$'
    IE_DESC = False


class YoutubeTruncatedURLIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:truncated_url'
    _VALID_URL = '(?x)\n        (?:https?://)?\n        (?:\\w+\\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie)?\\.com/\n        (?:watch\\?(?:\n            feature=[a-z_]+|\n            annotation_id=annotation_[^&]+|\n            x-yt-cl=[0-9]+|\n            hl=[^&]*|\n            t=[0-9]+\n        )?\n        |\n            attribution_link\\?a=[^&]+\n        )\n        $\n    '
    IE_DESC = False


class YoutubeYtBeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'YoutubeYtBe'
    _VALID_URL = 'https?://youtu\\.be/(?P<id>[0-9A-Za-z_-]{11})/*?.*?\\blist=(?P<playlist_id>(?:(?:PL|LL|EC|UU|FL|RD|UL|TL|PU|OLAK5uy_)[0-9A-Za-z-_]{10,}|RDMM|WL|LL|LM))'
    IE_DESC = 'youtu.be'
    _RETURN_TYPE = 'video'


class YoutubeYtUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:user'
    _VALID_URL = 'ytuser:(?P<id>.+)'
    IE_DESC = 'YouTube user videos; "ytuser:" prefix'


class YoutubeWatchLaterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:watchlater'
    _VALID_URL = ':ytwatchlater'
    IE_DESC = 'Youtube watch later list; ":ytwatchlater" keyword (requires cookies)'


class YoutubeShortsAudioPivotIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:shorts:pivot:audio'
    _VALID_URL = 'https?://(?:www\\.)?youtube\\.com/source/(?P<id>[\\w-]{11})/shorts'
    IE_DESC = 'YouTube Shorts audio pivot (Shorts using audio of a given video)'


class YoutubeConsentRedirectIE(YoutubeBaseInfoExtractor):
    _module = 'yt_dlp.extractor.youtube'
    IE_NAME = 'youtube:consent'
    _VALID_URL = 'https?://consent\\.youtube\\.com/m\\?'
    IE_DESC = False
    _RETURN_TYPE = 'video'


class ABCIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.abc'
    IE_NAME = 'abc.net.au'
    _VALID_URL = 'https?://(?:www\\.)?abc\\.net\\.au/(?:news|btn)/(?:[^/]+/){1,4}(?P<id>\\d{5,})'
    _RETURN_TYPE = 'video'


class ABCIViewIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.abc'
    IE_NAME = 'abc.net.au:iview'
    _VALID_URL = 'https?://iview\\.abc\\.net\\.au/(?:[^/]+/)*video/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class ABCIViewShowSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.abc'
    IE_NAME = 'abc.net.au:iview:showseries'
    _VALID_URL = 'https?://iview\\.abc\\.net\\.au/show/(?P<id>[^/]+)(?:/series/\\d+)?$'
    _RETURN_TYPE = 'any'


class AbcNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.abcnews'
    IE_NAME = 'abcnews'
    _VALID_URL = 'https?://abcnews\\.go\\.com/(?:[^/]+/)+(?P<display_id>[0-9a-z-]+)/story\\?id=(?P<id>\\d+)'
    _RETURN_TYPE = 'any'


class AMPIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.amp'
    IE_NAME = 'AMP'


class AbcNewsVideoIE(AMPIE):
    _module = 'yt_dlp.extractor.abcnews'
    IE_NAME = 'abcnews:video'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            abcnews\\.go\\.com/\n                            (?:\n                                (?:[^/]+/)*video/(?P<display_id>[0-9a-z-]+)-|\n                                video/(?:embed|itemfeed)\\?.*?\\bid=\n                            )|\n                            fivethirtyeight\\.abcnews\\.go\\.com/video/embed/\\d+/\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class ABCOTVSIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.abcotvs'
    IE_NAME = 'abcotvs'
    _VALID_URL = 'https?://(?P<site>abc(?:7(?:news|ny|chicago)?|11|13|30)|6abc)\\.com(?:(?:/[^/]+)*/(?P<display_id>[^/]+))?/(?P<id>\\d+)'
    IE_DESC = 'ABC Owned Television Stations'
    _RETURN_TYPE = 'video'


class ABCOTVSClipsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.abcotvs'
    IE_NAME = 'abcotvs:clips'
    _VALID_URL = 'https?://clips\\.abcotvs\\.com/(?:[^/]+/)*video/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AbemaTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.abematv'
    IE_NAME = 'AbemaTVBase'


class AbemaTVIE(AbemaTVBaseIE):
    _module = 'yt_dlp.extractor.abematv'
    IE_NAME = 'AbemaTV'
    _VALID_URL = 'https?://abema\\.tv/(?P<type>now-on-air|video/episode|channels/.+?/slots)/(?P<id>[^?/]+)'
    _NETRC_MACHINE = 'abematv'
    _RETURN_TYPE = 'video'


class AbemaTVTitleIE(AbemaTVBaseIE):
    _module = 'yt_dlp.extractor.abematv'
    IE_NAME = 'AbemaTVTitle'
    _VALID_URL = 'https?://abema\\.tv/video/title/(?P<id>[^?/]+)'
    _RETURN_TYPE = 'playlist'


class AcademicEarthCourseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.academicearth'
    IE_NAME = 'AcademicEarth:Course'
    _VALID_URL = '^https?://(?:www\\.)?academicearth\\.org/playlists/(?P<id>[^?#/]+)'
    _RETURN_TYPE = 'playlist'


class ACastBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.acast'
    IE_NAME = 'ACastBase'


class ACastIE(ACastBaseIE):
    _module = 'yt_dlp.extractor.acast'
    IE_NAME = 'acast'
    _VALID_URL = '(?x:\n                    https?://\n                        (?:\n                            (?:(?:embed|www)\\.)?acast\\.com/|\n                            play\\.acast\\.com/s/\n                        )\n                        (?P<channel>[^/]+)/(?P<id>[^/#?"]+)\n                    )'
    _RETURN_TYPE = 'video'


class ACastChannelIE(ACastBaseIE):
    _module = 'yt_dlp.extractor.acast'
    IE_NAME = 'acast:channel'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:www\\.)?acast\\.com/|\n                            play\\.acast\\.com/s/\n                        )\n                        (?P<id>[^/#?]+)\n                    '
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if ACastIE.suitable(url) else super(ACastChannelIE, cls).suitable(url)


class AcFunVideoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.acfun'
    IE_NAME = 'AcFunVideoBase'


class AcFunVideoIE(AcFunVideoBaseIE):
    _module = 'yt_dlp.extractor.acfun'
    IE_NAME = 'AcFunVideo'
    _VALID_URL = 'https?://www\\.acfun\\.cn/v/ac(?P<id>[_\\d]+)'
    _RETURN_TYPE = 'video'


class AcFunBangumiIE(AcFunVideoBaseIE):
    _module = 'yt_dlp.extractor.acfun'
    IE_NAME = 'AcFunBangumi'
    _VALID_URL = 'https?://www\\.acfun\\.cn/bangumi/(?P<id>aa[_\\d]+)'
    _RETURN_TYPE = 'video'


class ADNIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.adn'
    IE_NAME = 'ADN'
    _VALID_URL = 'https?://(?:www\\.)?(?:animation|anime)digitalnetwork\\.fr/video/[^/]+/(?P<id>\\d+)'
    IE_DESC = 'Animation Digital Network'
    _NETRC_MACHINE = 'animationdigitalnetwork'
    _RETURN_TYPE = 'video'


class AdobeConnectIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.adobeconnect'
    IE_NAME = 'AdobeConnect'
    _VALID_URL = 'https?://\\w+\\.adobeconnect\\.com/(?P<id>[\\w-]+)'


class AdobeTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.adobetv'
    IE_NAME = 'AdobeTVBase'


class AdobeTVEmbedIE(AdobeTVBaseIE):
    _module = 'yt_dlp.extractor.adobetv'
    IE_NAME = 'adobetv:embed'
    _VALID_URL = 'https?://tv\\.adobe\\.com/embed/\\d+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AdobeTVIE(AdobeTVBaseIE):
    _module = 'yt_dlp.extractor.adobetv'
    IE_NAME = 'adobetv'
    _VALID_URL = 'https?://tv\\.adobe\\.com/(?:(?P<language>fr|de|es|jp)/)?watch/(?P<show_urlname>[^/]+)/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class AdobeTVPlaylistBaseIE(AdobeTVBaseIE):
    _module = 'yt_dlp.extractor.adobetv'
    IE_NAME = 'AdobeTVPlaylistBase'


class AdobeTVShowIE(AdobeTVPlaylistBaseIE):
    _module = 'yt_dlp.extractor.adobetv'
    IE_NAME = 'adobetv:show'
    _VALID_URL = 'https?://tv\\.adobe\\.com/(?:(?P<language>fr|de|es|jp)/)?show/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class AdobeTVChannelIE(AdobeTVPlaylistBaseIE):
    _module = 'yt_dlp.extractor.adobetv'
    IE_NAME = 'adobetv:channel'
    _VALID_URL = 'https?://tv\\.adobe\\.com/(?:(?P<language>fr|de|es|jp)/)?channel/(?P<id>[^/]+)(?:/(?P<category_urlname>[^/]+))?'
    _RETURN_TYPE = 'playlist'


class AdobeTVVideoIE(AdobeTVBaseIE):
    _module = 'yt_dlp.extractor.adobetv'
    IE_NAME = 'adobetv:video'
    _VALID_URL = 'https?://video\\.tv\\.adobe\\.com/v/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AdobePassIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.adobepass'
    IE_NAME = 'AdobePass'


class TurnerBaseIE(AdobePassIE):
    _module = 'yt_dlp.extractor.turner'
    IE_NAME = 'TurnerBase'


class AdultSwimIE(TurnerBaseIE):
    _module = 'yt_dlp.extractor.adultswim'
    IE_NAME = 'AdultSwim'
    _VALID_URL = 'https?://(?:www\\.)?adultswim\\.com/videos/(?P<show_path>[^/?#]+)(?:/(?P<episode_path>[^/?#]+))?'
    _RETURN_TYPE = 'any'


class AeonCoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.aeonco'
    IE_NAME = 'AeonCo'
    _VALID_URL = 'https?://(?:www\\.)?aeon\\.co/videos/(?P<id>[^/?]+)'
    _RETURN_TYPE = 'video'


class AfreecaTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.afreecatv'
    IE_NAME = 'afreecatv'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:(?:live|afbbs|www)\\.)?afreeca(?:tv)?\\.com(?::\\d+)?\n                            (?:\n                                /app/(?:index|read_ucc_bbs)\\.cgi|\n                                /player/[Pp]layer\\.(?:swf|html)\n                            )\\?.*?\\bnTitleNo=|\n                            vod\\.afreecatv\\.com/(PLAYER/STATION|player)/\n                        )\n                        (?P<id>\\d+)\n                    '
    IE_DESC = 'afreecatv.com'
    _NETRC_MACHINE = 'afreecatv'
    _RETURN_TYPE = 'any'


class AfreecaTVLiveIE(AfreecaTVIE):
    _module = 'yt_dlp.extractor.afreecatv'
    IE_NAME = 'afreecatv:live'
    _VALID_URL = 'https?://play\\.afreeca(?:tv)?\\.com/(?P<id>[^/]+)(?:/(?P<bno>\\d+))?'
    IE_DESC = 'afreecatv.com'
    _NETRC_MACHINE = 'afreecatv'
    _RETURN_TYPE = 'video'


class AfreecaTVUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.afreecatv'
    IE_NAME = 'afreecatv:user'
    _VALID_URL = 'https?://bj\\.afreeca(?:tv)?\\.com/(?P<id>[^/]+)/vods/?(?P<slug_type>[^/]+)?'
    _RETURN_TYPE = 'playlist'


class TokFMAuditionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.agora'
    IE_NAME = 'tokfm:audition'
    _VALID_URL = '(?:https?://audycje\\.tokfm\\.pl/audycja/|tokfm:audition:)(?P<id>\\d+),?'
    _RETURN_TYPE = 'playlist'


class TokFMPodcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.agora'
    IE_NAME = 'tokfm:podcast'
    _VALID_URL = '(?:https?://audycje\\.tokfm\\.pl/podcast/|tokfm:podcast:)(?P<id>\\d+),?'
    _RETURN_TYPE = 'video'


class WyborczaPodcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.agora'
    IE_NAME = 'WyborczaPodcast'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?(?:\n            wyborcza\\.pl/podcast(?:/0,172673\\.html)?|\n            wysokieobcasy\\.pl/wysokie-obcasy/0,176631\\.html\n        )(?:\\?(?:[^&#]+?&)*podcast=(?P<id>\\d+))?\n    '
    _RETURN_TYPE = 'any'


class WyborczaVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.agora'
    IE_NAME = 'wyborcza:video'
    _VALID_URL = '(?:wyborcza:video:|https?://wyborcza\\.pl/(?:api-)?video/)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AirMozillaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.airmozilla'
    IE_NAME = 'AirMozilla'
    _VALID_URL = 'https?://air\\.mozilla\\.org/(?P<id>[0-9a-z-]+)/?'
    _RETURN_TYPE = 'video'


class AirTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.airtv'
    IE_NAME = 'AirTV'
    _VALID_URL = 'https?://www\\.air\\.tv/watch\\?v=(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class AitubeKZVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.aitube'
    IE_NAME = 'AitubeKZVideo'
    _VALID_URL = 'https?://aitube\\.kz/(?:video|embed/)\\?(?:[^\\?]+)?id=(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class AlJazeeraIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.aljazeera'
    IE_NAME = 'AlJazeera'
    _VALID_URL = 'https?://(?P<base>\\w+\\.aljazeera\\.\\w+)/(?P<type>programs?/[^/]+|(?:feature|video|new)s)?/\\d{4}/\\d{1,2}/\\d{1,2}/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class AlphaPornoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.alphaporno'
    IE_NAME = 'AlphaPorno'
    _VALID_URL = 'https?://(?:www\\.)?alphaporno\\.com/videos/(?P<id>[^/]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class AmaraIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.amara'
    IE_NAME = 'Amara'
    _VALID_URL = 'https?://(?:www\\.)?amara\\.org/(?:\\w+/)?videos/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class AluraIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.alura'
    IE_NAME = 'Alura'
    _VALID_URL = 'https?://(?:cursos\\.)?alura\\.com\\.br/course/(?P<course_name>[^/]+)/task/(?P<id>\\d+)'
    _NETRC_MACHINE = 'alura'
    _RETURN_TYPE = 'video'


class AluraCourseIE(AluraIE):
    _module = 'yt_dlp.extractor.alura'
    IE_NAME = 'AluraCourse'
    _VALID_URL = 'https?://(?:cursos\\.)?alura\\.com\\.br/course/(?P<id>[^/]+)'
    _NETRC_MACHINE = 'aluracourse'

    @classmethod
    def suitable(cls, url):
        return False if AluraIE.suitable(url) else super(AluraCourseIE, cls).suitable(url)


class AmazonStoreIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.amazon'
    IE_NAME = 'AmazonStore'
    _VALID_URL = 'https?://(?:www\\.)?amazon\\.(?:[a-z]{2,3})(?:\\.[a-z]{2})?/(?:[^/]+/)?(?:dp|gp/product)/(?P<id>[^/&#$?]+)'
    _RETURN_TYPE = 'playlist'


class AmazonReviewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.amazon'
    IE_NAME = 'AmazonReviews'
    _VALID_URL = 'https?://(?:www\\.)?amazon\\.(?:[a-z]{2,3})(?:\\.[a-z]{2})?/gp/customer-reviews/(?P<id>[^/&#$?]+)'
    _RETURN_TYPE = 'video'


class AmazonMiniTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.amazonminitv'
    IE_NAME = 'AmazonMiniTVBase'


class AmazonMiniTVIE(AmazonMiniTVBaseIE):
    _module = 'yt_dlp.extractor.amazonminitv'
    IE_NAME = 'AmazonMiniTV'
    _VALID_URL = '(?:https?://(?:www\\.)?amazon\\.in/minitv/tp/|amazonminitv:(?:amzn1\\.dv\\.gti\\.)?)(?P<id>[a-f0-9-]+)'
    _RETURN_TYPE = 'video'


class AmazonMiniTVSeasonIE(AmazonMiniTVBaseIE):
    _module = 'yt_dlp.extractor.amazonminitv'
    IE_NAME = 'amazonminitv:season'
    _VALID_URL = 'amazonminitv:season:(?:amzn1\\.dv\\.gti\\.)?(?P<id>[a-f0-9-]+)'
    IE_DESC = 'Amazon MiniTV Season, "minitv:season:" prefix'
    _RETURN_TYPE = 'playlist'


class AmazonMiniTVSeriesIE(AmazonMiniTVBaseIE):
    _module = 'yt_dlp.extractor.amazonminitv'
    IE_NAME = 'amazonminitv:series'
    _VALID_URL = 'amazonminitv:series:(?:amzn1\\.dv\\.gti\\.)?(?P<id>[a-f0-9-]+)'
    IE_DESC = 'Amazon MiniTV Series, "minitv:series:" prefix'
    _RETURN_TYPE = 'playlist'


class AmericasTestKitchenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.americastestkitchen'
    IE_NAME = 'AmericasTestKitchen'
    _VALID_URL = 'https?://(?:www\\.)?(?:americastestkitchen|cooks(?:country|illustrated))\\.com/(?:cooks(?:country|illustrated)/)?(?P<resource_type>episode|videos)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AmericasTestKitchenSeasonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.americastestkitchen'
    IE_NAME = 'AmericasTestKitchenSeason'
    _VALID_URL = 'https?://(?:www\\.)?(?P<show>americastestkitchen|(?P<cooks>cooks(?:country|illustrated)))\\.com(?:(?:/(?P<show2>cooks(?:country|illustrated)))?(?:/?$|(?<!ated)(?<!ated\\.com)/episodes/browse/season_(?P<season>\\d+)))'
    _RETURN_TYPE = 'playlist'


class AnchorFMEpisodeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.anchorfm'
    IE_NAME = 'AnchorFMEpisode'
    _VALID_URL = 'https?://anchor\\.fm/(?P<channel_name>\\w+)/(?:embed/)?episodes/[\\w-]+-(?P<episode_id>\\w+)'
    _RETURN_TYPE = 'video'


class AngelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.angel'
    IE_NAME = 'Angel'
    _VALID_URL = 'https?://(?:www\\.)?angel\\.com/watch/(?P<series>[^/?#]+)/episode/(?P<id>[\\w-]+)/season-(?P<season_number>\\d+)/episode-(?P<episode_number>\\d+)/(?P<title>[^/?#]+)'
    _RETURN_TYPE = 'video'


class AnvatoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.anvato'
    IE_NAME = 'Anvato'
    _VALID_URL = 'anvato:(?P<access_key_or_mcp>[^:]+):(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AllocineIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.allocine'
    IE_NAME = 'Allocine'
    _VALID_URL = 'https?://(?:www\\.)?allocine\\.fr/(?:article|video|film)/(?:fichearticle_gen_carticle=|player_gen_cmedia=|fichefilm_gen_cfilm=|video-)(?P<id>[0-9]+)(?:\\.html)?'
    _RETURN_TYPE = 'video'


class AliExpressLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.aliexpress'
    IE_NAME = 'AliExpressLive'
    _VALID_URL = 'https?://live\\.aliexpress\\.com/live/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class Alsace20TVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.alsace20tv'
    IE_NAME = 'Alsace20TVBase'


class Alsace20TVIE(Alsace20TVBaseIE):
    _module = 'yt_dlp.extractor.alsace20tv'
    IE_NAME = 'Alsace20TV'
    _VALID_URL = 'https?://(?:www\\.)?alsace20\\.tv/(?:[\\w-]+/)+[\\w-]+-(?P<id>[\\w]+)'
    _RETURN_TYPE = 'video'


class Alsace20TVEmbedIE(Alsace20TVBaseIE):
    _module = 'yt_dlp.extractor.alsace20tv'
    IE_NAME = 'Alsace20TVEmbed'
    _VALID_URL = 'https?://(?:www\\.)?alsace20\\.tv/emb/(?P<id>[\\w]+)'
    _RETURN_TYPE = 'video'


class APAIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.apa'
    IE_NAME = 'APA'
    _VALID_URL = '(?P<base_url>https?://[^/]+\\.apa\\.at)/embed/(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class AparatIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.aparat'
    IE_NAME = 'Aparat'
    _VALID_URL = 'https?://(?:www\\.)?aparat\\.com/(?:v/|video/video/embed/videohash/)(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'


class AppleConnectIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.appleconnect'
    IE_NAME = 'AppleConnect'
    _VALID_URL = 'https?://itunes\\.apple\\.com/\\w{0,2}/?post/(?:id)?sa\\.(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class AppleTrailersIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.appletrailers'
    IE_NAME = 'appletrailers'
    _VALID_URL = 'https?://(?:www\\.|movie)?trailers\\.apple\\.com/(?:trailers|ca)/(?P<company>[^/]+)/(?P<movie>[^/]+)'
    _RETURN_TYPE = 'playlist'


class AppleTrailersSectionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.appletrailers'
    IE_NAME = 'appletrailers:section'
    _VALID_URL = 'https?://(?:www\\.)?trailers\\.apple\\.com/#section=(?P<id>justadded|exclusive|justhd|mostpopular|moviestudios)'
    _RETURN_TYPE = 'playlist'


class ApplePodcastsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.applepodcasts'
    IE_NAME = 'ApplePodcasts'
    _VALID_URL = 'https?://podcasts\\.apple\\.com/(?:[^/]+/)?podcast(?:/[^/]+){1,2}.*?\\bi=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ArchiveOrgIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.archiveorg'
    IE_NAME = 'archive.org'
    _VALID_URL = 'https?://(?:www\\.)?archive\\.org/(?:details|embed)/(?P<id>[^?#]+)(?:[?].*)?$'
    IE_DESC = 'archive.org video and audio'
    _RETURN_TYPE = 'any'


class YoutubeWebArchiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.archiveorg'
    IE_NAME = 'web.archive:youtube'
    _VALID_URL = '(?x)(?:(?P<prefix>ytarchive:)|\n            (?:https?://)?web\\.archive\\.org/\n            (?:web/)?(?:(?P<date>[0-9]{14})?[0-9A-Za-z_*]*/)?  # /web and the version index is optional\n            (?:https?(?::|%3[Aa])//)?(?:\n                (?:\\w+\\.)?youtube\\.com(?::(?:80|443))?/watch(?:\\.php)?(?:\\?|%3[fF])(?:[^\\#]+(?:&|%26))?v(?:=|%3[dD])  # Youtube URL\n                |(?:wayback-fakeurl\\.archive\\.org/yt/)  # Or the internal fake url\n            )\n        )(?P<id>[0-9A-Za-z_-]{11})\n        (?(prefix)\n            (?::(?P<date2>[0-9]{14}))?$|\n            (?:%26|[#&]|$)\n        )'
    IE_DESC = 'web.archive.org saved youtube videos, "ytarchive:" prefix'
    _RETURN_TYPE = 'video'


class VLiveWebArchiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.archiveorg'
    IE_NAME = 'web.archive:vlive'
    _VALID_URL = '(?x)\n            (?:https?://)?web\\.archive\\.org/\n            (?:web/)?(?:(?P<date>[0-9]{14})?[0-9A-Za-z_*]*/)?  # /web and the version index is optional\n            (?:https?(?::|%3[Aa])//)?(?:\n                (?:(?:www|m)\\.)?vlive\\.tv(?::(?:80|443))?/(?:video|embed)/(?P<id>[0-9]+)  # VLive URL\n            )\n        '
    IE_DESC = 'web.archive.org saved vlive videos'
    _RETURN_TYPE = 'video'


class ArcPublishingIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.arcpublishing'
    IE_NAME = 'ArcPublishing'
    _VALID_URL = 'arcpublishing:(?P<org>[a-z]+):(?P<id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})'


class ArkenaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.arkena'
    IE_NAME = 'Arkena'
    _VALID_URL = '(?x)\n                        https?://\n                            (?:\n                                video\\.(?:arkena|qbrick)\\.com/play2/embed/player\\?|\n                                play\\.arkena\\.com/(?:config|embed)/avp/v\\d/player/media/(?P<id>[^/]+)/[^/]+/(?P<account_id>\\d+)\n                            )\n                        '
    _RETURN_TYPE = 'video'


class ARDMediathekBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ard'
    IE_NAME = 'ARDMediathekBase'


class ARDBetaMediathekIE(ARDMediathekBaseIE):
    _module = 'yt_dlp.extractor.ard'
    IE_NAME = 'ARDBetaMediathek'
    _VALID_URL = '(?x)https://\n        (?:(?:beta|www)\\.)?ardmediathek\\.de/\n        (?:(?P<client>[^/]+)/)?\n        (?:player|live|video|(?P<playlist>sendung|sammlung))/\n        (?:(?P<display_id>(?(playlist)[^?#]+?|[^?#]+))/)?\n        (?P<id>(?(playlist)|Y3JpZDovL)[a-zA-Z0-9]+)\n        (?(playlist)/(?P<season>\\d+)?/?(?:[?#]|$))'
    age_limit = 12
    _RETURN_TYPE = 'video'


class ARDIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ard'
    IE_NAME = 'ARD'
    _VALID_URL = '(?P<mainurl>https?://(?:www\\.)?daserste\\.de/(?:[^/?#&]+/)+(?P<id>[^/?#&]+))\\.html'
    _RETURN_TYPE = 'video'


class ARDMediathekIE(ARDMediathekBaseIE):
    _module = 'yt_dlp.extractor.ard'
    IE_NAME = 'ARD:mediathek'
    _VALID_URL = '^https?://(?:(?:(?:www|classic)\\.)?ardmediathek\\.de|mediathek\\.(?:daserste|rbb-online)\\.de|one\\.ard\\.de)/(?:.*/)(?P<video_id>[0-9]+|[^0-9][^/\\?]+)[^/\\?]*(?:\\?.*)?'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if ARDBetaMediathekIE.suitable(url) else super(ARDMediathekIE, cls).suitable(url)


class ArteTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.arte'
    IE_NAME = 'ArteTVBase'


class ArteTVIE(ArteTVBaseIE):
    _module = 'yt_dlp.extractor.arte'
    IE_NAME = 'ArteTV'
    _VALID_URL = '(?x)\n                    (?:https?://\n                        (?:\n                            (?:www\\.)?arte\\.tv/(?P<lang>fr|de|en|es|it|pl)/videos|\n                            api\\.arte\\.tv/api/player/v\\d+/config/(?P<lang_2>fr|de|en|es|it|pl)\n                        )\n                    |arte://program)\n                        /(?P<id>\\d{6}-\\d{3}-[AF]|LIVE)\n                    '
    _RETURN_TYPE = 'video'


class ArteTVEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.arte'
    IE_NAME = 'ArteTVEmbed'
    _VALID_URL = 'https?://(?:www\\.)?arte\\.tv/player/v\\d+/index\\.php\\?.*?\\bjson_url=.+'
    _RETURN_TYPE = 'video'


class ArteTVPlaylistIE(ArteTVBaseIE):
    _module = 'yt_dlp.extractor.arte'
    IE_NAME = 'ArteTVPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?arte\\.tv/(?P<lang>fr|de|en|es|it|pl)/videos/(?P<id>RC-\\d{6})'
    _RETURN_TYPE = 'playlist'


class ArteTVCategoryIE(ArteTVBaseIE):
    _module = 'yt_dlp.extractor.arte'
    IE_NAME = 'ArteTVCategory'
    _VALID_URL = 'https?://(?:www\\.)?arte\\.tv/(?P<lang>fr|de|en|es|it|pl)/videos/(?P<id>[\\w-]+(?:/[\\w-]+)*)/?\\s*$'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (
            not any(ie.suitable(url) for ie in (ArteTVIE, ArteTVPlaylistIE, ))
            and super().suitable(url))


class ArnesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.arnes'
    IE_NAME = 'video.arnes.si'
    _VALID_URL = 'https?://video\\.arnes\\.si/(?:[a-z]{2}/)?(?:watch|embed|api/(?:asset|public/video))/(?P<id>[0-9a-zA-Z]{12})'
    IE_DESC = 'Arnes Video'
    _RETURN_TYPE = 'video'


class AsianCrushBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.asiancrush'
    IE_NAME = 'AsianCrushBase'


class AsianCrushIE(AsianCrushBaseIE):
    _module = 'yt_dlp.extractor.asiancrush'
    IE_NAME = 'AsianCrush'
    _VALID_URL = 'https?://(?:www\\.)?(?P<host>(?:(?:asiancrush|yuyutv|midnightpulp)\\.com|(?:cocoro|retrocrush)\\.tv))/video/(?:[^/]+/)?0+(?P<id>\\d+)v\\b'
    age_limit = 13
    _RETURN_TYPE = 'video'


class AsianCrushPlaylistIE(AsianCrushBaseIE):
    _module = 'yt_dlp.extractor.asiancrush'
    IE_NAME = 'AsianCrushPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?(?P<host>(?:(?:asiancrush|yuyutv|midnightpulp)\\.com|(?:cocoro|retrocrush)\\.tv))/series/0+(?P<id>\\d+)s\\b'
    _RETURN_TYPE = 'playlist'


class AtresPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.atresplayer'
    IE_NAME = 'AtresPlayer'
    _VALID_URL = 'https?://(?:www\\.)?atresplayer\\.com/[^/]+/[^/]+/[^/]+/[^/]+/(?P<display_id>.+?)_(?P<id>[0-9a-f]{24})'
    _NETRC_MACHINE = 'atresplayer'
    _RETURN_TYPE = 'video'


class AtScaleConfEventIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.atscaleconf'
    IE_NAME = 'AtScaleConfEvent'
    _VALID_URL = 'https?://(?:www\\.)?atscaleconference\\.com/events/(?P<id>[^/&$?]+)'
    _RETURN_TYPE = 'playlist'


class ATTTechChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.atttechchannel'
    IE_NAME = 'ATTTechChannel'
    _VALID_URL = 'https?://techchannel\\.att\\.com/play-video\\.cfm/([^/]+/)*(?P<id>.+)'
    _RETURN_TYPE = 'video'


class ATVAtIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.atvat'
    IE_NAME = 'ATVAt'
    _VALID_URL = 'https?://(?:www\\.)?atv\\.at/tv/(?:[^/]+/){2,3}(?P<id>.*)'
    _RETURN_TYPE = 'video'


class AudiMediaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.audimedia'
    IE_NAME = 'AudiMedia'
    _VALID_URL = 'https?://(?:www\\.)?audi-mediacenter\\.com/(?:en|de)/audimediatv/(?:video/)?(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class AudioBoomIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.audioboom'
    IE_NAME = 'AudioBoom'
    _VALID_URL = 'https?://(?:www\\.)?audioboom\\.com/(?:boos|posts)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class AudiodraftBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.audiodraft'
    IE_NAME = 'AudiodraftBase'


class AudiodraftCustomIE(AudiodraftBaseIE):
    _module = 'yt_dlp.extractor.audiodraft'
    IE_NAME = 'Audiodraft:custom'
    _VALID_URL = 'https?://(?:[-\\w]+)\\.audiodraft\\.com/entry/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AudiodraftGenericIE(AudiodraftBaseIE):
    _module = 'yt_dlp.extractor.audiodraft'
    IE_NAME = 'Audiodraft:generic'
    _VALID_URL = 'https?://www\\.audiodraft\\.com/contests/[^/#]+#entries&eid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AudiomackIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.audiomack'
    IE_NAME = 'audiomack'
    _VALID_URL = 'https?://(?:www\\.)?audiomack\\.com/(?:song/|(?=.+/song/))(?P<id>[\\w/-]+)'
    _RETURN_TYPE = 'video'


class AudiomackAlbumIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.audiomack'
    IE_NAME = 'audiomack:album'
    _VALID_URL = 'https?://(?:www\\.)?audiomack\\.com/(?:album/|(?=.+/album/))(?P<id>[\\w/-]+)'
    _RETURN_TYPE = 'playlist'


class AudiusBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.audius'
    IE_NAME = 'AudiusBase'


class AudiusIE(AudiusBaseIE):
    _module = 'yt_dlp.extractor.audius'
    IE_NAME = 'Audius'
    _VALID_URL = '(?x)https?://(?:www\\.)?(?:audius\\.co/(?P<uploader>[\\w\\d-]+)(?!/album|/playlist)/(?P<title>\\S+))'
    IE_DESC = 'Audius.co'
    _RETURN_TYPE = 'video'


class AudiusTrackIE(AudiusIE):
    _module = 'yt_dlp.extractor.audius'
    IE_NAME = 'audius:track'
    _VALID_URL = '(?x)(?:audius:)(?:https?://(?:www\\.)?.+/v1/tracks/)?(?P<track_id>\\w+)'
    IE_DESC = 'Audius track ID or API link. Prepend with "audius:"'


class AudiusPlaylistIE(AudiusBaseIE):
    _module = 'yt_dlp.extractor.audius'
    IE_NAME = 'audius:playlist'
    _VALID_URL = 'https?://(?:www\\.)?audius\\.co/(?P<uploader>[\\w\\d-]+)/(?:album|playlist)/(?P<title>\\S+)'
    IE_DESC = 'Audius.co playlists'
    _RETURN_TYPE = 'playlist'


class AudiusProfileIE(AudiusPlaylistIE):
    _module = 'yt_dlp.extractor.audius'
    IE_NAME = 'audius:artist'
    _VALID_URL = 'https?://(?:www)?audius\\.co/(?P<id>[^\\/]+)/?(?:[?#]|$)'
    IE_DESC = 'Audius.co profile/artist pages'
    _RETURN_TYPE = 'playlist'


class AWAANIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.awaan'
    IE_NAME = 'AWAAN'
    _VALID_URL = 'https?://(?:www\\.)?(?:awaan|dcndigital)\\.ae/(?:#/)?show/(?P<show_id>\\d+)/[^/]+(?:/(?P<id>\\d+)/(?P<season_id>\\d+))?'


class AWAANBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.awaan'
    IE_NAME = 'AWAANBase'


class AWAANVideoIE(AWAANBaseIE):
    _module = 'yt_dlp.extractor.awaan'
    IE_NAME = 'awaan:video'
    _VALID_URL = 'https?://(?:www\\.)?(?:awaan|dcndigital)\\.ae/(?:#/)?(?:video(?:/[^/]+)?|media|catchup/[^/]+/[^/]+)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AWAANLiveIE(AWAANBaseIE):
    _module = 'yt_dlp.extractor.awaan'
    IE_NAME = 'awaan:live'
    _VALID_URL = 'https?://(?:www\\.)?(?:awaan|dcndigital)\\.ae/(?:#/)?live/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class AWAANSeasonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.awaan'
    IE_NAME = 'awaan:season'
    _VALID_URL = 'https?://(?:www\\.)?(?:awaan|dcndigital)\\.ae/(?:#/)?program/(?:(?P<show_id>\\d+)|season/(?P<season_id>\\d+))'
    _RETURN_TYPE = 'playlist'


class AZMedienIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.azmedien'
    IE_NAME = 'AZMedien'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.|tv\\.)?\n                        (?P<host>\n                            telezueri\\.ch|\n                            telebaern\\.tv|\n                            telem1\\.ch|\n                            tvo-online\\.ch\n                        )/\n                        [^/]+/\n                        (?P<id>\n                            [^/]+-(?P<article_id>\\d+)\n                        )\n                        (?:\n                            \\#video=\n                            (?P<kaltura_id>\n                                [_0-9a-z]+\n                            )\n                        )?\n                    '
    IE_DESC = 'AZ Medien videos'
    _RETURN_TYPE = 'video'


class BaiduVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.baidu'
    IE_NAME = 'BaiduVideo'
    _VALID_URL = 'https?://v\\.baidu\\.com/(?P<type>[a-z]+)/(?P<id>\\d+)\\.htm'
    IE_DESC = '百度视频'
    _RETURN_TYPE = 'playlist'


class BanByeBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.banbye'
    IE_NAME = 'BanByeBase'


class BanByeIE(BanByeBaseIE):
    _module = 'yt_dlp.extractor.banbye'
    IE_NAME = 'BanBye'
    _VALID_URL = 'https?://(?:www\\.)?banbye.com/(?:en/)?watch/(?P<id>\\w+)'
    _RETURN_TYPE = 'any'


class BanByeChannelIE(BanByeBaseIE):
    _module = 'yt_dlp.extractor.banbye'
    IE_NAME = 'BanByeChannel'
    _VALID_URL = 'https?://(?:www\\.)?banbye.com/(?:en/)?channel/(?P<id>\\w+)'
    _RETURN_TYPE = 'playlist'


class BrightcoveNewBaseIE(AdobePassIE):
    _module = 'yt_dlp.extractor.brightcove'
    IE_NAME = 'BrightcoveNewBase'


class BandaiChannelIE(BrightcoveNewBaseIE):
    _module = 'yt_dlp.extractor.bandaichannel'
    IE_NAME = 'bandaichannel'
    _VALID_URL = 'https?://(?:www\\.)?b-ch\\.com/titles/(?P<id>\\d+/\\d+)'
    _RETURN_TYPE = 'video'


class BandcampIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bandcamp'
    IE_NAME = 'Bandcamp'
    _VALID_URL = 'https?://(?P<uploader>[^/]+)\\.bandcamp\\.com/track/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class BandcampAlbumIE(BandcampIE):
    _module = 'yt_dlp.extractor.bandcamp'
    IE_NAME = 'Bandcamp:album'
    _VALID_URL = 'https?://(?:(?P<subdomain>[^.]+)\\.)?bandcamp\\.com/album/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False
                if BandcampWeeklyIE.suitable(url) or BandcampIE.suitable(url)
                else super(BandcampAlbumIE, cls).suitable(url))


class BandcampWeeklyIE(BandcampIE):
    _module = 'yt_dlp.extractor.bandcamp'
    IE_NAME = 'Bandcamp:weekly'
    _VALID_URL = 'https?://(?:www\\.)?bandcamp\\.com/?\\?(?:.*?&)?show=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class BandcampUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bandcamp'
    IE_NAME = 'Bandcamp:user'
    _VALID_URL = 'https?://(?!www\\.)(?P<id>[^.]+)\\.bandcamp\\.com(?:/music)?/?(?:[#?]|$)'
    _RETURN_TYPE = 'playlist'


class BannedVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bannedvideo'
    IE_NAME = 'BannedVideo'
    _VALID_URL = 'https?://(?:www\\.)?banned\\.video/watch\\?id=(?P<id>[0-f]{24})'
    _RETURN_TYPE = 'video'


class BBCCoUkIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'bbc.co.uk'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?bbc\\.co\\.uk/\n                        (?:\n                            programmes/(?!articles/)|\n                            iplayer(?:/[^/]+)?/(?:episode/|playlist/)|\n                            music/(?:clips|audiovideo/popular)[/#]|\n                            radio/player/|\n                            sounds/play/|\n                            events/[^/]+/play/[^/]+/\n                        )\n                        (?P<id>(?:[pbml][\\da-z]{7}|w[\\da-z]{7,14}))(?!/(?:episodes|broadcasts|clips))\n                    '
    IE_DESC = 'BBC iPlayer'
    _NETRC_MACHINE = 'bbc'
    _RETURN_TYPE = 'video'


class BBCCoUkArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'bbc.co.uk:article'
    _VALID_URL = 'https?://(?:www\\.)?bbc\\.co\\.uk/programmes/articles/(?P<id>[a-zA-Z0-9]+)'
    IE_DESC = 'BBC articles'
    _RETURN_TYPE = 'playlist'


class BBCCoUkIPlayerPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'BBCCoUkIPlayerPlaylistBase'


class BBCCoUkIPlayerEpisodesIE(BBCCoUkIPlayerPlaylistBaseIE):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'bbc.co.uk:iplayer:episodes'
    _VALID_URL = 'https?://(?:www\\.)?bbc\\.co\\.uk/iplayer/episodes/(?P<id>(?:[pbml][\\da-z]{7}|w[\\da-z]{7,14}))'
    _RETURN_TYPE = 'playlist'


class BBCCoUkIPlayerGroupIE(BBCCoUkIPlayerPlaylistBaseIE):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'bbc.co.uk:iplayer:group'
    _VALID_URL = 'https?://(?:www\\.)?bbc\\.co\\.uk/iplayer/group/(?P<id>(?:[pbml][\\da-z]{7}|w[\\da-z]{7,14}))'
    _RETURN_TYPE = 'playlist'


class BBCCoUkPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'BBCCoUkPlaylistBase'


class BBCCoUkPlaylistIE(BBCCoUkPlaylistBaseIE):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'bbc.co.uk:playlist'
    _VALID_URL = 'https?://(?:www\\.)?bbc\\.co\\.uk/programmes/(?P<id>(?:[pbml][\\da-z]{7}|w[\\da-z]{7,14}))/(?:episodes|broadcasts|clips)'
    _RETURN_TYPE = 'playlist'


class BBCIE(BBCCoUkIE):
    _module = 'yt_dlp.extractor.bbc'
    IE_NAME = 'bbc'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?(?:\n            bbc\\.(?:com|co\\.uk)|\n            bbcnewsd73hkzno2ini43t4gblxvycyac5aw4gnv7t2rccijh7745uqd\\.onion|\n            bbcweb3hytmzhn5d532owbu6oqadra5z3ar726vq5kgwwn6aucdccrad\\.onion\n        )/(?:[^/]+/)+(?P<id>[^/#?]+)'
    IE_DESC = 'BBC'
    _NETRC_MACHINE = 'bbc'
    _RETURN_TYPE = 'any'

    @classmethod
    def suitable(cls, url):
        EXCLUDE_IE = (BBCCoUkIE, BBCCoUkArticleIE, BBCCoUkIPlayerEpisodesIE, BBCCoUkIPlayerGroupIE, BBCCoUkPlaylistIE)
        return (False if any(ie.suitable(url) for ie in EXCLUDE_IE)
                else super(BBCIE, cls).suitable(url))


class BeegIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.beeg'
    IE_NAME = 'Beeg'
    _VALID_URL = 'https?://(?:www\\.)?beeg\\.(?:com(?:/video)?)/-?(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class BehindKinkIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.behindkink'
    IE_NAME = 'BehindKink'
    _VALID_URL = 'https?://(?:www\\.)?behindkink\\.com/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<id>[^/#?_]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class BellMediaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bellmedia'
    IE_NAME = 'BellMedia'
    _VALID_URL = '(?x)https?://(?:www\\.)?\n        (?P<domain>\n            (?:\n                ctv|\n                tsn|\n                bnn(?:bloomberg)?|\n                thecomedynetwork|\n                discovery|\n                discoveryvelocity|\n                sciencechannel|\n                investigationdiscovery|\n                animalplanet|\n                bravo|\n                mtv|\n                space|\n                etalk|\n                marilyn\n            )\\.ca|\n            (?:much|cp24)\\.com\n        )/.*?(?:\\b(?:vid(?:eoid)?|clipId)=|-vid|~|%7E|/(?:episode)?)(?P<id>[0-9]{6,})'
    _RETURN_TYPE = 'video'


class BeatBumpVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.beatbump'
    IE_NAME = 'BeatBumpVideo'
    _VALID_URL = 'https://beatbump\\.ml/listen\\?id=(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class BeatBumpPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.beatbump'
    IE_NAME = 'BeatBumpPlaylist'
    _VALID_URL = 'https://beatbump\\.ml/(?:release\\?id=|artist/|playlist/)(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class BeatportIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.beatport'
    IE_NAME = 'Beatport'
    _VALID_URL = 'https?://(?:www\\.|pro\\.)?beatport\\.com/track/(?P<display_id>[^/]+)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class BerufeTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.berufetv'
    IE_NAME = 'BerufeTV'
    _VALID_URL = 'https?://(?:www\\.)?web\\.arbeitsagentur\\.de/berufetv/[^?#]+/film;filmId=(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class MTVServicesInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'MTVServicesInfoExtract'


class BetIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.bet'
    IE_NAME = 'Bet'
    _VALID_URL = 'https?://(?:www\\.)?bet\\.com/(?:[^/]+/)+(?P<id>.+?)\\.html'
    _RETURN_TYPE = 'video'


class BFIPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bfi'
    IE_NAME = 'bfi:player'
    _VALID_URL = 'https?://player\\.bfi\\.org\\.uk/[^/]+/film/watch-(?P<id>[\\w-]+)-online'
    _RETURN_TYPE = 'video'


class BFMTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bfmtv'
    IE_NAME = 'BFMTVBase'


class BFMTVIE(BFMTVBaseIE):
    _module = 'yt_dlp.extractor.bfmtv'
    IE_NAME = 'bfmtv'
    _VALID_URL = 'https?://(?:www\\.|rmc\\.)?bfmtv\\.com/(?:[^/]+/)*[^/?&#]+_V[A-Z]-(?P<id>\\d{12})\\.html'
    _RETURN_TYPE = 'video'


class BFMTVLiveIE(BFMTVIE):
    _module = 'yt_dlp.extractor.bfmtv'
    IE_NAME = 'bfmtv:live'
    _VALID_URL = 'https?://(?:www\\.|rmc\\.)?bfmtv\\.com/(?P<id>(?:[^/]+/)?en-direct)'
    _RETURN_TYPE = 'video'


class BFMTVArticleIE(BFMTVBaseIE):
    _module = 'yt_dlp.extractor.bfmtv'
    IE_NAME = 'bfmtv:article'
    _VALID_URL = 'https?://(?:www\\.|rmc\\.)?bfmtv\\.com/(?:[^/]+/)*[^/?&#]+_A[A-Z]-(?P<id>\\d{12})\\.html'
    _RETURN_TYPE = 'any'


class BibelTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bibeltv'
    IE_NAME = 'BibelTVBase'


class BibelTVLiveIE(BibelTVBaseIE):
    _module = 'yt_dlp.extractor.bibeltv'
    IE_NAME = 'bibeltv:live'
    _VALID_URL = 'https?://(?:www\\.)?bibeltv\\.de/livestreams/(?P<id>[\\w-]+)'
    IE_DESC = 'BibelTV live program'
    _RETURN_TYPE = 'video'


class BibelTVSeriesIE(BibelTVBaseIE):
    _module = 'yt_dlp.extractor.bibeltv'
    IE_NAME = 'bibeltv:series'
    _VALID_URL = 'https?://(?:www\\.)?bibeltv\\.de/mediathek/serien/(?P<id>\\d+)[\\w-]+'
    IE_DESC = 'BibelTV series playlist'
    _RETURN_TYPE = 'playlist'


class BibelTVVideoIE(BibelTVBaseIE):
    _module = 'yt_dlp.extractor.bibeltv'
    IE_NAME = 'bibeltv:video'
    _VALID_URL = 'https?://(?:www\\.)?bibeltv\\.de/mediathek/videos/(?P<id>\\d+)[\\w-]+'
    IE_DESC = 'BibelTV single video'
    _RETURN_TYPE = 'video'


class BigflixIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bigflix'
    IE_NAME = 'Bigflix'
    _VALID_URL = 'https?://(?:www\\.)?bigflix\\.com/.+/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class BigoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bigo'
    IE_NAME = 'Bigo'
    _VALID_URL = 'https?://(?:www\\.)?bigo\\.tv/(?:[a-z]{2,}/)?(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class BildIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bild'
    IE_NAME = 'Bild'
    _VALID_URL = 'https?://(?:www\\.)?bild\\.de/(?:[^/]+/)+(?P<display_id>[^/]+)-(?P<id>\\d+)(?:,auto=true)?\\.bild\\.html'
    IE_DESC = 'Bild.de'
    _RETURN_TYPE = 'video'


class BilibiliBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliBase'


class BiliBiliIE(BilibiliBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliBili'
    _VALID_URL = 'https?://www\\.bilibili\\.com/(?:video/|festival/\\w+\\?(?:[^#]*&)?bvid=)[aAbB][vV](?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'any'


class BiliBiliBangumiIE(BilibiliBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliBiliBangumi'
    _VALID_URL = '(?x)https?://www\\.bilibili\\.com/bangumi/play/(?P<id>(?:ss|ep)\\d+)'
    _RETURN_TYPE = 'video'


class BiliBiliBangumiMediaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliBiliBangumiMedia'
    _VALID_URL = 'https?://www\\.bilibili\\.com/bangumi/media/md(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class BiliBiliSearchIE(LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliBiliSearch'
    _VALID_URL = 'bilisearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'Bilibili video search'
    SEARCH_KEY = 'bilisearch'
    _RETURN_TYPE = 'playlist'


class BilibiliCategoryIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'Bilibili category extractor'
    _VALID_URL = 'https?://www\\.bilibili\\.com/v/[a-zA-Z]+\\/[a-zA-Z]+'
    _RETURN_TYPE = 'playlist'


class BilibiliAudioBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliAudioBase'


class BilibiliAudioIE(BilibiliAudioBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliAudio'
    _VALID_URL = 'https?://(?:www\\.)?bilibili\\.com/audio/au(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class BilibiliAudioAlbumIE(BilibiliAudioBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliAudioAlbum'
    _VALID_URL = 'https?://(?:www\\.)?bilibili\\.com/audio/am(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class BiliBiliPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliBiliPlayer'
    _VALID_URL = 'https?://player\\.bilibili\\.com/player\\.html\\?.*?\\baid=(?P<id>\\d+)'


class BilibiliSpaceBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliSpaceBase'


class BilibiliSpaceVideoIE(BilibiliSpaceBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliSpaceVideo'
    _VALID_URL = 'https?://space\\.bilibili\\.com/(?P<id>\\d+)(?P<video>/video)?/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class BilibiliSpaceAudioIE(BilibiliSpaceBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliSpaceAudio'
    _VALID_URL = 'https?://space\\.bilibili\\.com/(?P<id>\\d+)/audio'
    _RETURN_TYPE = 'playlist'


class BilibiliSpacePlaylistIE(BilibiliSpaceBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BilibiliSpacePlaylist'
    _VALID_URL = 'https?://space.bilibili\\.com/(?P<mid>\\d+)/channel/collectiondetail\\?sid=(?P<sid>\\d+)'
    _RETURN_TYPE = 'playlist'


class BiliIntlBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliIntlBase'
    _NETRC_MACHINE = 'biliintl'


class BiliIntlIE(BiliIntlBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliIntl'
    _VALID_URL = 'https?://(?:www\\.)?bili(?:bili\\.tv|intl\\.com)/(?:[a-zA-Z]{2}/)?(play/(?P<season_id>\\d+)/(?P<ep_id>\\d+)|video/(?P<aid>\\d+))'
    _NETRC_MACHINE = 'biliintl'
    _RETURN_TYPE = 'video'


class BiliIntlSeriesIE(BiliIntlBaseIE):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'biliIntl:series'
    _VALID_URL = 'https?://(?:www\\.)?bili(?:bili\\.tv|intl\\.com)/(?:[a-zA-Z]{2}/)?(?:play|media)/(?P<id>\\d+)/?(?:[?#]|$)'
    _NETRC_MACHINE = 'biliintl'
    _RETURN_TYPE = 'playlist'


class BiliLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bilibili'
    IE_NAME = 'BiliLive'
    _VALID_URL = 'https?://live.bilibili.com/(?:blanc/)?(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class BioBioChileTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.biobiochiletv'
    IE_NAME = 'BioBioChileTV'
    _VALID_URL = 'https?://(?:tv|www)\\.biobiochile\\.cl/(?:notas|noticias)/(?:[^/]+/)+(?P<id>[^/]+)\\.shtml'
    _RETURN_TYPE = 'video'


class BitChuteIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bitchute'
    IE_NAME = 'BitChute'
    _VALID_URL = 'https?://(?:www\\.)?bitchute\\.com/(?:video|embed|torrent/[^/]+)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class BitChuteChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bitchute'
    IE_NAME = 'BitChuteChannel'
    _VALID_URL = 'https?://(?:www\\.)?bitchute\\.com/(?P<type>channel|playlist)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class BitwaveReplayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bitwave'
    IE_NAME = 'bitwave:replay'
    _VALID_URL = 'https?://(?:www\\.)?bitwave\\.tv/(?P<user>\\w+)/replay/(?P<id>\\w+)/?$'


class BitwaveStreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bitwave'
    IE_NAME = 'bitwave:stream'
    _VALID_URL = 'https?://(?:www\\.)?bitwave\\.tv/(?P<id>\\w+)/?$'


class BIQLEIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.biqle'
    IE_NAME = 'BIQLE'
    _VALID_URL = 'https?://(?:www\\.)?biqle\\.(?:com|org|ru)/watch/(?P<id>-?\\d+_\\d+)'
    _RETURN_TYPE = 'video'


class BlackboardCollaborateIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.blackboardcollaborate'
    IE_NAME = 'BlackboardCollaborate'
    _VALID_URL = '(?x)\n                        https?://\n                        (?P<region>[a-z-]+)\\.bbcollab\\.com/\n                        (?:\n                            collab/ui/session/playback/load|\n                            recording\n                        )/\n                        (?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class BleacherReportIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bleacherreport'
    IE_NAME = 'BleacherReport'
    _VALID_URL = 'https?://(?:www\\.)?bleacherreport\\.com/articles/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class BleacherReportCMSIE(AMPIE):
    _module = 'yt_dlp.extractor.bleacherreport'
    IE_NAME = 'BleacherReportCMS'
    _VALID_URL = 'https?://(?:www\\.)?bleacherreport\\.com/video_embed\\?id=(?P<id>[0-9a-f-]{36}|\\d{5})'
    _RETURN_TYPE = 'video'


class BlerpIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.blerp'
    IE_NAME = 'blerp'
    _VALID_URL = 'https?://(?:www\\.)?blerp\\.com/soundbites/(?P<id>[0-9a-zA-Z]+)'
    _RETURN_TYPE = 'video'


class BloggerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.blogger'
    IE_NAME = 'blogger.com'
    _VALID_URL = 'https?://(?:www\\.)?blogger\\.com/video\\.g\\?token=(?P<id>.+)'
    _RETURN_TYPE = 'video'


class BloombergIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bloomberg'
    IE_NAME = 'Bloomberg'
    _VALID_URL = 'https?://(?:www\\.)?bloomberg\\.com/(?:[^/]+/)*(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class BokeCCBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bokecc'
    IE_NAME = 'BokeCCBase'


class BokeCCIE(BokeCCBaseIE):
    _module = 'yt_dlp.extractor.bokecc'
    IE_NAME = 'BokeCC'
    _VALID_URL = 'https?://union\\.bokecc\\.com/playvideo\\.bo\\?(?P<query>.*)'
    _RETURN_TYPE = 'video'


class BongaCamsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bongacams'
    IE_NAME = 'BongaCams'
    _VALID_URL = 'https?://(?P<host>(?:[^/]+\\.)?bongacams\\d*\\.(?:com|net))/(?P<id>[^/?&#]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class BostonGlobeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bostonglobe'
    IE_NAME = 'BostonGlobe'
    _VALID_URL = '(?i)https?://(?:www\\.)?bostonglobe\\.com/.*/(?P<id>[^/]+)/\\w+(?:\\.html)?'
    _RETURN_TYPE = 'video'


class BoxIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.box'
    IE_NAME = 'Box'
    _VALID_URL = 'https?://(?:[^.]+\\.)?app\\.box\\.com/s/(?P<shared_name>[^/]+)/file/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class BoxCastVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.boxcast'
    IE_NAME = 'BoxCastVideo'
    _VALID_URL = '(?x)\n        https?://boxcast\\.tv/(?:\n            view-embed/|\n            channel/\\w+\\?(?:[^#]+&)?b=|\n            video-portal/(?:\\w+/){2}\n        )(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class BpbIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bpb'
    IE_NAME = 'Bpb'
    _VALID_URL = 'https?://(?:www\\.)?bpb\\.de/mediathek/(?P<id>[0-9]+)/'
    IE_DESC = 'Bundeszentrale für politische Bildung'
    _RETURN_TYPE = 'video'


class BRIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.br'
    IE_NAME = 'BR'
    _VALID_URL = '(?P<base_url>https?://(?:www\\.)?br(?:-klassik)?\\.de)/(?:[a-z0-9\\-_]+/)+(?P<id>[a-z0-9\\-_]+)\\.html'
    IE_DESC = 'Bayerischer Rundfunk'
    _RETURN_TYPE = 'video'


class BRMediathekIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.br'
    IE_NAME = 'BRMediathek'
    _VALID_URL = 'https?://(?:www\\.)?br\\.de/mediathek//?video/(?:[^/?&#]+?-)?(?P<id>av:[0-9a-f]{24})'
    IE_DESC = 'Bayerischer Rundfunk Mediathek'
    _RETURN_TYPE = 'video'


class BravoTVIE(AdobePassIE):
    _module = 'yt_dlp.extractor.bravotv'
    IE_NAME = 'BravoTV'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>bravotv|oxygen)\\.com/(?:[^/]+/)+(?P<id>[^/?#]+)'
    age_limit = 14
    _RETURN_TYPE = 'video'


class BrainPOPBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOPBase'
    _VALID_URL = '/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'brainpop'


class BrainPOPIE(BrainPOPBaseIE):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOP'
    _VALID_URL = 'https?://(?:www\\.)?brainpop\\.com/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'brainpop'
    _RETURN_TYPE = 'video'


class BrainPOPLegacyBaseIE(BrainPOPBaseIE):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOPLegacyBase'
    _VALID_URL = '/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'brainpop'


class BrainPOPJrIE(BrainPOPLegacyBaseIE):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOPJr'
    _VALID_URL = 'https?://jr\\.brainpop\\.com/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'brainpop'
    _RETURN_TYPE = 'video'


class BrainPOPELLIE(BrainPOPLegacyBaseIE):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOPELL'
    _VALID_URL = 'https?://ell\\.brainpop\\.com/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'brainpop'
    _RETURN_TYPE = 'video'


class BrainPOPEspIE(BrainPOPLegacyBaseIE):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOPEsp'
    _VALID_URL = 'https?://esp\\.brainpop\\.com/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    IE_DESC = 'BrainPOP Español'
    _NETRC_MACHINE = 'brainpop'
    _RETURN_TYPE = 'video'


class BrainPOPFrIE(BrainPOPLegacyBaseIE):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOPFr'
    _VALID_URL = 'https?://fr\\.brainpop\\.com/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    IE_DESC = 'BrainPOP Français'
    _NETRC_MACHINE = 'brainpop'
    _RETURN_TYPE = 'video'


class BrainPOPIlIE(BrainPOPLegacyBaseIE):
    _module = 'yt_dlp.extractor.brainpop'
    IE_NAME = 'BrainPOPIl'
    _VALID_URL = 'https?://il\\.brainpop\\.com/(?P<slug>[^/]+/[^/]+/(?P<id>[^/?#&]+))'
    IE_DESC = 'BrainPOP Hebrew'
    _NETRC_MACHINE = 'brainpop'
    _RETURN_TYPE = 'video'


class BreakIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.breakcom'
    IE_NAME = 'Break'
    _VALID_URL = 'https?://(?:www\\.)?break\\.com/video/(?P<display_id>[^/]+?)(?:-(?P<id>\\d+))?(?:[/?#&]|$)'
    age_limit = 13
    _RETURN_TYPE = 'video'


class BreitBartIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.breitbart'
    IE_NAME = 'BreitBart'
    _VALID_URL = 'https?:\\/\\/(?:www\\.)breitbart.com/videos/v/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class BrightcoveLegacyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.brightcove'
    IE_NAME = 'brightcove:legacy'
    _VALID_URL = '(?:https?://.*brightcove\\.com/(services|viewer).*?\\?|brightcove:)(?P<query>.*)'
    _RETURN_TYPE = 'any'


class BrightcoveNewIE(BrightcoveNewBaseIE):
    _module = 'yt_dlp.extractor.brightcove'
    IE_NAME = 'brightcove:new'
    _VALID_URL = 'https?://players\\.brightcove\\.net/(?P<account_id>\\d+)/(?P<player_id>[^/]+)_(?P<embed>[^/]+)/index\\.html\\?.*(?P<content_type>video|playlist)Id=(?P<video_id>\\d+|ref:[^&]+)'
    _RETURN_TYPE = 'any'


class BusinessInsiderIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.businessinsider'
    IE_NAME = 'BusinessInsider'
    _VALID_URL = 'https?://(?:[^/]+\\.)?businessinsider\\.(?:com|nl)/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class BundesligaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.bundesliga'
    IE_NAME = 'Bundesliga'
    _VALID_URL = 'https?://(?:www\\.)?bundesliga\\.com/[a-z]{2}/bundesliga/videos(?:/[^?]+)?\\?vid=(?P<id>[a-zA-Z0-9]{8})'
    _RETURN_TYPE = 'video'


class BuzzFeedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.buzzfeed'
    IE_NAME = 'BuzzFeed'
    _VALID_URL = 'https?://(?:www\\.)?buzzfeed\\.com/[^?#]*?/(?P<id>[^?#]+)'
    _RETURN_TYPE = 'playlist'


class BYUtvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.byutv'
    IE_NAME = 'BYUtv'
    _VALID_URL = 'https?://(?:www\\.)?byutv\\.org/(?:watch|player)/(?!event/)(?P<id>[0-9a-f-]+)(?:/(?P<display_id>[^/?#&]+))?'
    _RETURN_TYPE = 'video'


class C56IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.c56'
    IE_NAME = '56.com'
    _VALID_URL = 'https?://(?:(?:www|player)\\.)?56\\.com/(?:.+?/)?(?:v_|(?:play_album.+-))(?P<textid>.+?)\\.(?:html|swf)'
    _RETURN_TYPE = 'any'


class CableAVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cableav'
    IE_NAME = 'CableAV'
    _VALID_URL = 'https://cableav\\.tv/(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'


class CallinIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.callin'
    IE_NAME = 'Callin'
    _VALID_URL = 'https?://(?:www\\.)?callin\\.com/(episode)/(?P<id>[-a-zA-Z]+)'
    _RETURN_TYPE = 'video'


class CaltransIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.caltrans'
    IE_NAME = 'Caltrans'
    _VALID_URL = 'https?://(?:[^/]+\\.)?ca\\.gov/vm/loc/[^/]+/(?P<id>[a-z0-9_]+)\\.htm'
    _RETURN_TYPE = 'video'


class CAM4IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cam4'
    IE_NAME = 'CAM4'
    _VALID_URL = 'https?://(?:[^/]+\\.)?cam4\\.com/(?P<id>[a-z0-9_]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class CamdemyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.camdemy'
    IE_NAME = 'Camdemy'
    _VALID_URL = 'https?://(?:www\\.)?camdemy\\.com/media/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CamdemyFolderIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.camdemy'
    IE_NAME = 'CamdemyFolder'
    _VALID_URL = 'https?://(?:www\\.)?camdemy\\.com/folder/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class CamFMEpisodeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.camfm'
    IE_NAME = 'CamFMEpisode'
    _VALID_URL = 'https://(?:www\\.)?camfm\\.co\\.uk/player/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class CamFMShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.camfm'
    IE_NAME = 'CamFMShow'
    _VALID_URL = 'https://(?:www\\.)?camfm\\.co\\.uk/shows/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class CamModelsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cammodels'
    IE_NAME = 'CamModels'
    _VALID_URL = 'https?://(?:www\\.)?cammodels\\.com/cam/(?P<id>[^/?#&]+)'


class CamsodaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.camsoda'
    IE_NAME = 'Camsoda'
    _VALID_URL = 'https?://www\\.camsoda\\.com/(?P<id>[\\w-]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class CamtasiaEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.camtasia'
    IE_NAME = 'CamtasiaEmbed'
    _VALID_URL = False


class CamWithHerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.camwithher'
    IE_NAME = 'CamWithHer'
    _VALID_URL = 'https?://(?:www\\.)?camwithher\\.tv/view_video\\.php\\?.*\\bviewkey=(?P<id>\\w+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class CanalAlphaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.canalalpha'
    IE_NAME = 'CanalAlpha'
    _VALID_URL = 'https?://(?:www\\.)?canalalpha\\.ch/play/[^/]+/[^/]+/(?P<id>\\d+)/?.*'
    _RETURN_TYPE = 'video'


class CanalplusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.canalplus'
    IE_NAME = 'Canalplus'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>mycanal|piwiplus)\\.fr/(?:[^/]+/)*(?P<display_id>[^?/]+)(?:\\.html\\?.*\\bvid=|/p/)(?P<id>\\d+)'
    IE_DESC = 'mycanal.fr and piwiplus.fr'
    _RETURN_TYPE = 'video'


class Canalc2IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.canalc2'
    IE_NAME = 'canalc2.tv'
    _VALID_URL = 'https?://(?:(?:www\\.)?canalc2\\.tv/video/|archives-canalc2\\.u-strasbg\\.fr/video\\.asp\\?.*\\bidVideo=)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CarambaTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.carambatv'
    IE_NAME = 'CarambaTV'
    _VALID_URL = '(?:carambatv:|https?://video1\\.carambatv\\.ru/v/)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CarambaTVPageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.carambatv'
    IE_NAME = 'CarambaTVPage'
    _VALID_URL = 'https?://carambatv\\.ru/(?:[^/]+/)+(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class CartoonNetworkIE(TurnerBaseIE):
    _module = 'yt_dlp.extractor.cartoonnetwork'
    IE_NAME = 'CartoonNetwork'
    _VALID_URL = 'https?://(?:www\\.)?cartoonnetwork\\.com/video/(?:[^/]+/)+(?P<id>[^/?#]+)-(?:clip|episode)\\.html'
    _RETURN_TYPE = 'video'


class CBCIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbc'
    IE_NAME = 'cbc.ca'
    _VALID_URL = 'https?://(?:www\\.)?cbc\\.ca/(?!player/)(?:[^/]+/)+(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'any'

    @classmethod
    def suitable(cls, url):
        return False if CBCPlayerIE.suitable(url) else super(CBCIE, cls).suitable(url)


class CBCPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbc'
    IE_NAME = 'cbc.ca:player'
    _VALID_URL = '(?:cbcplayer:|https?://(?:www\\.)?cbc\\.ca/(?:player/play/|i/caffeine/syndicate/\\?mediaId=))(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CBCGemIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbc'
    IE_NAME = 'gem.cbc.ca'
    _VALID_URL = 'https?://gem\\.cbc\\.ca/(?:media/)?(?P<id>[0-9a-z-]+/s[0-9]+[a-z][0-9]+)'
    _NETRC_MACHINE = 'cbcgem'
    _RETURN_TYPE = 'video'


class CBCGemPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbc'
    IE_NAME = 'gem.cbc.ca:playlist'
    _VALID_URL = 'https?://gem\\.cbc\\.ca/(?:media/)?(?P<id>(?P<show>[0-9a-z-]+)/s(?P<season>[0-9]+))/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class CBCGemLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbc'
    IE_NAME = 'gem.cbc.ca:live'
    _VALID_URL = 'https?://gem\\.cbc\\.ca/live(?:-event)?/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ParamountPressExpressIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbs'
    IE_NAME = 'ParamountPressExpress'
    _VALID_URL = 'https?://(?:www\\.)?paramountpressexpress\\.com(?:/[\\w-]+)+/(?P<yt>yt-)?video/?\\?watch=(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class CBSNewsBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'CBSNewsBase'


class CBSNewsEmbedIE(CBSNewsBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'cbsnews:embed'
    _VALID_URL = 'https?://(?:www\\.)?cbsnews\\.com/embed/video[^#]*#(?P<id>.+)'
    _RETURN_TYPE = 'video'


class CBSNewsIE(CBSNewsBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'cbsnews'
    _VALID_URL = 'https?://(?:www\\.)?cbsnews\\.com/(?:news|video)/(?P<id>[\\w-]+)'
    IE_DESC = 'CBS News'
    _RETURN_TYPE = 'any'


class CBSLocalBaseIE(CBSNewsBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'CBSLocalBase'


class CBSLocalIE(CBSLocalBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'CBSLocal'
    _VALID_URL = 'https?://(?:www\\.)?cbsnews\\.com/(?:atlanta|baltimore|boston|chicago|colorado|detroit|losangeles|miami|minnesota|newyork|philadelphia|pittsburgh|sacramento|sanfrancisco|texas)/(?:live/)?video/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class CBSLocalArticleIE(CBSLocalBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'CBSLocalArticle'
    _VALID_URL = 'https?://(?:www\\.)?cbsnews\\.com/(?:atlanta|baltimore|boston|chicago|colorado|detroit|losangeles|miami|minnesota|newyork|philadelphia|pittsburgh|sacramento|sanfrancisco|texas)/news/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'any'


class CBSNewsLiveBaseIE(CBSNewsBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'CBSNewsLiveBase'


class CBSLocalLiveIE(CBSNewsLiveBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'CBSLocalLive'
    _VALID_URL = 'https?://(?:www\\.)?cbsnews\\.com/(?P<id>atlanta|baltimore|boston|chicago|colorado|detroit|losangeles|miami|minnesota|newyork|philadelphia|pittsburgh|sacramento|sanfrancisco|texas)/live/?(?:[?#]|$)'
    _RETURN_TYPE = 'video'


class CBSNewsLiveIE(CBSNewsLiveBaseIE):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'cbsnews:live'
    _VALID_URL = 'https?://(?:www\\.)?cbsnews\\.com/live/?(?:[?#]|$)'
    IE_DESC = 'CBS News Livestream'
    _RETURN_TYPE = 'video'


class CBSNewsLiveVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbsnews'
    IE_NAME = 'cbsnews:livevideo'
    _VALID_URL = 'https?://(?:www\\.)?cbsnews\\.com/live/video/(?P<id>[^/?#]+)'
    IE_DESC = 'CBS News Live Videos'
    _RETURN_TYPE = 'video'


class CBSSportsEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbssports'
    IE_NAME = 'cbssports:embed'
    _VALID_URL = '(?ix)https?://(?:(?:www\\.)?cbs|embed\\.247)sports\\.com/player/embed.+?\n        (?:\n            ids%3D(?P<id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})|\n            pcid%3D(?P<pcid>\\d+)\n        )'


class CBSSportsBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cbssports'
    IE_NAME = 'CBSSportsBase'


class CBSSportsIE(CBSSportsBaseIE):
    _module = 'yt_dlp.extractor.cbssports'
    IE_NAME = 'cbssports'
    _VALID_URL = 'https?://(?:www\\.)?cbssports\\.com/[^/]+/video/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class TwentyFourSevenSportsIE(CBSSportsBaseIE):
    _module = 'yt_dlp.extractor.cbssports'
    IE_NAME = '247sports'
    _VALID_URL = 'https?://(?:www\\.)?247sports\\.com/Video/(?:[^/?#&]+-)?(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CCCIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ccc'
    IE_NAME = 'media.ccc.de'
    _VALID_URL = 'https?://(?:www\\.)?media\\.ccc\\.de/v/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class CCCPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ccc'
    IE_NAME = 'media.ccc.de:lists'
    _VALID_URL = 'https?://(?:www\\.)?media\\.ccc\\.de/c/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class CCMAIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ccma'
    IE_NAME = 'CCMA'
    _VALID_URL = 'https?://(?:www\\.)?ccma\\.cat/(?:[^/]+/)*?(?P<type>video|audio)/(?P<id>\\d+)'
    age_limit = 16
    _RETURN_TYPE = 'video'


class CCTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cctv'
    IE_NAME = 'CCTV'
    _VALID_URL = 'https?://(?:(?:[^/]+)\\.(?:cntv|cctv)\\.(?:com|cn)|(?:www\\.)?ncpa-classic\\.com)/(?:[^/]+/)*?(?P<id>[^/?#&]+?)(?:/index)?(?:\\.s?html|[?#&]|$)'
    IE_DESC = '央视网'
    _RETURN_TYPE = 'video'


class CDAIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cda'
    IE_NAME = 'CDA'
    _VALID_URL = 'https?://(?:(?:www\\.)?cda\\.pl/video|ebd\\.cda\\.pl/[0-9]+x[0-9]+)/(?P<id>[0-9a-z]+)'
    _NETRC_MACHINE = 'cdapl'
    age_limit = 18
    _RETURN_TYPE = 'video'


class CellebriteIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cellebrite'
    IE_NAME = 'Cellebrite'
    _VALID_URL = 'https?://cellebrite\\.com/(?:\\w+)?/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class CeskaTelevizeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ceskatelevize'
    IE_NAME = 'CeskaTelevize'
    _VALID_URL = 'https?://(?:www\\.)?ceskatelevize\\.cz/(?:ivysilani|porady|zive)/(?:[^/?#&]+/)*(?P<id>[^/#?]+)'
    _RETURN_TYPE = 'any'


class CGTNIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cgtn'
    IE_NAME = 'CGTN'
    _VALID_URL = 'https?://news\\.cgtn\\.com/news/[0-9]{4}-[0-9]{2}-[0-9]{2}/[a-zA-Z0-9-]+-(?P<id>[a-zA-Z0-9-]+)/index\\.html'
    _RETURN_TYPE = 'video'


class Channel9IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.channel9'
    IE_NAME = 'channel9'
    _VALID_URL = 'https?://(?:www\\.)?(?:channel9\\.msdn\\.com|s\\.ch9\\.ms)/(?P<contentpath>.+?)(?P<rss>/RSS)?/?(?:[?#&]|$)'
    IE_DESC = 'Channel 9'
    _RETURN_TYPE = 'any'


class CharlieRoseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.charlierose'
    IE_NAME = 'CharlieRose'
    _VALID_URL = 'https?://(?:www\\.)?charlierose\\.com/(?:video|episode)(?:s|/player)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ChaturbateIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.chaturbate'
    IE_NAME = 'Chaturbate'
    _VALID_URL = 'https?://(?:[^/]+\\.)?chaturbate\\.com/(?:fullvideo/?\\?.*?\\bb=)?(?P<id>[^/?&#]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class ChilloutzoneIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.chilloutzone'
    IE_NAME = 'Chilloutzone'
    _VALID_URL = 'https?://(?:www\\.)?chilloutzone\\.net/video/(?P<id>[\\w-]+)\\.html'
    _RETURN_TYPE = 'video'


class ChingariBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.chingari'
    IE_NAME = 'ChingariBase'


class ChingariIE(ChingariBaseIE):
    _module = 'yt_dlp.extractor.chingari'
    IE_NAME = 'Chingari'
    _VALID_URL = 'https?://(?:www\\.)?chingari\\.io/share/post\\?id=(?P<id>[^&/#?]+)'
    _RETURN_TYPE = 'video'


class ChingariUserIE(ChingariBaseIE):
    _module = 'yt_dlp.extractor.chingari'
    IE_NAME = 'ChingariUser'
    _VALID_URL = 'https?://(?:www\\.)?chingari\\.io/(?!share/post)(?P<id>[^/?]+)'
    _RETURN_TYPE = 'playlist'


class ChirbitIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.chirbit'
    IE_NAME = 'chirbit'
    _VALID_URL = 'https?://(?:www\\.)?chirb\\.it/(?:(?:wp|pl)/|fb_chirbit_player\\.swf\\?key=)?(?P<id>[\\da-zA-Z]+)'
    _RETURN_TYPE = 'video'


class ChirbitProfileIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.chirbit'
    IE_NAME = 'chirbit:profile'
    _VALID_URL = 'https?://(?:www\\.)?chirbit\\.com/(?:rss/)?(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class CinchcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cinchcast'
    IE_NAME = 'Cinchcast'
    _VALID_URL = 'https?://player\\.cinchcast\\.com/.*?(?:assetId|show_id)=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class HBOBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hbo'
    IE_NAME = 'HBOBase'


class CinemaxIE(HBOBaseIE):
    _module = 'yt_dlp.extractor.cinemax'
    IE_NAME = 'Cinemax'
    _VALID_URL = 'https?://(?:www\\.)?cinemax\\.com/(?P<path>[^/]+/video/[0-9a-z-]+-(?P<id>\\d+))'
    _RETURN_TYPE = 'video'


class CinetecaMilanoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cinetecamilano'
    IE_NAME = 'CinetecaMilano'
    _VALID_URL = 'https?://(?:www\\.)?cinetecamilano\\.it/film/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CiscoLiveBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ciscolive'
    IE_NAME = 'CiscoLiveBase'


class CiscoLiveSessionIE(CiscoLiveBaseIE):
    _module = 'yt_dlp.extractor.ciscolive'
    IE_NAME = 'CiscoLiveSession'
    _VALID_URL = 'https?://(?:www\\.)?ciscolive(?:\\.cisco)?\\.com/[^#]*#/session/(?P<id>[^/?&]+)'
    _RETURN_TYPE = 'video'


class CiscoLiveSearchIE(CiscoLiveBaseIE):
    _module = 'yt_dlp.extractor.ciscolive'
    IE_NAME = 'CiscoLiveSearch'
    _VALID_URL = 'https?://(?:www\\.)?ciscolive(?:\\.cisco)?\\.com/(?:global/)?on-demand-library(?:\\.html|/)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if CiscoLiveSessionIE.suitable(url) else super(CiscoLiveSearchIE, cls).suitable(url)


class CiscoWebexIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ciscowebex'
    IE_NAME = 'ciscowebex'
    _VALID_URL = '(?x)\n                    (?P<url>https?://(?P<subdomain>[^/#?]*)\\.webex\\.com/(?:\n                        (?P<siteurl_1>[^/#?]*)/(?:ldr|lsr).php\\?(?:[^#]*&)*RCID=(?P<rcid>[0-9a-f]{32})|\n                        (?:recordingservice|webappng)/sites/(?P<siteurl_2>[^/#?]*)/recording/(?:playback/|play/)?(?P<id>[0-9a-f]{32})\n                    ))'
    IE_DESC = 'Cisco Webex'


class CJSWIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cjsw'
    IE_NAME = 'CJSW'
    _VALID_URL = 'https?://(?:www\\.)?cjsw\\.com/program/(?P<program>[^/]+)/episode/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ClipchampIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.clipchamp'
    IE_NAME = 'Clipchamp'
    _VALID_URL = 'https?://(?:www\\.)?clipchamp\\.com/watch/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class CliphunterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cliphunter'
    IE_NAME = 'cliphunter'
    _VALID_URL = '(?x)https?://(?:www\\.)?cliphunter\\.com/w/\n        (?P<id>[0-9]+)/\n        (?P<seo>.+?)(?:$|[#\\?])\n    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class ClippitIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.clippit'
    IE_NAME = 'Clippit'
    _VALID_URL = 'https?://(?:www\\.)?clippituser\\.tv/c/(?P<id>[a-z]+)'
    _RETURN_TYPE = 'video'


class OnetBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.onet'
    IE_NAME = 'OnetBase'


class ClipRsIE(OnetBaseIE):
    _module = 'yt_dlp.extractor.cliprs'
    IE_NAME = 'ClipRs'
    _VALID_URL = 'https?://(?:www\\.)?clip\\.rs/(?P<id>[^/]+)/\\d+'
    _RETURN_TYPE = 'video'


class ClipsyndicateIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.clipsyndicate'
    IE_NAME = 'Clipsyndicate'
    _VALID_URL = 'https?://(?:chic|www)\\.clipsyndicate\\.com/video/play(list/\\d+)?/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CloserToTruthIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.closertotruth'
    IE_NAME = 'CloserToTruth'
    _VALID_URL = 'https?://(?:www\\.)?closertotruth\\.com/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'any'


class CloudflareStreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cloudflarestream'
    IE_NAME = 'CloudflareStream'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:watch\\.)?(?:cloudflarestream\\.com|(?:videodelivery|bytehighway)\\.net)/|\n                            embed\\.(?:cloudflarestream\\.com|(?:videodelivery|bytehighway)\\.net)/embed/[^/]+\\.js\\?.*?\\bvideo=\n                        )\n                        (?P<id>[\\da-f]{32}|[\\w-]+\\.[\\w-]+\\.[\\w-]+)\n                    '
    _RETURN_TYPE = 'video'


class CloudyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cloudy'
    IE_NAME = 'Cloudy'
    _VALID_URL = 'https?://(?:www\\.)?cloudy\\.ec/(?:v/|embed\\.php\\?.*?\\bid=)(?P<id>[A-Za-z0-9]+)'
    _RETURN_TYPE = 'video'


class ClubicIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.clubic'
    IE_NAME = 'Clubic'
    _VALID_URL = 'https?://(?:www\\.)?clubic\\.com/video/(?:[^/]+/)*video.*-(?P<id>[0-9]+)\\.html'
    _RETURN_TYPE = 'video'


class ClypIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.clyp'
    IE_NAME = 'Clyp'
    _VALID_URL = 'https?://(?:www\\.)?clyp\\.it/(?P<id>[a-z0-9]+)'
    _RETURN_TYPE = 'video'


class CNBCIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cnbc'
    IE_NAME = 'CNBC'
    _VALID_URL = 'https?://video\\.cnbc\\.com/gallery/\\?video=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class CNBCVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cnbc'
    IE_NAME = 'CNBCVideo'
    _VALID_URL = 'https?://(?:www\\.)?cnbc\\.com(?P<path>/video/(?:[^/]+/)+(?P<id>[^./?#&]+)\\.html)'
    _RETURN_TYPE = 'video'


class CNNIE(TurnerBaseIE):
    _module = 'yt_dlp.extractor.cnn'
    IE_NAME = 'CNN'
    _VALID_URL = '(?x)https?://(?:(?P<sub_domain>edition|www|money)\\.)?cnn\\.com/(?:video/(?:data/.+?|\\?)/)?videos?/\n        (?P<path>.+?/(?P<title>[^/]+?)(?:\\.(?:[a-z\\-]+)|(?=&)))'
    _RETURN_TYPE = 'video'


class CNNBlogsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cnn'
    IE_NAME = 'CNNBlogs'
    _VALID_URL = 'https?://[^\\.]+\\.blogs\\.cnn\\.com/.+'
    _RETURN_TYPE = 'video'


class CNNArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cnn'
    IE_NAME = 'CNNArticle'
    _VALID_URL = 'https?://(?:(?:edition|www)\\.)?cnn\\.com/(?!videos?/)'
    _RETURN_TYPE = 'video'


class CNNIndonesiaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cnn'
    IE_NAME = 'CNNIndonesia'
    _VALID_URL = 'https?://www\\.cnnindonesia\\.com/[\\w-]+/(?P<upload_date>\\d{8})\\d+-\\d+-(?P<id>\\d+)/(?P<display_id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class CoubIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.coub'
    IE_NAME = 'Coub'
    _VALID_URL = '(?:coub:|https?://(?:coub\\.com/(?:view|embed|coubs)/|c-cdn\\.coub\\.com/fb-player\\.swf\\?.*\\bcoub(?:ID|id)=))(?P<id>[\\da-z]+)'
    _RETURN_TYPE = 'video'


class ComedyCentralIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.comedycentral'
    IE_NAME = 'ComedyCentral'
    _VALID_URL = 'https?://(?:www\\.)?cc\\.com/(?:episodes|video(?:-clips)?|collection-playlist|movies)/(?P<id>[0-9a-z]{6})'
    _RETURN_TYPE = 'video'


class ComedyCentralTVIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.comedycentral'
    IE_NAME = 'ComedyCentralTV'
    _VALID_URL = 'https?://(?:www\\.)?comedycentral\\.tv/folgen/(?P<id>[0-9a-z]{6})'
    _RETURN_TYPE = 'video'


class CommonMistakesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.commonmistakes'
    IE_NAME = 'CommonMistakes'
    _VALID_URL = '(?:url|URL|yt-dlp)$'
    IE_DESC = False


class UnicodeBOMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.commonmistakes'
    IE_NAME = 'UnicodeBOM'
    _VALID_URL = '(?P<bom>\\ufeff)(?P<id>.*)$'
    IE_DESC = False


class MmsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.commonprotocols'
    IE_NAME = 'Mms'
    _VALID_URL = '(?i)mms://.+'
    IE_DESC = False
    _RETURN_TYPE = 'video'


class RtmpIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.commonprotocols'
    IE_NAME = 'Rtmp'
    _VALID_URL = '(?i)rtmp[est]?://.+'
    IE_DESC = False


class ViewSourceIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.commonprotocols'
    IE_NAME = 'ViewSource'
    _VALID_URL = 'view-source:(?P<url>.+)'
    IE_DESC = False


class CondeNastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.condenast'
    IE_NAME = 'CondeNast'
    _VALID_URL = '(?x)https?://(?:video|www|player(?:-backend)?)\\.(?:allure|architecturaldigest|arstechnica|bonappetit|brides|cnevids|cntraveler|details|epicurious|glamour|golfdigest|gq|newyorker|self|teenvogue|vanityfair|vogue|wired|wmagazine)\\.com/\n        (?:\n            (?:\n                embed(?:js)?|\n                (?:script|inline)/video\n            )/(?P<id>[0-9a-f]{24})(?:/(?P<player_id>[0-9a-f]{24}))?(?:.+?\\btarget=(?P<target>[^&]+))?|\n            (?P<type>watch|series|video)/(?P<display_id>[^/?#]+)\n        )'
    IE_DESC = 'Condé Nast media group: Allure, Architectural Digest, Ars Technica, Bon Appétit, Brides, Condé Nast, Condé Nast Traveler, Details, Epicurious, GQ, Glamour, Golf Digest, SELF, Teen Vogue, The New Yorker, Vanity Fair, Vogue, W Magazine, WIRED'
    _RETURN_TYPE = 'video'


class CONtvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.contv'
    IE_NAME = 'CONtv'
    _VALID_URL = 'https?://(?:www\\.)?contv\\.com/details-movie/(?P<id>[^/]+)'
    _RETURN_TYPE = 'any'


class CPACIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cpac'
    IE_NAME = 'cpac'
    _VALID_URL = 'https?://(?:www\\.)?cpac\\.ca/(?P<fr>l-)?episode\\?id=(?P<id>[\\da-f]{8}(?:-[\\da-f]{4}){3}-[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class CPACPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cpac'
    IE_NAME = 'cpac:playlist'
    _VALID_URL = '(?i)https?://(?:www\\.)?cpac\\.ca/(?:program|search|(?P<fr>emission|rechercher))\\?(?:[^&]+&)*?(?P<id>(?:id=\\d+|programId=\\d+|key=[^&]+))'
    _RETURN_TYPE = 'playlist'


class CozyTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cozytv'
    IE_NAME = 'CozyTV'
    _VALID_URL = 'https?://(?:www\\.)?cozy\\.tv/(?P<uploader>[^/]+)/replays/(?P<id>[^/$#&?]+)'
    _RETURN_TYPE = 'video'


class CrackedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cracked'
    IE_NAME = 'Cracked'
    _VALID_URL = 'https?://(?:www\\.)?cracked\\.com/video_(?P<id>\\d+)_[\\da-z-]+\\.html'
    _RETURN_TYPE = 'video'


class CrackleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.crackle'
    IE_NAME = 'Crackle'
    _VALID_URL = '(?:crackle:|https?://(?:(?:www|m)\\.)?(?:sony)?crackle\\.com/(?:playlist/\\d+/|(?:[^/]+/)+))(?P<id>\\d+)'
    age_limit = 17
    _RETURN_TYPE = 'video'


class CraftsyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.craftsy'
    IE_NAME = 'Craftsy'
    _VALID_URL = 'https?://www.craftsy.com/class/(?P<id>[a-z0-9_-]+)/'
    _RETURN_TYPE = 'playlist'


class CrooksAndLiarsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.crooksandliars'
    IE_NAME = 'CrooksAndLiars'
    _VALID_URL = 'https?://embed\\.crooksandliars\\.com/(?:embed|v)/(?P<id>[A-Za-z0-9]+)'
    _RETURN_TYPE = 'video'


class CrowdBunkerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.crowdbunker'
    IE_NAME = 'CrowdBunker'
    _VALID_URL = 'https?://(?:www\\.)?crowdbunker\\.com/v/(?P<id>[^/?#$&]+)'
    _RETURN_TYPE = 'video'


class CrowdBunkerChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.crowdbunker'
    IE_NAME = 'CrowdBunkerChannel'
    _VALID_URL = 'https?://(?:www\\.)?crowdbunker\\.com/@(?P<id>[^/?#$&]+)'
    _RETURN_TYPE = 'playlist'


class CrtvgIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.crtvg'
    IE_NAME = 'Crtvg'
    _VALID_URL = 'https?://(?:www\\.)?crtvg\\.es/tvg/a-carta/[^/#?]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class CrunchyrollBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.crunchyroll'
    IE_NAME = 'CrunchyrollBase'
    _NETRC_MACHINE = 'crunchyroll'


class CrunchyrollCmsBaseIE(CrunchyrollBaseIE):
    _module = 'yt_dlp.extractor.crunchyroll'
    IE_NAME = 'CrunchyrollCmsBase'
    _NETRC_MACHINE = 'crunchyroll'


class CrunchyrollBetaIE(CrunchyrollCmsBaseIE):
    _module = 'yt_dlp.extractor.crunchyroll'
    IE_NAME = 'crunchyroll'
    _VALID_URL = '(?x)\n        https?://(?:beta\\.|www\\.)?crunchyroll\\.com/\n        (?P<lang>(?:\\w{2}(?:-\\w{2})?/)?)\n        watch/(?!concert|musicvideo)(?P<id>\\w+)'
    _NETRC_MACHINE = 'crunchyroll'
    age_limit = 14
    _RETURN_TYPE = 'video'


class CrunchyrollBetaShowIE(CrunchyrollCmsBaseIE):
    _module = 'yt_dlp.extractor.crunchyroll'
    IE_NAME = 'crunchyroll:playlist'
    _VALID_URL = '(?x)\n        https?://(?:beta\\.|www\\.)?crunchyroll\\.com/\n        (?P<lang>(?:\\w{2}(?:-\\w{2})?/)?)\n        series/(?P<id>\\w+)'
    _NETRC_MACHINE = 'crunchyroll'
    age_limit = 14
    _RETURN_TYPE = 'playlist'


class CrunchyrollMusicIE(CrunchyrollBaseIE):
    _module = 'yt_dlp.extractor.crunchyroll'
    IE_NAME = 'crunchyroll:music'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?crunchyroll\\.com/\n        (?P<lang>(?:\\w{2}(?:-\\w{2})?/)?)\n        watch/(?P<type>concert|musicvideo)/(?P<id>\\w+)'
    _NETRC_MACHINE = 'crunchyroll'
    _RETURN_TYPE = 'video'


class CrunchyrollArtistIE(CrunchyrollBaseIE):
    _module = 'yt_dlp.extractor.crunchyroll'
    IE_NAME = 'crunchyroll:artist'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?crunchyroll\\.com/\n        (?P<lang>(?:\\w{2}(?:-\\w{2})?/)?)\n        artist/(?P<id>\\w{10})'
    _NETRC_MACHINE = 'crunchyroll'
    _RETURN_TYPE = 'playlist'


class CSpanIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cspan'
    IE_NAME = 'CSpan'
    _VALID_URL = 'https?://(?:www\\.)?c-span\\.org/video/\\?(?P<id>[0-9a-f]+)'
    IE_DESC = 'C-SPAN'
    _RETURN_TYPE = 'any'


class CSpanCongressIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cspan'
    IE_NAME = 'CSpanCongress'
    _VALID_URL = 'https?://(?:www\\.)?c-span\\.org/congress/'
    _RETURN_TYPE = 'video'


class CtsNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ctsnews'
    IE_NAME = 'CtsNews'
    _VALID_URL = 'https?://news\\.cts\\.com\\.tw/[a-z]+/[a-z]+/\\d+/(?P<id>\\d+)\\.html'
    IE_DESC = '華視新聞'
    _RETURN_TYPE = 'video'


class CTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ctv'
    IE_NAME = 'CTV'
    _VALID_URL = 'https?://(?:www\\.)?ctv\\.ca/(?P<id>(?:show|movie)s/[^/]+/[^/?#&]+)'
    _RETURN_TYPE = 'video'


class CTVNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ctvnews'
    IE_NAME = 'CTVNews'
    _VALID_URL = 'https?://(?:.+?\\.)?ctvnews\\.ca/(?:video\\?(?:clip|playlist|bin)Id=|.*?)(?P<id>[0-9.]+)'
    _RETURN_TYPE = 'any'


class CultureUnpluggedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cultureunplugged'
    IE_NAME = 'CultureUnplugged'
    _VALID_URL = 'https?://(?:www\\.)?cultureunplugged\\.com/documentary/watch-online/play/(?P<id>\\d+)(?:/(?P<display_id>[^/]+))?'
    _RETURN_TYPE = 'video'


class CuriosityStreamBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.curiositystream'
    IE_NAME = 'CuriosityStreamBase'
    _NETRC_MACHINE = 'curiositystream'


class CuriosityStreamIE(CuriosityStreamBaseIE):
    _module = 'yt_dlp.extractor.curiositystream'
    IE_NAME = 'curiositystream'
    _VALID_URL = 'https?://(?:app\\.)?curiositystream\\.com/video/(?P<id>\\d+)'
    _NETRC_MACHINE = 'curiositystream'
    _RETURN_TYPE = 'video'


class CuriosityStreamCollectionBaseIE(CuriosityStreamBaseIE):
    _module = 'yt_dlp.extractor.curiositystream'
    IE_NAME = 'CuriosityStreamCollectionBase'
    _NETRC_MACHINE = 'curiositystream'


class CuriosityStreamCollectionsIE(CuriosityStreamCollectionBaseIE):
    _module = 'yt_dlp.extractor.curiositystream'
    IE_NAME = 'curiositystream:collections'
    _VALID_URL = 'https?://(?:app\\.)?curiositystream\\.com/collections/(?P<id>\\d+)'
    _NETRC_MACHINE = 'curiositystream'
    _RETURN_TYPE = 'playlist'


class CuriosityStreamSeriesIE(CuriosityStreamCollectionBaseIE):
    _module = 'yt_dlp.extractor.curiositystream'
    IE_NAME = 'curiositystream:series'
    _VALID_URL = 'https?://(?:app\\.)?curiositystream\\.com/(?:series|collection)/(?P<id>\\d+)'
    _NETRC_MACHINE = 'curiositystream'
    _RETURN_TYPE = 'playlist'


class CWTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cwtv'
    IE_NAME = 'CWTV'
    _VALID_URL = 'https?://(?:www\\.)?cw(?:tv(?:pr)?|seed)\\.com/(?:shows/)?(?:[^/]+/)+[^?]*\\?.*\\b(?:play|watch)=(?P<id>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})'
    age_limit = 14
    _RETURN_TYPE = 'video'


class CybraryBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.cybrary'
    IE_NAME = 'CybraryBase'
    _NETRC_MACHINE = 'cybrary'


class CybraryIE(CybraryBaseIE):
    _module = 'yt_dlp.extractor.cybrary'
    IE_NAME = 'Cybrary'
    _VALID_URL = 'https?://app.cybrary.it/immersive/(?P<enrollment>[0-9]+)/activity/(?P<id>[0-9]+)'
    _NETRC_MACHINE = 'cybrary'
    _RETURN_TYPE = 'video'


class CybraryCourseIE(CybraryBaseIE):
    _module = 'yt_dlp.extractor.cybrary'
    IE_NAME = 'CybraryCourse'
    _VALID_URL = 'https://app.cybrary.it/browse/course/(?P<id>[\\w-]+)/?(?:$|[#?])'
    _NETRC_MACHINE = 'cybrary'
    _RETURN_TYPE = 'playlist'


class DacastBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dacast'
    IE_NAME = 'DacastBase'
    _VALID_URL = 'https?://iframe\\.dacast\\.com/None/(?P<user_id>[\\w-]+)/(?P<id>[\\w-]+)'


class DacastVODIE(DacastBaseIE):
    _module = 'yt_dlp.extractor.dacast'
    IE_NAME = 'DacastVOD'
    _VALID_URL = 'https?://iframe\\.dacast\\.com/vod/(?P<user_id>[\\w-]+)/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class DacastPlaylistIE(DacastBaseIE):
    _module = 'yt_dlp.extractor.dacast'
    IE_NAME = 'DacastPlaylist'
    _VALID_URL = 'https?://iframe\\.dacast\\.com/playlist/(?P<user_id>[\\w-]+)/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class DaftsexIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.daftsex'
    IE_NAME = 'Daftsex'
    _VALID_URL = 'https?://(?:www\\.)?daft\\.sex/watch/(?P<id>-?\\d+_\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class DailyMailIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dailymail'
    IE_NAME = 'DailyMail'
    _VALID_URL = 'https?://(?:www\\.)?dailymail\\.co\\.uk/(?:video/[^/]+/video-|embed/video/)(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class DailymotionBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dailymotion'
    IE_NAME = 'DailymotionBaseInfoExtract'
    _NETRC_MACHINE = 'dailymotion'


class DailymotionIE(DailymotionBaseInfoExtractor):
    _module = 'yt_dlp.extractor.dailymotion'
    IE_NAME = 'dailymotion'
    _VALID_URL = '(?ix)\n                    https?://\n                        (?:\n                            (?:(?:www|touch|geo)\\.)?dailymotion\\.[a-z]{2,3}/(?:(?:(?:(?:embed|swf|\\#)/)|player\\.html\\?)?video|swf)|\n                            (?:www\\.)?lequipe\\.fr/video\n                        )\n                        [/=](?P<id>[^/?_&]+)(?:.+?\\bplaylist=(?P<playlist_id>x[0-9a-z]+))?\n                    '
    _NETRC_MACHINE = 'dailymotion'
    age_limit = 18
    _RETURN_TYPE = 'video'


class DailymotionPlaylistBaseIE(DailymotionBaseInfoExtractor):
    _module = 'yt_dlp.extractor.dailymotion'
    IE_NAME = 'DailymotionPlaylistBase'
    _NETRC_MACHINE = 'dailymotion'


class DailymotionPlaylistIE(DailymotionPlaylistBaseIE):
    _module = 'yt_dlp.extractor.dailymotion'
    IE_NAME = 'dailymotion:playlist'
    _VALID_URL = '(?:https?://)?(?:www\\.)?dailymotion\\.[a-z]{2,3}/playlist/(?P<id>x[0-9a-z]+)'
    _NETRC_MACHINE = 'dailymotion'
    _RETURN_TYPE = 'playlist'


class DailymotionUserIE(DailymotionPlaylistBaseIE):
    _module = 'yt_dlp.extractor.dailymotion'
    IE_NAME = 'dailymotion:user'
    _VALID_URL = 'https?://(?:www\\.)?dailymotion\\.[a-z]{2,3}/(?!(?:embed|swf|#|video|playlist)/)(?:(?:old/)?user/)?(?P<id>[^/]+)'
    _NETRC_MACHINE = 'dailymotion'
    _RETURN_TYPE = 'playlist'


class DailyWireBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dailywire'
    IE_NAME = 'DailyWireBase'


class DailyWireIE(DailyWireBaseIE):
    _module = 'yt_dlp.extractor.dailywire'
    IE_NAME = 'DailyWire'
    _VALID_URL = 'https?://(?:www\\.)dailywire(?:\\.com)/(?P<sites_type>episode|videos)/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class DailyWirePodcastIE(DailyWireBaseIE):
    _module = 'yt_dlp.extractor.dailywire'
    IE_NAME = 'DailyWirePodcast'
    _VALID_URL = 'https?://(?:www\\.)dailywire(?:\\.com)/(?P<sites_type>podcasts)/(?P<podcaster>[\\w-]+/(?P<id>[\\w-]+))'
    _RETURN_TYPE = 'video'


class DamtomoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.damtomo'
    IE_NAME = 'DamtomoBase'


class DamtomoRecordIE(DamtomoBaseIE):
    _module = 'yt_dlp.extractor.damtomo'
    IE_NAME = 'damtomo:record'
    _VALID_URL = 'https?://(?:www\\.)?clubdam\\.com/app/damtomo/(?:SP/)?karaokePost/StreamingKrk\\.do\\?karaokeContributeId=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class DamtomoVideoIE(DamtomoBaseIE):
    _module = 'yt_dlp.extractor.damtomo'
    IE_NAME = 'damtomo:video'
    _VALID_URL = 'https?://(?:www\\.)?clubdam\\.com/app/damtomo/(?:SP/)?karaokeMovie/StreamingDkm\\.do\\?karaokeMovieId=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class DaumBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.daum'
    IE_NAME = 'DaumBase'


class DaumIE(DaumBaseIE):
    _module = 'yt_dlp.extractor.daum'
    IE_NAME = 'daum.net'
    _VALID_URL = 'https?://(?:(?:m\\.)?tvpot\\.daum\\.net/v/|videofarm\\.daum\\.net/controller/player/VodPlayer\\.swf\\?vid=)(?P<id>[^?#&]+)'
    _RETURN_TYPE = 'video'


class DaumClipIE(DaumBaseIE):
    _module = 'yt_dlp.extractor.daum'
    IE_NAME = 'daum.net:clip'
    _VALID_URL = 'https?://(?:m\\.)?tvpot\\.daum\\.net/(?:clip/ClipView.(?:do|tv)|mypot/View.do)\\?.*?clipid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if DaumPlaylistIE.suitable(url) or DaumUserIE.suitable(url) else super(DaumClipIE, cls).suitable(url)


class DaumListIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.daum'
    IE_NAME = 'DaumList'


class DaumPlaylistIE(DaumListIE):
    _module = 'yt_dlp.extractor.daum'
    IE_NAME = 'daum.net:playlist'
    _VALID_URL = 'https?://(?:m\\.)?tvpot\\.daum\\.net/mypot/(?:View\\.do|Top\\.tv)\\?.*?playlistid=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'any'

    @classmethod
    def suitable(cls, url):
        return False if DaumUserIE.suitable(url) else super(DaumPlaylistIE, cls).suitable(url)


class DaumUserIE(DaumListIE):
    _module = 'yt_dlp.extractor.daum'
    IE_NAME = 'daum.net:user'
    _VALID_URL = 'https?://(?:m\\.)?tvpot\\.daum\\.net/mypot/(?:View|Top)\\.(?:do|tv)\\?.*?ownerid=(?P<id>[0-9a-zA-Z]+)'
    _RETURN_TYPE = 'any'


class DaystarClipIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.daystar'
    IE_NAME = 'daystar:clip'
    _VALID_URL = 'https?://player\\.daystar\\.tv/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class DBTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dbtv'
    IE_NAME = 'DBTV'
    _VALID_URL = 'https?://(?:www\\.)?dagbladet\\.no/video/(?:(?:embed|(?P<display_id>[^/]+))/)?(?P<id>[0-9A-Za-z_-]{11}|[a-zA-Z0-9]{8})'
    _RETURN_TYPE = 'video'


class DctpTvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dctp'
    IE_NAME = 'DctpTv'
    _VALID_URL = 'https?://(?:www\\.)?dctp\\.tv/(?:#/)?filme/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class DeezerBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.deezer'
    IE_NAME = 'DeezerBaseInfoExtract'


class DeezerPlaylistIE(DeezerBaseInfoExtractor):
    _module = 'yt_dlp.extractor.deezer'
    IE_NAME = 'DeezerPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?deezer\\.com/(../)?playlist/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'playlist'


class DeezerAlbumIE(DeezerBaseInfoExtractor):
    _module = 'yt_dlp.extractor.deezer'
    IE_NAME = 'DeezerAlbum'
    _VALID_URL = 'https?://(?:www\\.)?deezer\\.com/(../)?album/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'playlist'


class DemocracynowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.democracynow'
    IE_NAME = 'democracynow'
    _VALID_URL = 'https?://(?:www\\.)?democracynow\\.org/(?P<id>[^\\?]*)'
    _RETURN_TYPE = 'video'


class DetikEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.detik'
    IE_NAME = 'DetikEmbed'
    _VALID_URL = False


class DLFBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dlf'
    IE_NAME = 'DLFBase'


class DLFIE(DLFBaseIE):
    _module = 'yt_dlp.extractor.dlf'
    IE_NAME = 'dlf'
    _VALID_URL = 'https?://(?:www\\.)?deutschlandfunk\\.de/[\\w-]+-dlf-(?P<id>[\\da-f]{8})-100\\.html'
    _RETURN_TYPE = 'video'


class DLFCorpusIE(DLFBaseIE):
    _module = 'yt_dlp.extractor.dlf'
    IE_NAME = 'dlf:corpus'
    _VALID_URL = 'https?://(?:www\\.)?deutschlandfunk\\.de/(?P<id>(?![\\w-]+-dlf-[\\da-f]{8})[\\w-]+-\\d+)\\.html'
    IE_DESC = 'DLF Multi-feed Archives'
    _RETURN_TYPE = 'playlist'


class DFBIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dfb'
    IE_NAME = 'tv.dfb.de'
    _VALID_URL = 'https?://tv\\.dfb\\.de/video/(?P<display_id>[^/]+)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class DHMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dhm'
    IE_NAME = 'DHM'
    _VALID_URL = 'https?://(?:www\\.)?dhm\\.de/filmarchiv/(?:[^/]+/)+(?P<id>[^/]+)'
    IE_DESC = 'Filmarchiv - Deutsches Historisches Museum'
    _RETURN_TYPE = 'video'


class DiggIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.digg'
    IE_NAME = 'Digg'
    _VALID_URL = 'https?://(?:www\\.)?digg\\.com/video/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class DotsubIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dotsub'
    IE_NAME = 'Dotsub'
    _VALID_URL = 'https?://(?:www\\.)?dotsub\\.com/view/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class DouyuShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.douyutv'
    IE_NAME = 'DouyuShow'
    _VALID_URL = 'https?://v(?:mobile)?\\.douyu\\.com/show/(?P<id>[0-9a-zA-Z]+)'
    _RETURN_TYPE = 'video'


class DouyuTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.douyutv'
    IE_NAME = 'DouyuTV'
    _VALID_URL = 'https?://(?:www\\.)?douyu(?:tv)?\\.com/(topic/\\w+\\?rid=|(?:[^/]+/))*(?P<id>[A-Za-z0-9]+)'
    IE_DESC = '斗鱼'
    _RETURN_TYPE = 'video'


class DPlayBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DPlayBase'


class DPlayIE(DPlayBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DPlay'
    _VALID_URL = '(?x)https?://\n        (?P<domain>\n            (?:www\\.)?(?P<host>d\n                (?:\n                    play\\.(?P<country>dk|fi|jp|se|no)|\n                    iscoveryplus\\.(?P<plus_country>dk|es|fi|it|se|no)\n                )\n            )|\n            (?P<subdomain_country>es|it)\\.dplay\\.com\n        )/[^/]+/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class DiscoveryPlusBaseIE(DPlayBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryPlusBase'


class DiscoveryPlusIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryPlus'
    _VALID_URL = 'https?://(?:www\\.)?discoveryplus\\.com/(?!it/)(?:\\w{2}/)?video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class HGTVDeIE(DPlayBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'HGTVDe'
    _VALID_URL = 'https?://de\\.hgtv\\.com/sendungen/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class GoDiscoveryIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'GoDiscovery'
    _VALID_URL = 'https?://(?:go\\.)?discovery\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class TravelChannelIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'TravelChannel'
    _VALID_URL = 'https?://(?:watch\\.)?travelchannel\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class CookingChannelIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'CookingChannel'
    _VALID_URL = 'https?://(?:watch\\.)?cookingchanneltv\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class HGTVUsaIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'HGTVUsa'
    _VALID_URL = 'https?://(?:watch\\.)?hgtv\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class FoodNetworkIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'FoodNetwork'
    _VALID_URL = 'https?://(?:watch\\.)?foodnetwork\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class InvestigationDiscoveryIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'InvestigationDiscovery'
    _VALID_URL = 'https?://(?:www\\.)?investigationdiscovery\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class DestinationAmericaIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DestinationAmerica'
    _VALID_URL = 'https?://(?:www\\.)?destinationamerica\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class AmHistoryChannelIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'AmHistoryChannel'
    _VALID_URL = 'https?://(?:www\\.)?ahctv\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class ScienceChannelIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'ScienceChannel'
    _VALID_URL = 'https?://(?:www\\.)?sciencechannel\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class DIYNetworkIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DIYNetwork'
    _VALID_URL = 'https?://(?:watch\\.)?diynetwork\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class DiscoveryLifeIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryLife'
    _VALID_URL = 'https?://(?:www\\.)?discoverylife\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class AnimalPlanetIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'AnimalPlanet'
    _VALID_URL = 'https?://(?:www\\.)?animalplanet\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class TLCIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'TLC'
    _VALID_URL = 'https?://(?:go\\.)?tlc\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class MotorTrendIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'MotorTrend'
    _VALID_URL = 'https?://(?:watch\\.)?motortrend\\.com/video/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class MotorTrendOnDemandIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'MotorTrendOnDemand'
    _VALID_URL = 'https?://(?:www\\.)?motortrendondemand\\.com/detail/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class DiscoveryPlusIndiaIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryPlusIndia'
    _VALID_URL = 'https?://(?:www\\.)?discoveryplus\\.in/videos?/(?P<id>[^/]+/[^/?#]+)'
    _RETURN_TYPE = 'video'


class DiscoveryNetworksDeIE(DPlayBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryNetworksDe'
    _VALID_URL = 'https?://(?:www\\.)?(?P<domain>(?:tlc|dmax)\\.de|dplay\\.co\\.uk)/(?:programme|show|sendungen)/(?P<programme>[^/]+)/(?:video/)?(?P<alternate_id>[^/]+)'
    _RETURN_TYPE = 'video'


class DiscoveryPlusItalyIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryPlusItaly'
    _VALID_URL = 'https?://(?:www\\.)?discoveryplus\\.com/it/video/(?P<id>[^/]+/[^/?#]+)'


class DiscoveryPlusShowBaseIE(DPlayBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryPlusShowBase'


class DiscoveryPlusItalyShowIE(DiscoveryPlusShowBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryPlusItalyShow'
    _VALID_URL = 'https?://(?:www\\.)?discoveryplus\\.it/programmi/(?P<show_name>[^/]+)/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class DiscoveryPlusIndiaShowIE(DiscoveryPlusShowBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'DiscoveryPlusIndiaShow'
    _VALID_URL = 'https?://(?:www\\.)?discoveryplus\\.in/show/(?P<show_name>[^/]+)/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class GlobalCyclingNetworkPlusIE(DiscoveryPlusBaseIE):
    _module = 'yt_dlp.extractor.dplay'
    IE_NAME = 'GlobalCyclingNetworkPlus'
    _VALID_URL = 'https?://plus\\.globalcyclingnetwork\\.com/watch/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class DRBonanzaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.drbonanza'
    IE_NAME = 'DRBonanza'
    _VALID_URL = 'https?://(?:www\\.)?dr\\.dk/bonanza/[^/]+/\\d+/[^/]+/(?P<id>\\d+)/(?P<display_id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class DrTuberIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.drtuber'
    IE_NAME = 'DrTuber'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)?drtuber\\.com/(?:video|embed)/(?P<id>\\d+)(?:/(?P<display_id>[\\w-]+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class DRTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.drtv'
    IE_NAME = 'drtv'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:www\\.)?dr\\.dk/(?:tv/se|nyheder|(?P<radio>radio|lyd)(?:/ondemand)?)/(?:[^/]+/)*|\n                            (?:www\\.)?(?:dr\\.dk|dr-massive\\.com)/drtv/(?:se|episode|program)/\n                        )\n                        (?P<id>[\\da-z_-]+)\n                    '
    _RETURN_TYPE = 'video'


class DRTVLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.drtv'
    IE_NAME = 'drtv:live'
    _VALID_URL = 'https?://(?:www\\.)?dr\\.dk/(?:tv|TV)/live/(?P<id>[\\da-z-]+)'
    _RETURN_TYPE = 'video'


class DRTVSeasonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.drtv'
    IE_NAME = 'drtv:season'
    _VALID_URL = 'https?://(?:www\\.)?(?:dr\\.dk|dr-massive\\.com)/drtv/saeson/(?P<display_id>[\\w-]+)_(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class DRTVSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.drtv'
    IE_NAME = 'drtv:series'
    _VALID_URL = 'https?://(?:www\\.)?(?:dr\\.dk|dr-massive\\.com)/drtv/serie/(?P<display_id>[\\w-]+)_(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class DTubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dtube'
    IE_NAME = 'DTube'
    _VALID_URL = 'https?://(?:www\\.)?d\\.tube/(?:#!/)?v/(?P<uploader_id>[0-9a-z.-]+)/(?P<id>[0-9a-z]{8})'
    _RETURN_TYPE = 'video'


class DVTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dvtv'
    IE_NAME = 'dvtv'
    _VALID_URL = 'https?://video\\.aktualne\\.cz/(?:[^/]+/)+r~(?P<id>[0-9a-f]{32})'
    IE_DESC = 'http://video.aktualne.cz/'
    _RETURN_TYPE = 'any'


class DubokuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.duboku'
    IE_NAME = 'duboku'
    _VALID_URL = '(?:https?://[^/]+\\.duboku\\.io/vodplay/)(?P<id>[0-9]+-[0-9-]+)\\.html.*'
    IE_DESC = 'www.duboku.io'
    _RETURN_TYPE = 'video'


class DubokuPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.duboku'
    IE_NAME = 'duboku:list'
    _VALID_URL = '(?:https?://[^/]+\\.duboku\\.io/voddetail/)(?P<id>[0-9]+)\\.html.*'
    IE_DESC = 'www.duboku.io entire series'
    _RETURN_TYPE = 'playlist'


class DumpertIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dumpert'
    IE_NAME = 'Dumpert'
    _VALID_URL = '(?x)\n        (?P<protocol>https?)://(?:(?:www|legacy)\\.)?dumpert\\.nl(?:\n            /(?:mediabase|embed|item)/|\n            (?:/toppers|/latest|/?)\\?selectedId=\n        )(?P<id>[0-9]+[/_][0-9a-zA-Z]+)'
    _RETURN_TYPE = 'video'


class DefenseGouvFrIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.defense'
    IE_NAME = 'defense.gouv.fr'
    _VALID_URL = 'https?://.*?\\.defense\\.gouv\\.fr/layout/set/ligthboxvideo/base-de-medias/webtv/(?P<id>[^/?#]*)'
    _RETURN_TYPE = 'video'


class DeuxMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.deuxm'
    IE_NAME = 'DeuxM'
    _VALID_URL = 'https?://(?:www\\.)?2m\\.ma/[^/]+/replay/single/(?P<id>([\\w.]{1,24})+)'
    _RETURN_TYPE = 'video'


class DeuxMNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.deuxm'
    IE_NAME = 'DeuxMNews'
    _VALID_URL = 'https?://(?:www\\.)?2m\\.ma/(?P<lang>\\w+)/news/(?P<id>[^/#?]+)'
    _RETURN_TYPE = 'video'


class DigitalConcertHallIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.digitalconcerthall'
    IE_NAME = 'DigitalConcertHall'
    _VALID_URL = 'https?://(?:www\\.)?digitalconcerthall\\.com/(?P<language>[a-z]+)/(?P<type>film|concert)/(?P<id>[0-9]+)'
    IE_DESC = 'DigitalConcertHall extractor'
    _NETRC_MACHINE = 'digitalconcerthall'
    _RETURN_TYPE = 'any'


class DiscogsReleasePlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.discogs'
    IE_NAME = 'DiscogsReleasePlaylist'
    _VALID_URL = 'https?://(?:www\\.)?discogs\\.com/(?P<type>release|master)/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class DiscoveryGoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.discoverygo'
    IE_NAME = 'DiscoveryGoBase'


class DiscoveryIE(DiscoveryGoBaseIE):
    _module = 'yt_dlp.extractor.discovery'
    IE_NAME = 'Discovery'
    _VALID_URL = '(?x)https?://\n        (?P<site>\n            go\\.discovery|\n            www\\.\n                (?:\n                    investigationdiscovery|\n                    discoverylife|\n                    animalplanet|\n                    ahctv|\n                    destinationamerica|\n                    sciencechannel|\n                    tlc\n                )|\n            watch\\.\n                (?:\n                    hgtv|\n                    foodnetwork|\n                    travelchannel|\n                    diynetwork|\n                    cookingchanneltv|\n                    motortrend\n                )\n        )\\.com/tv-shows/(?P<show_slug>[^/]+)/(?:video|full-episode)s/(?P<id>[^./?#]+)'
    _RETURN_TYPE = 'video'


class DisneyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.disney'
    IE_NAME = 'Disney'
    _VALID_URL = '(?x)\n        https?://(?P<domain>(?:[^/]+\\.)?(?:disney\\.[a-z]{2,3}(?:\\.[a-z]{2})?|disney(?:(?:me|latino)\\.com|turkiye\\.com\\.tr|channel\\.de)|(?:starwars|marvelkids)\\.com))/(?:(?:embed/|(?:[^/]+/)+[\\w-]+-)(?P<id>[a-z0-9]{24})|(?:[^/]+/)?(?P<display_id>[^/?#]+))'
    _RETURN_TYPE = 'video'


class DigitallySpeakingIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dispeak'
    IE_NAME = 'DigitallySpeaking'
    _VALID_URL = 'https?://(?:s?evt\\.dispeak|events\\.digitallyspeaking)\\.com/(?:[^/]+/)+xml/(?P<id>[^.]+)\\.xml'
    _RETURN_TYPE = 'video'


class DropboxIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dropbox'
    IE_NAME = 'Dropbox'
    _VALID_URL = 'https?://(?:www\\.)?dropbox[.]com/sh?/(?P<id>[a-zA-Z0-9]{15})/.*'
    _RETURN_TYPE = 'video'


class DropoutSeasonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dropout'
    IE_NAME = 'DropoutSeason'
    _VALID_URL = 'https?://(?:www\\.)?dropout\\.tv/(?P<id>[^\\/$&?#]+)(?:/?$|/season:(?P<season>[0-9]+)/?$)'
    _RETURN_TYPE = 'playlist'


class DropoutIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dropout'
    IE_NAME = 'Dropout'
    _VALID_URL = 'https?://(?:www\\.)?dropout\\.tv/(?:[^/]+/)*videos/(?P<id>[^/]+)/?$'
    _NETRC_MACHINE = 'dropout'
    _RETURN_TYPE = 'video'


class DWIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dw'
    IE_NAME = 'dw'
    _VALID_URL = 'https?://(?:www\\.)?dw\\.com/(?:[^/]+/)+(?:av|e)-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class DWArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dw'
    IE_NAME = 'dw:article'
    _VALID_URL = 'https?://(?:www\\.)?dw\\.com/(?:[^/]+/)+a-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class EaglePlatformIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eagleplatform'
    IE_NAME = 'EaglePlatform'
    _VALID_URL = '(?x)\n                    (?:\n                        eagleplatform:(?P<custom_host>[^/]+):|\n                        https?://(?P<host>.+?\\.media\\.eagleplatform\\.com)/index/player\\?.*\\brecord_id=\n                    )\n                    (?P<id>\\d+)\n                '
    _RETURN_TYPE = 'video'


class ClipYouEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eagleplatform'
    IE_NAME = 'ClipYouEmbed'
    _VALID_URL = False


class EbaumsWorldIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ebaumsworld'
    IE_NAME = 'EbaumsWorld'
    _VALID_URL = 'https?://(?:www\\.)?ebaumsworld\\.com/videos/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class EbayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ebay'
    IE_NAME = 'Ebay'
    _VALID_URL = 'https?://(?:www\\.)?ebay\\.com/itm/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class EchoMskIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.echomsk'
    IE_NAME = 'EchoMsk'
    _VALID_URL = 'https?://(?:www\\.)?echo\\.msk\\.ru/sounds/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class EggheadBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.egghead'
    IE_NAME = 'EggheadBase'


class EggheadCourseIE(EggheadBaseIE):
    _module = 'yt_dlp.extractor.egghead'
    IE_NAME = 'egghead:course'
    _VALID_URL = 'https://(?:app\\.)?egghead\\.io/(?:course|playlist)s/(?P<id>[^/?#&]+)'
    IE_DESC = 'egghead.io course'
    _RETURN_TYPE = 'playlist'


class EggheadLessonIE(EggheadBaseIE):
    _module = 'yt_dlp.extractor.egghead'
    IE_NAME = 'egghead:lesson'
    _VALID_URL = 'https://(?:app\\.)?egghead\\.io/(?:api/v1/)?lessons/(?P<id>[^/?#&]+)'
    IE_DESC = 'egghead.io lesson'
    _RETURN_TYPE = 'video'


class EHowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ehow'
    IE_NAME = 'eHow'
    _VALID_URL = 'https?://(?:www\\.)?ehow\\.com/[^/_?]*_(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class EightTracksIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eighttracks'
    IE_NAME = '8tracks'
    _VALID_URL = 'https?://8tracks\\.com/(?P<user>[^/]+)/(?P<id>[^/#]+)(?:#.*)?$'
    _RETURN_TYPE = 'playlist'


class EinthusanIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.einthusan'
    IE_NAME = 'Einthusan'
    _VALID_URL = 'https?://(?P<host>einthusan\\.(?:tv|com|ca))/movie/watch/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class EitbIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eitb'
    IE_NAME = 'eitb.tv'
    _VALID_URL = 'https?://(?:www\\.)?eitb\\.tv/(?:eu/bideoa|es/video)/[^/]+/\\d+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ElevenSportsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.elevensports'
    IE_NAME = 'ElevenSports'
    _VALID_URL = 'https?://(?:www\\.)?elevensports\\.com/view/event/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class EllenTubeBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ellentube'
    IE_NAME = 'EllenTubeBase'


class EllenTubeIE(EllenTubeBaseIE):
    _module = 'yt_dlp.extractor.ellentube'
    IE_NAME = 'EllenTube'
    _VALID_URL = '(?x)\n                        (?:\n                            ellentube:|\n                            https://api-prod\\.ellentube\\.com/ellenapi/api/item/\n                        )\n                        (?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})\n                    '
    _RETURN_TYPE = 'video'


class EllenTubeVideoIE(EllenTubeBaseIE):
    _module = 'yt_dlp.extractor.ellentube'
    IE_NAME = 'EllenTubeVideo'
    _VALID_URL = 'https?://(?:www\\.)?ellentube\\.com/video/(?P<id>.+?)\\.html'


class EllenTubePlaylistIE(EllenTubeBaseIE):
    _module = 'yt_dlp.extractor.ellentube'
    IE_NAME = 'EllenTubePlaylist'
    _VALID_URL = 'https?://(?:www\\.)?ellentube\\.com/(?:episode|studios)/(?P<id>.+?)\\.html'
    _RETURN_TYPE = 'playlist'


class ElonetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.elonet'
    IE_NAME = 'Elonet'
    _VALID_URL = 'https?://elonet\\.finna\\.fi/Record/kavi\\.elonet_elokuva_(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class ElPaisIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.elpais'
    IE_NAME = 'ElPais'
    _VALID_URL = 'https?://(?:[^.]+\\.)?elpais\\.com/.*/(?P<id>[^/#?]+)\\.html(?:$|[?#])'
    IE_DESC = 'El País'
    _RETURN_TYPE = 'video'


class EmbedlyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.embedly'
    IE_NAME = 'Embedly'
    _VALID_URL = 'https?://(?:www|cdn\\.)?embedly\\.com/widgets/media\\.html\\?(?:[^#]*?&)?(?:src|url)=(?:[^#&]+)'
    _RETURN_TYPE = 'any'


class EngadgetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.engadget'
    IE_NAME = 'Engadget'
    _VALID_URL = 'https?://(?:www\\.)?engadget\\.com/video/(?P<id>[^/?#]+)'


class EpiconIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.epicon'
    IE_NAME = 'Epicon'
    _VALID_URL = 'https?://(?:www\\.)?epicon\\.in/(?:documentaries|movies|tv-shows/[^/?#]+/[^/?#]+)/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class EpiconSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.epicon'
    IE_NAME = 'EpiconSeries'
    _VALID_URL = '(?!.*season)https?://(?:www\\.)?epicon\\.in/tv-shows/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'playlist'


class EpochIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.epoch'
    IE_NAME = 'Epoch'
    _VALID_URL = 'https?://www.theepochtimes\\.com/[\\w-]+_(?P<id>\\d+).html'
    _RETURN_TYPE = 'video'


class EpornerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eporner'
    IE_NAME = 'Eporner'
    _VALID_URL = 'https?://(?:www\\.)?eporner\\.com/(?:(?:hd-porn|embed)/|video-)(?P<id>\\w+)(?:/(?P<display_id>[\\w-]+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class EroProfileIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eroprofile'
    IE_NAME = 'EroProfile'
    _VALID_URL = 'https?://(?:www\\.)?eroprofile\\.com/m/videos/view/(?P<id>[^/]+)'
    _NETRC_MACHINE = 'eroprofile'
    age_limit = 18
    _RETURN_TYPE = 'video'


class EroProfileAlbumIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eroprofile'
    IE_NAME = 'EroProfile:album'
    _VALID_URL = 'https?://(?:www\\.)?eroprofile\\.com/m/videos/album/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class ERTFlixBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ertgr'
    IE_NAME = 'ERTFlixBase'


class ERTFlixCodenameIE(ERTFlixBaseIE):
    _module = 'yt_dlp.extractor.ertgr'
    IE_NAME = 'ertflix:codename'
    _VALID_URL = 'ertflix:(?P<id>[\\w-]+)'
    IE_DESC = 'ERTFLIX videos by codename'
    _RETURN_TYPE = 'video'


class ERTFlixIE(ERTFlixBaseIE):
    _module = 'yt_dlp.extractor.ertgr'
    IE_NAME = 'ertflix'
    _VALID_URL = 'https?://www\\.ertflix\\.gr/(?:[^/]+/)?(?:series|vod)/(?P<id>[a-z]{3}\\.\\d+)'
    IE_DESC = 'ERTFLIX videos'
    age_limit = 8
    _RETURN_TYPE = 'any'


class ERTWebtvEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ertgr'
    IE_NAME = 'ertwebtv:embed'
    _VALID_URL = 'https?://www\\.ert\\.gr/webtv/live\\-uni/vod/dt\\-uni\\-vod\\.php\\?([^#]+&)?f=(?P<id>[^#&]+)'
    IE_DESC = 'ert.gr webtv embedded videos'
    _RETURN_TYPE = 'video'


class EscapistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.escapist'
    IE_NAME = 'Escapist'
    _VALID_URL = 'https?://?(?:(?:www|v1)\\.)?escapistmagazine\\.com/videos/view/[^/]+/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class OnceIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.once'
    IE_NAME = 'Once'
    _VALID_URL = 'https?://.+?\\.unicornmedia\\.com/now/(?:ads/vmap/)?[^/]+/[^/]+/(?P<domain_id>[^/]+)/(?P<application_id>[^/]+)/(?:[^/]+/)?(?P<media_item_id>[^/]+)/content\\.(?:once|m3u8|mp4)'


class ESPNIE(OnceIE):
    _module = 'yt_dlp.extractor.espn'
    IE_NAME = 'ESPN'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:\n                                (?:\n                                    (?:(?:\\w+\\.)+)?espn\\.go|\n                                    (?:www\\.)?espn\n                                )\\.com/\n                                (?:\n                                    (?:\n                                        video/(?:clip|iframe/twitter)|\n                                    )\n                                    (?:\n                                        .*?\\?.*?\\bid=|\n                                        /_/id/\n                                    )|\n                                    [^/]+/video/\n                                )\n                            )|\n                            (?:www\\.)espnfc\\.(?:com|us)/(?:video/)?[^/]+/\\d+/video/\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class WatchESPNIE(AdobePassIE):
    _module = 'yt_dlp.extractor.espn'
    IE_NAME = 'WatchESPN'
    _VALID_URL = 'https?://(?:www\\.)?espn\\.com/(?:watch|espnplus)/player/_/id/(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    _RETURN_TYPE = 'video'


class ESPNArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.espn'
    IE_NAME = 'ESPNArticle'
    _VALID_URL = 'https?://(?:espn\\.go|(?:www\\.)?espn)\\.com/(?:[^/]+/)*(?P<id>[^/]+)'

    @classmethod
    def suitable(cls, url):
        return False if (ESPNIE.suitable(url) or WatchESPNIE.suitable(url)) else super().suitable(url)


class FiveThirtyEightIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.espn'
    IE_NAME = 'FiveThirtyEight'
    _VALID_URL = 'https?://(?:www\\.)?fivethirtyeight\\.com/features/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class ESPNCricInfoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.espn'
    IE_NAME = 'ESPNCricInfo'
    _VALID_URL = 'https?://(?:www\\.)?espncricinfo\\.com/(?:cricket-)?videos?/[^#$&?/]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class EsriVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.esri'
    IE_NAME = 'EsriVideo'
    _VALID_URL = 'https?://video\\.esri\\.com/watch/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class EttuTvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ettutv'
    IE_NAME = 'EttuTv'
    _VALID_URL = 'https?://(?:www\\.)?ettu\\.tv/[^?#]+/playerpage/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class EuropaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.europa'
    IE_NAME = 'Europa'
    _VALID_URL = 'https?://ec\\.europa\\.eu/avservices/(?:video/player|audio/audioDetails)\\.cfm\\?.*?\\bref=(?P<id>[A-Za-z0-9-]+)'
    _RETURN_TYPE = 'video'


class EuroParlWebstreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.europa'
    IE_NAME = 'EuroParlWebstream'
    _VALID_URL = '(?x)\n        https?://multimedia\\.europarl\\.europa\\.eu/[^/#?]+/\n        (?:(?!video)[^/#?]+/[\\w-]+_)(?P<id>[\\w-]+)\n    '
    _RETURN_TYPE = 'video'


class EuropeanTourIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.europeantour'
    IE_NAME = 'EuropeanTour'
    _VALID_URL = 'https?://(?:www\\.)?europeantour\\.com/dpworld-tour/news/video/(?P<id>[^/&?#$]+)'
    _RETURN_TYPE = 'video'


class EurosportIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eurosport'
    IE_NAME = 'Eurosport'
    _VALID_URL = 'https?://www\\.eurosport\\.com/\\w+/(?:[\\w-]+/[\\d-]+/)?[\\w-]+_(?P<id>vid\\d+)'
    _RETURN_TYPE = 'video'


class EUScreenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.euscreen'
    IE_NAME = 'EUScreen'
    _VALID_URL = 'https?://(?:www\\.)?euscreen\\.eu/item.html\\?id=(?P<id>[^&?$/]+)'
    _RETURN_TYPE = 'video'


class ExpoTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.expotv'
    IE_NAME = 'ExpoTV'
    _VALID_URL = 'https?://(?:www\\.)?expotv\\.com/videos/[^?#]*/(?P<id>[0-9]+)($|[?#])'
    _RETURN_TYPE = 'video'


class ExpressenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.expressen'
    IE_NAME = 'Expressen'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?(?:expressen|di)\\.se/\n                        (?:(?:tvspelare/video|videoplayer/embed)/)?\n                        tv/(?:[^/]+/)*\n                        (?P<id>[^/?#&]+)\n                    '
    _RETURN_TYPE = 'video'


class EyedoTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.eyedotv'
    IE_NAME = 'EyedoTV'
    _VALID_URL = 'https?://(?:www\\.)?eyedo\\.tv/[^/]+/(?:#!/)?Live/Detail/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class FacebookIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.facebook'
    IE_NAME = 'facebook'
    _VALID_URL = '(?x)\n                (?:\n                    https?://\n                        (?:[\\w-]+\\.)?(?:facebook\\.com|facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd\\.onion)/\n                        (?:[^#]*?\\#!/)?\n                        (?:\n                            (?:\n                                video/video\\.php|\n                                photo\\.php|\n                                video\\.php|\n                                video/embed|\n                                story\\.php|\n                                watch(?:/live)?/?\n                            )\\?(?:.*?)(?:v|video_id|story_fbid)=|\n                            [^/]+/videos/(?:[^/]+/)?|\n                            [^/]+/posts/|\n                            groups/[^/]+/permalink/|\n                            watchparty/\n                        )|\n                    facebook:\n                )\n                (?P<id>[0-9]+)\n                '
    _NETRC_MACHINE = 'facebook'
    _RETURN_TYPE = 'any'


class FacebookPluginsVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.facebook'
    IE_NAME = 'FacebookPluginsVideo'
    _VALID_URL = 'https?://(?:[\\w-]+\\.)?facebook\\.com/plugins/video\\.php\\?.*?\\bhref=(?P<id>https.+)'
    _RETURN_TYPE = 'video'


class FacebookRedirectURLIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.facebook'
    IE_NAME = 'FacebookRedirectURL'
    _VALID_URL = 'https?://(?:[\\w-]+\\.)?facebook\\.com/flx/warn[/?]'
    IE_DESC = False
    _RETURN_TYPE = 'video'


class FacebookReelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.facebook'
    IE_NAME = 'facebook:reel'
    _VALID_URL = 'https?://(?:[\\w-]+\\.)?facebook\\.com/reel/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class FancodeVodIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fancode'
    IE_NAME = 'fancode:vod'
    _VALID_URL = 'https?://(?:www\\.)?fancode\\.com/video/(?P<id>[0-9]+)\\b'
    _NETRC_MACHINE = 'fancode'
    _RETURN_TYPE = 'video'


class FancodeLiveIE(FancodeVodIE):
    _module = 'yt_dlp.extractor.fancode'
    IE_NAME = 'fancode:live'
    _VALID_URL = 'https?://(www\\.)?fancode\\.com/match/(?P<id>[0-9]+).+'
    _NETRC_MACHINE = 'fancode'
    _RETURN_TYPE = 'video'


class FazIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.faz'
    IE_NAME = 'faz.net'
    _VALID_URL = 'https?://(?:www\\.)?faz\\.net/(?:[^/]+/)*.*?-(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class FC2IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fc2'
    IE_NAME = 'fc2'
    _VALID_URL = '^(?:https?://video\\.fc2\\.com/(?:[^/]+/)*content/|fc2:)(?P<id>[^/]+)'
    _NETRC_MACHINE = 'fc2'
    _RETURN_TYPE = 'video'


class FC2EmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fc2'
    IE_NAME = 'fc2:embed'
    _VALID_URL = 'https?://video\\.fc2\\.com/flv2\\.swf\\?(?P<query>.+)'
    _RETURN_TYPE = 'video'


class FC2LiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fc2'
    IE_NAME = 'fc2:live'
    _VALID_URL = 'https?://live\\.fc2\\.com/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class FczenitIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fczenit'
    IE_NAME = 'Fczenit'
    _VALID_URL = 'https?://(?:www\\.)?fc-zenit\\.ru/video/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class FifaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fifa'
    IE_NAME = 'Fifa'
    _VALID_URL = 'https?://www.fifa.com/fifaplus/(?P<locale>\\w{2})/watch/([^#?]+/)?(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class FilmmoduIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.filmmodu'
    IE_NAME = 'Filmmodu'
    _VALID_URL = 'https?://(?:www.)?filmmodu.org/(?P<id>[^/]+-(?:turkce-dublaj-izle|altyazili-izle))'
    _RETURN_TYPE = 'video'


class FilmOnIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.filmon'
    IE_NAME = 'filmon'
    _VALID_URL = '(?:https?://(?:www\\.)?filmon\\.com/vod/view/|filmon:)(?P<id>\\d+)'
    _RETURN_TYPE = 'any'


class FilmOnChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.filmon'
    IE_NAME = 'filmon:channel'
    _VALID_URL = 'https?://(?:www\\.)?filmon\\.com/(?:tv|channel)/(?P<id>[a-z0-9-]+)'
    _RETURN_TYPE = 'video'


class FilmwebIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.filmweb'
    IE_NAME = 'Filmweb'
    _VALID_URL = 'https?://(?:www\\.)?filmweb\\.no/(?P<type>trailere|filmnytt)/article(?P<id>\\d+)\\.ece'
    _RETURN_TYPE = 'video'


class FirstTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.firsttv'
    IE_NAME = '1tv'
    _VALID_URL = 'https?://(?:www\\.)?1tv\\.ru/(?:[^/]+/)+(?P<id>[^/?#]+)'
    IE_DESC = 'Первый канал'
    _RETURN_TYPE = 'any'


class FiveTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fivetv'
    IE_NAME = 'FiveTV'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?5-tv\\.ru/\n                        (?:\n                            (?:[^/]+/)+(?P<id>\\d+)|\n                            (?P<path>[^/?#]+)(?:[/?#])?\n                        )\n                    '
    _RETURN_TYPE = 'video'


class FlickrIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.flickr'
    IE_NAME = 'Flickr'
    _VALID_URL = 'https?://(?:www\\.|secure\\.)?flickr\\.com/photos/[\\w\\-_@]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class FolketingetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.folketinget'
    IE_NAME = 'Folketinget'
    _VALID_URL = 'https?://(?:www\\.)?ft\\.dk/webtv/video/[^?#]*?\\.(?P<id>[0-9]+)\\.aspx'
    IE_DESC = 'Folketinget (ft.dk; Danish parliament)'
    _RETURN_TYPE = 'video'


class FootyRoomIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.footyroom'
    IE_NAME = 'FootyRoom'
    _VALID_URL = 'https?://footyroom\\.com/matches/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class Formula1IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.formula1'
    IE_NAME = 'Formula1'
    _VALID_URL = 'https?://(?:www\\.)?formula1\\.com/en/latest/video\\.[^.]+\\.(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class FourTubeBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fourtube'
    IE_NAME = 'FourTubeBase'


class FourTubeIE(FourTubeBaseIE):
    _module = 'yt_dlp.extractor.fourtube'
    IE_NAME = '4tube'
    _VALID_URL = 'https?://(?:(?P<kind>www|m)\\.)?4tube\\.com/(?:videos|embed)/(?P<id>\\d+)(?:/(?P<display_id>[^/?#&]+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornTubeIE(FourTubeBaseIE):
    _module = 'yt_dlp.extractor.fourtube'
    IE_NAME = 'PornTube'
    _VALID_URL = 'https?://(?:(?P<kind>www|m)\\.)?porntube\\.com/(?:videos/(?P<display_id>[^/]+)_|embed/)(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornerBrosIE(FourTubeBaseIE):
    _module = 'yt_dlp.extractor.fourtube'
    IE_NAME = 'PornerBros'
    _VALID_URL = 'https?://(?:(?P<kind>www|m)\\.)?pornerbros\\.com/(?:videos/(?P<display_id>[^/]+)_|embed/)(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class FuxIE(FourTubeBaseIE):
    _module = 'yt_dlp.extractor.fourtube'
    IE_NAME = 'Fux'
    _VALID_URL = 'https?://(?:(?P<kind>www|m)\\.)?fux\\.com/(?:video|embed)/(?P<id>\\d+)(?:/(?P<display_id>[^/?#&]+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class FourZeroStudioArchiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fourzerostudio'
    IE_NAME = '0000studio:archive'
    _VALID_URL = 'https?://0000\\.studio/(?P<uploader_id>[^/]+)/broadcasts/(?P<id>[^/]+)/archive'
    _RETURN_TYPE = 'video'


class FourZeroStudioClipIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fourzerostudio'
    IE_NAME = '0000studio:clip'
    _VALID_URL = 'https?://0000\\.studio/(?P<uploader_id>[^/]+)/archive-clip/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class FOXIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fox'
    IE_NAME = 'FOX'
    _VALID_URL = 'https?://(?:www\\.)?fox\\.com/watch/(?P<id>[\\da-fA-F]+)'
    age_limit = 14
    _RETURN_TYPE = 'video'


class FOX9IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fox9'
    IE_NAME = 'FOX9'
    _VALID_URL = 'https?://(?:www\\.)?fox9\\.com/video/(?P<id>\\d+)'


class FOX9NewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fox9'
    IE_NAME = 'FOX9News'
    _VALID_URL = 'https?://(?:www\\.)?fox9\\.com/news/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class FoxgayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.foxgay'
    IE_NAME = 'Foxgay'
    _VALID_URL = 'https?://(?:www\\.)?foxgay\\.com/videos/(?:\\S+-)?(?P<id>\\d+)\\.shtml'
    age_limit = 18
    _RETURN_TYPE = 'video'


class FoxNewsIE(AMPIE):
    _module = 'yt_dlp.extractor.foxnews'
    IE_NAME = 'foxnews'
    _VALID_URL = 'https?://video\\.(?:insider\\.)?fox(?:news|business)\\.com/v/(?:video-embed\\.html\\?video_id=)?(?P<id>\\d+)'
    IE_DESC = 'Fox News and Fox Business Video'
    _RETURN_TYPE = 'video'


class FoxNewsArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.foxnews'
    IE_NAME = 'foxnews:article'
    _VALID_URL = 'https?://(?:www\\.)?(?:insider\\.)?foxnews\\.com/(?!v)([^/]+/)+(?P<id>[a-z-]+)'
    _RETURN_TYPE = 'video'


class FoxNewsVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.foxnews'
    IE_NAME = 'FoxNewsVideo'
    _VALID_URL = 'https?://(?:www\\.)?foxnews\\.com/video/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class FoxSportsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.foxsports'
    IE_NAME = 'FoxSports'
    _VALID_URL = 'https?://(?:www\\.)?foxsports\\.com/watch/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class FptplayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fptplay'
    IE_NAME = 'fptplay'
    _VALID_URL = 'https?://fptplay\\.vn/xem-video/[^/]+\\-(?P<id>\\w+)(?:/tap-(?P<episode>\\d+)?/?(?:[?#]|$)|)'
    IE_DESC = 'fptplay.vn'
    _RETURN_TYPE = 'video'


class FranceInterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.franceinter'
    IE_NAME = 'FranceInter'
    _VALID_URL = 'https?://(?:www\\.)?franceinter\\.fr/emissions/(?P<id>[^?#]+)'
    _RETURN_TYPE = 'video'


class FranceTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.francetv'
    IE_NAME = 'FranceTV'
    _VALID_URL = '(?x)\n                    (?:\n                        https?://\n                            sivideo\\.webservices\\.francetelevisions\\.fr/tools/getInfosOeuvre/v2/\\?\n                            .*?\\bidDiffusion=[^&]+|\n                        (?:\n                            https?://videos\\.francetv\\.fr/video/|\n                            francetv:\n                        )\n                        (?P<id>[^@]+)(?:@(?P<catalog>.+))?\n                    )\n                    '
    _RETURN_TYPE = 'video'


class FranceTVBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.francetv'
    IE_NAME = 'FranceTVBaseInfoExtract'


class FranceTVSiteIE(FranceTVBaseInfoExtractor):
    _module = 'yt_dlp.extractor.francetv'
    IE_NAME = 'FranceTVSite'
    _VALID_URL = 'https?://(?:(?:www\\.)?france\\.tv|mobile\\.france\\.tv)/(?:[^/]+/)*(?P<id>[^/]+)\\.html'
    _RETURN_TYPE = 'video'


class FranceTVInfoIE(FranceTVBaseInfoExtractor):
    _module = 'yt_dlp.extractor.francetv'
    IE_NAME = 'francetvinfo.fr'
    _VALID_URL = 'https?://(?:www|mobile|france3-regions)\\.francetvinfo\\.fr/(?:[^/]+/)*(?P<id>[^/?#&.]+)'
    _RETURN_TYPE = 'video'


class FreesoundIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.freesound'
    IE_NAME = 'Freesound'
    _VALID_URL = 'https?://(?:www\\.)?freesound\\.org/people/[^/]+/sounds/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class FreespeechIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.freespeech'
    IE_NAME = 'freespeech.org'
    _VALID_URL = 'https?://(?:www\\.)?freespeech\\.org/stories/(?P<id>.+)'
    _RETURN_TYPE = 'video'


class FrontendMastersBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.frontendmasters'
    IE_NAME = 'FrontendMastersBase'
    _NETRC_MACHINE = 'frontendmasters'


class FrontendMastersIE(FrontendMastersBaseIE):
    _module = 'yt_dlp.extractor.frontendmasters'
    IE_NAME = 'FrontendMasters'
    _VALID_URL = '(?:frontendmasters:|https?://api\\.frontendmasters\\.com/v\\d+/kabuki/video/)(?P<id>[^/]+)'
    _NETRC_MACHINE = 'frontendmasters'
    _RETURN_TYPE = 'video'


class FrontendMastersPageBaseIE(FrontendMastersBaseIE):
    _module = 'yt_dlp.extractor.frontendmasters'
    IE_NAME = 'FrontendMastersPageBase'
    _NETRC_MACHINE = 'frontendmasters'


class FrontendMastersLessonIE(FrontendMastersPageBaseIE):
    _module = 'yt_dlp.extractor.frontendmasters'
    IE_NAME = 'FrontendMastersLesson'
    _VALID_URL = 'https?://(?:www\\.)?frontendmasters\\.com/courses/(?P<course_name>[^/]+)/(?P<lesson_name>[^/]+)'
    _NETRC_MACHINE = 'frontendmasters'
    _RETURN_TYPE = 'video'


class FrontendMastersCourseIE(FrontendMastersPageBaseIE):
    _module = 'yt_dlp.extractor.frontendmasters'
    IE_NAME = 'FrontendMastersCourse'
    _VALID_URL = 'https?://(?:www\\.)?frontendmasters\\.com/courses/(?P<id>[^/]+)'
    _NETRC_MACHINE = 'frontendmasters'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if FrontendMastersLessonIE.suitable(url) else super(
            FrontendMastersBaseIE, cls).suitable(url)


class FreeTvBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.freetv'
    IE_NAME = 'FreeTvBase'


class FreeTvIE(FreeTvBaseIE):
    _module = 'yt_dlp.extractor.freetv'
    IE_NAME = 'freetv:series'
    _VALID_URL = 'https?://(?:www\\.)?freetv\\.com/series/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class FreeTvMoviesIE(FreeTvBaseIE):
    _module = 'yt_dlp.extractor.freetv'
    IE_NAME = 'FreeTvMovies'
    _VALID_URL = 'https?://(?:www\\.)?freetv\\.com/peliculas/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class FujiTVFODPlus7IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fujitv'
    IE_NAME = 'FujiTVFODPlus7'
    _VALID_URL = 'https?://fod\\.fujitv\\.co\\.jp/title/(?P<sid>[0-9a-z]{4})/(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class FunimationBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.funimation'
    IE_NAME = 'FunimationBase'
    _NETRC_MACHINE = 'funimation'


class FunimationIE(FunimationBaseIE):
    _module = 'yt_dlp.extractor.funimation'
    IE_NAME = 'Funimation'
    _VALID_URL = 'https?://(?:www\\.)?funimation\\.com/player/(?P<id>\\d+)'
    _NETRC_MACHINE = 'funimation'
    _RETURN_TYPE = 'video'


class FunimationPageIE(FunimationBaseIE):
    _module = 'yt_dlp.extractor.funimation'
    IE_NAME = 'funimation:page'
    _VALID_URL = 'https?://(?:www\\.)?funimation(?:\\.com|now\\.uk)/(?:(?P<lang>[^/]+)/)?(?:shows|v)/(?P<show>[^/]+)/(?P<episode>[^/?#&]+)'
    _NETRC_MACHINE = 'funimation'
    _RETURN_TYPE = 'video'


class FunimationShowIE(FunimationBaseIE):
    _module = 'yt_dlp.extractor.funimation'
    IE_NAME = 'funimation:show'
    _VALID_URL = '(?P<url>https?://(?:www\\.)?funimation(?:\\.com|now\\.uk)/(?P<locale>[^/]+)?/?shows/(?P<id>[^/?#&]+))/?(?:[?#]|$)'
    _NETRC_MACHINE = 'funimation'
    _RETURN_TYPE = 'playlist'


class FunkIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.funk'
    IE_NAME = 'Funk'
    _VALID_URL = 'https?://(?:www\\.|origin\\.)?funk\\.net/(?:channel|playlist)/[^/]+/(?P<display_id>[0-9a-z-]+)-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class Funker530IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.funker530'
    IE_NAME = 'Funker530'
    _VALID_URL = 'https?://(?:www\\.)?funker530\\.com/video/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class FusionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fusion'
    IE_NAME = 'Fusion'
    _VALID_URL = 'https?://(?:www\\.)?fusion\\.(?:net|tv)/(?:video/|show/.+?\\bvideo=)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class FuyinTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.fuyintv'
    IE_NAME = 'FuyinTV'
    _VALID_URL = 'https?://(?:www\\.)?fuyin\\.tv/html/(?:\\d+)/(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class GabTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gab'
    IE_NAME = 'GabTV'
    _VALID_URL = 'https?://tv\\.gab\\.com/channel/[^/]+/view/(?P<id>[a-z0-9-]+)'
    _RETURN_TYPE = 'video'


class GabIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gab'
    IE_NAME = 'Gab'
    _VALID_URL = 'https?://(?:www\\.)?gab\\.com/[^/]+/posts/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class GaiaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gaia'
    IE_NAME = 'Gaia'
    _VALID_URL = 'https?://(?:www\\.)?gaia\\.com/video/(?P<id>[^/?]+).*?\\bfullplayer=(?P<type>feature|preview)'
    _NETRC_MACHINE = 'gaia'
    _RETURN_TYPE = 'video'


class GameInformerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gameinformer'
    IE_NAME = 'GameInformer'
    _VALID_URL = 'https?://(?:www\\.)?gameinformer\\.com/(?:[^/]+/)*(?P<id>[^.?&#]+)'
    _RETURN_TYPE = 'video'


class GameJoltBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJoltBase'


class GameJoltIE(GameJoltBaseIE):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJolt'
    _VALID_URL = 'https?://(?:www\\.)?gamejolt\\.com/p/(?:[\\w-]*-)?(?P<id>\\w{8})'
    _RETURN_TYPE = 'any'


class GameJoltPostListBaseIE(GameJoltBaseIE):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJoltPostListBase'


class GameJoltUserIE(GameJoltPostListBaseIE):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJoltUser'
    _VALID_URL = 'https?://(?:www\\.)?gamejolt\\.com/@(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class GameJoltGameIE(GameJoltPostListBaseIE):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJoltGame'
    _VALID_URL = 'https?://(?:www\\.)?gamejolt\\.com/games/[\\w-]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class GameJoltGameSoundtrackIE(GameJoltBaseIE):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJoltGameSoundtrack'
    _VALID_URL = 'https?://(?:www\\.)?gamejolt\\.com/get/soundtrack(?:\\?|\\#!?)(?:.*?[&;])??game=(?P<id>(?:\\d+)+)'
    _RETURN_TYPE = 'playlist'


class GameJoltCommunityIE(GameJoltPostListBaseIE):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJoltCommunity'
    _VALID_URL = 'https?://(?:www\\.)?gamejolt\\.com/c/(?P<id>(?P<community>[\\w-]+)(?:/(?P<channel>[\\w-]+))?)(?:(?:\\?|\\#!?)(?:.*?[&;])??sort=(?P<sort>\\w+))?'
    _RETURN_TYPE = 'playlist'


class GameJoltSearchIE(GameJoltPostListBaseIE):
    _module = 'yt_dlp.extractor.gamejolt'
    IE_NAME = 'GameJoltSearch'
    _VALID_URL = 'https?://(?:www\\.)?gamejolt\\.com/search(?:/(?P<filter>communities|users|games))?(?:\\?|\\#!?)(?:.*?[&;])??q=(?P<id>(?:[^&#]+)+)'
    _RETURN_TYPE = 'playlist'


class GameSpotIE(OnceIE):
    _module = 'yt_dlp.extractor.gamespot'
    IE_NAME = 'GameSpot'
    _VALID_URL = 'https?://(?:www\\.)?gamespot\\.com/(?:video|article|review)s/(?:[^/]+/\\d+-|embed/)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class GameStarIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gamestar'
    IE_NAME = 'GameStar'
    _VALID_URL = 'https?://(?:www\\.)?game(?P<site>pro|star)\\.de/videos/.*,(?P<id>[0-9]+)\\.html'
    _RETURN_TYPE = 'video'


class GaskrankIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gaskrank'
    IE_NAME = 'Gaskrank'
    _VALID_URL = 'https?://(?:www\\.)?gaskrank\\.tv/tv/(?P<categories>[^/]+)/(?P<id>[^/]+)\\.htm'
    _RETURN_TYPE = 'video'


class GazetaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gazeta'
    IE_NAME = 'Gazeta'
    _VALID_URL = '(?P<url>https?://(?:www\\.)?gazeta\\.ru/(?:[^/]+/)?video/(?:main/)*(?:\\d{4}/\\d{2}/\\d{2}/)?(?P<id>[A-Za-z0-9-_.]+)\\.s?html)'
    _RETURN_TYPE = 'video'


class GDCVaultIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gdcvault'
    IE_NAME = 'GDCVault'
    _VALID_URL = 'https?://(?:www\\.)?gdcvault\\.com/play/(?P<id>\\d+)(?:/(?P<name>[\\w-]+))?'
    _NETRC_MACHINE = 'gdcvault'
    _RETURN_TYPE = 'video'


class GediDigitalIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gedidigital'
    IE_NAME = 'GediDigital'
    _VALID_URL = '(?x:(?P<base_url>(?:https?:)//video\\.\n        (?:\n            (?:\n                (?:espresso\\.)?repubblica\n                |lastampa\n                |ilsecoloxix\n                |huffingtonpost\n            )|\n            (?:\n                iltirreno\n                |messaggeroveneto\n                |ilpiccolo\n                |gazzettadimantova\n                |mattinopadova\n                |laprovinciapavese\n                |tribunatreviso\n                |nuovavenezia\n                |gazzettadimodena\n                |lanuovaferrara\n                |corrierealpi\n                |lasentinella\n            )\\.gelocal\n        )\\.it(?:/[^/]+){2,4}/(?P<id>\\d+))(?:$|[?&].*))'
    _RETURN_TYPE = 'video'


class GeniusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.genius'
    IE_NAME = 'Genius'
    _VALID_URL = 'https?://(?:www\\.)?genius\\.com/(?:videos|(?P<article>a))/(?P<id>[^?/#]+)'
    _RETURN_TYPE = 'video'


class GeniusLyricsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.genius'
    IE_NAME = 'GeniusLyrics'
    _VALID_URL = 'https?://(?:www\\.)?genius\\.com/(?P<id>[^?/#]+)-lyrics(?:[?/#]|$)'
    _RETURN_TYPE = 'playlist'


class GettrBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gettr'
    IE_NAME = 'GettrBase'


class GettrIE(GettrBaseIE):
    _module = 'yt_dlp.extractor.gettr'
    IE_NAME = 'Gettr'
    _VALID_URL = 'https?://(www\\.)?gettr\\.com/post/(?P<id>[a-z0-9]+)'
    _RETURN_TYPE = 'video'


class GettrStreamingIE(GettrBaseIE):
    _module = 'yt_dlp.extractor.gettr'
    IE_NAME = 'GettrStreaming'
    _VALID_URL = 'https?://(www\\.)?gettr\\.com/streaming/(?P<id>[a-z0-9]+)'
    _RETURN_TYPE = 'video'


class GfycatIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gfycat'
    IE_NAME = 'Gfycat'
    _VALID_URL = 'https?://(?:(?:www|giant|thumbs)\\.)?gfycat\\.com/(?i:ru/|ifr/|gifs/detail/)?(?P<id>[^-/?#\\."\\\']+)'
    _RETURN_TYPE = 'video'


class GiantBombIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.giantbomb'
    IE_NAME = 'GiantBomb'
    _VALID_URL = 'https?://(?:www\\.)?giantbomb\\.com/(?:videos|shows)/(?P<display_id>[^/]+)/(?P<id>\\d+-\\d+)'
    _RETURN_TYPE = 'video'


class GigaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.giga'
    IE_NAME = 'Giga'
    _VALID_URL = 'https?://(?:www\\.)?giga\\.de/(?:[^/]+/)*(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class GlideIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.glide'
    IE_NAME = 'Glide'
    _VALID_URL = 'https?://share\\.glide\\.me/(?P<id>[A-Za-z0-9\\-=_+]+)'
    IE_DESC = 'Glide mobile video messages (glide.me)'
    _RETURN_TYPE = 'video'


class GlobalPlayerBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.globalplayer'
    IE_NAME = 'GlobalPlayerBase'


class GlobalPlayerLiveIE(GlobalPlayerBaseIE):
    _module = 'yt_dlp.extractor.globalplayer'
    IE_NAME = 'GlobalPlayerLive'
    _VALID_URL = 'https?://www\\.globalplayer\\.com/live/(?P<id>\\w+)/\\w+'
    _RETURN_TYPE = 'video'


class GlobalPlayerLivePlaylistIE(GlobalPlayerBaseIE):
    _module = 'yt_dlp.extractor.globalplayer'
    IE_NAME = 'GlobalPlayerLivePlaylist'
    _VALID_URL = 'https?://www\\.globalplayer\\.com/playlists/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class GlobalPlayerAudioIE(GlobalPlayerBaseIE):
    _module = 'yt_dlp.extractor.globalplayer'
    IE_NAME = 'GlobalPlayerAudio'
    _VALID_URL = 'https?://www\\.globalplayer\\.com/(?:(?P<podcast>podcasts)/|catchup/\\w+/\\w+/)(?P<id>\\w+)/?(?:$|[?#])'
    _RETURN_TYPE = 'playlist'


class GlobalPlayerAudioEpisodeIE(GlobalPlayerBaseIE):
    _module = 'yt_dlp.extractor.globalplayer'
    IE_NAME = 'GlobalPlayerAudioEpisode'
    _VALID_URL = 'https?://www\\.globalplayer\\.com/(?:(?P<podcast>podcasts)|catchup/\\w+/\\w+)/episodes/(?P<id>\\w+)/?(?:$|[?#])'
    _RETURN_TYPE = 'video'


class GlobalPlayerVideoIE(GlobalPlayerBaseIE):
    _module = 'yt_dlp.extractor.globalplayer'
    IE_NAME = 'GlobalPlayerVideo'
    _VALID_URL = 'https?://www\\.globalplayer\\.com/videos/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class GloboIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.globo'
    IE_NAME = 'Globo'
    _VALID_URL = '(?:globo:|https?://.+?\\.globo\\.com/(?:[^/]+/)*(?:v/(?:[^/]+/)?|videos/))(?P<id>\\d{7,})'
    _NETRC_MACHINE = 'globo'
    _RETURN_TYPE = 'video'


class GloboArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.globo'
    IE_NAME = 'GloboArticle'
    _VALID_URL = 'https?://.+?\\.globo\\.com/(?:[^/]+/)*(?P<id>[^/.]+)(?:\\.html)?'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if GloboIE.suitable(url) else super(GloboArticleIE, cls).suitable(url)


class GMANetworkVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gmanetwork'
    IE_NAME = 'GMANetworkVideo'
    _VALID_URL = 'https?://(?:www)\\.gmanetwork\\.com/(?:\\w+/){3}(?P<id>\\d+)/(?P<display_id>[\\w-]+)/video'
    _RETURN_TYPE = 'video'


class GoIE(AdobePassIE):
    _module = 'yt_dlp.extractor.go'
    IE_NAME = 'Go'
    _VALID_URL = '(?x)\n                    https?://\n                        (?P<sub_domain>\n                            (?:abc\\.|freeform\\.|watchdisneychannel\\.|watchdisneyjunior\\.|watchdisneyxd\\.|disneynow\\.|fxnow.fxnetworks\\.)?go|fxnow\\.fxnetworks|\n                            (?:www\\.)?(?:abc|freeform|disneynow)\n                        )\\.com/\n                        (?:\n                            (?:[^/]+/)*(?P<id>[Vv][Dd][Kk][Aa]\\w+)|\n                            (?:[^/]+/)*(?P<display_id>[^/?\\#]+)\n                        )\n                    '
    age_limit = 14
    _RETURN_TYPE = 'any'


class GodTubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.godtube'
    IE_NAME = 'GodTube'
    _VALID_URL = 'https?://(?:www\\.)?godtube\\.com/watch/\\?v=(?P<id>[\\da-zA-Z]+)'
    _RETURN_TYPE = 'video'


class GofileIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gofile'
    IE_NAME = 'Gofile'
    _VALID_URL = 'https?://(?:www\\.)?gofile\\.io/d/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class GolemIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.golem'
    IE_NAME = 'Golem'
    _VALID_URL = '^https?://video\\.golem\\.de/.+?/(?P<id>.+?)/'
    _RETURN_TYPE = 'video'


class GoodGameIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.goodgame'
    IE_NAME = 'goodgame:stream'
    _VALID_URL = 'https?://goodgame\\.ru/channel/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class GoogleDriveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.googledrive'
    IE_NAME = 'GoogleDrive'
    _VALID_URL = '(?x)\n                        https?://\n                            (?:\n                                (?:docs|drive)\\.google\\.com/\n                                (?:\n                                    (?:uc|open)\\?.*?id=|\n                                    file/d/\n                                )|\n                                video\\.google\\.com/get_player\\?.*?docid=\n                            )\n                            (?P<id>[a-zA-Z0-9_-]{28,})\n                    '
    _RETURN_TYPE = 'video'


class GoogleDriveFolderIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.googledrive'
    IE_NAME = 'GoogleDrive:Folder'
    _VALID_URL = 'https?://(?:docs|drive)\\.google\\.com/drive/folders/(?P<id>[\\w-]{28,})'
    _RETURN_TYPE = 'playlist'


class GooglePodcastsBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.googlepodcasts'
    IE_NAME = 'GooglePodcastsBase'


class GooglePodcastsIE(GooglePodcastsBaseIE):
    _module = 'yt_dlp.extractor.googlepodcasts'
    IE_NAME = 'google:podcasts'
    _VALID_URL = 'https?://podcasts\\.google\\.com/feed/(?P<feed_url>[^/]+)/episode/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class GooglePodcastsFeedIE(GooglePodcastsBaseIE):
    _module = 'yt_dlp.extractor.googlepodcasts'
    IE_NAME = 'google:podcasts:feed'
    _VALID_URL = 'https?://podcasts\\.google\\.com/feed/(?P<id>[^/?&#]+)/?(?:[?#&]|$)'
    _RETURN_TYPE = 'playlist'


class GoogleSearchIE(LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.googlesearch'
    IE_NAME = 'video.google:search'
    _VALID_URL = 'gvsearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'Google Video search'
    SEARCH_KEY = 'gvsearch'
    _RETURN_TYPE = 'playlist'


class GoProIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gopro'
    IE_NAME = 'GoPro'
    _VALID_URL = 'https?://(www\\.)?gopro\\.com/v/(?P<id>[A-Za-z0-9]+)'
    _RETURN_TYPE = 'video'


class GoPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.goplay'
    IE_NAME = 'GoPlay'
    _VALID_URL = 'https?://(www\\.)?goplay\\.be/video/([^/]+/[^/]+/|)(?P<display_id>[^/#]+)'
    _NETRC_MACHINE = 'goplay'
    _RETURN_TYPE = 'video'


class GoshgayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.goshgay'
    IE_NAME = 'Goshgay'
    _VALID_URL = 'https?://(?:www\\.)?goshgay\\.com/video(?P<id>\\d+?)($|/)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class GoToStageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gotostage'
    IE_NAME = 'GoToStage'
    _VALID_URL = 'https?://(?:www\\.)?gotostage\\.com/channel/[a-z0-9]+/recording/(?P<id>[a-z0-9]+)/watch'
    _RETURN_TYPE = 'video'


class GPUTechConfIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gputechconf'
    IE_NAME = 'GPUTechConf'
    _VALID_URL = 'https?://on-demand\\.gputechconf\\.com/gtc/2015/video/S(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class GronkhIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gronkh'
    IE_NAME = 'Gronkh'
    _VALID_URL = 'https?://(?:www\\.)?gronkh\\.tv/(?:watch/)?streams?/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class GronkhFeedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gronkh'
    IE_NAME = 'gronkh:feed'
    _VALID_URL = 'https?://(?:www\\.)?gronkh\\.tv(?:/feed)?/?(?:#|$)'
    _RETURN_TYPE = 'playlist'


class GronkhVodsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gronkh'
    IE_NAME = 'gronkh:vods'
    _VALID_URL = 'https?://(?:www\\.)?gronkh\\.tv/vods/streams/?(?:#|$)'
    _RETURN_TYPE = 'playlist'


class GrouponIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.groupon'
    IE_NAME = 'Groupon'
    _VALID_URL = 'https?://(?:www\\.)?groupon\\.com/deals/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class HarpodeonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.harpodeon'
    IE_NAME = 'Harpodeon'
    _VALID_URL = 'https?://(?:www\\.)?harpodeon\\.com/(?:video|preview)/\\w+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class HBOIE(HBOBaseIE):
    _module = 'yt_dlp.extractor.hbo'
    IE_NAME = 'hbo'
    _VALID_URL = 'https?://(?:www\\.)?hbo\\.com/(?:video|embed)(?:/[^/]+)*/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class HearThisAtIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hearthisat'
    IE_NAME = 'HearThisAt'
    _VALID_URL = 'https?://(?:www\\.)?hearthis\\.at/(?P<artist>[^/]+)/(?P<title>[A-Za-z0-9\\-]+)/?$'
    _RETURN_TYPE = 'video'


class HeiseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.heise'
    IE_NAME = 'Heise'
    _VALID_URL = 'https?://(?:www\\.)?heise\\.de/(?:[^/]+/)+[^/]+-(?P<id>[0-9]+)\\.html'
    _RETURN_TYPE = 'video'


class HellPornoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hellporno'
    IE_NAME = 'HellPorno'
    _VALID_URL = 'https?://(?:www\\.)?hellporno\\.(?:com/videos|net/v)/(?P<id>[^/]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class HelsinkiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.helsinki'
    IE_NAME = 'Helsinki'
    _VALID_URL = 'https?://video\\.helsinki\\.fi/Arkisto/flash\\.php\\?id=(?P<id>\\d+)'
    IE_DESC = 'helsinki.fi'
    _RETURN_TYPE = 'video'


class HGTVComShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hgtv'
    IE_NAME = 'hgtv.com:show'
    _VALID_URL = 'https?://(?:www\\.)?hgtv\\.com/shows/[^/]+/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class HKETVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hketv'
    IE_NAME = 'hketv'
    _VALID_URL = 'https?://(?:www\\.)?hkedcity\\.net/etv/resource/(?P<id>[0-9]+)'
    IE_DESC = '香港教育局教育電視 (HKETV) Educational Television, Hong Kong Educational Bureau'
    _RETURN_TYPE = 'video'


class HiDiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hidive'
    IE_NAME = 'HiDive'
    _VALID_URL = 'https?://(?:www\\.)?hidive\\.com/stream/(?P<id>(?P<title>[^/]+)/(?P<key>[^/?#&]+))'
    _NETRC_MACHINE = 'hidive'
    _RETURN_TYPE = 'video'


class HistoricFilmsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.historicfilms'
    IE_NAME = 'HistoricFilms'
    _VALID_URL = 'https?://(?:www\\.)?historicfilms\\.com/(?:tapes/|play)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class HitboxIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hitbox'
    IE_NAME = 'hitbox'
    _VALID_URL = 'https?://(?:www\\.)?(?:hitbox|smashcast)\\.tv/(?:[^/]+/)*videos?/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class HitboxLiveIE(HitboxIE):
    _module = 'yt_dlp.extractor.hitbox'
    IE_NAME = 'hitbox:live'
    _VALID_URL = 'https?://(?:www\\.)?(?:hitbox|smashcast)\\.tv/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if HitboxIE.suitable(url) else super(HitboxLiveIE, cls).suitable(url)


class HitRecordIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hitrecord'
    IE_NAME = 'HitRecord'
    _VALID_URL = 'https?://(?:www\\.)?hitrecord\\.org/records/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class HollywoodReporterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hollywoodreporter'
    IE_NAME = 'HollywoodReporter'
    _VALID_URL = 'https?://(?:www\\.)?hollywoodreporter\\.com/video/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class HollywoodReporterPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hollywoodreporter'
    IE_NAME = 'HollywoodReporterPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?hollywoodreporter\\.com/vcategory/(?P<slug>[\\w-]+)-(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class HolodexIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.holodex'
    IE_NAME = 'Holodex'
    _VALID_URL = '(?x)https?://(?:www\\.|staging\\.)?holodex\\.net/(?:\n            api/v2/playlist/(?P<playlist>\\d+)|\n            watch/(?P<id>[\\w-]{11})(?:\\?(?:[^#]+&)?playlist=(?P<playlist2>\\d+))?\n        )'
    _RETURN_TYPE = 'any'


class HotNewHipHopIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hotnewhiphop'
    IE_NAME = 'HotNewHipHop'
    _VALID_URL = 'https?://(?:www\\.)?hotnewhiphop\\.com/.*\\.(?P<id>.*)\\.html'
    _RETURN_TYPE = 'video'


class HotStarBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hotstar'
    IE_NAME = 'HotStarBase'


class HotStarIE(HotStarBaseIE):
    _module = 'yt_dlp.extractor.hotstar'
    IE_NAME = 'hotstar'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?hotstar\\.com(?:/in)?/(?!in/)\n        (?:\n            (?P<type>movies|sports|episode|(?P<tv>tv|shows))/\n            (?(tv)(?:[^/?#]+/){2}|[^?#]*)\n        )?\n        [^/?#]+/\n        (?P<id>\\d{10})\n    '
    _RETURN_TYPE = 'video'


class HotStarPrefixIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hotstar'
    IE_NAME = 'HotStarPrefix'
    _VALID_URL = 'hotstar:(?:(?P<type>\\w+):)?(?P<id>\\d+)$'
    IE_DESC = False
    _RETURN_TYPE = 'video'


class HotStarPlaylistIE(HotStarBaseIE):
    _module = 'yt_dlp.extractor.hotstar'
    IE_NAME = 'hotstar:playlist'
    _VALID_URL = 'https?://(?:www\\.)?hotstar\\.com(?:/in)?/(?:tv|shows)(?:/[^/]+){2}/list/[^/]+/t-(?P<id>\\w+)'
    _RETURN_TYPE = 'playlist'


class HotStarSeasonIE(HotStarBaseIE):
    _module = 'yt_dlp.extractor.hotstar'
    IE_NAME = 'hotstar:season'
    _VALID_URL = '(?P<url>https?://(?:www\\.)?hotstar\\.com(?:/in)?/(?:tv|shows)/[^/]+/\\w+)/seasons/[^/]+/ss-(?P<id>\\w+)'
    _RETURN_TYPE = 'playlist'


class HotStarSeriesIE(HotStarBaseIE):
    _module = 'yt_dlp.extractor.hotstar'
    IE_NAME = 'hotstar:series'
    _VALID_URL = '(?P<url>https?://(?:www\\.)?hotstar\\.com(?:/in)?/(?:tv|shows)/[^/]+/(?P<id>\\d+))/?(?:[#?]|$)'
    _RETURN_TYPE = 'playlist'


class HowcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.howcast'
    IE_NAME = 'Howcast'
    _VALID_URL = 'https?://(?:www\\.)?howcast\\.com/videos/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class HowStuffWorksIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.howstuffworks'
    IE_NAME = 'HowStuffWorks'
    _VALID_URL = 'https?://[\\da-z-]+\\.(?:howstuffworks|stuff(?:(?:youshould|theydontwantyouto)know|toblowyourmind|momnevertoldyou)|(?:brain|car)stuffshow|fwthinking|geniusstuff)\\.com/(?:[^/]+/)*(?:\\d+-)?(?P<id>.+?)-video\\.htm'
    _RETURN_TYPE = 'video'


class HrefLiRedirectIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hrefli'
    IE_NAME = 'href.li'
    _VALID_URL = 'https?://href\\.li/\\?(?P<url>.+)'
    IE_DESC = False


class HRFernsehenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hrfensehen'
    IE_NAME = 'hrfernsehen'
    _VALID_URL = '^https?://www\\.(?:hr-fernsehen|hessenschau)\\.de/.*,video-(?P<id>[0-9]{6})\\.html'
    _RETURN_TYPE = 'video'


class HRTiBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hrti'
    IE_NAME = 'HRTiBase'
    _NETRC_MACHINE = 'hrti'


class HRTiIE(HRTiBaseIE):
    _module = 'yt_dlp.extractor.hrti'
    IE_NAME = 'HRTi'
    _VALID_URL = '(?x)\n                        (?:\n                            hrti:(?P<short_id>[0-9]+)|\n                            https?://\n                                hrti\\.hrt\\.hr/(?:\\#/)?video/show/(?P<id>[0-9]+)/(?P<display_id>[^/]+)?\n                        )\n                    '
    _NETRC_MACHINE = 'hrti'
    age_limit = 12
    _RETURN_TYPE = 'video'


class HRTiPlaylistIE(HRTiBaseIE):
    _module = 'yt_dlp.extractor.hrti'
    IE_NAME = 'HRTiPlaylist'
    _VALID_URL = 'https?://hrti\\.hrt\\.hr/(?:#/)?video/list/category/(?P<id>[0-9]+)/(?P<display_id>[^/]+)?'
    _NETRC_MACHINE = 'hrti'
    _RETURN_TYPE = 'playlist'


class HSEShowBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hse'
    IE_NAME = 'HSEShowBaseInfoExtract'


class HSEShowIE(HSEShowBaseInfoExtractor):
    _module = 'yt_dlp.extractor.hse'
    IE_NAME = 'HSEShow'
    _VALID_URL = 'https?://(?:www\\.)?hse\\.de/dpl/c/tv-shows/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class HSEProductIE(HSEShowBaseInfoExtractor):
    _module = 'yt_dlp.extractor.hse'
    IE_NAME = 'HSEProduct'
    _VALID_URL = 'https?://(?:www\\.)?hse\\.de/dpl/p/product/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class HTML5MediaEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.genericembeds'
    IE_NAME = 'html5'
    _VALID_URL = False


class QuotedHTMLIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.genericembeds'
    IE_NAME = 'generic:quoted-html'
    _VALID_URL = False
    IE_DESC = False


class HuajiaoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.huajiao'
    IE_NAME = 'Huajiao'
    _VALID_URL = 'https?://(?:www\\.)?huajiao\\.com/l/(?P<id>[0-9]+)'
    IE_DESC = '花椒直播'
    _RETURN_TYPE = 'video'


class HuyaLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.huya'
    IE_NAME = 'huya:live'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?huya\\.com/(?P<id>[^/#?&]+)(?:\\D|$)'
    IE_DESC = 'huya.com'


class HuffPostIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.huffpost'
    IE_NAME = 'HuffPost'
    _VALID_URL = '(?x)\n        https?://(embed\\.)?live\\.huffingtonpost\\.com/\n        (?:\n            r/segment/[^/]+/|\n            HPLEmbedPlayer/\\?segmentId=\n        )\n        (?P<id>[0-9a-f]+)'
    IE_DESC = 'Huffington Post'
    _RETURN_TYPE = 'video'


class HungamaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hungama'
    IE_NAME = 'Hungama'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?hungama\\.com/\n                        (?:\n                            (?:video|movie)/[^/]+/|\n                            tv-show/(?:[^/]+/){2}\\d+/episode/[^/]+/\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class HungamaSongIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hungama'
    IE_NAME = 'HungamaSong'
    _VALID_URL = 'https?://(?:www\\.)?hungama\\.com/song/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class HungamaAlbumPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hungama'
    IE_NAME = 'HungamaAlbumPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?hungama\\.com/(?:playlists|album)/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class HypemIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hypem'
    IE_NAME = 'Hypem'
    _VALID_URL = 'https?://(?:www\\.)?hypem\\.com/track/(?P<id>[0-9a-z]{5})'
    _RETURN_TYPE = 'video'


class MonsterSirenHypergryphMusicIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hypergryph'
    IE_NAME = 'MonsterSirenHypergryphMusic'
    _VALID_URL = 'https?://monster-siren\\.hypergryph\\.com/music/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class HytaleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.hytale'
    IE_NAME = 'Hytale'
    _VALID_URL = 'https?://(?:www\\.)?hytale\\.com/news/\\d+/\\d+/(?P<id>[a-z0-9-]+)'
    _RETURN_TYPE = 'playlist'


class IcareusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.icareus'
    IE_NAME = 'Icareus'
    _VALID_URL = '(?P<base_url>https?://(?:www\\.)?(?:asahitv\\.fi|helsinkikanava\\.fi|hyvinvointitv\\.fi|inez\\.fi|permanto\\.fi|suite\\.icareus\\.com|videos\\.minifiddlers\\.org))/[^?#]+/player/[^?#]+\\?(?:[^#]+&)?(?:assetId|eventId)=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class IchinanaLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ichinanalive'
    IE_NAME = '17live'
    _VALID_URL = 'https?://(?:www\\.)?17\\.live/(?:[^/]+/)*(?:live|profile/r)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return not IchinanaLiveClipIE.suitable(url) and super(IchinanaLiveIE, cls).suitable(url)


class IchinanaLiveClipIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ichinanalive'
    IE_NAME = '17live:clip'
    _VALID_URL = 'https?://(?:www\\.)?17\\.live/(?:[^/]+/)*profile/r/(?P<uploader_id>\\d+)/clip/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class IdolPlusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.idolplus'
    IE_NAME = 'IdolPlus'
    _VALID_URL = 'https?://(?:www\\.)?idolplus\\.com/z[us]/(?:concert/|contents/?\\?(?:[^#]+&)?albumId=)(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class IGNBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ign'
    IE_NAME = 'IGNBase'


class IGNIE(IGNBaseIE):
    _module = 'yt_dlp.extractor.ign'
    IE_NAME = 'ign.com'
    _VALID_URL = 'https?://(?:.+?\\.ign|www\\.pcmag)\\.com/videos(?:/(?:\\d{4}/\\d{2}/\\d{2}/)?(?P<id>.+?)(?:[/?&#]|$)|(?:/?\\?(?P<filt>[^&#]+))?)'
    _RETURN_TYPE = 'video'


class IGNVideoIE(IGNBaseIE):
    _module = 'yt_dlp.extractor.ign'
    IE_NAME = 'IGNVideo'
    _VALID_URL = 'https?://.+?\\.ign\\.com/(?:[a-z]{2}/)?[^/]+/(?P<id>\\d+)/(?:video|trailer)/'
    _RETURN_TYPE = 'video'


class IGNArticleIE(IGNBaseIE):
    _module = 'yt_dlp.extractor.ign'
    IE_NAME = 'IGNArticle'
    _VALID_URL = 'https?://.+?\\.ign\\.com/(?:articles(?:/\\d{4}/\\d{2}/\\d{2})?|(?:[a-z]{2}/)?(?:[\\w-]+/)*?feature/\\d+)/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'playlist'


class IHeartRadioBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iheart'
    IE_NAME = 'IHeartRadioBase'


class IHeartRadioIE(IHeartRadioBaseIE):
    _module = 'yt_dlp.extractor.iheart'
    IE_NAME = 'IHeartRadio'
    _VALID_URL = '(?:https?://(?:www\\.)?iheart\\.com/podcast/[^/]+/episode/(?P<display_id>[^/?&#]+)-|iheartradio:)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class IHeartRadioPodcastIE(IHeartRadioBaseIE):
    _module = 'yt_dlp.extractor.iheart'
    IE_NAME = 'iheartradio:podcast'
    _VALID_URL = 'https?://(?:www\\.)?iheart(?:podcastnetwork)?\\.com/podcast/[^/?&#]+-(?P<id>\\d+)/?(?:[?#&]|$)'
    _RETURN_TYPE = 'playlist'


class IltalehtiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iltalehti'
    IE_NAME = 'Iltalehti'
    _VALID_URL = 'https?://(?:www\\.)?iltalehti\\.fi/[^/?#]+/a/(?P<id>[^/?#])'
    _RETURN_TYPE = 'video'


class ImdbIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.imdb'
    IE_NAME = 'imdb'
    _VALID_URL = 'https?://(?:www|m)\\.imdb\\.com/(?:video|title|list).*?[/-]vi(?P<id>\\d+)'
    IE_DESC = 'Internet Movie Database trailers'
    _RETURN_TYPE = 'video'


class ImdbListIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.imdb'
    IE_NAME = 'imdb:list'
    _VALID_URL = 'https?://(?:www\\.)?imdb\\.com/list/ls(?P<id>\\d{9})(?!/videoplayer/vi\\d+)'
    IE_DESC = 'Internet Movie Database lists'
    _RETURN_TYPE = 'playlist'


class ImgurIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.imgur'
    IE_NAME = 'Imgur'
    _VALID_URL = 'https?://(?:i\\.)?imgur\\.com/(?!(?:a|gallery|(?:t(?:opic)?|r)/[^/]+)/)(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'


class ImgurGalleryIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.imgur'
    IE_NAME = 'imgur:gallery'
    _VALID_URL = 'https?://(?:i\\.)?imgur\\.com/(?:gallery|(?:t(?:opic)?|r)/[^/]+)/(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'any'


class ImgurAlbumIE(ImgurGalleryIE):
    _module = 'yt_dlp.extractor.imgur'
    IE_NAME = 'imgur:album'
    _VALID_URL = 'https?://(?:i\\.)?imgur\\.com/a/(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'playlist'


class InaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ina'
    IE_NAME = 'Ina'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)?ina\\.fr/(?:[^?#]+/)(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class IncIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.inc'
    IE_NAME = 'Inc'
    _VALID_URL = 'https?://(?:www\\.)?inc\\.com/(?:[^/]+/)+(?P<id>[^.]+).html'
    _RETURN_TYPE = 'video'


class IndavideoEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.indavideo'
    IE_NAME = 'IndavideoEmbed'
    _VALID_URL = 'https?://(?:(?:embed\\.)?indavideo\\.hu/player/video/|assets\\.indavideo\\.hu/swf/player\\.swf\\?.*\\b(?:v(?:ID|id))=)(?P<id>[\\da-f]+)'
    _RETURN_TYPE = 'video'


class InfoQIE(BokeCCBaseIE):
    _module = 'yt_dlp.extractor.infoq'
    IE_NAME = 'InfoQ'
    _VALID_URL = 'https?://(?:www\\.)?infoq\\.com/(?:[^/]+/)+(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class InstagramBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.instagram'
    IE_NAME = 'InstagramBase'
    _NETRC_MACHINE = 'instagram'


class InstagramIE(InstagramBaseIE):
    _module = 'yt_dlp.extractor.instagram'
    IE_NAME = 'Instagram'
    _VALID_URL = '(?P<url>https?://(?:www\\.)?instagram\\.com(?:/[^/]+)?/(?:p|tv|reel)/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'instagram'
    _RETURN_TYPE = 'any'


class InstagramIOSIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.instagram'
    IE_NAME = 'InstagramIOS'
    _VALID_URL = 'instagram://media\\?id=(?P<id>[\\d_]+)'
    IE_DESC = 'IOS instagram:// URL'
    _RETURN_TYPE = 'video'


class InstagramPlaylistBaseIE(InstagramBaseIE):
    _module = 'yt_dlp.extractor.instagram'
    IE_NAME = 'InstagramPlaylistBase'
    _NETRC_MACHINE = 'instagram'


class InstagramUserIE(InstagramPlaylistBaseIE):
    _module = 'yt_dlp.extractor.instagram'
    IE_NAME = 'instagram:user'
    _VALID_URL = 'https?://(?:www\\.)?instagram\\.com/(?P<id>[^/]{2,})/?(?:$|[?#])'
    IE_DESC = 'Instagram user profile'
    _NETRC_MACHINE = 'instagram'
    _RETURN_TYPE = 'playlist'


class InstagramTagIE(InstagramPlaylistBaseIE):
    _module = 'yt_dlp.extractor.instagram'
    IE_NAME = 'instagram:tag'
    _VALID_URL = 'https?://(?:www\\.)?instagram\\.com/explore/tags/(?P<id>[^/]+)'
    IE_DESC = 'Instagram hashtag search URLs'
    _NETRC_MACHINE = 'instagram'
    _RETURN_TYPE = 'playlist'


class InstagramStoryIE(InstagramBaseIE):
    _module = 'yt_dlp.extractor.instagram'
    IE_NAME = 'instagram:story'
    _VALID_URL = 'https?://(?:www\\.)?instagram\\.com/stories/(?P<user>[^/]+)/(?P<id>\\d+)'
    _NETRC_MACHINE = 'instagram'
    _RETURN_TYPE = 'playlist'


class InternazionaleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.internazionale'
    IE_NAME = 'Internazionale'
    _VALID_URL = 'https?://(?:www\\.)?internazionale\\.it/video/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class InternetVideoArchiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.internetvideoarchive'
    IE_NAME = 'InternetVideoArchive'
    _VALID_URL = 'https?://video\\.internetvideoarchive\\.net/(?:player|flash/players)/.*?\\?.*?publishedid.*?'
    _RETURN_TYPE = 'video'


class IPrimaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iprima'
    IE_NAME = 'IPrima'
    _VALID_URL = 'https?://(?!cnn)(?:[^/]+)\\.iprima\\.cz/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'iprima'
    _RETURN_TYPE = 'video'


class IPrimaCNNIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iprima'
    IE_NAME = 'IPrimaCNN'
    _VALID_URL = 'https?://cnn\\.iprima\\.cz/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class IqiyiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iqiyi'
    IE_NAME = 'iqiyi'
    _VALID_URL = 'https?://(?:(?:[^.]+\\.)?iqiyi\\.com|www\\.pps\\.tv)/.+\\.html'
    IE_DESC = '爱奇艺'
    _NETRC_MACHINE = 'iqiyi'
    _RETURN_TYPE = 'any'


class IqIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iqiyi'
    IE_NAME = 'iq.com'
    _VALID_URL = 'https?://(?:www\\.)?iq\\.com/play/(?:[\\w%-]*-)?(?P<id>\\w+)'
    IE_DESC = 'International version of iQiyi'
    age_limit = 13
    _RETURN_TYPE = 'video'


class IqAlbumIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iqiyi'
    IE_NAME = 'iq.com:album'
    _VALID_URL = 'https?://(?:www\\.)?iq\\.com/album/(?:[\\w%-]*-)?(?P<id>\\w+)'
    age_limit = 13
    _RETURN_TYPE = 'any'


class IslamChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.islamchannel'
    IE_NAME = 'IslamChannel'
    _VALID_URL = 'https?://watch\\.islamchannel\\.tv/watch/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class IslamChannelSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.islamchannel'
    IE_NAME = 'IslamChannelSeries'
    _VALID_URL = 'https?://watch\\.islamchannel\\.tv/series/(?P<id>[a-f\\d-]+)'
    _RETURN_TYPE = 'playlist'


class IsraelNationalNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.israelnationalnews'
    IE_NAME = 'IsraelNationalNews'
    _VALID_URL = 'https?://(?:www\\.)?israelnationalnews\\.com/news/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class ITProTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.itprotv'
    IE_NAME = 'ITProTVBase'


class ITProTVIE(ITProTVBaseIE):
    _module = 'yt_dlp.extractor.itprotv'
    IE_NAME = 'ITProTV'
    _VALID_URL = 'https://app.itpro.tv/course/(?P<course>[\\w-]+)/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class ITProTVCourseIE(ITProTVBaseIE):
    _module = 'yt_dlp.extractor.itprotv'
    IE_NAME = 'ITProTVCourse'
    _VALID_URL = 'https?://app.itpro.tv/course/(?P<id>[\\w-]+)/?(?:$|[#?])'
    _RETURN_TYPE = 'playlist'


class ITVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.itv'
    IE_NAME = 'ITV'
    _VALID_URL = 'https?://(?:www\\.)?itv\\.com/hub/[^/]+/(?P<id>[0-9a-zA-Z]+)'
    _RETURN_TYPE = 'video'


class ITVBTCCIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.itv'
    IE_NAME = 'ITVBTCC'
    _VALID_URL = 'https?://(?:www\\.)?itv\\.com/(?:news|btcc)/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class IviIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ivi'
    IE_NAME = 'ivi'
    _VALID_URL = 'https?://(?:www\\.)?ivi\\.(?:ru|tv)/(?:watch/(?:[^/]+/)?|video/player\\?.*?videoId=)(?P<id>\\d+)'
    IE_DESC = 'ivi.ru'
    _RETURN_TYPE = 'video'


class IviCompilationIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ivi'
    IE_NAME = 'ivi:compilation'
    _VALID_URL = 'https?://(?:www\\.)?ivi\\.ru/watch/(?!\\d+)(?P<compilationid>[a-z\\d_-]+)(?:/season(?P<seasonid>\\d+))?$'
    IE_DESC = 'ivi.ru compilations'
    _RETURN_TYPE = 'playlist'


class IvideonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ivideon'
    IE_NAME = 'ivideon'
    _VALID_URL = 'https?://(?:www\\.)?ivideon\\.com/tv/(?:[^/]+/)*camera/(?P<id>\\d+-[\\da-f]+)/(?P<camera_id>\\d+)'
    IE_DESC = 'Ivideon TV'
    _RETURN_TYPE = 'video'


class IwaraBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.iwara'
    IE_NAME = 'IwaraBase'
    _NETRC_MACHINE = 'iwara'


class IwaraIE(IwaraBaseIE):
    _module = 'yt_dlp.extractor.iwara'
    IE_NAME = 'iwara'
    _VALID_URL = 'https?://(?:www\\.|ecchi\\.)?iwara\\.tv/videos?/(?P<id>[a-zA-Z0-9]+)'
    _NETRC_MACHINE = 'iwara'
    age_limit = 18
    _RETURN_TYPE = 'video'


class IwaraPlaylistIE(IwaraBaseIE):
    _module = 'yt_dlp.extractor.iwara'
    IE_NAME = 'iwara:playlist'
    _VALID_URL = 'https?://(?:www\\.)?iwara\\.tv/playlist/(?P<id>[0-9a-f-]+)'
    _NETRC_MACHINE = 'iwara'
    _RETURN_TYPE = 'playlist'


class IwaraUserIE(IwaraBaseIE):
    _module = 'yt_dlp.extractor.iwara'
    IE_NAME = 'iwara:user'
    _VALID_URL = 'https?://(?:www\\.)?iwara\\.tv/profile/(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'iwara'
    _RETURN_TYPE = 'playlist'


class IxiguaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ixigua'
    IE_NAME = 'Ixigua'
    _VALID_URL = 'https?://(?:\\w+\\.)?ixigua\\.com/(?:video/)?(?P<id>\\d+).+'
    _RETURN_TYPE = 'video'


class IzleseneIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.izlesene'
    IE_NAME = 'Izlesene'
    _VALID_URL = '(?x)\n        https?://(?:(?:www|m)\\.)?izlesene\\.com/\n        (?:video|embedplayer)/(?:[^/]+/)?(?P<id>[0-9]+)\n        '
    _RETURN_TYPE = 'video'


class JableIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jable'
    IE_NAME = 'Jable'
    _VALID_URL = 'https?://(?:www\\.)?jable.tv/videos/(?P<id>[\\w-]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class JablePlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jable'
    IE_NAME = 'JablePlaylist'
    _VALID_URL = 'https?://(?:www\\.)?jable.tv/(?:categories|models|tags)/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class JamendoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jamendo'
    IE_NAME = 'Jamendo'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            licensing\\.jamendo\\.com/[^/]+|\n                            (?:www\\.)?jamendo\\.com\n                        )\n                        /track/(?P<id>[0-9]+)(?:/(?P<display_id>[^/?#&]+))?\n                    '
    _RETURN_TYPE = 'video'


class JamendoAlbumIE(JamendoIE):
    _module = 'yt_dlp.extractor.jamendo'
    IE_NAME = 'JamendoAlbum'
    _VALID_URL = 'https?://(?:www\\.)?jamendo\\.com/album/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'playlist'


class ShugiinItvBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.japandiet'
    IE_NAME = 'ShugiinItvBase'


class ShugiinItvLiveIE(ShugiinItvBaseIE):
    _module = 'yt_dlp.extractor.japandiet'
    IE_NAME = 'ShugiinItvLive'
    _VALID_URL = 'https?://(?:www\\.)?shugiintv\\.go\\.jp/(?:jp|en)(?:/index\\.php)?$'
    IE_DESC = '衆議院インターネット審議中継'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return super().suitable(url) and not any(x.suitable(url) for x in (ShugiinItvLiveRoomIE, ShugiinItvVodIE))


class ShugiinItvLiveRoomIE(ShugiinItvBaseIE):
    _module = 'yt_dlp.extractor.japandiet'
    IE_NAME = 'ShugiinItvLiveRoom'
    _VALID_URL = 'https?://(?:www\\.)?shugiintv\\.go\\.jp/(?:jp|en)/index\\.php\\?room_id=(?P<id>room\\d+)'
    IE_DESC = '衆議院インターネット審議中継 (中継)'
    _RETURN_TYPE = 'video'


class ShugiinItvVodIE(ShugiinItvBaseIE):
    _module = 'yt_dlp.extractor.japandiet'
    IE_NAME = 'ShugiinItvVod'
    _VALID_URL = 'https?://(?:www\\.)?shugiintv\\.go\\.jp/(?:jp|en)/index\\.php\\?ex=VL(?:\\&[^=]+=[^&]*)*\\&deli_id=(?P<id>\\d+)'
    IE_DESC = '衆議院インターネット審議中継 (ビデオライブラリ)'
    _RETURN_TYPE = 'video'


class SangiinInstructionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.japandiet'
    IE_NAME = 'SangiinInstruction'
    _VALID_URL = '^https?://www\\.webtv\\.sangiin\\.go\\.jp/webtv/index\\.php'
    IE_DESC = False


class SangiinIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.japandiet'
    IE_NAME = 'Sangiin'
    _VALID_URL = 'https?://www\\.webtv\\.sangiin\\.go\\.jp/webtv/detail\\.php\\?sid=(?P<id>\\d+)'
    IE_DESC = '参議院インターネット審議中継 (archive)'
    _RETURN_TYPE = 'video'


class JeuxVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jeuxvideo'
    IE_NAME = 'JeuxVideo'
    _VALID_URL = 'https?://.*?\\.jeuxvideo\\.com/.*/(.*?)\\.htm'
    _RETURN_TYPE = 'video'


class JoveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jove'
    IE_NAME = 'Jove'
    _VALID_URL = 'https?://(?:www\\.)?jove\\.com/video/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class JojIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.joj'
    IE_NAME = 'Joj'
    _VALID_URL = '(?x)\n                    (?:\n                        joj:|\n                        https?://media\\.joj\\.sk/embed/\n                    )\n                    (?P<id>[^/?#^]+)\n                '
    _RETURN_TYPE = 'video'


class JStreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jstream'
    IE_NAME = 'JStream'
    _VALID_URL = 'jstream:(?P<host>www\\d+):(?P<id>(?P<publisher>[a-z0-9]+):(?P<mid>\\d+))'
    _RETURN_TYPE = 'video'


class JWPlatformIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jwplatform'
    IE_NAME = 'JWPlatform'
    _VALID_URL = '(?:https?://(?:content\\.jwplatform|cdn\\.jwplayer)\\.com/(?:(?:feed|player|thumb|preview|manifest)s|jw6|v2/media)/|jwplatform:)(?P<id>[a-zA-Z0-9]{8})'
    _RETURN_TYPE = 'video'


class KakaoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kakao'
    IE_NAME = 'Kakao'
    _VALID_URL = 'https?://(?:play-)?tv\\.kakao\\.com/(?:channel/\\d+|embed/player)/cliplink/(?P<id>\\d+|[^?#&]+@my)'
    _RETURN_TYPE = 'video'


class KalturaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kaltura'
    IE_NAME = 'Kaltura'
    _VALID_URL = '(?x)\n                (?:\n                    kaltura:(?P<partner_id>\\w+):(?P<id>\\w+)(?::(?P<player_type>\\w+))?|\n                    https?://\n                        (:?(?:www|cdnapi(?:sec)?)\\.)?kaltura\\.com(?::\\d+)?/\n                        (?:\n                            (?:\n                                # flash player\n                                index\\.php/(?:kwidget|extwidget/preview)|\n                                # html5 player\n                                html5/html5lib/[^/]+/mwEmbedFrame\\.php\n                            )\n                        )(?:/(?P<path>[^?]+))?(?:\\?(?P<query>.*))?\n                )\n                '
    _RETURN_TYPE = 'any'


class Kanal2IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kanal2'
    IE_NAME = 'Kanal2'
    _VALID_URL = 'https?://kanal2\\.postimees\\.ee/[^?#]+\\?([^#]+&)?id=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class KankaNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kankanews'
    IE_NAME = 'KankaNews'
    _VALID_URL = 'https?://(?:www\\.)?kankanews\\.com/a/\\d+\\-\\d+\\-\\d+/(?P<id>\\d+)\\.shtml'
    _RETURN_TYPE = 'video'


class KaraoketvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.karaoketv'
    IE_NAME = 'Karaoketv'
    _VALID_URL = 'https?://(?:www\\.)?karaoketv\\.co\\.il/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class KarriereVideosIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.karrierevideos'
    IE_NAME = 'KarriereVideos'
    _VALID_URL = 'https?://(?:www\\.)?karrierevideos\\.at(?:/[^/]+)+/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class KeezMoviesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.keezmovies'
    IE_NAME = 'KeezMovies'
    _VALID_URL = 'https?://(?:www\\.)?keezmovies\\.com/video/(?:(?P<display_id>[^/]+)-)?(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class ExtremeTubeIE(KeezMoviesIE):
    _module = 'yt_dlp.extractor.extremetube'
    IE_NAME = 'ExtremeTube'
    _VALID_URL = 'https?://(?:www\\.)?extremetube\\.com/(?:[^/]+/)?video/(?P<id>[^/#?&]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class KelbyOneIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kelbyone'
    IE_NAME = 'KelbyOne'
    _VALID_URL = 'https?://members\\.kelbyone\\.com/course/(?P<id>[^$&?#/]+)'
    _RETURN_TYPE = 'playlist'


class KhanAcademyBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.khanacademy'
    IE_NAME = 'KhanAcademyBase'


class KhanAcademyIE(KhanAcademyBaseIE):
    _module = 'yt_dlp.extractor.khanacademy'
    IE_NAME = 'khanacademy'
    _VALID_URL = 'https?://(?:www\\.)?khanacademy\\.org/(?P<id>(?:[^/]+/){4}v/[^?#/&]+)'
    _RETURN_TYPE = 'video'


class KhanAcademyUnitIE(KhanAcademyBaseIE):
    _module = 'yt_dlp.extractor.khanacademy'
    IE_NAME = 'khanacademy:unit'
    _VALID_URL = 'https?://(?:www\\.)?khanacademy\\.org/(?P<id>(?:[^/]+/){2}[^?#/&]+)/?(?:[?#&]|$)'
    _RETURN_TYPE = 'playlist'


class KickBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kick'
    IE_NAME = 'KickBase'


class KickIE(KickBaseIE):
    _module = 'yt_dlp.extractor.kick'
    IE_NAME = 'Kick'
    _VALID_URL = 'https?://(?:www\\.)?kick\\.com/(?!(?:video|categories|search|auth)(?:[/?#]|$))(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class KickVODIE(KickBaseIE):
    _module = 'yt_dlp.extractor.kick'
    IE_NAME = 'KickVOD'
    _VALID_URL = 'https?://(?:www\\.)?kick\\.com/video/(?P<id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class KickerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kicker'
    IE_NAME = 'Kicker'
    _VALID_URL = 'https?://(?:www\\.)kicker\\.(?:de)/(?P<id>[\\w-]+)/video'
    _RETURN_TYPE = 'video'


class KickStarterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kickstarter'
    IE_NAME = 'KickStarter'
    _VALID_URL = 'https?://(?:www\\.)?kickstarter\\.com/projects/(?P<id>[^/]*)/.*'
    _RETURN_TYPE = 'video'


class KinjaEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kinja'
    IE_NAME = 'KinjaEmbed'
    _VALID_URL = '(?x)https?://(?:[^.]+\\.)?\n        (?:\n            avclub|\n            clickhole|\n            deadspin|\n            gizmodo|\n            jalopnik|\n            jezebel|\n            kinja|\n            kotaku|\n            lifehacker|\n            splinternews|\n            the(?:inventory|onion|root|takeout)\n        )\\.com/\n        (?:\n            ajax/inset|\n            embed/video\n        )/iframe\\?.*?\\bid=\n        (?P<type>\n            fb|\n            imgur|\n            instagram|\n            jwp(?:layer)?-video|\n            kinjavideo|\n            mcp|\n            megaphone|\n            ooyala|\n            soundcloud(?:-playlist)?|\n            tumblr-post|\n            twitch-stream|\n            twitter|\n            ustream-channel|\n            vimeo|\n            vine|\n            youtube-(?:list|video)\n        )-(?P<id>[^&]+)'


class KinoPoiskIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kinopoisk'
    IE_NAME = 'KinoPoisk'
    _VALID_URL = 'https?://(?:www\\.)?kinopoisk\\.ru/film/(?P<id>\\d+)'
    age_limit = 12
    _RETURN_TYPE = 'video'


class KommunetvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kommunetv'
    IE_NAME = 'Kommunetv'
    _VALID_URL = 'https://(\\w+).kommunetv.no/archive/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class JixieBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.jixie'
    IE_NAME = 'JixieBase'


class KompasVideoIE(JixieBaseIE):
    _module = 'yt_dlp.extractor.kompas'
    IE_NAME = 'KompasVideo'
    _VALID_URL = 'https?://video\\.kompas\\.com/\\w+/(?P<id>\\d+)/(?P<slug>[\\w-]+)'
    _RETURN_TYPE = 'video'


class KonserthusetPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.konserthusetplay'
    IE_NAME = 'KonserthusetPlay'
    _VALID_URL = 'https?://(?:www\\.)?(?:konserthusetplay|rspoplay)\\.se/\\?.*\\bm=(?P<id>[^&]+)'
    _RETURN_TYPE = 'video'


class KooIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.koo'
    IE_NAME = 'Koo'
    _VALID_URL = 'https?://(?:www\\.)?kooapp\\.com/koo/[^/]+/(?P<id>[^/&#$?]+)'
    _RETURN_TYPE = 'video'


class KTHIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kth'
    IE_NAME = 'KTH'
    _VALID_URL = 'https?://play\\.kth\\.se/(?:[^/]+/)+(?P<id>[a-z0-9_]+)'
    _RETURN_TYPE = 'video'


class KrasViewIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.krasview'
    IE_NAME = 'KrasView'
    _VALID_URL = 'https?://krasview\\.ru/(?:video|embed)/(?P<id>\\d+)'
    IE_DESC = 'Красвью'
    _RETURN_TYPE = 'video'


class Ku6IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ku6'
    IE_NAME = 'Ku6'
    _VALID_URL = 'https?://v\\.ku6\\.com/show/(?P<id>[a-zA-Z0-9\\-\\_]+)(?:\\.)*html'
    _RETURN_TYPE = 'video'


class KUSIIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kusi'
    IE_NAME = 'KUSI'
    _VALID_URL = 'https?://(?:www\\.)?kusi\\.com/(?P<path>story/.+|video\\?clipId=(?P<clipId>\\d+))'
    _RETURN_TYPE = 'video'


class KuwoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kuwo'
    IE_NAME = 'KuwoBase'


class KuwoIE(KuwoBaseIE):
    _module = 'yt_dlp.extractor.kuwo'
    IE_NAME = 'kuwo:song'
    _VALID_URL = 'https?://(?:www\\.)?kuwo\\.cn/yinyue/(?P<id>\\d+)'
    IE_DESC = '酷我音乐'
    _RETURN_TYPE = 'video'


class KuwoAlbumIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kuwo'
    IE_NAME = 'kuwo:album'
    _VALID_URL = 'https?://(?:www\\.)?kuwo\\.cn/album/(?P<id>\\d+?)/'
    IE_DESC = '酷我音乐 - 专辑'
    _RETURN_TYPE = 'playlist'


class KuwoChartIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kuwo'
    IE_NAME = 'kuwo:chart'
    _VALID_URL = 'https?://yinyue\\.kuwo\\.cn/billboard_(?P<id>[^.]+).htm'
    IE_DESC = '酷我音乐 - 排行榜'
    _RETURN_TYPE = 'playlist'


class KuwoSingerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kuwo'
    IE_NAME = 'kuwo:singer'
    _VALID_URL = 'https?://(?:www\\.)?kuwo\\.cn/mingxing/(?P<id>[^/]+)'
    IE_DESC = '酷我音乐 - 歌手'
    _RETURN_TYPE = 'playlist'


class KuwoCategoryIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.kuwo'
    IE_NAME = 'kuwo:category'
    _VALID_URL = 'https?://yinyue\\.kuwo\\.cn/yy/cinfo_(?P<id>\\d+?).htm'
    IE_DESC = '酷我音乐 - 分类'
    _RETURN_TYPE = 'playlist'


class KuwoMvIE(KuwoBaseIE):
    _module = 'yt_dlp.extractor.kuwo'
    IE_NAME = 'kuwo:mv'
    _VALID_URL = 'https?://(?:www\\.)?kuwo\\.cn/mv/(?P<id>\\d+?)/'
    IE_DESC = '酷我音乐 - MV'
    _RETURN_TYPE = 'video'


class LA7IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.la7'
    IE_NAME = 'la7.it'
    _VALID_URL = '(?x)https?://(?:\n        (?:www\\.)?la7\\.it/([^/]+)/(?:rivedila7|video|news)/|\n        tg\\.la7\\.it/repliche-tgla7\\?id=\n    )(?P<id>.+)'
    _RETURN_TYPE = 'video'


class LA7PodcastEpisodeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.la7'
    IE_NAME = 'la7.it:pod:episode'
    _VALID_URL = 'https?://(?:www\\.)?la7\\.it/[^/]+/podcast/([^/]+-)?(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class LA7PodcastIE(LA7PodcastEpisodeIE):
    _module = 'yt_dlp.extractor.la7'
    IE_NAME = 'la7.it:podcast'
    _VALID_URL = 'https?://(?:www\\.)?la7\\.it/(?P<id>[^/]+)/podcast/?(?:$|[#?])'
    _RETURN_TYPE = 'playlist'


class Laola1TvEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.laola1tv'
    IE_NAME = 'laola1tv:embed'
    _VALID_URL = 'https?://(?:www\\.)?laola1\\.tv/titanplayer\\.php\\?.*?\\bvideoid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class Laola1TvBaseIE(Laola1TvEmbedIE):
    _module = 'yt_dlp.extractor.laola1tv'
    IE_NAME = 'laola1tv:embed'
    _VALID_URL = 'https?://(?:www\\.)?laola1\\.tv/titanplayer\\.php\\?.*?\\bvideoid=(?P<id>\\d+)'


class Laola1TvIE(Laola1TvBaseIE):
    _module = 'yt_dlp.extractor.laola1tv'
    IE_NAME = 'laola1tv'
    _VALID_URL = 'https?://(?:www\\.)?laola1\\.tv/[a-z]+-[a-z]+/[^/]+/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class EHFTVIE(Laola1TvBaseIE):
    _module = 'yt_dlp.extractor.laola1tv'
    IE_NAME = 'ehftv'
    _VALID_URL = 'https?://(?:www\\.)?ehftv\\.com/[a-z]+(?:-[a-z]+)?/[^/]+/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class ITTFIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.laola1tv'
    IE_NAME = 'ITTF'
    _VALID_URL = 'https?://tv\\.ittf\\.com/video/[^/]+/(?P<id>\\d+)'


class LastFMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lastfm'
    IE_NAME = 'LastFM'
    _VALID_URL = 'https?://(?:www\\.)?last\\.fm/music(?:/[^/]+){2}/(?P<id>[^/#?]+)'
    _RETURN_TYPE = 'video'


class LastFMPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lastfm'
    IE_NAME = 'LastFMPlaylistBase'


class LastFMPlaylistIE(LastFMPlaylistBaseIE):
    _module = 'yt_dlp.extractor.lastfm'
    IE_NAME = 'LastFMPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?last\\.fm/(music|tag)/(?P<id>[^/]+)(?:/[^/]+)?/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class LastFMUserIE(LastFMPlaylistBaseIE):
    _module = 'yt_dlp.extractor.lastfm'
    IE_NAME = 'LastFMUser'
    _VALID_URL = 'https?://(?:www\\.)?last\\.fm/user/[^/]+/playlists/(?P<id>[^/#?]+)'
    _RETURN_TYPE = 'playlist'


class LBRYBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lbry'
    IE_NAME = 'LBRYBase'


class LBRYIE(LBRYBaseIE):
    _module = 'yt_dlp.extractor.lbry'
    IE_NAME = 'lbry'
    _VALID_URL = '(?:https?://(?:www\\.)?(?:lbry\\.tv|odysee\\.com)/|lbry://)(?P<id>\\$/[^/]+/[^/]+/[0-9a-f]{1,40}|@[^:/?#&]+(?:[:#][0-9a-f]{1,40})?/[^:/?#&]+(?:[:#][0-9a-f]{1,40})?|(?!@)[^:/?#&]+(?:[:#][0-9a-f]{1,40})?)'
    _RETURN_TYPE = 'video'


class LBRYChannelIE(LBRYBaseIE):
    _module = 'yt_dlp.extractor.lbry'
    IE_NAME = 'lbry:channel'
    _VALID_URL = '(?:https?://(?:www\\.)?(?:lbry\\.tv|odysee\\.com)/|lbry://)(?P<id>@[^:/?#&]+(?:[:#][0-9a-f]{1,40})?)/?(?:[?&]|$)'
    _RETURN_TYPE = 'playlist'


class LCIIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lci'
    IE_NAME = 'LCI'
    _VALID_URL = 'https?://(?:www\\.)?(?:lci|tf1info)\\.fr/[^/]+/[\\w-]+-(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class LcpPlayIE(ArkenaIE):
    _module = 'yt_dlp.extractor.lcp'
    IE_NAME = 'LcpPlay'
    _VALID_URL = 'https?://play\\.lcp\\.fr/embed/(?P<id>[^/]+)/(?P<account_id>[^/]+)/[^/]+/[^/]+'
    _RETURN_TYPE = 'video'


class LcpIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lcp'
    IE_NAME = 'Lcp'
    _VALID_URL = 'https?://(?:www\\.)?lcp\\.fr/(?:[^/]+/)*(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class Lecture2GoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lecture2go'
    IE_NAME = 'Lecture2Go'
    _VALID_URL = 'https?://lecture2go\\.uni-hamburg\\.de/veranstaltungen/-/v/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class LecturioBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lecturio'
    IE_NAME = 'LecturioBase'
    _NETRC_MACHINE = 'lecturio'


class LecturioIE(LecturioBaseIE):
    _module = 'yt_dlp.extractor.lecturio'
    IE_NAME = 'Lecturio'
    _VALID_URL = '(?x)\n                    https://\n                        (?:\n                            app\\.lecturio\\.com/([^/]+/(?P<nt>[^/?#&]+)\\.lecture|(?:\\#/)?lecture/c/\\d+/(?P<id>\\d+))|\n                            (?:www\\.)?lecturio\\.de/[^/]+/(?P<nt_de>[^/?#&]+)\\.vortrag\n                        )\n                    '
    _NETRC_MACHINE = 'lecturio'
    _RETURN_TYPE = 'video'


class LecturioCourseIE(LecturioBaseIE):
    _module = 'yt_dlp.extractor.lecturio'
    IE_NAME = 'LecturioCourse'
    _VALID_URL = 'https://app\\.lecturio\\.com/(?:[^/]+/(?P<nt>[^/?#&]+)\\.course|(?:#/)?course/c/(?P<id>\\d+))'
    _NETRC_MACHINE = 'lecturio'
    _RETURN_TYPE = 'playlist'


class LecturioDeCourseIE(LecturioBaseIE):
    _module = 'yt_dlp.extractor.lecturio'
    IE_NAME = 'LecturioDeCourse'
    _VALID_URL = 'https://(?:www\\.)?lecturio\\.de/[^/]+/(?P<id>[^/?#&]+)\\.kurs'
    _NETRC_MACHINE = 'lecturio'


class LeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.leeco'
    IE_NAME = 'Le'
    _VALID_URL = 'https?://(?:www\\.le\\.com/ptv/vplay|(?:sports\\.le|(?:www\\.)?lesports)\\.com/(?:match|video))/(?P<id>\\d+)\\.html'
    IE_DESC = '乐视网'
    _RETURN_TYPE = 'video'


class LePlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.leeco'
    IE_NAME = 'LePlaylist'
    _VALID_URL = 'https?://[a-z]+\\.le\\.com/(?!video)[a-z]+/(?P<id>[a-z0-9_]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if LeIE.suitable(url) else super(LePlaylistIE, cls).suitable(url)


class LetvCloudIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.leeco'
    IE_NAME = 'LetvCloud'
    _VALID_URL = 'https?://yuntv\\.letv\\.com/bcloud.html\\?.+'
    IE_DESC = '乐视云'
    _RETURN_TYPE = 'video'


class LeFigaroVideoEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lefigaro'
    IE_NAME = 'LeFigaroVideoEmbed'
    _VALID_URL = 'https?://video\\.lefigaro\\.fr/embed/[^?#]+/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class LeFigaroVideoSectionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lefigaro'
    IE_NAME = 'LeFigaroVideoSection'
    _VALID_URL = 'https?://video\\.lefigaro\\.fr/figaro/(?P<id>[\\w-]+)/?(?:[#?]|$)'
    _RETURN_TYPE = 'playlist'


class LEGOIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lego'
    IE_NAME = 'LEGO'
    _VALID_URL = 'https?://(?:www\\.)?lego\\.com/(?P<locale>[a-z]{2}-[a-z]{2})/(?:[^/]+/)*videos/(?:[^/]+/)*[^/?#]+-(?P<id>[0-9a-f]{32})'
    age_limit = 5
    _RETURN_TYPE = 'video'


class LemondeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lemonde'
    IE_NAME = 'Lemonde'
    _VALID_URL = 'https?://(?:.+?\\.)?lemonde\\.fr/(?:[^/]+/)*(?P<id>[^/]+)\\.html'
    _RETURN_TYPE = 'video'


class LentaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lenta'
    IE_NAME = 'Lenta'
    _VALID_URL = 'https?://(?:www\\.)?lenta\\.ru/[^/]+/\\d+/\\d+/\\d+/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class LibraryOfCongressIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.libraryofcongress'
    IE_NAME = 'loc'
    _VALID_URL = 'https?://(?:www\\.)?loc\\.gov/(?:item/|today/cyberlc/feature_wdesc\\.php\\?.*\\brec=)(?P<id>[0-9a-z_.]+)'
    IE_DESC = 'Library of Congress'
    _RETURN_TYPE = 'video'


class LibsynIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.libsyn'
    IE_NAME = 'Libsyn'
    _VALID_URL = '(?P<mainurl>https?://html5-player\\.libsyn\\.com/embed/episode/id/(?P<id>[0-9]+))'
    _RETURN_TYPE = 'video'


class LifeNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lifenews'
    IE_NAME = 'life'
    _VALID_URL = 'https?://life\\.ru/t/[^/]+/(?P<id>\\d+)'
    IE_DESC = 'Life.ru'
    _RETURN_TYPE = 'any'


class LifeEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lifenews'
    IE_NAME = 'life:embed'
    _VALID_URL = 'https?://embed\\.life\\.ru/(?:embed|video)/(?P<id>[\\da-f]{32})'
    _RETURN_TYPE = 'video'


class LikeeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.likee'
    IE_NAME = 'likee'
    _VALID_URL = '(?x)https?://(www\\.)?likee\\.video/(?:(?P<channel_name>[^/]+)/video/|v/)(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class LikeeUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.likee'
    IE_NAME = 'likee:user'
    _VALID_URL = 'https?://(www\\.)?likee\\.video/(?P<id>[^/]+)/?$'
    _RETURN_TYPE = 'playlist'


class LimelightBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.limelight'
    IE_NAME = 'LimelightBase'


class LimelightMediaIE(LimelightBaseIE):
    _module = 'yt_dlp.extractor.limelight'
    IE_NAME = 'limelight'
    _VALID_URL = '(?x)\n                        (?:\n                            limelight:media:|\n                            https?://\n                                (?:\n                                    link\\.videoplatform\\.limelight\\.com/media/|\n                                    assets\\.delvenetworks\\.com/player/loader\\.swf\n                                )\n                                \\?.*?\\bmediaId=\n                        )\n                        (?P<id>[a-z0-9]{32})\n                    '
    _RETURN_TYPE = 'video'


class LimelightChannelIE(LimelightBaseIE):
    _module = 'yt_dlp.extractor.limelight'
    IE_NAME = 'limelight:channel'
    _VALID_URL = '(?x)\n                        (?:\n                            limelight:channel:|\n                            https?://\n                                (?:\n                                    link\\.videoplatform\\.limelight\\.com/media/|\n                                    assets\\.delvenetworks\\.com/player/loader\\.swf\n                                )\n                                \\?.*?\\bchannelId=\n                        )\n                        (?P<id>[a-z0-9]{32})\n                    '
    _RETURN_TYPE = 'playlist'


class LimelightChannelListIE(LimelightBaseIE):
    _module = 'yt_dlp.extractor.limelight'
    IE_NAME = 'limelight:channel_list'
    _VALID_URL = '(?x)\n                        (?:\n                            limelight:channel_list:|\n                            https?://\n                                (?:\n                                    link\\.videoplatform\\.limelight\\.com/media/|\n                                    assets\\.delvenetworks\\.com/player/loader\\.swf\n                                )\n                                \\?.*?\\bchannelListId=\n                        )\n                        (?P<id>[a-z0-9]{32})\n                    '
    _RETURN_TYPE = 'playlist'


class LinkedInBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.linkedin'
    IE_NAME = 'LinkedInBase'
    _NETRC_MACHINE = 'linkedin'


class LinkedInIE(LinkedInBaseIE):
    _module = 'yt_dlp.extractor.linkedin'
    IE_NAME = 'LinkedIn'
    _VALID_URL = 'https?://(?:www\\.)?linkedin\\.com/posts/.+?(?P<id>\\d+)'
    _NETRC_MACHINE = 'linkedin'
    _RETURN_TYPE = 'video'


class LinkedInLearningBaseIE(LinkedInBaseIE):
    _module = 'yt_dlp.extractor.linkedin'
    IE_NAME = 'LinkedInLearningBase'
    _NETRC_MACHINE = 'linkedin'


class LinkedInLearningIE(LinkedInLearningBaseIE):
    _module = 'yt_dlp.extractor.linkedin'
    IE_NAME = 'linkedin:learning'
    _VALID_URL = 'https?://(?:www\\.)?linkedin\\.com/learning/(?P<course_slug>[^/]+)/(?P<id>[^/?#]+)'
    _NETRC_MACHINE = 'linkedin'
    _RETURN_TYPE = 'video'


class LinkedInLearningCourseIE(LinkedInLearningBaseIE):
    _module = 'yt_dlp.extractor.linkedin'
    IE_NAME = 'linkedin:learning:course'
    _VALID_URL = 'https?://(?:www\\.)?linkedin\\.com/learning/(?P<id>[^/?#]+)'
    _NETRC_MACHINE = 'linkedin'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if LinkedInLearningIE.suitable(url) else super(LinkedInLearningCourseIE, cls).suitable(url)


class LinuxAcademyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.linuxacademy'
    IE_NAME = 'LinuxAcademy'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?linuxacademy\\.com/cp/\n                        (?:\n                            courses/lesson/course/(?P<chapter_id>\\d+)/lesson/(?P<lesson_id>\\d+)|\n                            modules/view/id/(?P<course_id>\\d+)\n                        )\n                    '
    _NETRC_MACHINE = 'linuxacademy'
    _RETURN_TYPE = 'any'


class Liputan6IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.liputan6'
    IE_NAME = 'Liputan6'
    _VALID_URL = 'https?://www\\.liputan6\\.com/\\w+/read/\\d+/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class ListenNotesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.listennotes'
    IE_NAME = 'ListenNotes'
    _VALID_URL = 'https?://(?:www\\.)?listennotes\\.com/podcasts/[^/]+/[^/]+-(?P<id>.+)/'
    _RETURN_TYPE = 'video'


class LiTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.litv'
    IE_NAME = 'LiTV'
    _VALID_URL = 'https?://(?:www\\.)?litv\\.tv/(?:vod|promo)/[^/]+/(?:content\\.do)?\\?.*?\\b(?:content_)?id=(?P<id>[^&]+)'
    _RETURN_TYPE = 'any'


class LiveJournalIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.livejournal'
    IE_NAME = 'LiveJournal'
    _VALID_URL = 'https?://(?:[^.]+\\.)?livejournal\\.com/video/album/\\d+.+?\\bid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class LivestreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.livestream'
    IE_NAME = 'livestream'
    _VALID_URL = '(?x)\n        https?://(?:new\\.)?livestream\\.com/\n        (?:accounts/(?P<account_id>\\d+)|(?P<account_name>[^/]+))\n        (?:/events/(?P<event_id>\\d+)|/(?P<event_name>[^/]+))?\n        (?:/videos/(?P<id>\\d+))?\n    '
    _RETURN_TYPE = 'any'


class LivestreamOriginalIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.livestream'
    IE_NAME = 'livestream:original'
    _VALID_URL = '(?x)https?://original\\.livestream\\.com/\n        (?P<user>[^/\\?#]+)(?:/(?P<type>video|folder)\n        (?:(?:\\?.*?Id=|/)(?P<id>.*?)(&|$))?)?\n        '
    _RETURN_TYPE = 'any'


class LivestreamShortenerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.livestream'
    IE_NAME = 'livestream:shortener'
    _VALID_URL = 'https?://livestre\\.am/(?P<id>.+)'
    IE_DESC = False


class LivestreamfailsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.livestreamfails'
    IE_NAME = 'Livestreamfails'
    _VALID_URL = 'https?://(?:www\\.)?livestreamfails\\.com/(?:clip|post)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class LnkGoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lnkgo'
    IE_NAME = 'LnkGo'
    _VALID_URL = 'https?://(?:www\\.)?lnk(?:go)?\\.(?:alfa\\.)?lt/(?:visi-video/[^/]+|video)/(?P<id>[A-Za-z0-9-]+)(?:/(?P<episode_id>\\d+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class LnkIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lnkgo'
    IE_NAME = 'Lnk'
    _VALID_URL = 'https?://(?:www\\.)?lnk\\.lt/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class LocalNews8IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.localnews8'
    IE_NAME = 'LocalNews8'
    _VALID_URL = 'https?://(?:www\\.)?localnews8\\.com/(?:[^/]+/)*(?P<display_id>[^/]+)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class NuevoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nuevo'
    IE_NAME = 'NuevoBase'


class LoveHomePornIE(NuevoBaseIE):
    _module = 'yt_dlp.extractor.lovehomeporn'
    IE_NAME = 'LoveHomePorn'
    _VALID_URL = 'https?://(?:www\\.)?lovehomeporn\\.com/video/(?P<id>\\d+)(?:/(?P<display_id>[^/?#&]+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class LRTBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lrt'
    IE_NAME = 'LRTBase'


class LRTVODIE(LRTBaseIE):
    _module = 'yt_dlp.extractor.lrt'
    IE_NAME = 'LRTVOD'
    _VALID_URL = 'https?://(?:www\\.)?lrt\\.lt(?P<path>/mediateka/irasas/(?P<id>[0-9]+))'
    _RETURN_TYPE = 'video'


class LRTStreamIE(LRTBaseIE):
    _module = 'yt_dlp.extractor.lrt'
    IE_NAME = 'LRTStream'
    _VALID_URL = 'https?://(?:www\\.)?lrt\\.lt/mediateka/tiesiogiai/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class LumniIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lumni'
    IE_NAME = 'Lumni'
    _VALID_URL = 'https?://(?:www\\.)?lumni\\.fr/video/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class LyndaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.lynda'
    IE_NAME = 'LyndaBase'
    _NETRC_MACHINE = 'lynda'


class LyndaIE(LyndaBaseIE):
    _module = 'yt_dlp.extractor.lynda'
    IE_NAME = 'lynda'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?(?:lynda\\.com|educourse\\.ga)/\n                        (?:\n                            (?:[^/]+/){2,3}(?P<course_id>\\d+)|\n                            player/embed\n                        )/\n                        (?P<id>\\d+)\n                    '
    IE_DESC = 'lynda.com videos'
    _NETRC_MACHINE = 'lynda'
    _RETURN_TYPE = 'video'


class LyndaCourseIE(LyndaBaseIE):
    _module = 'yt_dlp.extractor.lynda'
    IE_NAME = 'lynda:course'
    _VALID_URL = 'https?://(?:www|m)\\.(?:lynda\\.com|educourse\\.ga)/(?P<coursepath>(?:[^/]+/){2,3}(?P<courseid>\\d+))-2\\.html'
    IE_DESC = 'lynda.com online courses'
    _NETRC_MACHINE = 'lynda'


class M6IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.m6'
    IE_NAME = 'm6'
    _VALID_URL = 'https?://(?:www\\.)?m6\\.fr/[^/]+/videos/(?P<id>\\d+)-[^\\.]+\\.html'
    _RETURN_TYPE = 'video'


class MagentaMusik360IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.magentamusik360'
    IE_NAME = 'MagentaMusik360'
    _VALID_URL = 'https?://(?:www\\.)?magenta-musik-360\\.de/([a-z0-9-]+-(?P<id>[0-9]+)|festivals/.+)'
    _RETURN_TYPE = 'video'


class MailRuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mailru'
    IE_NAME = 'mailru'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:(?:www|m|videoapi)\\.)?my\\.mail\\.ru/+\n                        (?:\n                            video/.*\\#video=/?(?P<idv1>(?:[^/]+/){3}\\d+)|\n                            (?:videos/embed/)?(?:(?P<idv2prefix>(?:[^/]+/+){2})(?:video/(?:embed/)?)?(?P<idv2suffix>[^/]+/\\d+))(?:\\.html)?|\n                            (?:video/embed|\\+/video/meta)/(?P<metaid>\\d+)\n                        )\n                    '
    IE_DESC = 'Видео@Mail.Ru'
    _RETURN_TYPE = 'video'


class MailRuMusicSearchBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mailru'
    IE_NAME = 'MailRuMusicSearchBase'


class MailRuMusicIE(MailRuMusicSearchBaseIE):
    _module = 'yt_dlp.extractor.mailru'
    IE_NAME = 'mailru:music'
    _VALID_URL = 'https?://my\\.mail\\.ru/+music/+songs/+[^/?#&]+-(?P<id>[\\da-f]+)'
    IE_DESC = 'Музыка@Mail.Ru'
    _RETURN_TYPE = 'video'


class MailRuMusicSearchIE(MailRuMusicSearchBaseIE):
    _module = 'yt_dlp.extractor.mailru'
    IE_NAME = 'mailru:music:search'
    _VALID_URL = 'https?://my\\.mail\\.ru/+music/+search/+(?P<id>[^/?#&]+)'
    IE_DESC = 'Музыка@Mail.Ru'
    _RETURN_TYPE = 'playlist'


class MainStreamingIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mainstreaming'
    IE_NAME = 'MainStreaming'
    _VALID_URL = 'https?://(?:webtools-?)?(?P<host>[A-Za-z0-9-]*\\.msvdn.net)/(?:embed|amp_embed|content)/(?P<id>\\w+)'
    IE_DESC = 'MainStreaming Player'
    _RETURN_TYPE = 'any'


class MallTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.malltv'
    IE_NAME = 'MallTV'
    _VALID_URL = 'https?://(?:(?:www|sk)\\.)?mall\\.tv/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class MangomoloBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mangomolo'
    IE_NAME = 'MangomoloBase'
    _VALID_URL = '(?:https?:)?//(?:admin\\.mangomolo\\.com/analytics/index\\.php/customers/embed/|player\\.mangomolo\\.com/v1/)None'


class MangomoloVideoIE(MangomoloBaseIE):
    _module = 'yt_dlp.extractor.mangomolo'
    IE_NAME = 'mangomolo:video'
    _VALID_URL = '(?:https?:)?//(?:admin\\.mangomolo\\.com/analytics/index\\.php/customers/embed/|player\\.mangomolo\\.com/v1/)video\\?.*?\\bid=(?P<id>\\d+)'


class MangomoloLiveIE(MangomoloBaseIE):
    _module = 'yt_dlp.extractor.mangomolo'
    IE_NAME = 'mangomolo:live'
    _VALID_URL = '(?:https?:)?//(?:admin\\.mangomolo\\.com/analytics/index\\.php/customers/embed/|player\\.mangomolo\\.com/v1/)(?:live|index)\\?.*?\\bchannelid=(?P<id>(?:[A-Za-z0-9+/=]|%2B|%2F|%3D)+)'


class ManotoTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.manoto'
    IE_NAME = 'ManotoTV'
    _VALID_URL = 'https?://(?:www\\.)?manototv\\.com/episode/(?P<id>[0-9]+)'
    IE_DESC = 'Manoto TV (Episode)'
    _RETURN_TYPE = 'video'


class ManotoTVShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.manoto'
    IE_NAME = 'ManotoTVShow'
    _VALID_URL = 'https?://(?:www\\.)?manototv\\.com/show/(?P<id>[0-9]+)'
    IE_DESC = 'Manoto TV (Show)'
    _RETURN_TYPE = 'playlist'


class ManotoTVLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.manoto'
    IE_NAME = 'ManotoTVLive'
    _VALID_URL = 'https?://(?:www\\.)?manototv\\.com/live/'
    IE_DESC = 'Manoto TV (Live)'
    _RETURN_TYPE = 'video'


class ManyVidsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.manyvids'
    IE_NAME = 'ManyVids'
    _VALID_URL = '(?i)https?://(?:www\\.)?manyvids\\.com/video/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MaoriTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.maoritv'
    IE_NAME = 'MaoriTV'
    _VALID_URL = 'https?://(?:www\\.)?maoritelevision\\.com/shows/(?:[^/]+/)+(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class MarkizaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.markiza'
    IE_NAME = 'Markiza'
    _VALID_URL = 'https?://(?:www\\.)?videoarchiv\\.markiza\\.sk/(?:video/(?:[^/]+/)*|embed/)(?P<id>\\d+)(?:[_/]|$)'
    _RETURN_TYPE = 'any'


class MarkizaPageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.markiza'
    IE_NAME = 'MarkizaPage'
    _VALID_URL = 'https?://(?:www\\.)?(?:(?:[^/]+\\.)?markiza|tvnoviny)\\.sk/(?:[^/]+/)*(?P<id>\\d+)_'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if MarkizaIE.suitable(url) else super(MarkizaPageIE, cls).suitable(url)


class MassengeschmackTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.massengeschmacktv'
    IE_NAME = 'massengeschmack.tv'
    _VALID_URL = 'https?://(?:www\\.)?massengeschmack\\.tv/play/(?P<id>[^?&#]+)'
    _RETURN_TYPE = 'video'


class MastersIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.masters'
    IE_NAME = 'Masters'
    _VALID_URL = 'https?://(?:www\\.)?masters\\.com/en_US/watch/(?P<date>\\d{4}-\\d{2}-\\d{2})/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MatchTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.matchtv'
    IE_NAME = 'MatchTV'
    _VALID_URL = 'https?://matchtv\\.ru(?:/on-air|/?#live-player)'
    _RETURN_TYPE = 'video'


class MDRIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mdr'
    IE_NAME = 'MDR'
    _VALID_URL = 'https?://(?:www\\.)?(?:mdr|kika)\\.de/(?:.*)/[a-z-]+-?(?P<id>\\d+)(?:_.+?)?\\.html'
    IE_DESC = 'MDR.DE and KiKA'
    _RETURN_TYPE = 'video'


class MedalTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.medaltv'
    IE_NAME = 'MedalTV'
    _VALID_URL = 'https?://(?:www\\.)?medal\\.tv/games/[^/?#&]+/clips/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class MediaiteIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mediaite'
    IE_NAME = 'Mediaite'
    _VALID_URL = 'https?://(?:www\\.)?mediaite.com(?!/category)(?:/[\\w-]+){2}'
    _RETURN_TYPE = 'video'


class MediaKlikkIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mediaklikk'
    IE_NAME = 'MediaKlikk'
    _VALID_URL = '(?x)https?://(?:www\\.)?\n                        (?:mediaklikk|m4sport|hirado|petofilive)\\.hu/.*?(?:videok?|cikk)/\n                        (?:(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/)?\n                        (?P<id>[^/#?_]+)'
    _RETURN_TYPE = 'video'


class ThePlatformBaseIE(OnceIE):
    _module = 'yt_dlp.extractor.theplatform'
    IE_NAME = 'ThePlatformBase'
    _VALID_URL = 'https?://.+?\\.unicornmedia\\.com/now/(?:ads/vmap/)?[^/]+/[^/]+/(?P<domain_id>[^/]+)/(?P<application_id>[^/]+)/(?:[^/]+/)?(?P<media_item_id>[^/]+)/content\\.(?:once|m3u8|mp4)'


class MediasetIE(ThePlatformBaseIE):
    _module = 'yt_dlp.extractor.mediaset'
    IE_NAME = 'Mediaset'
    _VALID_URL = '(?x)\n                    (?:\n                        mediaset:|\n                        https?://\n                            (?:\\w+\\.)+mediaset\\.it/\n                            (?:\n                                (?:video|on-demand|movie)/(?:[^/]+/)+[^/]+_|\n                                player/(?:v\\d+/)?index\\.html\\?\\S*?\\bprogramGuid=\n                            )\n                    )(?P<id>F[0-9A-Z]{15})\n                    '
    _RETURN_TYPE = 'video'


class MediasetShowIE(MediasetIE):
    _module = 'yt_dlp.extractor.mediaset'
    IE_NAME = 'MediasetShow'
    _VALID_URL = '(?x)\n                    (?:\n                        https?://\n                            (\\w+\\.)+mediaset\\.it/\n                            (?:\n                                (?:fiction|programmi-tv|serie-tv|kids)/(?:.+?/)?\n                                    (?:[a-z-]+)_SE(?P<id>\\d{12})\n                                    (?:,ST(?P<st>\\d{12}))?\n                                    (?:,sb(?P<sb>\\d{9}))?$\n                            )\n                    )\n                    '
    _RETURN_TYPE = 'playlist'


class MediasiteIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mediasite'
    IE_NAME = 'Mediasite'
    _VALID_URL = '(?xi)https?://[^/]+/Mediasite/(?:Play|Showcase/[^/#?]+/Presentation)/(?P<id>(?:[0-9a-f]{32,34}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12,14}))(?P<query>\\?[^#]+|)'
    _RETURN_TYPE = 'video'


class MediasiteCatalogIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mediasite'
    IE_NAME = 'MediasiteCatalog'
    _VALID_URL = '(?xi)\n                        (?P<url>https?://[^/]+/Mediasite)\n                        /Catalog/Full/\n                        (?P<catalog_id>(?:[0-9a-f]{32,34}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12,14}))\n                        (?:\n                            /(?P<current_folder_id>(?:[0-9a-f]{32,34}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12,14}))\n                            /(?P<root_dynamic_folder_id>(?:[0-9a-f]{32,34}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12,14}))\n                        )?\n                    '
    _RETURN_TYPE = 'playlist'


class MediasiteNamedCatalogIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mediasite'
    IE_NAME = 'MediasiteNamedCatalog'
    _VALID_URL = '(?xi)(?P<url>https?://[^/]+/Mediasite)/Catalog/catalogs/(?P<catalog_name>[^/?#&]+)'


class MediaStreamBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mediastream'
    IE_NAME = 'MediaStreamBase'


class MediaStreamIE(MediaStreamBaseIE):
    _module = 'yt_dlp.extractor.mediastream'
    IE_NAME = 'MediaStream'
    _VALID_URL = 'https?://mdstrm\\.com/(?:embed|live-stream)/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class WinSportsVideoIE(MediaStreamBaseIE):
    _module = 'yt_dlp.extractor.mediastream'
    IE_NAME = 'WinSportsVideo'
    _VALID_URL = 'https?://www\\.winsports\\.co/videos/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class MediaWorksNZVODIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mediaworksnz'
    IE_NAME = 'MediaWorksNZVOD'
    _VALID_URL = 'https?://vodupload-api\\.mediaworks\\.nz/library/asset/published/(?P<id>[A-Za-z0-9-]+)'
    _RETURN_TYPE = 'video'


class MediciIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.medici'
    IE_NAME = 'Medici'
    _VALID_URL = 'https?://(?:www\\.)?medici\\.tv/#!/(?P<id>[^?#&]+)'
    _RETURN_TYPE = 'video'


class MegaphoneIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.megaphone'
    IE_NAME = 'megaphone.fm'
    _VALID_URL = 'https://player\\.megaphone\\.fm/(?P<id>[A-Z0-9]+)'
    IE_DESC = 'megaphone.fm embedded players'
    _RETURN_TYPE = 'video'


class MeipaiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.meipai'
    IE_NAME = 'Meipai'
    _VALID_URL = 'https?://(?:www\\.)?meipai\\.com/media/(?P<id>[0-9]+)'
    IE_DESC = '美拍'
    _RETURN_TYPE = 'video'


class MelonVODIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.melonvod'
    IE_NAME = 'MelonVOD'
    _VALID_URL = 'https?://vod\\.melon\\.com/video/detail2\\.html?\\?.*?mvId=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class METAIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.meta'
    IE_NAME = 'META'
    _VALID_URL = 'https?://video\\.meta\\.ua/(?:iframe/)?(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MetacafeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.metacafe'
    IE_NAME = 'metacafe'
    _VALID_URL = 'https?://(?:www\\.)?metacafe\\.com/watch/(?P<id>[^/]+)/(?P<display_id>[^/?#]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class MetacriticIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.metacritic'
    IE_NAME = 'Metacritic'
    _VALID_URL = 'https?://(?:www\\.)?metacritic\\.com/.+?/trailers/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MgoonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mgoon'
    IE_NAME = 'Mgoon'
    _VALID_URL = '(?x)https?://(?:www\\.)?\n    (?:(:?m\\.)?mgoon\\.com/(?:ch/(?:.+)/v|play/view)|\n        video\\.mgoon\\.com)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MGTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mgtv'
    IE_NAME = 'MangoTV'
    _VALID_URL = 'https?://(?:w(?:ww)?\\.)?mgtv\\.com/(v|b)/(?:[^/]+/)*(?P<id>\\d+)\\.html'
    IE_DESC = '芒果TV'
    _RETURN_TYPE = 'video'


class MiaoPaiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.miaopai'
    IE_NAME = 'MiaoPai'
    _VALID_URL = 'https?://(?:www\\.)?miaopai\\.com/show/(?P<id>[-A-Za-z0-9~_]+)'
    _RETURN_TYPE = 'video'


class MicrosoftStreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.microsoftstream'
    IE_NAME = 'microsoftstream'
    _VALID_URL = 'https?://(?:web|www|msit)\\.microsoftstream\\.com/video/(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'
    IE_DESC = 'Microsoft Stream'


class MicrosoftVirtualAcademyBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.microsoftvirtualacademy'
    IE_NAME = 'MicrosoftVirtualAcademyBase'


class MicrosoftVirtualAcademyIE(MicrosoftVirtualAcademyBaseIE):
    _module = 'yt_dlp.extractor.microsoftvirtualacademy'
    IE_NAME = 'mva'
    _VALID_URL = '(?:mva:|https?://(?:mva\\.microsoft|(?:www\\.)?microsoftvirtualacademy)\\.com/[^/]+/training-courses/[^/?#&]+-)(?P<course_id>\\d+)(?::|\\?l=)(?P<id>[\\da-zA-Z]+_\\d+)'
    IE_DESC = 'Microsoft Virtual Academy videos'
    _RETURN_TYPE = 'video'


class MicrosoftVirtualAcademyCourseIE(MicrosoftVirtualAcademyBaseIE):
    _module = 'yt_dlp.extractor.microsoftvirtualacademy'
    IE_NAME = 'mva:course'
    _VALID_URL = '(?:mva:course:|https?://(?:mva\\.microsoft|(?:www\\.)?microsoftvirtualacademy)\\.com/[^/]+/training-courses/(?P<display_id>[^/?#&]+)-)(?P<id>\\d+)'
    IE_DESC = 'Microsoft Virtual Academy courses'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if MicrosoftVirtualAcademyIE.suitable(url) else super(
            MicrosoftVirtualAcademyCourseIE, cls).suitable(url)


class MicrosoftEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.microsoftembed'
    IE_NAME = 'MicrosoftEmbed'
    _VALID_URL = 'https?://(?:www\\.)?microsoft\\.com/(?:[^/]+/)?videoplayer/embed/(?P<id>[a-z0-9A-Z]+)'
    _RETURN_TYPE = 'video'


class MildomBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mildom'
    IE_NAME = 'MildomBase'


class MildomIE(MildomBaseIE):
    _module = 'yt_dlp.extractor.mildom'
    IE_NAME = 'mildom'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)mildom\\.com/(?P<id>\\d+)'
    IE_DESC = 'Record ongoing live by specific user in Mildom'


class MildomVodIE(MildomBaseIE):
    _module = 'yt_dlp.extractor.mildom'
    IE_NAME = 'mildom:vod'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)mildom\\.com/playback/(?P<user_id>\\d+)/(?P<id>(?P=user_id)-[a-zA-Z0-9]+-?[0-9]*)'
    IE_DESC = 'VOD in Mildom'
    _RETURN_TYPE = 'video'


class MildomClipIE(MildomBaseIE):
    _module = 'yt_dlp.extractor.mildom'
    IE_NAME = 'mildom:clip'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)mildom\\.com/clip/(?P<id>(?P<user_id>\\d+)-[a-zA-Z0-9]+)'
    IE_DESC = 'Clip in Mildom'
    _RETURN_TYPE = 'video'


class MildomUserVodIE(MildomBaseIE):
    _module = 'yt_dlp.extractor.mildom'
    IE_NAME = 'mildom:user:vod'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)mildom\\.com/profile/(?P<id>\\d+)'
    IE_DESC = 'Download all VODs from specific user in Mildom'
    _RETURN_TYPE = 'playlist'


class MindsBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.minds'
    IE_NAME = 'MindsBase'


class MindsIE(MindsBaseIE):
    _module = 'yt_dlp.extractor.minds'
    IE_NAME = 'minds'
    _VALID_URL = 'https?://(?:www\\.)?minds\\.com/(?:media|newsfeed|archive/view)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MindsFeedBaseIE(MindsBaseIE):
    _module = 'yt_dlp.extractor.minds'
    IE_NAME = 'MindsFeedBase'


class MindsChannelIE(MindsFeedBaseIE):
    _module = 'yt_dlp.extractor.minds'
    IE_NAME = 'minds:channel'
    _VALID_URL = 'https?://(?:www\\.)?minds\\.com/(?!(?:newsfeed|media|api|archive|groups)/)(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'playlist'


class MindsGroupIE(MindsFeedBaseIE):
    _module = 'yt_dlp.extractor.minds'
    IE_NAME = 'minds:group'
    _VALID_URL = 'https?://(?:www\\.)?minds\\.com/groups/profile/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'playlist'


class MinistryGridIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ministrygrid'
    IE_NAME = 'MinistryGrid'
    _VALID_URL = 'https?://(?:www\\.)?ministrygrid\\.com/([^/?#]*/)*(?P<id>[^/#?]+)/?(?:$|[?#])'
    _RETURN_TYPE = 'video'


class MinotoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.minoto'
    IE_NAME = 'Minoto'
    _VALID_URL = '(?:minoto:|https?://(?:play|iframe|embed)\\.minoto-video\\.com/(?P<player_id>[0-9]+)/)(?P<id>[a-zA-Z0-9]+)'


class MioMioIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.miomio'
    IE_NAME = 'miomio.tv'
    _VALID_URL = 'https?://(?:www\\.)?miomio\\.tv/watch/cc(?P<id>[0-9]+)'
    _RETURN_TYPE = 'any'


class MirrativBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mirrativ'
    IE_NAME = 'MirrativBase'


class MirrativIE(MirrativBaseIE):
    _module = 'yt_dlp.extractor.mirrativ'
    IE_NAME = 'mirrativ'
    _VALID_URL = 'https?://(?:www\\.)?mirrativ\\.com/live/(?P<id>[^/?#&]+)'


class MirrativUserIE(MirrativBaseIE):
    _module = 'yt_dlp.extractor.mirrativ'
    IE_NAME = 'mirrativ:user'
    _VALID_URL = 'https?://(?:www\\.)?mirrativ\\.com/user/(?P<id>\\d+)'


class MirrorCoUKIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mirrorcouk'
    IE_NAME = 'MirrorCoUK'
    _VALID_URL = 'https?://(?:www\\.)?mirror\\.co\\.uk/[/+[\\w-]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TechTVMITIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mit'
    IE_NAME = 'techtv.mit.edu'
    _VALID_URL = 'https?://techtv\\.mit\\.edu/(?:videos|embeds)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class OCWMITIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mit'
    IE_NAME = 'ocw.mit.edu'
    _VALID_URL = '^https?://ocw\\.mit\\.edu/courses/(?P<topic>[a-z0-9\\-]+)'
    _RETURN_TYPE = 'video'


class MixchIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mixch'
    IE_NAME = 'mixch'
    _VALID_URL = 'https?://(?:www\\.)?mixch\\.tv/u/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MixchArchiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mixch'
    IE_NAME = 'mixch:archive'
    _VALID_URL = 'https?://(?:www\\.)?mixch\\.tv/archive/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MixcloudBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mixcloud'
    IE_NAME = 'MixcloudBase'


class MixcloudIE(MixcloudBaseIE):
    _module = 'yt_dlp.extractor.mixcloud'
    IE_NAME = 'mixcloud'
    _VALID_URL = 'https?://(?:(?:www|beta|m)\\.)?mixcloud\\.com/([^/]+)/(?!stream|uploads|favorites|listens|playlists)([^/]+)'
    _RETURN_TYPE = 'video'


class MixcloudPlaylistBaseIE(MixcloudBaseIE):
    _module = 'yt_dlp.extractor.mixcloud'
    IE_NAME = 'MixcloudPlaylistBase'


class MixcloudUserIE(MixcloudPlaylistBaseIE):
    _module = 'yt_dlp.extractor.mixcloud'
    IE_NAME = 'mixcloud:user'
    _VALID_URL = 'https?://(?:www\\.)?mixcloud\\.com/(?P<id>[^/]+)/(?P<type>uploads|favorites|listens|stream)?/?$'
    _RETURN_TYPE = 'playlist'


class MixcloudPlaylistIE(MixcloudPlaylistBaseIE):
    _module = 'yt_dlp.extractor.mixcloud'
    IE_NAME = 'mixcloud:playlist'
    _VALID_URL = 'https?://(?:www\\.)?mixcloud\\.com/(?P<user>[^/]+)/playlists/(?P<playlist>[^/]+)/?$'
    _RETURN_TYPE = 'playlist'


class MLBBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mlb'
    IE_NAME = 'MLBBase'


class MLBIE(MLBBaseIE):
    _module = 'yt_dlp.extractor.mlb'
    IE_NAME = 'MLB'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:[\\da-z_-]+\\.)*mlb\\.com/\n                        (?:\n                            (?:\n                                (?:[^/]+/)*video/[^/]+/c-|\n                                (?:\n                                    shared/video/embed/(?:embed|m-internal-embed)\\.html|\n                                    (?:[^/]+/)+(?:play|index)\\.jsp|\n                                )\\?.*?\\bcontent_id=\n                            )\n                            (?P<id>\\d+)\n                        )\n                    '
    _RETURN_TYPE = 'video'


class MLBVideoIE(MLBBaseIE):
    _module = 'yt_dlp.extractor.mlb'
    IE_NAME = 'MLBVideo'
    _VALID_URL = 'https?://(?:www\\.)?mlb\\.com/(?:[^/]+/)*video/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if MLBIE.suitable(url) else super(MLBVideoIE, cls).suitable(url)


class MLBTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mlb'
    IE_NAME = 'MLBTV'
    _VALID_URL = 'https?://(?:www\\.)?mlb\\.com/tv/g(?P<id>\\d{6})'
    _NETRC_MACHINE = 'mlb'
    _RETURN_TYPE = 'video'


class MLBArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mlb'
    IE_NAME = 'MLBArticle'
    _VALID_URL = 'https?://www\\.mlb\\.com/news/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class MLSSoccerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mlssoccer'
    IE_NAME = 'MLSSoccer'
    _VALID_URL = 'https?://(?:www\\.)?(?:(?:cfmontreal|intermiamicf|lagalaxy|lafc|houstondynamofc|dcunited|atlutd|mlssoccer|fcdallas|columbuscrew|coloradorapids|fccincinnati|chicagofirefc|austinfc|nashvillesc|whitecapsfc|sportingkc|soundersfc|sjearthquakes|rsl|timbers|philadelphiaunion|orlandocitysc|newyorkredbulls|nycfc)\\.com|(?:torontofc)\\.ca|(?:revolutionsoccer)\\.net)/video/#?(?P<id>[^/&$#?]+)'
    _RETURN_TYPE = 'video'


class MnetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mnet'
    IE_NAME = 'Mnet'
    _VALID_URL = 'https?://(?:www\\.)?mnet\\.(?:com|interest\\.me)/tv/vod/(?:.*?\\bclip_id=)?(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MochaVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mocha'
    IE_NAME = 'MochaVideo'
    _VALID_URL = 'https?://video.mocha.com.vn/(?P<video_slug>[\\w-]+)'
    _RETURN_TYPE = 'video'


class MoeVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.moevideo'
    IE_NAME = 'MoeVideo'
    _VALID_URL = '(?x)\n        https?://(?P<host>(?:www\\.)?\n        (?:(?:moevideo|playreplay|videochart)\\.net|thesame\\.tv))/\n        (?:video|framevideo|embed)/(?P<id>[0-9a-z]+\\.[0-9A-Za-z]+)'
    IE_DESC = 'LetitBit video services: moevideo.net, playreplay.net and videochart.net'
    _RETURN_TYPE = 'video'


class MofosexIE(KeezMoviesIE):
    _module = 'yt_dlp.extractor.mofosex'
    IE_NAME = 'Mofosex'
    _VALID_URL = 'https?://(?:www\\.)?mofosex\\.com/videos/(?P<id>\\d+)/(?P<display_id>[^/?#&.]+)\\.html'
    age_limit = 18
    _RETURN_TYPE = 'video'


class MofosexEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mofosex'
    IE_NAME = 'MofosexEmbed'
    _VALID_URL = 'https?://(?:www\\.)?mofosex\\.com/embed/?\\?.*?\\bvideoid=(?P<id>\\d+)'


class MojvideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mojvideo'
    IE_NAME = 'Mojvideo'
    _VALID_URL = 'https?://(?:www\\.)?mojvideo\\.com/video-(?P<display_id>[^/]+)/(?P<id>[a-f0-9]+)'
    _RETURN_TYPE = 'video'


class MorningstarIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.morningstar'
    IE_NAME = 'Morningstar'
    _VALID_URL = 'https?://(?:(?:www|news)\\.)morningstar\\.com/[cC]over/video[cC]enter\\.aspx\\?id=(?P<id>[0-9]+)'
    IE_DESC = 'morningstar.com'
    _RETURN_TYPE = 'video'


class MotherlessIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.motherless'
    IE_NAME = 'Motherless'
    _VALID_URL = 'https?://(?:www\\.)?motherless\\.com/(?:g/[a-z0-9_]+/|G[VIG]?[A-F0-9]+/)?(?P<id>[A-F0-9]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class MotherlessPaginatedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.motherless'
    IE_NAME = 'MotherlessPaginated'


class MotherlessGroupIE(MotherlessPaginatedIE):
    _module = 'yt_dlp.extractor.motherless'
    IE_NAME = 'MotherlessGroup'
    _VALID_URL = 'https?://(?:www\\.)?motherless\\.com/g[vifm]?/(?P<id>[a-z0-9_]+)/?(?:$|[#?])'
    _RETURN_TYPE = 'playlist'


class MotherlessGalleryIE(MotherlessPaginatedIE):
    _module = 'yt_dlp.extractor.motherless'
    IE_NAME = 'MotherlessGallery'
    _VALID_URL = 'https?://(?:www\\.)?motherless\\.com/G[VIG]?(?P<id>[A-F0-9]+)/?(?:$|[#?])'
    _RETURN_TYPE = 'playlist'


class MotorsportIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.motorsport'
    IE_NAME = 'Motorsport'
    _VALID_URL = 'https?://(?:www\\.)?motorsport\\.com/[^/?#]+/video/(?:[^/?#]+/)(?P<id>[^/]+)/?(?:$|[?#])'
    IE_DESC = 'motorsport.com'
    _RETURN_TYPE = 'video'


class MovieClipsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.movieclips'
    IE_NAME = 'MovieClips'
    _VALID_URL = 'https?://(?:www\\.)?movieclips\\.com/videos/.+-(?P<id>\\d+)(?:\\?|$)'
    _RETURN_TYPE = 'video'


class MoviepilotIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.moviepilot'
    IE_NAME = 'Moviepilot'
    _VALID_URL = 'https?://(?:www\\.)?moviepilot\\.de/movies/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class MoviewPlayIE(JixieBaseIE):
    _module = 'yt_dlp.extractor.moview'
    IE_NAME = 'MoviewPlay'
    _VALID_URL = 'https?://www\\.moview\\.id/play/\\d+/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class MoviezineIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.moviezine'
    IE_NAME = 'Moviezine'
    _VALID_URL = 'https?://(?:www\\.)?moviezine\\.se/video/(?P<id>[^?#]+)'
    _RETURN_TYPE = 'video'


class MovingImageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.movingimage'
    IE_NAME = 'MovingImage'
    _VALID_URL = 'https?://movingimage\\.nls\\.uk/film/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MSNIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.msn'
    IE_NAME = 'MSN'
    _VALID_URL = 'https?://(?:(?:www|preview)\\.)?msn\\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/[a-z]{2}-(?P<id>[\\da-zA-Z]+)'
    _RETURN_TYPE = 'any'


class MTVIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'mtv'
    _VALID_URL = 'https?://(?:www\\.)?mtv\\.com/(?:video-clips|(?:full-)?episodes)/(?P<id>[^/?#.]+)'
    _RETURN_TYPE = 'video'


class CMTIE(MTVIE):
    _module = 'yt_dlp.extractor.cmt'
    IE_NAME = 'cmt.com'
    _VALID_URL = 'https?://(?:www\\.)?cmt\\.com/(?:videos|shows|(?:full-)?episodes|video-clips)/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class MTVVideoIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'mtv:video'
    _VALID_URL = '(?x)^https?://\n        (?:(?:www\\.)?mtv\\.com/videos/.+?/(?P<videoid>[0-9]+)/[^/]+$|\n           m\\.mtv\\.com/videos/video\\.rbml\\?.*?id=(?P<mgid>[^&]+))'
    _RETURN_TYPE = 'video'


class MTVServicesEmbeddedIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'mtvservices:embedded'
    _VALID_URL = 'https?://media\\.mtvnservices\\.com/embed/(?P<mgid>.+?)(\\?|/|$)'
    _RETURN_TYPE = 'video'


class MTVDEIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'mtv.de'
    _VALID_URL = 'https?://(?:www\\.)?mtv\\.de/(?:musik/videoclips|folgen|news)/(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class MTVJapanIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'mtvjapan'
    _VALID_URL = 'https?://(?:www\\.)?mtvjapan\\.com/videos/(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class MTVItaliaIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'mtv.it'
    _VALID_URL = 'https?://(?:www\\.)?mtv\\.it/(?:episodi|video|musica)/(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class MTVItaliaProgrammaIE(MTVItaliaIE):
    _module = 'yt_dlp.extractor.mtv'
    IE_NAME = 'mtv.it:programma'
    _VALID_URL = 'https?://(?:www\\.)?mtv\\.it/(?:programmi|playlist)/(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'playlist'


class MuenchenTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.muenchentv'
    IE_NAME = 'MuenchenTV'
    _VALID_URL = 'https?://(?:www\\.)?muenchen\\.tv/livestream'
    IE_DESC = 'münchen.tv'
    _RETURN_TYPE = 'video'


class MurrtubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.murrtube'
    IE_NAME = 'Murrtube'
    _VALID_URL = '(?x)\n                        (?:\n                            murrtube:|\n                            https?://murrtube\\.net/videos/(?P<slug>[a-z0-9\\-]+)\\-\n                        )\n                        (?P<id>[a-f0-9]{8}\\-[a-f0-9]{4}\\-[a-f0-9]{4}\\-[a-f0-9]{4}\\-[a-f0-9]{12})\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class MurrtubeUserIE(MurrtubeIE):
    _module = 'yt_dlp.extractor.murrtube'
    IE_NAME = 'MurrtubeUser'
    _VALID_URL = 'https?://murrtube\\.net/(?P<id>[^/]+)$'
    IE_DESC = 'Murrtube user profile'
    _RETURN_TYPE = 'playlist'


class MuseScoreIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.musescore'
    IE_NAME = 'MuseScore'
    _VALID_URL = 'https?://(?:www\\.)?musescore\\.com/(?:user/\\d+|[^/]+)(?:/scores)?/(?P<id>[^#&?]+)'
    _RETURN_TYPE = 'video'


class MusicdexBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.musicdex'
    IE_NAME = 'MusicdexBase'


class MusicdexSongIE(MusicdexBaseIE):
    _module = 'yt_dlp.extractor.musicdex'
    IE_NAME = 'MusicdexSong'
    _VALID_URL = 'https?://(?:www\\.)?musicdex\\.org/track/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MusicdexAlbumIE(MusicdexBaseIE):
    _module = 'yt_dlp.extractor.musicdex'
    IE_NAME = 'MusicdexAlbum'
    _VALID_URL = 'https?://(?:www\\.)?musicdex\\.org/album/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class MusicdexPageIE(MusicdexBaseIE):
    _module = 'yt_dlp.extractor.musicdex'
    IE_NAME = 'MusicdexPage'


class MusicdexArtistIE(MusicdexPageIE):
    _module = 'yt_dlp.extractor.musicdex'
    IE_NAME = 'MusicdexArtist'
    _VALID_URL = 'https?://(?:www\\.)?musicdex\\.org/artist/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class MusicdexPlaylistIE(MusicdexPageIE):
    _module = 'yt_dlp.extractor.musicdex'
    IE_NAME = 'MusicdexPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?musicdex\\.org/playlist/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class MwaveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mwave'
    IE_NAME = 'Mwave'
    _VALID_URL = 'https?://mwave\\.interest\\.me/(?:[^/]+/)?mnettv/videodetail\\.m\\?searchVideoDetailVO\\.clip_id=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MwaveMeetGreetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mwave'
    IE_NAME = 'MwaveMeetGreet'
    _VALID_URL = 'https?://mwave\\.interest\\.me/(?:[^/]+/)?meetgreet/view/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MxplayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mxplayer'
    IE_NAME = 'Mxplayer'
    _VALID_URL = 'https?://(?:www\\.)?mxplayer\\.in/(?P<type>movie|show/[-\\w]+/[-\\w]+)/(?P<display_id>[-\\w]+)-(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class MxplayerShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mxplayer'
    IE_NAME = 'MxplayerShow'
    _VALID_URL = 'https?://(?:www\\.)?mxplayer\\.in/show/(?P<display_id>[-\\w]+)-(?P<id>\\w+)/?(?:$|[#?])'
    _RETURN_TYPE = 'playlist'


class MyChannelsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mychannels'
    IE_NAME = 'MyChannels'
    _VALID_URL = 'https?://(?:www\\.)?mychannels\\.com/.*(?P<id_type>video|production)_id=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MySpaceIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.myspace'
    IE_NAME = 'MySpace'
    _VALID_URL = '(?x)\n                    https?://\n                        myspace\\.com/[^/]+/\n                        (?P<mediatype>\n                            video/[^/]+/(?P<video_id>\\d+)|\n                            music/song/[^/?#&]+-(?P<song_id>\\d+)-\\d+(?:[/?#&]|$)\n                        )\n                    '
    _RETURN_TYPE = 'video'


class MySpaceAlbumIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.myspace'
    IE_NAME = 'MySpace:album'
    _VALID_URL = 'https?://myspace\\.com/([^/]+)/music/album/(?P<title>.*-)(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class MySpassIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.myspass'
    IE_NAME = 'MySpass'
    _VALID_URL = 'https?://(?:www\\.)?myspass\\.de/(?:[^/]+/)*(?P<id>\\d+)/?[^/]*$'
    _RETURN_TYPE = 'video'


class SprutoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vimple'
    IE_NAME = 'SprutoBase'


class MyviIE(SprutoBaseIE):
    _module = 'yt_dlp.extractor.myvi'
    IE_NAME = 'Myvi'
    _VALID_URL = '(?x)\n                        (?:\n                            https?://\n                                (?:www\\.)?\n                                myvi\\.\n                                (?:\n                                    (?:ru/player|tv)/\n                                    (?:\n                                        (?:\n                                            embed/html|\n                                            flash|\n                                            api/Video/Get\n                                        )/|\n                                        content/preloader\\.swf\\?.*\\bid=\n                                    )|\n                                    ru/watch/\n                                )|\n                            myvi:\n                        )\n                        (?P<id>[\\da-zA-Z_-]+)\n                    '
    _RETURN_TYPE = 'video'


class MyviEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.myvi'
    IE_NAME = 'MyviEmbed'
    _VALID_URL = 'https?://(?:www\\.)?myvi\\.tv/(?:[^?]+\\?.*?\\bv=|embed/)(?P<id>[\\da-z]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if MyviIE.suitable(url) else super(MyviEmbedIE, cls).suitable(url)


class MyVideoGeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.myvideoge'
    IE_NAME = 'MyVideoGe'
    _VALID_URL = 'https?://(?:www\\.)?myvideo\\.ge/v/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MyVidsterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.myvidster'
    IE_NAME = 'MyVidster'
    _VALID_URL = 'https?://(?:www\\.)?myvidster\\.com/video/(?P<id>\\d+)/'
    age_limit = 18
    _RETURN_TYPE = 'video'


class MzaaloIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.mzaalo'
    IE_NAME = 'Mzaalo'
    _VALID_URL = 'https?://(?:www\\.)?mzaalo\\.com/play/(?P<type>movie|original|clip)/(?P<id>[a-fA-F0-9-]+)/[\\w-]+'
    age_limit = 13
    _RETURN_TYPE = 'video'


class N1InfoAssetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.n1'
    IE_NAME = 'N1InfoAsset'
    _VALID_URL = 'https?://best-vod\\.umn\\.cdn\\.united\\.cloud/stream\\?asset=(?P<id>[^&]+)'
    _RETURN_TYPE = 'video'


class N1InfoIIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.n1'
    IE_NAME = 'N1Info:article'
    _VALID_URL = 'https?://(?:(?:(?:ba|rs|hr)\\.)?n1info\\.(?:com|si)|nova\\.rs)/(?:[^/]+/){1,2}(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class NateIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nate'
    IE_NAME = 'Nate'
    _VALID_URL = 'https?://tv\\.nate\\.com/clip/(?P<id>[0-9]+)'
    age_limit = 15
    _RETURN_TYPE = 'video'


class NateProgramIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nate'
    IE_NAME = 'NateProgram'
    _VALID_URL = 'https?://tv\\.nate\\.com/program/clips/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'playlist'


class NationalGeographicVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nationalgeographic'
    IE_NAME = 'natgeo:video'
    _VALID_URL = 'https?://video\\.nationalgeographic\\.com/.*?'
    _RETURN_TYPE = 'video'


class NationalGeographicTVIE(FOXIE):
    _module = 'yt_dlp.extractor.nationalgeographic'
    IE_NAME = 'NationalGeographicTV'
    _VALID_URL = 'https?://(?:www\\.)?nationalgeographic\\.com/tv/watch/(?P<id>[\\da-fA-F]+)'
    age_limit = 14
    _RETURN_TYPE = 'video'


class NaverBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.naver'
    IE_NAME = 'NaverBase'


class NaverIE(NaverBaseIE):
    _module = 'yt_dlp.extractor.naver'
    IE_NAME = 'Naver'
    _VALID_URL = 'https?://(?:m\\.)?tv(?:cast)?\\.naver\\.com/(?:v|embed)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NaverLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.naver'
    IE_NAME = 'Naver:live'
    _VALID_URL = 'https?://(?:m\\.)?tv(?:cast)?\\.naver\\.com/l/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NaverNowIE(NaverBaseIE):
    _module = 'yt_dlp.extractor.naver'
    IE_NAME = 'navernow'
    _VALID_URL = 'https?://now\\.naver\\.com/s/now\\.(?P<id>\\w+)'
    _RETURN_TYPE = 'any'


class NBACVPBaseIE(TurnerBaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'NBACVPBase'


class NBAWatchBaseIE(NBACVPBaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'NBAWatchBase'


class NBAWatchEmbedIE(NBAWatchBaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'NBAWatchEmbed'
    _VALID_URL = 'https?://(?:(?:www\\.)?nba\\.com(?:/watch)?|watch\\.nba\\.com)/embed\\?.*?\\bid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NBAWatchIE(NBAWatchBaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'nba:watch'
    _VALID_URL = 'https?://(?:(?:www\\.)?nba\\.com(?:/watch)?|watch\\.nba\\.com)/(?:nba/)?video/(?P<id>.+?(?=/index\\.html)|(?:[^/]+/)*[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NBAWatchCollectionIE(NBAWatchBaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'nba:watch:collection'
    _VALID_URL = 'https?://(?:(?:www\\.)?nba\\.com(?:/watch)?|watch\\.nba\\.com)/list/collection/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class NBABaseIE(NBACVPBaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'NBABase'


class NBAEmbedIE(NBABaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'NBAEmbed'
    _VALID_URL = 'https?://secure\\.nba\\.com/assets/amp/include/video/(?:topI|i)frame\\.html\\?.*?\\bcontentId=(?P<id>[^?#&]+)'


class NBAIE(NBABaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'NBA'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?nba\\.com/\n            (?P<team>\n                blazers|\n                bucks|\n                bulls|\n                cavaliers|\n                celtics|\n                clippers|\n                grizzlies|\n                hawks|\n                heat|\n                hornets|\n                jazz|\n                kings|\n                knicks|\n                lakers|\n                magic|\n                mavericks|\n                nets|\n                nuggets|\n                pacers|\n                pelicans|\n                pistons|\n                raptors|\n                rockets|\n                sixers|\n                spurs|\n                suns|\n                thunder|\n                timberwolves|\n                warriors|\n                wizards\n            )\n        (?:/play\\#)?/(?!video/channel|series)video/(?P<id>(?:[^/]+/)*[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NBAChannelIE(NBABaseIE):
    _module = 'yt_dlp.extractor.nba'
    IE_NAME = 'NBAChannel'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?nba\\.com/\n            (?P<team>\n                blazers|\n                bucks|\n                bulls|\n                cavaliers|\n                celtics|\n                clippers|\n                grizzlies|\n                hawks|\n                heat|\n                hornets|\n                jazz|\n                kings|\n                knicks|\n                lakers|\n                magic|\n                mavericks|\n                nets|\n                nuggets|\n                pacers|\n                pelicans|\n                pistons|\n                raptors|\n                rockets|\n                sixers|\n                spurs|\n                suns|\n                thunder|\n                timberwolves|\n                warriors|\n                wizards\n            )\n        (?:/play\\#)?/(?:video/channel|series)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class NBCOlympicsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'nbcolympics'
    _VALID_URL = 'https?://www\\.nbcolympics\\.com/videos?/(?P<id>[0-9a-z-]+)'
    _RETURN_TYPE = 'video'


class NBCOlympicsStreamIE(AdobePassIE):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'nbcolympics:stream'
    _VALID_URL = 'https?://stream\\.nbcolympics\\.com/(?P<id>[0-9a-z-]+)'
    _RETURN_TYPE = 'video'


class NBCSportsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'NBCSports'
    _VALID_URL = 'https?://(?:www\\.)?nbcsports\\.com//?(?!vplayer/)(?:[^/]+/)+(?P<id>[0-9a-z-]+)'
    _RETURN_TYPE = 'video'


class NBCSportsStreamIE(AdobePassIE):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'NBCSportsStream'
    _VALID_URL = 'https?://stream\\.nbcsports\\.com/.+?\\bpid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NBCSportsVPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'NBCSportsVPlayer'
    _VALID_URL = 'https?://(?:vplayer\\.nbcsports\\.com|(?:www\\.)?nbcsports\\.com/vplayer)/(?:[^/]+/)+(?P<id>[0-9a-zA-Z_]+)'
    _RETURN_TYPE = 'video'


class NBCStationsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'NBCStations'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>nbcbayarea|nbcboston|nbcchicago|nbcconnecticut|nbcdfw|nbclosangeles|nbcmiami|nbcnewyork|nbcphiladelphia|nbcsandiego|nbcwashington|necn|telemundo52|telemundoarizona|telemundochicago|telemundonuevainglaterra)\\.com/(?:[^/?#]+/)*(?P<id>[^/?#]+)/?(?:$|[#?])'
    _RETURN_TYPE = 'video'


class NDRBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ndr'
    IE_NAME = 'NDRBase'


class NDRIE(NDRBaseIE):
    _module = 'yt_dlp.extractor.ndr'
    IE_NAME = 'ndr'
    _VALID_URL = 'https?://(?:\\w+\\.)*ndr\\.de/(?:[^/]+/)*(?P<id>[^/?#]+),[\\da-z]+\\.html'
    IE_DESC = 'NDR.de - Norddeutscher Rundfunk'
    _RETURN_TYPE = 'video'


class NJoyIE(NDRBaseIE):
    _module = 'yt_dlp.extractor.ndr'
    IE_NAME = 'njoy'
    _VALID_URL = 'https?://(?:www\\.)?n-joy\\.de/(?:[^/]+/)*(?:(?P<display_id>[^/?#]+),)?(?P<id>[\\da-z]+)\\.html'
    IE_DESC = 'N-JOY'
    _RETURN_TYPE = 'video'


class NDREmbedBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ndr'
    IE_NAME = 'ndr:embed:base'
    _VALID_URL = '(?:ndr:(?P<id_s>[\\da-z]+)|https?://www\\.ndr\\.de/(?P<id>[\\da-z]+)-ppjson\\.json)'


class NDREmbedIE(NDREmbedBaseIE):
    _module = 'yt_dlp.extractor.ndr'
    IE_NAME = 'ndr:embed'
    _VALID_URL = 'https?://(?:\\w+\\.)*ndr\\.de/(?:[^/]+/)*(?P<id>[\\da-z]+)-(?:(?:ard)?player|externalPlayer)\\.html'
    _RETURN_TYPE = 'video'


class NJoyEmbedIE(NDREmbedBaseIE):
    _module = 'yt_dlp.extractor.ndr'
    IE_NAME = 'njoy:embed'
    _VALID_URL = 'https?://(?:www\\.)?n-joy\\.de/(?:[^/]+/)*(?P<id>[\\da-z]+)-(?:player|externalPlayer)_[^/]+\\.html'
    _RETURN_TYPE = 'video'


class NDTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ndtv'
    IE_NAME = 'NDTV'
    _VALID_URL = 'https?://(?:[^/]+\\.)?ndtv\\.com/(?:[^/]+/)*videos?/?(?:[^/]+/)*[^/?^&]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NebulaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nebula'
    IE_NAME = 'NebulaBase'
    _NETRC_MACHINE = 'watchnebula'


class NebulaIE(NebulaBaseIE):
    _module = 'yt_dlp.extractor.nebula'
    IE_NAME = 'Nebula'
    _VALID_URL = 'https?://(?:www\\.|beta\\.)?(?:watchnebula\\.com|nebula\\.app|nebula\\.tv)/videos/(?P<id>[-\\w]+)'
    _NETRC_MACHINE = 'watchnebula'
    _RETURN_TYPE = 'video'


class NebulaSubscriptionsIE(NebulaBaseIE):
    _module = 'yt_dlp.extractor.nebula'
    IE_NAME = 'nebula:subscriptions'
    _VALID_URL = 'https?://(?:www\\.|beta\\.)?(?:watchnebula\\.com|nebula\\.app|nebula\\.tv)/myshows'
    _NETRC_MACHINE = 'watchnebula'
    _RETURN_TYPE = 'playlist'


class NebulaChannelIE(NebulaBaseIE):
    _module = 'yt_dlp.extractor.nebula'
    IE_NAME = 'nebula:channel'
    _VALID_URL = 'https?://(?:www\\.|beta\\.)?(?:watchnebula\\.com|nebula\\.app|nebula\\.tv)/(?!myshows|videos/)(?P<id>[-\\w]+)'
    _NETRC_MACHINE = 'watchnebula'
    _RETURN_TYPE = 'playlist'


class NekoHackerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nekohacker'
    IE_NAME = 'NekoHacker'
    _VALID_URL = 'https?://(?:www\\.)?nekohacker\\.com/(?P<id>(?!free-dl)[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class NerdCubedFeedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nerdcubed'
    IE_NAME = 'NerdCubedFeed'
    _VALID_URL = 'https?://(?:www\\.)?nerdcubed\\.co\\.uk/feed\\.json'
    _RETURN_TYPE = 'playlist'


class NetzkinoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.netzkino'
    IE_NAME = 'Netzkino'
    _VALID_URL = 'https?://(?:www\\.)?netzkino\\.de/\\#!/[^/]+/(?P<id>[^/]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class NetEaseMusicBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'NetEaseMusicBase'


class NetEaseMusicIE(NetEaseMusicBaseIE):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'netease:song'
    _VALID_URL = 'https?://(y\\.)?music\\.163\\.com/(?:[#m]/)?song\\?.*?\\bid=(?P<id>[0-9]+)'
    IE_DESC = '网易云音乐'
    _RETURN_TYPE = 'video'


class NetEaseMusicAlbumIE(NetEaseMusicBaseIE):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'netease:album'
    _VALID_URL = 'https?://music\\.163\\.com/(#/)?album\\?id=(?P<id>[0-9]+)'
    IE_DESC = '网易云音乐 - 专辑'
    _RETURN_TYPE = 'playlist'


class NetEaseMusicSingerIE(NetEaseMusicBaseIE):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'netease:singer'
    _VALID_URL = 'https?://music\\.163\\.com/(#/)?artist\\?id=(?P<id>[0-9]+)'
    IE_DESC = '网易云音乐 - 歌手'
    _RETURN_TYPE = 'playlist'


class NetEaseMusicListIE(NetEaseMusicBaseIE):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'netease:playlist'
    _VALID_URL = 'https?://music\\.163\\.com/(#/)?(playlist|discover/toplist)\\?id=(?P<id>[0-9]+)'
    IE_DESC = '网易云音乐 - 歌单'
    _RETURN_TYPE = 'playlist'


class NetEaseMusicMvIE(NetEaseMusicBaseIE):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'netease:mv'
    _VALID_URL = 'https?://music\\.163\\.com/(#/)?mv\\?id=(?P<id>[0-9]+)'
    IE_DESC = '网易云音乐 - MV'
    _RETURN_TYPE = 'video'


class NetEaseMusicProgramIE(NetEaseMusicBaseIE):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'netease:program'
    _VALID_URL = 'https?://music\\.163\\.com/(#/?)program\\?id=(?P<id>[0-9]+)'
    IE_DESC = '网易云音乐 - 电台节目'
    _RETURN_TYPE = 'any'


class NetEaseMusicDjRadioIE(NetEaseMusicBaseIE):
    _module = 'yt_dlp.extractor.neteasemusic'
    IE_NAME = 'netease:djradio'
    _VALID_URL = 'https?://music\\.163\\.com/(#/)?djradio\\?id=(?P<id>[0-9]+)'
    IE_DESC = '网易云音乐 - 电台'
    _RETURN_TYPE = 'playlist'


class NetverseBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.netverse'
    IE_NAME = 'NetverseBase'


class NetverseIE(NetverseBaseIE):
    _module = 'yt_dlp.extractor.netverse'
    IE_NAME = 'Netverse'
    _VALID_URL = 'https?://(?:\\w+\\.)?netverse\\.id/(?P<type>watch|video)/(?P<display_id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NetversePlaylistIE(NetverseBaseIE):
    _module = 'yt_dlp.extractor.netverse'
    IE_NAME = 'NetversePlaylist'
    _VALID_URL = 'https?://(?:\\w+\\.)?netverse\\.id/(?P<type>webseries)/(?P<display_id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class NetverseSearchIE(LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.netverse'
    IE_NAME = 'NetverseSearch'
    _VALID_URL = 'netsearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    SEARCH_KEY = 'netsearch'
    _RETURN_TYPE = 'playlist'


class NewgroundsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.newgrounds'
    IE_NAME = 'Newgrounds'
    _VALID_URL = 'https?://(?:www\\.)?newgrounds\\.com/(?:audio/listen|portal/view)/(?P<id>\\d+)(?:/format/flash)?'
    age_limit = 17
    _RETURN_TYPE = 'video'


class NewgroundsPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.newgrounds'
    IE_NAME = 'Newgrounds:playlist'
    _VALID_URL = 'https?://(?:www\\.)?newgrounds\\.com/(?:collection|[^/]+/search/[^/]+)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class NewgroundsUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.newgrounds'
    IE_NAME = 'Newgrounds:user'
    _VALID_URL = 'https?://(?P<id>[^\\.]+)\\.newgrounds\\.com/(?:movies|audio)/?(?:[#?]|$)'
    _RETURN_TYPE = 'playlist'


class NewsPicksIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.newspicks'
    IE_NAME = 'NewsPicks'
    _VALID_URL = 'https://newspicks\\.com/movie-series/(?P<channel_id>\\d+)\\?movieId=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NewstubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.newstube'
    IE_NAME = 'Newstube'
    _VALID_URL = 'https?://(?:www\\.)?newstube\\.ru/media/(?P<id>.+)'
    _RETURN_TYPE = 'video'


class NewsyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.newsy'
    IE_NAME = 'Newsy'
    _VALID_URL = 'https?://(?:www\\.)?newsy\\.com/stories/(?P<id>[^/?#$&]+)'
    _RETURN_TYPE = 'video'


class NextMediaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nextmedia'
    IE_NAME = 'NextMedia'
    _VALID_URL = 'https?://hk\\.apple\\.nextmedia\\.com/[^/]+/[^/]+/(?P<date>\\d+)/(?P<id>\\d+)'
    IE_DESC = '蘋果日報'
    _RETURN_TYPE = 'video'


class NextMediaActionNewsIE(NextMediaIE):
    _module = 'yt_dlp.extractor.nextmedia'
    IE_NAME = 'NextMediaActionNews'
    _VALID_URL = 'https?://hk\\.dv\\.nextmedia\\.com/actionnews/[^/]+/(?P<date>\\d+)/(?P<id>\\d+)/\\d+'
    IE_DESC = '蘋果日報 - 動新聞'
    _RETURN_TYPE = 'video'


class AppleDailyIE(NextMediaIE):
    _module = 'yt_dlp.extractor.nextmedia'
    IE_NAME = 'AppleDaily'
    _VALID_URL = 'https?://(www|ent)\\.appledaily\\.com\\.tw/[^/]+/[^/]+/[^/]+/(?P<date>\\d+)/(?P<id>\\d+)(/.*)?'
    IE_DESC = '臺灣蘋果日報'
    _RETURN_TYPE = 'video'


class NextTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nextmedia'
    IE_NAME = 'NextTV'
    _VALID_URL = 'https?://(?:www\\.)?nexttv\\.com\\.tw/(?:[^/]+/)+(?P<id>\\d+)'
    IE_DESC = '壹電視'
    _RETURN_TYPE = 'video'


class NexxIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nexx'
    IE_NAME = 'Nexx'
    _VALID_URL = '(?x)\n                        (?:\n                            https?://api\\.nexx(?:\\.cloud|cdn\\.com)/v3(?:\\.\\d)?/(?P<domain_id>\\d+)/videos/byid/|\n                            nexx:(?:(?P<domain_id_s>\\d+):)?|\n                            https?://arc\\.nexx\\.cloud/api/video/\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class NexxEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nexx'
    IE_NAME = 'NexxEmbed'
    _VALID_URL = 'https?://embed\\.nexx(?:\\.cloud|cdn\\.com)/\\d+/(?:video/)?(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NFBIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nfb'
    IE_NAME = 'NFB'
    _VALID_URL = 'https?://(?:www\\.)?nfb\\.ca/film/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NFHSNetworkIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nfhsnetwork'
    IE_NAME = 'NFHSNetwork'
    _VALID_URL = 'https?://(?:www\\.)?nfhsnetwork\\.com/events/[\\w-]+/(?P<id>(?:gam|evt|dd|)?[\\w\\d]{0,10})'
    _RETURN_TYPE = 'video'


class NFLBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nfl'
    IE_NAME = 'NFLBase'


class NFLIE(NFLBaseIE):
    _module = 'yt_dlp.extractor.nfl'
    IE_NAME = 'nfl.com'
    _VALID_URL = '(?x)\n                    https?://\n                        (?P<host>\n                            (?:www\\.)?\n                            (?:\n                                (?:\n                                    nfl|\n                                    buffalobills|\n                                    miamidolphins|\n                                    patriots|\n                                    newyorkjets|\n                                    baltimoreravens|\n                                    bengals|\n                                    clevelandbrowns|\n                                    steelers|\n                                    houstontexans|\n                                    colts|\n                                    jaguars|\n                                    (?:titansonline|tennesseetitans)|\n                                    denverbroncos|\n                                    (?:kc)?chiefs|\n                                    raiders|\n                                    chargers|\n                                    dallascowboys|\n                                    giants|\n                                    philadelphiaeagles|\n                                    (?:redskins|washingtonfootball)|\n                                    chicagobears|\n                                    detroitlions|\n                                    packers|\n                                    vikings|\n                                    atlantafalcons|\n                                    panthers|\n                                    neworleanssaints|\n                                    buccaneers|\n                                    azcardinals|\n                                    (?:stlouis|the)rams|\n                                    49ers|\n                                    seahawks\n                                )\\.com|\n                                .+?\\.clubs\\.nfl\\.com\n                            )\n                        )/\n                    (?:videos?|listen|audio)/(?P<id>[^/#?&]+)'
    _RETURN_TYPE = 'video'


class NFLArticleIE(NFLBaseIE):
    _module = 'yt_dlp.extractor.nfl'
    IE_NAME = 'nfl.com:article'
    _VALID_URL = '(?x)\n                    https?://\n                        (?P<host>\n                            (?:www\\.)?\n                            (?:\n                                (?:\n                                    nfl|\n                                    buffalobills|\n                                    miamidolphins|\n                                    patriots|\n                                    newyorkjets|\n                                    baltimoreravens|\n                                    bengals|\n                                    clevelandbrowns|\n                                    steelers|\n                                    houstontexans|\n                                    colts|\n                                    jaguars|\n                                    (?:titansonline|tennesseetitans)|\n                                    denverbroncos|\n                                    (?:kc)?chiefs|\n                                    raiders|\n                                    chargers|\n                                    dallascowboys|\n                                    giants|\n                                    philadelphiaeagles|\n                                    (?:redskins|washingtonfootball)|\n                                    chicagobears|\n                                    detroitlions|\n                                    packers|\n                                    vikings|\n                                    atlantafalcons|\n                                    panthers|\n                                    neworleanssaints|\n                                    buccaneers|\n                                    azcardinals|\n                                    (?:stlouis|the)rams|\n                                    49ers|\n                                    seahawks\n                                )\\.com|\n                                .+?\\.clubs\\.nfl\\.com\n                            )\n                        )/\n                    news/(?P<id>[^/#?&]+)'
    _RETURN_TYPE = 'playlist'


class NFLPlusEpisodeIE(NFLBaseIE):
    _module = 'yt_dlp.extractor.nfl'
    IE_NAME = 'nfl.com:plus:episode'
    _VALID_URL = 'https?://(?:www\\.)?nfl.com/plus/episodes/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class NFLPlusReplayIE(NFLBaseIE):
    _module = 'yt_dlp.extractor.nfl'
    IE_NAME = 'nfl.com:plus:replay'
    _VALID_URL = 'https?://(?:www\\.)?nfl.com/plus/games/[\\w-]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NhkBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkBase'


class NhkVodIE(NhkBaseIE):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkVod'
    _VALID_URL = 'https?://www3\\.nhk\\.or\\.jp/nhkworld/(?P<lang>[a-z]{2})/ondemand/(?P<type>video|audio)/(?P<id>[0-9a-z]{7}|[^/]+?-\\d{8}-[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class NhkVodProgramIE(NhkBaseIE):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkVodProgram'
    _VALID_URL = 'https?://www3\\.nhk\\.or\\.jp/nhkworld/(?P<lang>[a-z]{2})/ondemand/program/(?P<type>video|audio)/(?P<id>[0-9a-z]+)(?:.+?\\btype=(?P<episode_type>clip|(?:radio|tv)Episode))?'
    _RETURN_TYPE = 'playlist'


class NhkForSchoolBangumiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkForSchoolBangumi'
    _VALID_URL = 'https?://www2\\.nhk\\.or\\.jp/school/movie/(?P<type>bangumi|clip)\\.cgi\\?das_id=(?P<id>[a-zA-Z0-9_-]+)'
    _RETURN_TYPE = 'video'


class NhkForSchoolSubjectIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkForSchoolSubject'
    _VALID_URL = 'https?://www\\.nhk\\.or\\.jp/school/(?P<id>rika|syakai|kokugo|sansuu|seikatsu|doutoku|ongaku|taiiku|zukou|gijutsu|katei|sougou|eigo|tokkatsu|tokushi|sonota)/?(?:[\\?#].*)?$'
    IE_DESC = 'Portal page for each school subjects, like Japanese (kokugo, 国語) or math (sansuu/suugaku or 算数・数学)'
    _RETURN_TYPE = 'playlist'


class NhkForSchoolProgramListIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkForSchoolProgramList'
    _VALID_URL = 'https?://www\\.nhk\\.or\\.jp/school/(?P<id>(?:rika|syakai|kokugo|sansuu|seikatsu|doutoku|ongaku|taiiku|zukou|gijutsu|katei|sougou|eigo|tokkatsu|tokushi|sonota)/[a-zA-Z0-9_-]+)'
    _RETURN_TYPE = 'playlist'


class NhkRadioNewsPageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkRadioNewsPage'
    _VALID_URL = 'https?://www\\.nhk\\.or\\.jp/radionews/?(?:$|[?#])'
    _RETURN_TYPE = 'playlist'


class NhkRadiruIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkRadiru'
    _VALID_URL = 'https?://www\\.nhk\\.or\\.jp/radio/(?:player/ondemand|ondemand/detail)\\.html\\?p=(?P<site>[\\da-zA-Z]+)_(?P<corner>[\\da-zA-Z]+)(?:_(?P<headline>[\\da-zA-Z]+))?'
    IE_DESC = 'NHK らじる (Radiru/Rajiru)'
    _RETURN_TYPE = 'any'


class NhkRadiruLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhk'
    IE_NAME = 'NhkRadiruLive'
    _VALID_URL = 'https?://www\\.nhk\\.or\\.jp/radio/player/\\?ch=(?P<id>r[12]|fm)'
    _RETURN_TYPE = 'video'


class NHLBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nhl'
    IE_NAME = 'NHLBase'


class NHLIE(NHLBaseIE):
    _module = 'yt_dlp.extractor.nhl'
    IE_NAME = 'nhl.com'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>nhl|wch2016)\\.com/(?:[^/]+/)*c-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NickIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.nick'
    IE_NAME = 'nick.com'
    _VALID_URL = 'https?://(?P<domain>(?:www\\.)?nick(?:jr)?\\.com)/(?:[^/]+/)?(?P<type>videos/clip|[^/]+/videos|episodes/[^/]+)/(?P<id>[^/?#.]+)'
    _RETURN_TYPE = 'any'


class NickBrIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.nick'
    IE_NAME = 'nickelodeon:br'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?P<domain>(?:www\\.)?nickjr|mundonick\\.uol)\\.com\\.br|\n                            (?:www\\.)?nickjr\\.[a-z]{2}|\n                            (?:www\\.)?nickelodeonjunior\\.fr\n                        )\n                        /(?:programas/)?[^/]+/videos/(?:episodios/)?(?P<id>[^/?\\#.]+)\n                    '


class NickDeIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.nick'
    IE_NAME = 'nick.de'
    _VALID_URL = 'https?://(?:www\\.)?(?P<host>nick\\.(?:de|com\\.pl|ch)|nickelodeon\\.(?:nl|be|at|dk|no|se))/[^/]+/(?:[^/]+/)*(?P<id>[^/?#&]+)'


class NickNightIE(NickDeIE):
    _module = 'yt_dlp.extractor.nick'
    IE_NAME = 'nicknight'
    _VALID_URL = 'https?://(?:www\\.)(?P<host>nicknight\\.(?:de|at|tv))/(?:playlist|shows)/(?:[^/]+/)*(?P<id>[^/?#&]+)'


class NickRuIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.nick'
    IE_NAME = 'nickelodeonru'
    _VALID_URL = 'https?://(?:www\\.)nickelodeon\\.(?:ru|fr|es|pt|ro|hu|com\\.tr)/[^/]+/(?:[^/]+/)*(?P<id>[^/?#&]+)'


class NiconicoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'niconico'
    _VALID_URL = 'https?://(?:(?:www\\.|secure\\.|sp\\.)?nicovideo\\.jp/watch|nico\\.ms)/(?P<id>(?:[a-z]{2})?[0-9]+)'
    IE_DESC = 'ニコニコ動画'
    _NETRC_MACHINE = 'niconico'
    _RETURN_TYPE = 'video'


class NiconicoPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'NiconicoPlaylistBase'


class NiconicoPlaylistIE(NiconicoPlaylistBaseIE):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'niconico:playlist'
    _VALID_URL = 'https?://(?:(?:www\\.|sp\\.)?nicovideo\\.jp|nico\\.ms)/(?:user/\\d+/)?(?:my/)?mylist/(?:#/)?(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class NiconicoUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'NiconicoUser'
    _VALID_URL = 'https?://(?:www\\.)?nicovideo\\.jp/user/(?P<id>\\d+)/?(?:$|[#?])'
    _RETURN_TYPE = 'playlist'


class NiconicoSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'niconico:series'
    _VALID_URL = 'https?://(?:(?:www\\.|sp\\.)?nicovideo\\.jp(?:/user/\\d+)?|nico\\.ms)/series/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class NiconicoHistoryIE(NiconicoPlaylistBaseIE):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'niconico:history'
    _VALID_URL = 'https?://(?:www\\.|sp\\.)?nicovideo\\.jp/my/(?P<id>history(?:/like)?)'
    IE_DESC = 'NicoNico user history or likes. Requires cookies.'


class NicovideoSearchBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'NicovideoSearchBase'


class NicovideoSearchDateIE(NicovideoSearchBaseIE, LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'nicovideo:search:date'
    _VALID_URL = 'nicosearchdate(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'Nico video search, newest first'
    SEARCH_KEY = 'nicosearchdate'
    _RETURN_TYPE = 'playlist'


class NicovideoSearchIE(NicovideoSearchBaseIE, LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'nicovideo:search'
    _VALID_URL = 'nicosearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'Nico video search'
    SEARCH_KEY = 'nicosearch'
    _RETURN_TYPE = 'playlist'


class NicovideoSearchURLIE(NicovideoSearchBaseIE):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'nicovideo:search_url'
    _VALID_URL = 'https?://(?:www\\.)?nicovideo\\.jp/search/(?P<id>[^?#&]+)?'
    IE_DESC = 'Nico video search URLs'
    _RETURN_TYPE = 'playlist'


class NicovideoTagURLIE(NicovideoSearchBaseIE):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'niconico:tag'
    _VALID_URL = 'https?://(?:www\\.)?nicovideo\\.jp/tag/(?P<id>[^?#&]+)?'
    IE_DESC = 'NicoNico video tag URLs'
    _RETURN_TYPE = 'playlist'


class NiconicoLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.niconico'
    IE_NAME = 'niconico:live'
    _VALID_URL = 'https?://(?:sp\\.)?live2?\\.nicovideo\\.jp/(?:watch|gate)/(?P<id>lv\\d+)'
    IE_DESC = 'ニコニコ生放送'
    _RETURN_TYPE = 'video'


class NineCNineMediaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ninecninemedia'
    IE_NAME = '9c9media'
    _VALID_URL = '9c9media:(?P<destination_code>[^:]+):(?P<id>\\d+)'


class CPTwentyFourIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ninecninemedia'
    IE_NAME = 'cp24'
    _VALID_URL = 'https?://(?:www\\.)?cp24\\.com/news/(?P<id>[^?#]+)'
    _RETURN_TYPE = 'video'


class NineGagIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ninegag'
    IE_NAME = '9gag'
    _VALID_URL = 'https?://(?:www\\.)?9gag\\.com/gag/(?P<id>[^/?&#]+)'
    IE_DESC = '9GAG'
    _RETURN_TYPE = 'video'


class NineNowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ninenow'
    IE_NAME = '9now.com.au'
    _VALID_URL = 'https?://(?:www\\.)?9now\\.com\\.au/(?:[^/]+/){2}(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class NintendoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nintendo'
    IE_NAME = 'Nintendo'
    _VALID_URL = 'https?://(?:www\\.)?nintendo\\.com/(?:games/detail|nintendo-direct)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'any'


class NitterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nitter'
    IE_NAME = 'Nitter'
    _VALID_URL = 'https?://(?:3nzoldnxplag42gqjs23xvghtzf6t6yzssrtytnntc6ppc7xxuoneoad\\.onion|nitter\\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\\.onion|nitter7bryz3jv7e3uekphigvmoyoem4al3fynerxkj22dmoxoq553qd\\.onion|npf37k3mtzwxreiw52ccs5ay4e6qt2fkcs2ndieurdyn2cuzzsfyfvid\\.onion|nitter\\.v6vgyqpa7yefkorazmg5d5fimstmvm2vtbirt6676mt7qmllrcnwycqd\\.onion|i23nv6w3juvzlw32xzoxcqzktegd4i4fu3nmnc2ewv4ggiu4ledwklad\\.onion|26oq3gioiwcmfojub37nz5gzbkdiqp7fue5kvye7d4txv4ny6fb4wwid\\.onion|vfaomgh4jxphpbdfizkm5gbtjahmei234giqj4facbwhrfjtcldauqad\\.onion|iwgu3cv7ywf3gssed5iqtavmrlszgsxazkmwwnt4h2kdait75thdyrqd\\.onion|erpnncl5nhyji3c32dcfmztujtl3xaddqb457jsbkulq24zqq7ifdgad\\.onion|ckzuw5misyahmg7j5t5xwwuj3bwy62jfolxyux4brfflramzsvvd3syd\\.onion|jebqj47jgxleaiosfcxfibx2xdahjettuydlxbg64azd4khsxv6kawid\\.onion|nttr2iupbb6fazdpr2rgbooon2tzbbsvvkagkgkwohhodjzj43stxhad\\.onion|nitraeju2mipeziu2wtcrqsxg7h62v5y4eqgwi75uprynkj74gevvuqd\\.onion|nitter\\.lqs5fjmajyp7rvp4qvyubwofzi6d4imua7vs237rkc4m5qogitqwrgyd\\.onion|ibsboeui2im5o7dxnik3s5yghufumgy5abevtij5nbizequfpu4qi4ad\\.onion|ec5nvbycpfa5k6ro77blxgkyrzbkv7uy6r5cngcbkadtjj2733nm3uyd\\.onion|nitter\\.i2p|u6ikd6zndl3c4dsdq4mmujpntgeevdk5qzkfb57r4tnfeccrn2qa\\.b32\\.i2p|nitterlgj3n5fgwesu3vxc5h67ruku33nqaoeoocae2mvlzhsu6k7fqd\\.onion|nitter\\.lacontrevoie\\.fr|nitter\\.fdn\\.fr|nitter\\.1d4\\.us|nitter\\.kavin\\.rocks|nitter\\.unixfox\\.eu|nitter\\.domain\\.glass|nitter\\.namazso\\.eu|birdsite\\.xanny\\.family|nitter\\.moomoo\\.me|bird\\.trom\\.tf|nitter\\.it|twitter\\.censors\\.us|nitter\\.grimneko\\.de|twitter\\.076\\.ne\\.jp|nitter\\.fly\\.dev|notabird\\.site|nitter\\.weiler\\.rocks|nitter\\.sethforprivacy\\.com|nitter\\.cutelab\\.space|nitter\\.nl|nitter\\.mint\\.lgbt|nitter\\.bus\\-hit\\.me|nitter\\.esmailelbob\\.xyz|tw\\.artemislena\\.eu|nitter\\.winscloud\\.net|nitter\\.tiekoetter\\.com|nitter\\.spaceint\\.fr|nitter\\.privacy\\.com\\.de|nitter\\.poast\\.org|nitter\\.bird\\.froth\\.zone|nitter\\.dcs0\\.hu|twitter\\.dr460nf1r3\\.org|nitter\\.garudalinux\\.org|twitter\\.femboy\\.hu|nitter\\.cz|nitter\\.privacydev\\.net|nitter\\.evil\\.site|tweet\\.lambda\\.dance|nitter\\.kylrth\\.com|nitter\\.foss\\.wtf|nitter\\.priv\\.pw|nitter\\.tokhmi\\.xyz|nitter\\.catalyst\\.sx|unofficialbird\\.com|nitter\\.projectsegfau\\.lt|nitter\\.eu\\.projectsegfau\\.lt|singapore\\.unofficialbird\\.com|canada\\.unofficialbird\\.com|india\\.unofficialbird\\.com|nederland\\.unofficialbird\\.com|uk\\.unofficialbird\\.com|n\\.l5\\.ca|nitter\\.slipfox\\.xyz|nitter\\.soopy\\.moe|nitter\\.qwik\\.space|read\\.whatever\\.social|nitter\\.rawbit\\.ninja|nt\\.vern\\.cc|ntr\\.odyssey346\\.dev|nitter\\.ir|nitter\\.privacytools\\.io|nitter\\.sneed\\.network|n\\.sneed\\.network|nitter\\.manasiwibi\\.com|nitter\\.smnz\\.de|nitter\\.twei\\.space|nitter\\.inpt\\.fr|nitter\\.d420\\.de|nitter\\.caioalonso\\.com|nitter\\.at|nitter\\.drivet\\.xyz|nitter\\.pw|nitter\\.nicfab\\.eu|bird\\.habedieeh\\.re|nitter\\.hostux\\.net|nitter\\.adminforge\\.de|nitter\\.platypush\\.tech|nitter\\.mask\\.sh|nitter\\.pufe\\.org|nitter\\.us\\.projectsegfau\\.lt|nitter\\.arcticfoxes\\.net|t\\.com\\.sb|nitter\\.kling\\.gg|nitter\\.ktachibana\\.party|nitter\\.riverside\\.rocks|nitter\\.girlboss\\.ceo|nitter\\.lunar\\.icu|twitter\\.moe\\.ngo|nitter\\.freedit\\.eu|ntr\\.frail\\.duckdns\\.org|nitter\\.librenode\\.org|n\\.opnxng\\.com|nitter\\.plus\\.st|nitter\\.ethibox\\.fr|nitter\\.net|is\\-nitter\\.resolv\\.ee|lu\\-nitter\\.resolv\\.ee|nitter\\.13ad\\.de|nitter\\.40two\\.app|nitter\\.cattube\\.org|nitter\\.cc|nitter\\.dark\\.fail|nitter\\.himiko\\.cloud|nitter\\.koyu\\.space|nitter\\.mailstation\\.de|nitter\\.mastodont\\.cat|nitter\\.tedomum\\.net|nitter\\.tokhmi\\.xyz|nitter\\.weaponizedhumiliation\\.com|nitter\\.vxempire\\.xyz|tweet\\.lambda\\.dance|nitter\\.ca|nitter\\.42l\\.fr|nitter\\.pussthecat\\.org|nitter\\.nixnet\\.services|nitter\\.eu|nitter\\.actionsack\\.com|nitter\\.hu|twitr\\.gq|nittereu\\.moomoo\\.me|bird\\.from\\.tf|twitter\\.grimneko\\.de|nitter\\.alefvanoon\\.xyz|n\\.hyperborea\\.cloud|twitter\\.mstdn\\.social|nitter\\.silkky\\.cloud|nttr\\.stream|fuckthesacklers\\.network|nitter\\.govt\\.land|nitter\\.datatunnel\\.xyz|de\\.nttr\\.stream|twtr\\.bch\\.bar|nitter\\.exonip\\.de|nitter\\.mastodon\\.pro|nitter\\.notraxx\\.ch|nitter\\.skrep\\.in|nitter\\.snopyta\\.org)/(?P<uploader_id>.+)/status/(?P<id>[0-9]+)(#.)?'
    _RETURN_TYPE = 'video'


class NJPWWorldIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.njpwworld'
    IE_NAME = 'NJPWWorld'
    _VALID_URL = 'https?://(front\\.)?njpwworld\\.com/p/(?P<id>[a-z0-9_]+)'
    IE_DESC = '新日本プロレスワールド'
    _NETRC_MACHINE = 'njpwworld'
    _RETURN_TYPE = 'video'


class NobelPrizeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nobelprize'
    IE_NAME = 'NobelPrize'
    _VALID_URL = 'https?://(?:www\\.)?nobelprize\\.org/mediaplayer.*?\\bid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NoicePodcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.noice'
    IE_NAME = 'NoicePodcast'
    _VALID_URL = 'https?://open\\.noice\\.id/content/(?P<id>[a-fA-F0-9-]+)'
    _RETURN_TYPE = 'video'


class NonkTubeIE(NuevoBaseIE):
    _module = 'yt_dlp.extractor.nonktube'
    IE_NAME = 'NonkTube'
    _VALID_URL = 'https?://(?:www\\.)?nonktube\\.com/(?:(?:video|embed)/|media/nuevo/embed\\.php\\?.*?\\bid=)(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class NoodleMagazineIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.noodlemagazine'
    IE_NAME = 'NoodleMagazine'
    _VALID_URL = 'https?://(?:www|adult\\.)?noodlemagazine\\.com/watch/(?P<id>[0-9-_]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class NoovoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.noovo'
    IE_NAME = 'Noovo'
    _VALID_URL = 'https?://(?:[^/]+\\.)?noovo\\.ca/videos/(?P<id>[^/]+/[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NormalbootsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.normalboots'
    IE_NAME = 'Normalboots'
    _VALID_URL = 'https?://(?:www\\.)?normalboots\\.com/video/(?P<id>[0-9a-z-]*)/?$'
    _RETURN_TYPE = 'video'


class NosVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nosvideo'
    IE_NAME = 'NosVideo'
    _VALID_URL = 'https?://(?:www\\.)?nosvideo\\.com/(?:embed/|\\?v=)(?P<id>[A-Za-z0-9]{12})/?'
    _RETURN_TYPE = 'video'


class NOSNLArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nosnl'
    IE_NAME = 'NOSNLArticle'
    _VALID_URL = 'https?://nos\\.nl/(?P<type>video|(\\w+/)?\\w+)/?\\d+-(?P<display_id>[\\w-]+)'
    _RETURN_TYPE = 'any'


class NovaEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nova'
    IE_NAME = 'NovaEmbed'
    _VALID_URL = 'https?://media\\.cms\\.nova\\.cz/embed/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NovaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nova'
    IE_NAME = 'Nova'
    _VALID_URL = 'https?://(?:[^.]+\\.)?(?P<site>tv(?:noviny)?|tn|novaplus|vymena|fanda|krasna|doma|prask)\\.nova\\.cz/(?:[^/]+/)+(?P<id>[^/]+?)(?:\\.html|/|$)'
    IE_DESC = 'TN.cz, Prásk.tv, Nova.cz, Novaplus.cz, FANDA.tv, Krásná.cz and Doma.cz'
    _RETURN_TYPE = 'video'


class NovaPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.novaplay'
    IE_NAME = 'NovaPlay'
    _VALID_URL = 'https://play.nova\\.bg/video/.*/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NownessBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nowness'
    IE_NAME = 'NownessBase'


class NownessIE(NownessBaseIE):
    _module = 'yt_dlp.extractor.nowness'
    IE_NAME = 'nowness'
    _VALID_URL = 'https?://(?:(?:www|cn)\\.)?nowness\\.com/(?:story|(?:series|category)/[^/]+)/(?P<id>[^/]+?)(?:$|[?#])'
    _RETURN_TYPE = 'video'


class NownessPlaylistIE(NownessBaseIE):
    _module = 'yt_dlp.extractor.nowness'
    IE_NAME = 'nowness:playlist'
    _VALID_URL = 'https?://(?:(?:www|cn)\\.)?nowness\\.com/playlist/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class NownessSeriesIE(NownessBaseIE):
    _module = 'yt_dlp.extractor.nowness'
    IE_NAME = 'nowness:series'
    _VALID_URL = 'https?://(?:(?:www|cn)\\.)?nowness\\.com/series/(?P<id>[^/]+?)(?:$|[?#])'
    _RETURN_TYPE = 'playlist'


class NozIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.noz'
    IE_NAME = 'Noz'
    _VALID_URL = 'https?://(?:www\\.)?noz\\.de/video/(?P<id>[0-9]+)/'
    _RETURN_TYPE = 'video'


class NPOIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'npo'
    _VALID_URL = '(?x)\n                    (?:\n                        npo:|\n                        https?://\n                            (?:www\\.)?\n                            (?:\n                                npo\\.nl/(?:[^/]+/)*|\n                                (?:ntr|npostart)\\.nl/(?:[^/]+/){2,}|\n                                omroepwnl\\.nl/video/fragment/[^/]+__|\n                                (?:zapp|npo3)\\.nl/(?:[^/]+/){2,}\n                            )\n                        )\n                        (?P<id>[^/?#]+)\n                '
    IE_DESC = 'npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return (False if any(ie.suitable(url)
                for ie in (NPOLiveIE, NPORadioIE, NPORadioFragmentIE))
                else super(NPOIE, cls).suitable(url))


class NPOPlaylistBaseIE(NPOIE):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'npo'
    _VALID_URL = '(?x)\n                    (?:\n                        npo:|\n                        https?://\n                            (?:www\\.)?\n                            (?:\n                                npo\\.nl/(?:[^/]+/)*|\n                                (?:ntr|npostart)\\.nl/(?:[^/]+/){2,}|\n                                omroepwnl\\.nl/video/fragment/[^/]+__|\n                                (?:zapp|npo3)\\.nl/(?:[^/]+/){2,}\n                            )\n                        )\n                        (?P<id>[^/?#]+)\n                '
    IE_DESC = 'npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl'

    @classmethod
    def suitable(cls, url):
        return (False if any(ie.suitable(url)
                for ie in (NPOLiveIE, NPORadioIE, NPORadioFragmentIE))
                else super(NPOIE, cls).suitable(url))


class AndereTijdenIE(NPOPlaylistBaseIE):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'anderetijden'
    _VALID_URL = 'https?://(?:www\\.)?anderetijden\\.nl/programma/(?:[^/]+/)+(?P<id>[^/?#&]+)'
    IE_DESC = 'npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if any(ie.suitable(url)
                for ie in (NPOLiveIE, NPORadioIE, NPORadioFragmentIE))
                else super(NPOIE, cls).suitable(url))


class NPOLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'npo.nl:live'
    _VALID_URL = 'https?://(?:www\\.)?npo(?:start)?\\.nl/live(?:/(?P<id>[^/?#&]+))?'
    _RETURN_TYPE = 'video'


class NPORadioIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'npo.nl:radio'
    _VALID_URL = 'https?://(?:www\\.)?npo\\.nl/radio/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if NPORadioFragmentIE.suitable(url) else super(NPORadioIE, cls).suitable(url)


class NPORadioFragmentIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'npo.nl:radio:fragment'
    _VALID_URL = 'https?://(?:www\\.)?npo\\.nl/radio/[^/]+/fragment/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NPODataMidEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'NPODataMidEmbed'


class SchoolTVIE(NPODataMidEmbedIE):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'schooltv'
    _VALID_URL = 'https?://(?:www\\.)?schooltv\\.nl/video/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class HetKlokhuisIE(NPODataMidEmbedIE):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'hetklokhuis'
    _VALID_URL = 'https?://(?:www\\.)?hetklokhuis\\.nl/[^/]+/\\d+/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class VPROIE(NPOPlaylistBaseIE):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'vpro'
    _VALID_URL = 'https?://(?:www\\.)?(?:(?:tegenlicht\\.)?vpro|2doc)\\.nl/(?:[^/]+/)*(?P<id>[^/]+)\\.html'
    IE_DESC = 'npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl'
    _RETURN_TYPE = 'any'

    @classmethod
    def suitable(cls, url):
        return (False if any(ie.suitable(url)
                for ie in (NPOLiveIE, NPORadioIE, NPORadioFragmentIE))
                else super(NPOIE, cls).suitable(url))


class WNLIE(NPOPlaylistBaseIE):
    _module = 'yt_dlp.extractor.npo'
    IE_NAME = 'wnl'
    _VALID_URL = 'https?://(?:www\\.)?omroepwnl\\.nl/video/detail/(?P<id>[^/]+)__\\d+'
    IE_DESC = 'npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if any(ie.suitable(url)
                for ie in (NPOLiveIE, NPORadioIE, NPORadioFragmentIE))
                else super(NPOIE, cls).suitable(url))


class NprIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.npr'
    IE_NAME = 'Npr'
    _VALID_URL = 'https?://(?:www\\.)?npr\\.org/(?:sections/[^/]+/)?\\d{4}/\\d{2}/\\d{2}/(?P<id>\\d+)'
    _RETURN_TYPE = 'any'


class NRKBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKBase'


class NRKIE(NRKBaseIE):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRK'
    _VALID_URL = '(?x)\n                        (?:\n                            nrk:|\n                            https?://\n                                (?:\n                                    (?:www\\.)?nrk\\.no/video/(?:PS\\*|[^_]+_)|\n                                    v8[-.]psapi\\.nrk\\.no/mediaelement/\n                                )\n                            )\n                            (?P<id>[^?\\#&]+)\n                        '
    _RETURN_TYPE = 'video'


class NRKPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKPlaylistBase'


class NRKPlaylistIE(NRKPlaylistBaseIE):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?nrk\\.no/(?!video|skole)(?:[^/]+/)+(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class NRKSkoleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKSkole'
    _VALID_URL = 'https?://(?:www\\.)?nrk\\.no/skole/?\\?.*\\bmediaId=(?P<id>\\d+)'
    IE_DESC = 'NRK Skole'
    _RETURN_TYPE = 'video'


class NRKTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKTV'
    _VALID_URL = 'https?://(?:tv|radio)\\.nrk(?:super)?\\.no/(?:[^/]+/)*(?P<id>[a-zA-Z]{4}\\d{8})'
    IE_DESC = 'NRK TV and NRK Radio'
    age_limit = 6
    _RETURN_TYPE = 'video'


class NRKTVDirekteIE(NRKTVIE):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKTVDirekte'
    _VALID_URL = 'https?://(?:tv|radio)\\.nrk\\.no/direkte/(?P<id>[^/?#&]+)'
    IE_DESC = 'NRK TV Direkte and NRK Radio Direkte'


class NRKRadioPodkastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKRadioPodkast'
    _VALID_URL = 'https?://radio\\.nrk\\.no/pod[ck]ast/(?:[^/]+/)+(?P<id>l_[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class NRKTVEpisodeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKTVEpisode'
    _VALID_URL = 'https?://tv\\.nrk\\.no/serie/(?P<id>[^/]+/sesong/(?P<season_number>\\d+)/episode/(?P<episode_number>\\d+))'
    age_limit = 6
    _RETURN_TYPE = 'video'


class NRKTVEpisodesIE(NRKPlaylistBaseIE):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKTVEpisodes'
    _VALID_URL = 'https?://tv\\.nrk\\.no/program/[Ee]pisodes/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class NRKTVSerieBaseIE(NRKBaseIE):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKTVSerieBase'


class NRKTVSeasonIE(NRKTVSerieBaseIE):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKTVSeason'
    _VALID_URL = '(?x)\n                    https?://\n                        (?P<domain>tv|radio)\\.nrk\\.no/\n                        (?P<serie_kind>serie|pod[ck]ast)/\n                        (?P<serie>[^/]+)/\n                        (?:\n                            (?:sesong/)?(?P<id>\\d+)|\n                            sesong/(?P<id_2>[^/?#&]+)\n                        )\n                    '
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if NRKTVIE.suitable(url) or NRKTVEpisodeIE.suitable(url) or NRKRadioPodkastIE.suitable(url)
                else super(NRKTVSeasonIE, cls).suitable(url))


class NRKTVSeriesIE(NRKTVSerieBaseIE):
    _module = 'yt_dlp.extractor.nrk'
    IE_NAME = 'NRKTVSeries'
    _VALID_URL = 'https?://(?P<domain>(?:tv|radio)\\.nrk|(?:tv\\.)?nrksuper)\\.no/(?P<serie_kind>serie|pod[ck]ast)/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (
            False if any(ie.suitable(url)
                         for ie in (NRKTVIE, NRKTVEpisodeIE, NRKRadioPodkastIE, NRKTVSeasonIE))
            else super(NRKTVSeriesIE, cls).suitable(url))


class NRLTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nrl'
    IE_NAME = 'NRLTV'
    _VALID_URL = 'https?://(?:www\\.)?nrl\\.com/tv(/[^/]+)*/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class NTVCoJpCUIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ntvcojp'
    IE_NAME = 'cu.ntv.co.jp'
    _VALID_URL = 'https?://cu\\.ntv\\.co\\.jp/(?!program)(?P<id>[^/?&#]+)'
    IE_DESC = 'Nippon Television Network'
    _RETURN_TYPE = 'video'


class NTVDeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ntvde'
    IE_NAME = 'n-tv.de'
    _VALID_URL = 'https?://(?:www\\.)?n-tv\\.de/mediathek/videos/[^/?#]+/[^/?#]+-article(?P<id>.+)\\.html'
    _RETURN_TYPE = 'video'


class NTVRuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ntvru'
    IE_NAME = 'ntv.ru'
    _VALID_URL = 'https?://(?:www\\.)?ntv\\.ru/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NubilesPornIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nubilesporn'
    IE_NAME = 'NubilesPorn'
    _VALID_URL = '(?x)\n        https://members.nubiles-porn.com/video/watch/(?P<id>\\d+)\n        (?:/(?P<display_id>[\\w\\-]+-s(?P<season>\\d+)e(?P<episode>\\d+)))?\n    '
    _NETRC_MACHINE = 'nubiles-porn'
    age_limit = 18
    _RETURN_TYPE = 'video'


class NYTimesBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nytimes'
    IE_NAME = 'NYTimesBase'


class NYTimesIE(NYTimesBaseIE):
    _module = 'yt_dlp.extractor.nytimes'
    IE_NAME = 'NYTimes'
    _VALID_URL = 'https?://(?:(?:www\\.)?nytimes\\.com/video/(?:[^/]+/)+?|graphics8\\.nytimes\\.com/bcvideo/\\d+(?:\\.\\d+)?/iframe/embed\\.html\\?videoId=)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NYTimesArticleIE(NYTimesBaseIE):
    _module = 'yt_dlp.extractor.nytimes'
    IE_NAME = 'NYTimesArticle'
    _VALID_URL = 'https?://(?:www\\.)?nytimes\\.com/(.(?<!video))*?/(?:[^/]+/)*(?P<id>[^.]+)(?:\\.html)?'
    _RETURN_TYPE = 'video'


class NYTimesCookingIE(NYTimesBaseIE):
    _module = 'yt_dlp.extractor.nytimes'
    IE_NAME = 'NYTimesCooking'
    _VALID_URL = 'https?://cooking\\.nytimes\\.com/(?:guid|recip)es/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class NuvidIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nuvid'
    IE_NAME = 'Nuvid'
    _VALID_URL = 'https?://(?:www|m)\\.nuvid\\.com/video/(?P<id>[0-9]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class NZHeraldIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nzherald'
    IE_NAME = 'nzherald'
    _VALID_URL = 'https?://(?:www\\.)?nzherald\\.co\\.nz/[\\w\\/-]+\\/(?P<id>[A-Z0-9]+)'
    _RETURN_TYPE = 'video'


class NZOnScreenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nzonscreen'
    IE_NAME = 'NZOnScreen'
    _VALID_URL = '^https://www\\.nzonscreen\\.com/title/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class NZZIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.nzz'
    IE_NAME = 'NZZ'
    _VALID_URL = 'https?://(?:www\\.)?nzz\\.ch/(?:[^/]+/)*[^/?#]+-ld\\.(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class OdaTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.odatv'
    IE_NAME = 'OdaTV'
    _VALID_URL = 'https?://(?:www\\.)?odatv\\.com/(?:mob|vid)_video\\.php\\?.*\\bid=(?P<id>[^&]+)'
    _RETURN_TYPE = 'video'


class OnDemandChinaEpisodeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.odkmedia'
    IE_NAME = 'OnDemandChinaEpisode'
    _VALID_URL = 'https?://www\\.ondemandchina\\.com/\\w+/watch/(?P<series>[\\w-]+)/(?P<id>ep-(?P<ep>\\d+))'
    _RETURN_TYPE = 'video'


class OdnoklassnikiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.odnoklassniki'
    IE_NAME = 'Odnoklassniki'
    _VALID_URL = '(?x)\n                https?://\n                    (?:(?:www|m|mobile)\\.)?\n                    (?:odnoklassniki|ok)\\.ru/\n                    (?:\n                        video(?P<embed>embed)?/|\n                        web-api/video/moviePlayer/|\n                        live/|\n                        dk\\?.*?st\\.mvId=\n                    )\n                    (?P<id>[\\d-]+)\n                '
    _RETURN_TYPE = 'video'


class OfTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.oftv'
    IE_NAME = 'OfTV'
    _VALID_URL = 'https?://(?:www\\.)?of.tv/video/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class OfTVPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.oftv'
    IE_NAME = 'OfTVPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?of.tv/creators/(?P<id>[a-zA-Z0-9-]+)/.?'
    _RETURN_TYPE = 'playlist'


class OktoberfestTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.oktoberfesttv'
    IE_NAME = 'OktoberfestTV'
    _VALID_URL = 'https?://(?:www\\.)?oktoberfest-tv\\.de/[^/]+/[^/]+/video/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class OlympicsReplayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.olympics'
    IE_NAME = 'OlympicsReplay'
    _VALID_URL = 'https?://(?:www\\.)?olympics\\.com(?:/tokyo-2020)?/[a-z]{2}/(?:replay|video)/(?P<id>[^/#&?]+)'
    _RETURN_TYPE = 'video'


class On24IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.on24'
    IE_NAME = 'on24'
    _VALID_URL = '(?x)\n                    https?://event\\.on24\\.com/(?:\n                        wcc/r/(?P<id_1>\\d{7})/(?P<key_1>[0-9A-F]{32})|\n                        eventRegistration/(?:console/EventConsoleApollo|EventLobbyServlet\\?target=lobby30)\n                            \\.jsp\\?(?:[^/#?]*&)?eventid=(?P<id_2>\\d{7})[^/#?]*&key=(?P<key_2>[0-9A-F]{32})\n                    )'
    IE_DESC = 'ON24'
    _RETURN_TYPE = 'video'


class OnDemandKoreaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ondemandkorea'
    IE_NAME = 'OnDemandKorea'
    _VALID_URL = 'https?://(?:www\\.)?ondemandkorea\\.com/(?P<id>[^/]+)\\.html'
    _RETURN_TYPE = 'video'


class OneFootballIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.onefootball'
    IE_NAME = 'OneFootball'
    _VALID_URL = 'https?://(?:www\\.)?onefootball\\.com/[a-z]{2}/video/[^/&?#]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class OneNewsNZIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.onenewsnz'
    IE_NAME = '1News'
    _VALID_URL = 'https?://(?:www\\.)?(?:1|one)news\\.co\\.nz/\\d+/\\d+/\\d+/(?P<id>[^/?#&]+)'
    IE_DESC = '1news.co.nz article videos'
    _RETURN_TYPE = 'playlist'


class OnePlacePodcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.oneplace'
    IE_NAME = 'OnePlacePodcast'
    _VALID_URL = 'https?://www\\.oneplace\\.com/[\\w]+/[^/]+/listen/[\\w-]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class OnetIE(OnetBaseIE):
    _module = 'yt_dlp.extractor.onet'
    IE_NAME = 'onet.tv'
    _VALID_URL = 'https?://(?:(?:www\\.)?onet\\.tv|onet100\\.vod\\.pl)/[a-z]/[a-z]+/(?P<display_id>[0-9a-z-]+)/(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class OnetChannelIE(OnetBaseIE):
    _module = 'yt_dlp.extractor.onet'
    IE_NAME = 'onet.tv:channel'
    _VALID_URL = 'https?://(?:(?:www\\.)?onet\\.tv|onet100\\.vod\\.pl)/[a-z]/(?P<id>[a-z]+)(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class OnetMVPIE(OnetBaseIE):
    _module = 'yt_dlp.extractor.onet'
    IE_NAME = 'OnetMVP'
    _VALID_URL = 'onetmvp:(?P<id>\\d+\\.\\d+)'


class OnetPlIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.onet'
    IE_NAME = 'onet.pl'
    _VALID_URL = 'https?://(?:[^/]+\\.)?(?:onet|businessinsider\\.com|plejada)\\.pl/(?:[^/]+/)+(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class OnionStudiosIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.onionstudios'
    IE_NAME = 'OnionStudios'
    _VALID_URL = 'https?://(?:www\\.)?onionstudios\\.com/(?:video(?:s/[^/]+-|/)|embed\\?.*\\bid=)(?P<id>\\d+)(?!-)'
    _RETURN_TYPE = 'video'


class OoyalaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ooyala'
    IE_NAME = 'OoyalaBase'


class OoyalaIE(OoyalaBaseIE):
    _module = 'yt_dlp.extractor.ooyala'
    IE_NAME = 'Ooyala'
    _VALID_URL = '(?:ooyala:|https?://.+?\\.ooyala\\.com/.*?(?:embedCode|ec)=)(?P<id>.+?)(&|$)'
    _RETURN_TYPE = 'video'


class OoyalaExternalIE(OoyalaBaseIE):
    _module = 'yt_dlp.extractor.ooyala'
    IE_NAME = 'OoyalaExternal'
    _VALID_URL = '(?x)\n                    (?:\n                        ooyalaexternal:|\n                        https?://.+?\\.ooyala\\.com/.*?\\bexternalId=\n                    )\n                    (?P<partner_id>[^:]+)\n                    :\n                    (?P<id>.+)\n                    (?:\n                        :|\n                        .*?&pcode=\n                    )\n                    (?P<pcode>.+?)\n                    (?:&|$)\n                    '
    _RETURN_TYPE = 'video'


class OpencastBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.opencast'
    IE_NAME = 'OpencastBase'


class OpencastIE(OpencastBaseIE):
    _module = 'yt_dlp.extractor.opencast'
    IE_NAME = 'Opencast'
    _VALID_URL = '(?x)\n        https?://(?P<host>(?:\n                            opencast\\.informatik\\.kit\\.edu|\n                            electures\\.uni-muenster\\.de|\n                            oc-presentation\\.ltcc\\.tuwien\\.ac\\.at|\n                            medien\\.ph-noe\\.ac\\.at|\n                            oc-video\\.ruhr-uni-bochum\\.de|\n                            oc-video1\\.ruhr-uni-bochum\\.de|\n                            opencast\\.informatik\\.uni-goettingen\\.de|\n                            heicast\\.uni-heidelberg\\.de|\n                            opencast\\.hawk\\.de:8080|\n                            opencast\\.hs-osnabrueck\\.de|\n                            video[0-9]+\\.virtuos\\.uni-osnabrueck\\.de|\n                            opencast\\.uni-koeln\\.de|\n                            media\\.opencast\\.hochschule-rhein-waal\\.de|\n                            matterhorn\\.dce\\.harvard\\.edu|\n                            hs-harz\\.opencast\\.uni-halle\\.de|\n                            videocampus\\.urz\\.uni-leipzig\\.de|\n                            media\\.uct\\.ac\\.za|\n                            vid\\.igb\\.illinois\\.edu|\n                            cursosabertos\\.c3sl\\.ufpr\\.br|\n                            mcmedia\\.missioncollege\\.org|\n                            clases\\.odon\\.edu\\.uy\n                        ))/paella/ui/watch\\.html\\?\n        (?:[^#]+&)?id=(?P<id>[\\da-fA-F]{8}-[\\da-fA-F]{4}-[\\da-fA-F]{4}-[\\da-fA-F]{4}-[\\da-fA-F]{12})'
    _RETURN_TYPE = 'video'


class OpencastPlaylistIE(OpencastBaseIE):
    _module = 'yt_dlp.extractor.opencast'
    IE_NAME = 'OpencastPlaylist'
    _VALID_URL = '(?x)\n        https?://(?P<host>(?:\n                            opencast\\.informatik\\.kit\\.edu|\n                            electures\\.uni-muenster\\.de|\n                            oc-presentation\\.ltcc\\.tuwien\\.ac\\.at|\n                            medien\\.ph-noe\\.ac\\.at|\n                            oc-video\\.ruhr-uni-bochum\\.de|\n                            oc-video1\\.ruhr-uni-bochum\\.de|\n                            opencast\\.informatik\\.uni-goettingen\\.de|\n                            heicast\\.uni-heidelberg\\.de|\n                            opencast\\.hawk\\.de:8080|\n                            opencast\\.hs-osnabrueck\\.de|\n                            video[0-9]+\\.virtuos\\.uni-osnabrueck\\.de|\n                            opencast\\.uni-koeln\\.de|\n                            media\\.opencast\\.hochschule-rhein-waal\\.de|\n                            matterhorn\\.dce\\.harvard\\.edu|\n                            hs-harz\\.opencast\\.uni-halle\\.de|\n                            videocampus\\.urz\\.uni-leipzig\\.de|\n                            media\\.uct\\.ac\\.za|\n                            vid\\.igb\\.illinois\\.edu|\n                            cursosabertos\\.c3sl\\.ufpr\\.br|\n                            mcmedia\\.missioncollege\\.org|\n                            clases\\.odon\\.edu\\.uy\n                        ))(?:\n            /engage/ui/index\\.html\\?(?:[^#]+&)?epFrom=|\n            /ltitools/index\\.html\\?(?:[^#]+&)?series=\n        )(?P<id>[\\da-fA-F]{8}-[\\da-fA-F]{4}-[\\da-fA-F]{4}-[\\da-fA-F]{4}-[\\da-fA-F]{12})'
    _RETURN_TYPE = 'playlist'


class OpenRecBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.openrec'
    IE_NAME = 'OpenRecBase'


class OpenRecIE(OpenRecBaseIE):
    _module = 'yt_dlp.extractor.openrec'
    IE_NAME = 'openrec'
    _VALID_URL = 'https?://(?:www\\.)?openrec\\.tv/live/(?P<id>[^/]+)'


class OpenRecCaptureIE(OpenRecBaseIE):
    _module = 'yt_dlp.extractor.openrec'
    IE_NAME = 'openrec:capture'
    _VALID_URL = 'https?://(?:www\\.)?openrec\\.tv/capture/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class OpenRecMovieIE(OpenRecBaseIE):
    _module = 'yt_dlp.extractor.openrec'
    IE_NAME = 'openrec:movie'
    _VALID_URL = 'https?://(?:www\\.)?openrec\\.tv/movie/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class OraTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ora'
    IE_NAME = 'OraTV'
    _VALID_URL = 'https?://(?:www\\.)?(?:ora\\.tv|unsafespeech\\.com)/([^/]+/)*(?P<id>[^/\\?#]+)'
    _RETURN_TYPE = 'video'


class ORFTVthekIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.orf'
    IE_NAME = 'orf:tvthek'
    _VALID_URL = '(?P<url>https?://tvthek\\.orf\\.at/(?:(?:[^/]+/){2}){1,2}(?P<id>\\d+))(/[^/]+/(?P<vid>\\d+))?(?:$|[?#])'
    IE_DESC = 'ORF TVthek'
    _RETURN_TYPE = 'any'


class ORFFM4StoryIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.orf'
    IE_NAME = 'orf:fm4:story'
    _VALID_URL = 'https?://fm4\\.orf\\.at/stories/(?P<id>\\d+)'
    IE_DESC = 'fm4.orf.at stories'
    _RETURN_TYPE = 'playlist'


class ORFRadioIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.orf'
    IE_NAME = 'orf:radio'
    _VALID_URL = '(?x)\n        https?://(?:\n            (?P<station>fm4|noe|wien|burgenland|ooe|steiermark|kaernten|salzburg|tirol|vorarlberg|oe3|oe1)\\.orf\\.at/player|\n            radiothek\\.orf\\.at/(?P<station2>fm4|noe|wien|burgenland|ooe|steiermark|kaernten|salzburg|tirol|vorarlberg|oe3|oe1)\n        )/(?P<date>[0-9]+)/(?P<show>\\w+)'
    _RETURN_TYPE = 'any'


class ORFIPTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.orf'
    IE_NAME = 'orf:iptv'
    _VALID_URL = 'https?://iptv\\.orf\\.at/(?:#/)?stories/(?P<id>\\d+)'
    IE_DESC = 'iptv.ORF.at'
    _RETURN_TYPE = 'video'


class OutsideTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.outsidetv'
    IE_NAME = 'OutsideTV'
    _VALID_URL = 'https?://(?:www\\.)?outsidetv\\.com/(?:[^/]+/)*?play/[a-zA-Z0-9]{8}/\\d+/\\d+/(?P<id>[a-zA-Z0-9]{8})'
    _RETURN_TYPE = 'video'


class OwnCloudIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.owncloud'
    IE_NAME = 'OwnCloud'
    _VALID_URL = 'https?://(?:(?:[^\\.]+\\.)?sciebo\\.de|cloud\\.uni-koblenz-landau\\.de)/s/(?P<id>[\\w.-]+)'
    _RETURN_TYPE = 'video'


class PacktPubBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.packtpub'
    IE_NAME = 'PacktPubBase'


class PacktPubIE(PacktPubBaseIE):
    _module = 'yt_dlp.extractor.packtpub'
    IE_NAME = 'PacktPub'
    _VALID_URL = 'https?://(?:(?:www\\.)?packtpub\\.com/mapt|subscription\\.packtpub\\.com)/video/[^/]+/(?P<course_id>\\d+)/(?P<chapter_id>[^/]+)/(?P<id>[^/]+)(?:/(?P<display_id>[^/?&#]+))?'
    _NETRC_MACHINE = 'packtpub'
    _RETURN_TYPE = 'video'


class PacktPubCourseIE(PacktPubBaseIE):
    _module = 'yt_dlp.extractor.packtpub'
    IE_NAME = 'PacktPubCourse'
    _VALID_URL = '(?P<url>https?://(?:(?:www\\.)?packtpub\\.com/mapt|subscription\\.packtpub\\.com)/video/[^/]+/(?P<id>\\d+))'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if PacktPubIE.suitable(url) else super(
            PacktPubCourseIE, cls).suitable(url)


class PalcoMP3BaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.palcomp3'
    IE_NAME = 'PalcoMP3Base'


class PalcoMP3IE(PalcoMP3BaseIE):
    _module = 'yt_dlp.extractor.palcomp3'
    IE_NAME = 'PalcoMP3:song'
    _VALID_URL = 'https?://(?:www\\.)?palcomp3\\.com(?:\\.br)?/(?P<artist>[^/]+)/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if PalcoMP3VideoIE.suitable(url) else super(PalcoMP3IE, cls).suitable(url)


class PalcoMP3ArtistIE(PalcoMP3BaseIE):
    _module = 'yt_dlp.extractor.palcomp3'
    IE_NAME = 'PalcoMP3:artist'
    _VALID_URL = 'https?://(?:www\\.)?palcomp3\\.com(?:\\.br)?/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if PalcoMP3IE._match_valid_url(url) else super(PalcoMP3ArtistIE, cls).suitable(url)


class PalcoMP3VideoIE(PalcoMP3BaseIE):
    _module = 'yt_dlp.extractor.palcomp3'
    IE_NAME = 'PalcoMP3:video'
    _VALID_URL = 'https?://(?:www\\.)?palcomp3\\.com(?:\\.br)?/(?P<artist>[^/]+)/(?P<id>[^/?&#]+)/?#clipe'
    _RETURN_TYPE = 'video'


class PandoraTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pandoratv'
    IE_NAME = 'pandora.tv'
    _VALID_URL = '(?x)\n                        https?://\n                            (?:\n                                (?:www\\.)?pandora\\.tv/view/(?P<user_id>[^/]+)/(?P<id>\\d+)|  # new format\n                                (?:.+?\\.)?channel\\.pandora\\.tv/channel/video\\.ptv\\?|        # old format\n                                m\\.pandora\\.tv/?\\?                                          # mobile\n                            )\n                    '
    IE_DESC = '판도라TV'
    _RETURN_TYPE = 'video'


class PanoptoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.panopto'
    IE_NAME = 'PanoptoBase'


class PanoptoIE(PanoptoBaseIE):
    _module = 'yt_dlp.extractor.panopto'
    IE_NAME = 'Panopto'
    _VALID_URL = '(?P<base_url>https?://[\\w.-]+\\.panopto.(?:com|eu)/Panopto)/Pages/(Viewer|Embed)\\.aspx.*(?:\\?|&)id=(?P<id>[a-f0-9-]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if PanoptoPlaylistIE.suitable(url) else super().suitable(url)


class PanoptoListIE(PanoptoBaseIE):
    _module = 'yt_dlp.extractor.panopto'
    IE_NAME = 'PanoptoList'
    _VALID_URL = '(?P<base_url>https?://[\\w.-]+\\.panopto.(?:com|eu)/Panopto)/Pages/Sessions/List\\.aspx'
    _RETURN_TYPE = 'playlist'


class PanoptoPlaylistIE(PanoptoBaseIE):
    _module = 'yt_dlp.extractor.panopto'
    IE_NAME = 'PanoptoPlaylist'
    _VALID_URL = '(?P<base_url>https?://[\\w.-]+\\.panopto.(?:com|eu)/Panopto)/Pages/(Viewer|Embed)\\.aspx.*(?:\\?|&)pid=(?P<id>[a-f0-9-]+)'
    _RETURN_TYPE = 'playlist'


class ParamountPlusSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.paramountplus'
    IE_NAME = 'ParamountPlusSeries'
    _VALID_URL = 'https?://(?:www\\.)?paramountplus\\.com/shows/(?P<id>[a-zA-Z0-9-_]+)/?(?:[#?]|$)'
    _RETURN_TYPE = 'playlist'


class ParlerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.parler'
    IE_NAME = 'Parler'
    _VALID_URL = 'https://parler\\.com/feed/(?P<id>[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})'
    IE_DESC = 'Posts on parler.com'
    _RETURN_TYPE = 'video'


class ParlviewIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.parlview'
    IE_NAME = 'Parlview'
    _VALID_URL = 'https?://(?:www\\.)?parlview\\.aph\\.gov\\.au/(?:[^/]+)?\\bvideoID=(?P<id>\\d{6})'
    _RETURN_TYPE = 'video'


class PatreonBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.patreon'
    IE_NAME = 'PatreonBase'


class PatreonIE(PatreonBaseIE):
    _module = 'yt_dlp.extractor.patreon'
    IE_NAME = 'Patreon'
    _VALID_URL = 'https?://(?:www\\.)?patreon\\.com/(?:creation\\?hid=|posts/(?:[\\w-]+-)?)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class PatreonCampaignIE(PatreonBaseIE):
    _module = 'yt_dlp.extractor.patreon'
    IE_NAME = 'PatreonCampaign'
    _VALID_URL = 'https?://(?:www\\.)?patreon\\.com/(?!rss)(?:(?:m/(?P<campaign_id>\\d+))|(?P<vanity>[-\\w]+))'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if PatreonIE.suitable(url) else super(PatreonCampaignIE, cls).suitable(url)


class PBSIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pbs'
    IE_NAME = 'pbs'
    _VALID_URL = '(?x)https?://\n        (?:\n           # Direct video URL\n           (?:(?:video|www|player)\\.pbs\\.org|video\\.aptv\\.org|video\\.gpb\\.org|video\\.mpbonline\\.org|video\\.wnpt\\.org|video\\.wfsu\\.org|video\\.wsre\\.org|video\\.wtcitv\\.org|video\\.pba\\.org|video\\.alaskapublic\\.org|video\\.azpbs\\.org|portal\\.knme\\.org|video\\.vegaspbs\\.org|watch\\.aetn\\.org|video\\.ket\\.org|video\\.wkno\\.org|video\\.lpb\\.org|videos\\.oeta\\.tv|video\\.optv\\.org|watch\\.wsiu\\.org|video\\.keet\\.org|pbs\\.kixe\\.org|video\\.kpbs\\.org|video\\.kqed\\.org|vids\\.kvie\\.org|video\\.pbssocal\\.org|video\\.valleypbs\\.org|video\\.cptv\\.org|watch\\.knpb\\.org|video\\.soptv\\.org|video\\.rmpbs\\.org|video\\.kenw\\.org|video\\.kued\\.org|video\\.wyomingpbs\\.org|video\\.cpt12\\.org|video\\.kbyueleven\\.org|video\\.thirteen\\.org|video\\.wgbh\\.org|video\\.wgby\\.org|watch\\.njtvonline\\.org|watch\\.wliw\\.org|video\\.mpt\\.tv|watch\\.weta\\.org|video\\.whyy\\.org|video\\.wlvt\\.org|video\\.wvpt\\.net|video\\.whut\\.org|video\\.wedu\\.org|video\\.wgcu\\.org|video\\.wpbt2\\.org|video\\.wucftv\\.org|video\\.wuft\\.org|watch\\.wxel\\.org|video\\.wlrn\\.org|video\\.wusf\\.usf\\.edu|video\\.scetv\\.org|video\\.unctv\\.org|video\\.pbshawaii\\.org|video\\.idahoptv\\.org|video\\.ksps\\.org|watch\\.opb\\.org|watch\\.nwptv\\.org|video\\.will\\.illinois\\.edu|video\\.networkknowledge\\.tv|video\\.wttw\\.com|video\\.iptv\\.org|video\\.ninenet\\.org|video\\.wfwa\\.org|video\\.wfyi\\.org|video\\.mptv\\.org|video\\.wnin\\.org|video\\.wnit\\.org|video\\.wpt\\.org|video\\.wvut\\.org|video\\.weiu\\.net|video\\.wqpt\\.org|video\\.wycc\\.org|video\\.wipb\\.org|video\\.indianapublicmedia\\.org|watch\\.cetconnect\\.org|video\\.thinktv\\.org|video\\.wbgu\\.org|video\\.wgvu\\.org|video\\.netnebraska\\.org|video\\.pioneer\\.org|watch\\.sdpb\\.org|video\\.tpt\\.org|watch\\.ksmq\\.org|watch\\.kpts\\.org|watch\\.ktwu\\.org|watch\\.easttennesseepbs\\.org|video\\.wcte\\.tv|video\\.wljt\\.org|video\\.wosu\\.org|video\\.woub\\.org|video\\.wvpublic\\.org|video\\.wkyupbs\\.org|video\\.kera\\.org|video\\.mpbn\\.net|video\\.mountainlake\\.org|video\\.nhptv\\.org|video\\.vpt\\.org|video\\.witf\\.org|watch\\.wqed\\.org|video\\.wmht\\.org|video\\.deltabroadcasting\\.org|video\\.dptv\\.org|video\\.wcmu\\.org|video\\.wkar\\.org|wnmuvideo\\.nmu\\.edu|video\\.wdse\\.org|video\\.wgte\\.org|video\\.lptv\\.org|video\\.kmos\\.org|watch\\.montanapbs\\.org|video\\.krwg\\.org|video\\.kacvtv\\.org|video\\.kcostv\\.org|video\\.wcny\\.org|video\\.wned\\.org|watch\\.wpbstv\\.org|video\\.wskg\\.org|video\\.wxxi\\.org|video\\.wpsu\\.org|on-demand\\.wvia\\.org|video\\.wtvi\\.org|video\\.westernreservepublicmedia\\.org|video\\.ideastream\\.org|video\\.kcts9\\.org|video\\.basinpbs\\.org|video\\.houstonpbs\\.org|video\\.klrn\\.org|video\\.klru\\.tv|video\\.wtjx\\.org|video\\.ideastations\\.org|video\\.kbtc\\.org)/(?:(?:vir|port)alplayer|video)/(?P<id>[0-9]+)(?:[?/]|$) |\n           # Article with embedded player (or direct video)\n           (?:www\\.)?pbs\\.org/(?:[^/]+/){1,5}(?P<presumptive_id>[^/]+?)(?:\\.html)?/?(?:$|[?\\#]) |\n           # Player\n           (?:video|player)\\.pbs\\.org/(?:widget/)?partnerplayer/(?P<player_id>[^/]+)\n        )\n    '
    IE_DESC = 'Public Broadcasting Service (PBS) and member stations: PBS: Public Broadcasting Service, APT - Alabama Public Television (WBIQ), GPB/Georgia Public Broadcasting (WGTV), Mississippi Public Broadcasting (WMPN), Nashville Public Television (WNPT), WFSU-TV (WFSU), WSRE (WSRE), WTCI (WTCI), WPBA/Channel 30 (WPBA), Alaska Public Media (KAKM), Arizona PBS (KAET), KNME-TV/Channel 5 (KNME), Vegas PBS (KLVX), AETN/ARKANSAS ETV NETWORK (KETS), KET (WKLE), WKNO/Channel 10 (WKNO), LPB/LOUISIANA PUBLIC BROADCASTING (WLPB), OETA (KETA), Ozarks Public Television (KOZK), WSIU Public Broadcasting (WSIU), KEET TV (KEET), KIXE/Channel 9 (KIXE), KPBS San Diego (KPBS), KQED (KQED), KVIE Public Television (KVIE), PBS SoCal/KOCE (KOCE), ValleyPBS (KVPT), CONNECTICUT PUBLIC TELEVISION (WEDH), KNPB Channel 5 (KNPB), SOPTV (KSYS), Rocky Mountain PBS (KRMA), KENW-TV3 (KENW), KUED Channel 7 (KUED), Wyoming PBS (KCWC), Colorado Public Television / KBDI 12 (KBDI), KBYU-TV (KBYU), Thirteen/WNET New York (WNET), WGBH/Channel 2 (WGBH), WGBY (WGBY), NJTV Public Media NJ (WNJT), WLIW21 (WLIW), mpt/Maryland Public Television (WMPB), WETA Television and Radio (WETA), WHYY (WHYY), PBS 39 (WLVT), WVPT - Your Source for PBS and More! (WVPT), Howard University Television (WHUT), WEDU PBS (WEDU), WGCU Public Media (WGCU), WPBT2 (WPBT), WUCF TV (WUCF), WUFT/Channel 5 (WUFT), WXEL/Channel 42 (WXEL), WLRN/Channel 17 (WLRN), WUSF Public Broadcasting (WUSF), ETV (WRLK), UNC-TV (WUNC), PBS Hawaii - Oceanic Cable Channel 10 (KHET), Idaho Public Television (KAID), KSPS (KSPS), OPB (KOPB), KWSU/Channel 10 & KTNW/Channel 31 (KWSU), WILL-TV (WILL), Network Knowledge - WSEC/Springfield (WSEC), WTTW11 (WTTW), Iowa Public Television/IPTV (KDIN), Nine Network (KETC), PBS39 Fort Wayne (WFWA), WFYI Indianapolis (WFYI), Milwaukee Public Television (WMVS), WNIN (WNIN), WNIT Public Television (WNIT), WPT (WPNE), WVUT/Channel 22 (WVUT), WEIU/Channel 51 (WEIU), WQPT-TV (WQPT), WYCC PBS Chicago (WYCC), WIPB-TV (WIPB), WTIU (WTIU), CET  (WCET), ThinkTVNetwork (WPTD), WBGU-TV (WBGU), WGVU TV (WGVU), NET1 (KUON), Pioneer Public Television (KWCM), SDPB Television (KUSD), TPT (KTCA), KSMQ (KSMQ), KPTS/Channel 8 (KPTS), KTWU/Channel 11 (KTWU), East Tennessee PBS (WSJK), WCTE-TV (WCTE), WLJT, Channel 11 (WLJT), WOSU TV (WOSU), WOUB/WOUC (WOUB), WVPB (WVPB), WKYU-PBS (WKYU), KERA 13 (KERA), MPBN (WCBB), Mountain Lake PBS (WCFE), NHPTV (WENH), Vermont PBS (WETK), witf (WITF), WQED Multimedia (WQED), WMHT Educational Telecommunications (WMHT), Q-TV (WDCQ), WTVS Detroit Public TV (WTVS), CMU Public Television (WCMU), WKAR-TV (WKAR), WNMU-TV Public TV 13 (WNMU), WDSE - WRPT (WDSE), WGTE TV (WGTE), Lakeland Public Television (KAWE), KMOS-TV - Channels 6.1, 6.2 and 6.3 (KMOS), MontanaPBS (KUSM), KRWG/Channel 22 (KRWG), KACV (KACV), KCOS/Channel 13 (KCOS), WCNY/Channel 24 (WCNY), WNED (WNED), WPBS (WPBS), WSKG Public TV (WSKG), WXXI (WXXI), WPSU (WPSU), WVIA Public Media Studios (WVIA), WTVI (WTVI), Western Reserve PBS (WNEO), WVIZ/PBS ideastream (WVIZ), KCTS 9 (KCTS), Basin PBS (KPBT), KUHT / Channel 8 (KUHT), KLRN (KLRN), KLRU (KLRU), WTJX Channel 12 (WTJX), WCVE PBS (WCVE), KBTC Public Television (KBTC)'
    age_limit = 10
    _RETURN_TYPE = 'any'


class PearVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pearvideo'
    IE_NAME = 'PearVideo'
    _VALID_URL = 'https?://(?:www\\.)?pearvideo\\.com/video_(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class PeekVidsBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.peekvids'
    IE_NAME = 'PeekVidsBase'


class PeekVidsIE(PeekVidsBaseIE):
    _module = 'yt_dlp.extractor.peekvids'
    IE_NAME = 'PeekVids'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?(?P<domain>peekvids\\.com)/\n        (?:(?:[^/?#]+/){2}|embed/?\\?(?:[^#]*&)?v=)\n        (?P<id>[^/?&#]*)\n    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class PlayVidsIE(PeekVidsBaseIE):
    _module = 'yt_dlp.extractor.peekvids'
    IE_NAME = 'PlayVids'
    _VALID_URL = 'https?://(?:www\\.)?(?P<domain>playvids\\.com)/(?:embed/|\\w\\w?/)?(?P<id>[^/?#]*)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PeerTubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.peertube'
    IE_NAME = 'PeerTube'
    _VALID_URL = '(?x)\n                    (?:\n                        peertube:(?P<host>[^:]+):|\n                        https?://(?P<host_2>(?:\n                            # Taken from https://instances.joinpeertube.org/instances\n                            40two\\.tube|\n                            a\\.metube\\.ch|\n                            advtv\\.ml|\n                            algorithmic\\.tv|\n                            alimulama\\.com|\n                            arcana\\.fun|\n                            archive\\.vidicon\\.org|\n                            artefac-paris\\.tv|\n                            auf1\\.eu|\n                            battlepenguin\\.video|\n                            beertube\\.epgn\\.ch|\n                            befree\\.nohost\\.me|\n                            bideoak\\.argia\\.eus|\n                            birkeundnymphe\\.de|\n                            bitcointv\\.com|\n                            cattube\\.org|\n                            clap\\.nerv-project\\.eu|\n                            climatejustice\\.video|\n                            comf\\.tube|\n                            conspiracydistillery\\.com|\n                            darkvapor\\.nohost\\.me|\n                            daschauher\\.aksel\\.rocks|\n                            digitalcourage\\.video|\n                            dreiecksnebel\\.alex-detsch\\.de|\n                            eduvid\\.org|\n                            evangelisch\\.video|\n                            exo\\.tube|\n                            fair\\.tube|\n                            fediverse\\.tv|\n                            film\\.k-prod\\.fr|\n                            flim\\.txmn\\.tk|\n                            fotogramas\\.politicaconciencia\\.org|\n                            ftsi\\.ru|\n                            gary\\.vger\\.cloud|\n                            graeber\\.video|\n                            greatview\\.video|\n                            grypstube\\.uni-greifswald\\.de|\n                            highvoltage\\.tv|\n                            hpstube\\.fr|\n                            htp\\.live|\n                            hyperreal\\.tube|\n                            juggling\\.digital|\n                            kino\\.kompot\\.si|\n                            kino\\.schuerz\\.at|\n                            kinowolnosc\\.pl|\n                            kirche\\.peertube-host\\.de|\n                            kodcast\\.com|\n                            kolektiva\\.media|\n                            kraut\\.zone|\n                            kumi\\.tube|\n                            lastbreach\\.tv|\n                            lepetitmayennais\\.fr\\.nf|\n                            lexx\\.impa\\.me|\n                            libertynode\\.tv|\n                            libra\\.syntazia\\.org|\n                            libremedia\\.video|\n                            live\\.libratoi\\.org|\n                            live\\.nanao\\.moe|\n                            live\\.toobnix\\.org|\n                            livegram\\.net|\n                            lolitube\\.freedomchan\\.moe|\n                            lucarne\\.balsamine\\.be|\n                            maindreieck-tv\\.de|\n                            mani\\.tube|\n                            manicphase\\.me|\n                            media\\.fsfe\\.org|\n                            media\\.gzevd\\.de|\n                            media\\.inno3\\.cricket|\n                            media\\.kaitaia\\.life|\n                            media\\.krashboyz\\.org|\n                            media\\.over-world\\.org|\n                            media\\.skewed\\.de|\n                            media\\.undeadnetwork\\.de|\n                            medias\\.pingbase\\.net|\n                            melsungen\\.peertube-host\\.de|\n                            mirametube\\.fr|\n                            mojotube\\.net|\n                            monplaisirtube\\.ddns\\.net|\n                            mountaintown\\.video|\n                            my\\.bunny\\.cafe|\n                            myfreetube\\.de|\n                            mytube\\.kn-cloud\\.de|\n                            mytube\\.madzel\\.de|\n                            myworkoutarenapeertube\\.cf|\n                            nanawel-peertube\\.dyndns\\.org|\n                            nastub\\.cz|\n                            offenes\\.tv|\n                            orgdup\\.media|\n                            ovaltube\\.codinglab\\.ch|\n                            p2ptv\\.ru|\n                            p\\.eertu\\.be|\n                            p\\.lu|\n                            peer\\.azurs\\.fr|\n                            peertube1\\.zeteo\\.me|\n                            peertube\\.020\\.pl|\n                            peertube\\.0x5e\\.eu|\n                            peertube\\.alpharius\\.io|\n                            peertube\\.am-networks\\.fr|\n                            peertube\\.anduin\\.net|\n                            peertube\\.anzui\\.dev|\n                            peertube\\.arbleizez\\.bzh|\n                            peertube\\.art3mis\\.de|\n                            peertube\\.atilla\\.org|\n                            peertube\\.atsuchan\\.page|\n                            peertube\\.aukfood\\.net|\n                            peertube\\.aventer\\.biz|\n                            peertube\\.b38\\.rural-it\\.org|\n                            peertube\\.beeldengeluid\\.nl|\n                            peertube\\.be|\n                            peertube\\.bgzashtita\\.es|\n                            peertube\\.bitsandlinux\\.com|\n                            peertube\\.biz|\n                            peertube\\.boba\\.best|\n                            peertube\\.br0\\.fr|\n                            peertube\\.bridaahost\\.ynh\\.fr|\n                            peertube\\.bubbletea\\.dev|\n                            peertube\\.bubuit\\.net|\n                            peertube\\.cabaal\\.net|\n                            peertube\\.cats-home\\.net|\n                            peertube\\.chemnitz\\.freifunk\\.net|\n                            peertube\\.chevro\\.fr|\n                            peertube\\.chrisspiegl\\.com|\n                            peertube\\.chtisurel\\.net|\n                            peertube\\.cipherbliss\\.com|\n                            peertube\\.cloud\\.sans\\.pub|\n                            peertube\\.cpge-brizeux\\.fr|\n                            peertube\\.ctseuro\\.com|\n                            peertube\\.cuatrolibertades\\.org|\n                            peertube\\.cybercirujas\\.club|\n                            peertube\\.cythin\\.com|\n                            peertube\\.davigge\\.com|\n                            peertube\\.dc\\.pini\\.fr|\n                            peertube\\.debian\\.social|\n                            peertube\\.demonix\\.fr|\n                            peertube\\.designersethiques\\.org|\n                            peertube\\.desmu\\.fr|\n                            peertube\\.devloprog\\.org|\n                            peertube\\.devol\\.it|\n                            peertube\\.dtmf\\.ca|\n                            peertube\\.ecologie\\.bzh|\n                            peertube\\.eu\\.org|\n                            peertube\\.european-pirates\\.eu|\n                            peertube\\.euskarabildua\\.eus|\n                            peertube\\.fenarinarsa\\.com|\n                            peertube\\.fomin\\.site|\n                            peertube\\.forsud\\.be|\n                            peertube\\.francoispelletier\\.org|\n                            peertube\\.freenet\\.ru|\n                            peertube\\.freetalklive\\.com|\n                            peertube\\.functional\\.cafe|\n                            peertube\\.gardeludwig\\.fr|\n                            peertube\\.gargantia\\.fr|\n                            peertube\\.gcfamily\\.fr|\n                            peertube\\.genma\\.fr|\n                            peertube\\.get-racing\\.de|\n                            peertube\\.gidikroon\\.eu|\n                            peertube\\.gruezishop\\.ch|\n                            peertube\\.habets\\.house|\n                            peertube\\.hackerfraternity\\.org|\n                            peertube\\.ichigo\\.everydayimshuflin\\.com|\n                            peertube\\.ignifi\\.me|\n                            peertube\\.inapurna\\.org|\n                            peertube\\.informaction\\.info|\n                            peertube\\.interhop\\.org|\n                            peertube\\.iselfhost\\.com|\n                            peertube\\.it|\n                            peertube\\.jensdiemer\\.de|\n                            peertube\\.joffreyverd\\.fr|\n                            peertube\\.kalua\\.im|\n                            peertube\\.kathryl\\.fr|\n                            peertube\\.keazilla\\.net|\n                            peertube\\.klaewyss\\.fr|\n                            peertube\\.kodcast\\.com|\n                            peertube\\.kx\\.studio|\n                            peertube\\.lagvoid\\.com|\n                            peertube\\.lavallee\\.tech|\n                            peertube\\.le5emeaxe\\.fr|\n                            peertube\\.lestutosdeprocessus\\.fr|\n                            peertube\\.librenet\\.co\\.za|\n                            peertube\\.logilab\\.fr|\n                            peertube\\.louisematic\\.site|\n                            peertube\\.luckow\\.org|\n                            peertube\\.luga\\.at|\n                            peertube\\.lyceeconnecte\\.fr|\n                            peertube\\.manalejandro\\.com|\n                            peertube\\.marud\\.fr|\n                            peertube\\.mattone\\.net|\n                            peertube\\.maxweiss\\.io|\n                            peertube\\.monlycee\\.net|\n                            peertube\\.mxinfo\\.fr|\n                            peertube\\.myrasp\\.eu|\n                            peertube\\.nebelcloud\\.de|\n                            peertube\\.netzbegruenung\\.de|\n                            peertube\\.newsocial\\.tech|\n                            peertube\\.nicolastissot\\.fr|\n                            peertube\\.nz|\n                            peertube\\.offerman\\.com|\n                            peertube\\.opencloud\\.lu|\n                            peertube\\.orthus\\.link|\n                            peertube\\.patapouf\\.xyz|\n                            peertube\\.pi2\\.dev|\n                            peertube\\.plataformess\\.org|\n                            peertube\\.pl|\n                            peertube\\.portaesgnos\\.org|\n                            peertube\\.r2\\.enst\\.fr|\n                            peertube\\.r5c3\\.fr|\n                            peertube\\.radres\\.xyz|\n                            peertube\\.red|\n                            peertube\\.robonomics\\.network|\n                            peertube\\.rtnkv\\.cloud|\n                            peertube\\.runfox\\.tk|\n                            peertube\\.satoshishop\\.de|\n                            peertube\\.scic-tetris\\.org|\n                            peertube\\.securitymadein\\.lu|\n                            peertube\\.semweb\\.pro|\n                            peertube\\.social\\.my-wan\\.de|\n                            peertube\\.soykaf\\.org|\n                            peertube\\.stefofficiel\\.me|\n                            peertube\\.stream|\n                            peertube\\.su|\n                            peertube\\.swrs\\.net|\n                            peertube\\.takeko\\.cyou|\n                            peertube\\.tangentfox\\.com|\n                            peertube\\.taxinachtegel\\.de|\n                            peertube\\.thenewoil\\.xyz|\n                            peertube\\.ti-fr\\.com|\n                            peertube\\.tiennot\\.net|\n                            peertube\\.troback\\.com|\n                            peertube\\.tspu\\.edu\\.ru|\n                            peertube\\.tux\\.ovh|\n                            peertube\\.tv|\n                            peertube\\.tweb\\.tv|\n                            peertube\\.ucy\\.de|\n                            peertube\\.underworld\\.fr|\n                            peertube\\.us\\.to|\n                            peertube\\.ventresmous\\.fr|\n                            peertube\\.vlaki\\.cz|\n                            peertube\\.w\\.utnw\\.de|\n                            peertube\\.westring\\.digital|\n                            peertube\\.xwiki\\.com|\n                            peertube\\.zoz-serv\\.org|\n                            peervideo\\.ru|\n                            periscope\\.numenaute\\.org|\n                            perron-tube\\.de|\n                            petitlutinartube\\.fr|\n                            phijkchu\\.com|\n                            pierre\\.tube|\n                            piraten\\.space|\n                            play\\.rosano\\.ca|\n                            player\\.ojamajo\\.moe|\n                            plextube\\.nl|\n                            pocketnetpeertube1\\.nohost\\.me|\n                            pocketnetpeertube3\\.nohost\\.me|\n                            pocketnetpeertube4\\.nohost\\.me|\n                            pocketnetpeertube5\\.nohost\\.me|\n                            pocketnetpeertube6\\.nohost\\.me|\n                            pt\\.24-7\\.ro|\n                            pt\\.apathy\\.top|\n                            pt\\.diaspodon\\.fr|\n                            pt\\.fedi\\.tech|\n                            pt\\.maciej\\.website|\n                            ptb\\.lunarviews\\.net|\n                            ptmir1\\.inter21\\.net|\n                            ptmir2\\.inter21\\.net|\n                            ptmir3\\.inter21\\.net|\n                            ptmir4\\.inter21\\.net|\n                            ptmir5\\.inter21\\.net|\n                            ptube\\.horsentiers\\.fr|\n                            ptube\\.xmanifesto\\.club|\n                            queermotion\\.org|\n                            re-wizja\\.re-medium\\.com|\n                            regarder\\.sans\\.pub|\n                            ruraletv\\.ovh|\n                            s1\\.gegenstimme\\.tv|\n                            s2\\.veezee\\.tube|\n                            sdmtube\\.fr|\n                            sender-fm\\.veezee\\.tube|\n                            serv1\\.wiki-tube\\.de|\n                            serv3\\.wiki-tube\\.de|\n                            sickstream\\.net|\n                            sleepy\\.tube|\n                            sovran\\.video|\n                            spectra\\.video|\n                            stream\\.elven\\.pw|\n                            stream\\.k-prod\\.fr|\n                            stream\\.shahab\\.nohost\\.me|\n                            streamsource\\.video|\n                            studios\\.racer159\\.com|\n                            testtube\\.florimond\\.eu|\n                            tgi\\.hosted\\.spacebear\\.ee|\n                            thaitube\\.in\\.th|\n                            the\\.jokertv\\.eu|\n                            theater\\.ethernia\\.net|\n                            thecool\\.tube|\n                            tilvids\\.com|\n                            toob\\.bub\\.org|\n                            tpaw\\.video|\n                            truetube\\.media|\n                            tuba\\.lhub\\.pl|\n                            tube-aix-marseille\\.beta\\.education\\.fr|\n                            tube-amiens\\.beta\\.education\\.fr|\n                            tube-besancon\\.beta\\.education\\.fr|\n                            tube-bordeaux\\.beta\\.education\\.fr|\n                            tube-clermont-ferrand\\.beta\\.education\\.fr|\n                            tube-corse\\.beta\\.education\\.fr|\n                            tube-creteil\\.beta\\.education\\.fr|\n                            tube-dijon\\.beta\\.education\\.fr|\n                            tube-education\\.beta\\.education\\.fr|\n                            tube-grenoble\\.beta\\.education\\.fr|\n                            tube-lille\\.beta\\.education\\.fr|\n                            tube-limoges\\.beta\\.education\\.fr|\n                            tube-montpellier\\.beta\\.education\\.fr|\n                            tube-nancy\\.beta\\.education\\.fr|\n                            tube-nantes\\.beta\\.education\\.fr|\n                            tube-nice\\.beta\\.education\\.fr|\n                            tube-normandie\\.beta\\.education\\.fr|\n                            tube-orleans-tours\\.beta\\.education\\.fr|\n                            tube-outremer\\.beta\\.education\\.fr|\n                            tube-paris\\.beta\\.education\\.fr|\n                            tube-poitiers\\.beta\\.education\\.fr|\n                            tube-reims\\.beta\\.education\\.fr|\n                            tube-rennes\\.beta\\.education\\.fr|\n                            tube-strasbourg\\.beta\\.education\\.fr|\n                            tube-toulouse\\.beta\\.education\\.fr|\n                            tube-versailles\\.beta\\.education\\.fr|\n                            tube1\\.it\\.tuwien\\.ac\\.at|\n                            tube\\.abolivier\\.bzh|\n                            tube\\.ac-amiens\\.fr|\n                            tube\\.aerztefueraufklaerung\\.de|\n                            tube\\.alexx\\.ml|\n                            tube\\.amic37\\.fr|\n                            tube\\.anufrij\\.de|\n                            tube\\.apolut\\.net|\n                            tube\\.arkhalabs\\.io|\n                            tube\\.arthack\\.nz|\n                            tube\\.as211696\\.net|\n                            tube\\.avensio\\.de|\n                            tube\\.azbyka\\.ru|\n                            tube\\.azkware\\.net|\n                            tube\\.bachaner\\.fr|\n                            tube\\.bmesh\\.org|\n                            tube\\.borked\\.host|\n                            tube\\.bstly\\.de|\n                            tube\\.chaoszone\\.tv|\n                            tube\\.chatelet\\.ovh|\n                            tube\\.cloud-libre\\.eu|\n                            tube\\.cms\\.garden|\n                            tube\\.cowfee\\.moe|\n                            tube\\.cryptography\\.dog|\n                            tube\\.darknight-coffee\\.org|\n                            tube\\.dev\\.lhub\\.pl|\n                            tube\\.distrilab\\.fr|\n                            tube\\.dsocialize\\.net|\n                            tube\\.ebin\\.club|\n                            tube\\.fdn\\.fr|\n                            tube\\.florimond\\.eu|\n                            tube\\.foxarmy\\.ml|\n                            tube\\.foxden\\.party|\n                            tube\\.frischesicht\\.de|\n                            tube\\.futuretic\\.fr|\n                            tube\\.gnous\\.eu|\n                            tube\\.grap\\.coop|\n                            tube\\.graz\\.social|\n                            tube\\.grin\\.hu|\n                            tube\\.hackerscop\\.org|\n                            tube\\.hordearii\\.fr|\n                            tube\\.jeena\\.net|\n                            tube\\.kai-stuht\\.com|\n                            tube\\.kockatoo\\.org|\n                            tube\\.kotur\\.org|\n                            tube\\.lacaveatonton\\.ovh|\n                            tube\\.linkse\\.media|\n                            tube\\.lokad\\.com|\n                            tube\\.lucie-philou\\.com|\n                            tube\\.melonbread\\.xyz|\n                            tube\\.mfraters\\.net|\n                            tube\\.motuhake\\.xyz|\n                            tube\\.mrbesen\\.de|\n                            tube\\.nah\\.re|\n                            tube\\.nchoco\\.net|\n                            tube\\.novg\\.net|\n                            tube\\.nox-rhea\\.org|\n                            tube\\.nuagelibre\\.fr|\n                            tube\\.nx12\\.net|\n                            tube\\.octaplex\\.net|\n                            tube\\.odat\\.xyz|\n                            tube\\.oisux\\.org|\n                            tube\\.opportunis\\.me|\n                            tube\\.org\\.il|\n                            tube\\.ortion\\.xyz|\n                            tube\\.others\\.social|\n                            tube\\.picasoft\\.net|\n                            tube\\.plomlompom\\.com|\n                            tube\\.pmj\\.rocks|\n                            tube\\.portes-imaginaire\\.org|\n                            tube\\.pyngu\\.com|\n                            tube\\.rebellion\\.global|\n                            tube\\.rhythms-of-resistance\\.org|\n                            tube\\.rita\\.moe|\n                            tube\\.rsi\\.cnr\\.it|\n                            tube\\.s1gm4\\.eu|\n                            tube\\.saumon\\.io|\n                            tube\\.schleuss\\.online|\n                            tube\\.schule\\.social|\n                            tube\\.seditio\\.fr|\n                            tube\\.shanti\\.cafe|\n                            tube\\.shela\\.nu|\n                            tube\\.skrep\\.in|\n                            tube\\.sp-codes\\.de|\n                            tube\\.sp4ke\\.com|\n                            tube\\.superseriousbusiness\\.org|\n                            tube\\.systest\\.eu|\n                            tube\\.tappret\\.fr|\n                            tube\\.tardis\\.world|\n                            tube\\.toontoet\\.nl|\n                            tube\\.tpshd\\.de|\n                            tube\\.troopers\\.agency|\n                            tube\\.tylerdavis\\.xyz|\n                            tube\\.undernet\\.uy|\n                            tube\\.vigilian-consulting\\.nl|\n                            tube\\.vraphim\\.com|\n                            tube\\.wehost\\.lgbt|\n                            tube\\.wien\\.rocks|\n                            tube\\.wolfe\\.casa|\n                            tube\\.xd0\\.de|\n                            tube\\.xy-space\\.de|\n                            tube\\.yapbreak\\.fr|\n                            tubedu\\.org|\n                            tubes\\.jodh\\.us|\n                            tuktube\\.com|\n                            turkum\\.me|\n                            tututu\\.tube|\n                            tuvideo\\.encanarias\\.info|\n                            tv1\\.cocu\\.cc|\n                            tv1\\.gomntu\\.space|\n                            tv2\\.cocu\\.cc|\n                            tv\\.adn\\.life|\n                            tv\\.atmx\\.ca|\n                            tv\\.bitma\\.st|\n                            tv\\.generallyrubbish\\.net\\.au|\n                            tv\\.lumbung\\.space|\n                            tv\\.mattchristiansenmedia\\.com|\n                            tv\\.netwhood\\.online|\n                            tv\\.neue\\.city|\n                            tv\\.piejacker\\.net|\n                            tv\\.pirateradio\\.social|\n                            tv\\.undersco\\.re|\n                            tvox\\.ru|\n                            twctube\\.twc-zone\\.eu|\n                            unfilter\\.tube|\n                            v\\.basspistol\\.org|\n                            v\\.kisombrella\\.top|\n                            v\\.lastorder\\.xyz|\n                            v\\.lor\\.sh|\n                            v\\.phreedom\\.club|\n                            v\\.sil\\.sh|\n                            v\\.szy\\.io|\n                            v\\.xxxapex\\.com|\n                            veezee\\.tube|\n                            vid\\.dascoyote\\.xyz|\n                            vid\\.garwood\\.io|\n                            vid\\.ncrypt\\.at|\n                            vid\\.pravdastalina\\.info|\n                            vid\\.qorg11\\.net|\n                            vid\\.rajeshtaylor\\.com|\n                            vid\\.samtripoli\\.com|\n                            vid\\.werefox\\.dev|\n                            vid\\.wildeboer\\.net|\n                            video-cave-v2\\.de|\n                            video\\.076\\.ne\\.jp|\n                            video\\.1146\\.nohost\\.me|\n                            video\\.altertek\\.org|\n                            video\\.anartist\\.org|\n                            video\\.apps\\.thedoodleproject\\.net|\n                            video\\.artist\\.cx|\n                            video\\.asgardius\\.company|\n                            video\\.balsillie\\.net|\n                            video\\.bards\\.online|\n                            video\\.binarydad\\.com|\n                            video\\.blast-info\\.fr|\n                            video\\.catgirl\\.biz|\n                            video\\.cigliola\\.com|\n                            video\\.cm-en-transition\\.fr|\n                            video\\.cnt\\.social|\n                            video\\.coales\\.co|\n                            video\\.codingfield\\.com|\n                            video\\.comptoir\\.net|\n                            video\\.comune\\.trento\\.it|\n                            video\\.cpn\\.so|\n                            video\\.csc49\\.fr|\n                            video\\.cybre\\.town|\n                            video\\.demokratischer-sommer\\.de|\n                            video\\.discord-insoumis\\.fr|\n                            video\\.dolphincastle\\.com|\n                            video\\.dresden\\.network|\n                            video\\.ecole-89\\.com|\n                            video\\.elgrillolibertario\\.org|\n                            video\\.emergeheart\\.info|\n                            video\\.eradicatinglove\\.xyz|\n                            video\\.ethantheenigma\\.me|\n                            video\\.exodus-privacy\\.eu\\.org|\n                            video\\.fbxl\\.net|\n                            video\\.fhtagn\\.org|\n                            video\\.greenmycity\\.eu|\n                            video\\.guerredeclasse\\.fr|\n                            video\\.gyt\\.is|\n                            video\\.hackers\\.town|\n                            video\\.hardlimit\\.com|\n                            video\\.hooli\\.co|\n                            video\\.igem\\.org|\n                            video\\.internet-czas-dzialac\\.pl|\n                            video\\.islameye\\.com|\n                            video\\.kicik\\.fr|\n                            video\\.kuba-orlik\\.name|\n                            video\\.kyushojitsu\\.ca|\n                            video\\.lavolte\\.net|\n                            video\\.lespoesiesdheloise\\.fr|\n                            video\\.liberta\\.vip|\n                            video\\.liege\\.bike|\n                            video\\.linc\\.systems|\n                            video\\.linux\\.it|\n                            video\\.linuxtrent\\.it|\n                            video\\.lokal\\.social|\n                            video\\.lono\\.space|\n                            video\\.lunasqu\\.ee|\n                            video\\.lundi\\.am|\n                            video\\.marcorennmaus\\.de|\n                            video\\.mass-trespass\\.uk|\n                            video\\.mugoreve\\.fr|\n                            video\\.mundodesconocido\\.com|\n                            video\\.mycrowd\\.ca|\n                            video\\.nogafam\\.es|\n                            video\\.odayacres\\.farm|\n                            video\\.ozgurkon\\.org|\n                            video\\.p1ng0ut\\.social|\n                            video\\.p3x\\.de|\n                            video\\.pcf\\.fr|\n                            video\\.pony\\.gallery|\n                            video\\.potate\\.space|\n                            video\\.pourpenser\\.pro|\n                            video\\.progressiv\\.dev|\n                            video\\.resolutions\\.it|\n                            video\\.rw501\\.de|\n                            video\\.screamer\\.wiki|\n                            video\\.sdm-tools\\.net|\n                            video\\.sftblw\\.moe|\n                            video\\.shitposter\\.club|\n                            video\\.skyn3t\\.in|\n                            video\\.soi\\.ch|\n                            video\\.stuartbrand\\.co\\.uk|\n                            video\\.thinkof\\.name|\n                            video\\.toot\\.pt|\n                            video\\.triplea\\.fr|\n                            video\\.turbo\\.chat|\n                            video\\.vaku\\.org\\.ua|\n                            video\\.veloma\\.org|\n                            video\\.violoncello\\.ch|\n                            video\\.wilkie\\.how|\n                            video\\.wsf2021\\.info|\n                            videorelay\\.co|\n                            videos-passages\\.huma-num\\.fr|\n                            videos\\.3d-wolf\\.com|\n                            videos\\.ahp-numerique\\.fr|\n                            videos\\.alexandrebadalo\\.pt|\n                            videos\\.archigny\\.net|\n                            videos\\.benjaminbrady\\.ie|\n                            videos\\.buceoluegoexisto\\.com|\n                            videos\\.capas\\.se|\n                            videos\\.casually\\.cat|\n                            videos\\.cloudron\\.io|\n                            videos\\.coletivos\\.org|\n                            videos\\.danksquad\\.org|\n                            videos\\.denshi\\.live|\n                            videos\\.fromouter\\.space|\n                            videos\\.fsci\\.in|\n                            videos\\.globenet\\.org|\n                            videos\\.hauspie\\.fr|\n                            videos\\.hush\\.is|\n                            videos\\.john-livingston\\.fr|\n                            videos\\.jordanwarne\\.xyz|\n                            videos\\.lavoixdessansvoix\\.org|\n                            videos\\.leslionsfloorball\\.fr|\n                            videos\\.lucero\\.top|\n                            videos\\.martyn\\.berlin|\n                            videos\\.mastodont\\.cat|\n                            videos\\.monstro1\\.com|\n                            videos\\.npo\\.city|\n                            videos\\.optoutpod\\.com|\n                            videos\\.petch\\.rocks|\n                            videos\\.pzelawski\\.xyz|\n                            videos\\.rampin\\.org|\n                            videos\\.scanlines\\.xyz|\n                            videos\\.shmalls\\.pw|\n                            videos\\.sibear\\.fr|\n                            videos\\.stadtfabrikanten\\.org|\n                            videos\\.tankernn\\.eu|\n                            videos\\.testimonia\\.org|\n                            videos\\.thisishowidontdisappear\\.com|\n                            videos\\.traumaheilung\\.net|\n                            videos\\.trom\\.tf|\n                            videos\\.wakkerewereld\\.nu|\n                            videos\\.weblib\\.re|\n                            videos\\.yesil\\.club|\n                            vids\\.roshless\\.me|\n                            vids\\.tekdmn\\.me|\n                            vidz\\.dou\\.bet|\n                            vod\\.lumikko\\.dev|\n                            vs\\.uniter\\.network|\n                            vulgarisation-informatique\\.fr|\n                            watch\\.breadtube\\.tv|\n                            watch\\.deranalyst\\.ch|\n                            watch\\.ignorance\\.eu|\n                            watch\\.krazy\\.party|\n                            watch\\.libertaria\\.space|\n                            watch\\.rt4mn\\.org|\n                            watch\\.softinio\\.com|\n                            watch\\.tubelab\\.video|\n                            web-fellow\\.de|\n                            webtv\\.vandoeuvre\\.net|\n                            wechill\\.space|\n                            wikileaks\\.video|\n                            wiwi\\.video|\n                            worldofvids\\.com|\n                            wwtube\\.net|\n                            www4\\.mir\\.inter21\\.net|\n                            www\\.birkeundnymphe\\.de|\n                            www\\.captain-german\\.com|\n                            www\\.wiki-tube\\.de|\n                            xxivproduction\\.video|\n                            xxx\\.noho\\.st|\n\n                            # from youtube-dl\n                            peertube\\.rainbowswingers\\.net|\n                            tube\\.stanisic\\.nl|\n                            peer\\.suiri\\.us|\n                            medias\\.libox\\.fr|\n                            videomensoif\\.ynh\\.fr|\n                            peertube\\.travelpandas\\.eu|\n                            peertube\\.rachetjay\\.fr|\n                            peertube\\.montecsys\\.fr|\n                            tube\\.eskuero\\.me|\n                            peer\\.tube|\n                            peertube\\.umeahackerspace\\.se|\n                            tube\\.nx-pod\\.de|\n                            video\\.monsieurbidouille\\.fr|\n                            tube\\.openalgeria\\.org|\n                            vid\\.lelux\\.fi|\n                            video\\.anormallostpod\\.ovh|\n                            tube\\.crapaud-fou\\.org|\n                            peertube\\.stemy\\.me|\n                            lostpod\\.space|\n                            exode\\.me|\n                            peertube\\.snargol\\.com|\n                            vis\\.ion\\.ovh|\n                            videosdulib\\.re|\n                            v\\.mbius\\.io|\n                            videos\\.judrey\\.eu|\n                            peertube\\.osureplayviewer\\.xyz|\n                            peertube\\.mathieufamily\\.ovh|\n                            www\\.videos-libr\\.es|\n                            fightforinfo\\.com|\n                            peertube\\.fediverse\\.ru|\n                            peertube\\.oiseauroch\\.fr|\n                            video\\.nesven\\.eu|\n                            v\\.bearvideo\\.win|\n                            video\\.qoto\\.org|\n                            justporn\\.cc|\n                            video\\.vny\\.fr|\n                            peervideo\\.club|\n                            tube\\.taker\\.fr|\n                            peertube\\.chantierlibre\\.org|\n                            tube\\.ipfixe\\.info|\n                            tube\\.kicou\\.info|\n                            tube\\.dodsorf\\.as|\n                            videobit\\.cc|\n                            video\\.yukari\\.moe|\n                            videos\\.elbinario\\.net|\n                            hkvideo\\.live|\n                            pt\\.tux\\.tf|\n                            www\\.hkvideo\\.live|\n                            FIGHTFORINFO\\.com|\n                            pt\\.765racing\\.com|\n                            peertube\\.gnumeria\\.eu\\.org|\n                            nordenmedia\\.com|\n                            peertube\\.co\\.uk|\n                            tube\\.darfweb\\.eu|\n                            tube\\.kalah-france\\.org|\n                            0ch\\.in|\n                            vod\\.mochi\\.academy|\n                            film\\.node9\\.org|\n                            peertube\\.hatthieves\\.es|\n                            video\\.fitchfamily\\.org|\n                            peertube\\.ddns\\.net|\n                            video\\.ifuncle\\.kr|\n                            video\\.fdlibre\\.eu|\n                            tube\\.22decembre\\.eu|\n                            peertube\\.harmoniescreatives\\.com|\n                            tube\\.fabrigli\\.fr|\n                            video\\.thedwyers\\.co|\n                            video\\.bruitbruit\\.com|\n                            peertube\\.foxfam\\.club|\n                            peer\\.philoxweb\\.be|\n                            videos\\.bugs\\.social|\n                            peertube\\.malbert\\.xyz|\n                            peertube\\.bilange\\.ca|\n                            libretube\\.net|\n                            diytelevision\\.com|\n                            peertube\\.fedilab\\.app|\n                            libre\\.video|\n                            video\\.mstddntfdn\\.online|\n                            us\\.tv|\n                            peertube\\.sl-network\\.fr|\n                            peertube\\.dynlinux\\.io|\n                            peertube\\.david\\.durieux\\.family|\n                            peertube\\.linuxrocks\\.online|\n                            peerwatch\\.xyz|\n                            v\\.kretschmann\\.social|\n                            tube\\.otter\\.sh|\n                            yt\\.is\\.nota\\.live|\n                            tube\\.dragonpsi\\.xyz|\n                            peertube\\.boneheadmedia\\.com|\n                            videos\\.funkwhale\\.audio|\n                            watch\\.44con\\.com|\n                            peertube\\.gcaillaut\\.fr|\n                            peertube\\.icu|\n                            pony\\.tube|\n                            spacepub\\.space|\n                            tube\\.stbr\\.io|\n                            v\\.mom-gay\\.faith|\n                            tube\\.port0\\.xyz|\n                            peertube\\.simounet\\.net|\n                            play\\.jergefelt\\.se|\n                            peertube\\.zeteo\\.me|\n                            tube\\.danq\\.me|\n                            peertube\\.kerenon\\.com|\n                            tube\\.fab-l3\\.org|\n                            tube\\.calculate\\.social|\n                            peertube\\.mckillop\\.org|\n                            tube\\.netzspielplatz\\.de|\n                            vod\\.ksite\\.de|\n                            peertube\\.laas\\.fr|\n                            tube\\.govital\\.net|\n                            peertube\\.stephenson\\.cc|\n                            bistule\\.nohost\\.me|\n                            peertube\\.kajalinifi\\.de|\n                            video\\.ploud\\.jp|\n                            video\\.omniatv\\.com|\n                            peertube\\.ffs2play\\.fr|\n                            peertube\\.leboulaire\\.ovh|\n                            peertube\\.tronic-studio\\.com|\n                            peertube\\.public\\.cat|\n                            peertube\\.metalbanana\\.net|\n                            video\\.1000i100\\.fr|\n                            peertube\\.alter-nativ-voll\\.de|\n                            tube\\.pasa\\.tf|\n                            tube\\.worldofhauru\\.xyz|\n                            pt\\.kamp\\.site|\n                            peertube\\.teleassist\\.fr|\n                            videos\\.mleduc\\.xyz|\n                            conf\\.tube|\n                            media\\.privacyinternational\\.org|\n                            pt\\.forty-two\\.nl|\n                            video\\.halle-leaks\\.de|\n                            video\\.grosskopfgames\\.de|\n                            peertube\\.schaeferit\\.de|\n                            peertube\\.jackbot\\.fr|\n                            tube\\.extinctionrebellion\\.fr|\n                            peertube\\.f-si\\.org|\n                            video\\.subak\\.ovh|\n                            videos\\.koweb\\.fr|\n                            peertube\\.zergy\\.net|\n                            peertube\\.roflcopter\\.fr|\n                            peertube\\.floss-marketing-school\\.com|\n                            vloggers\\.social|\n                            peertube\\.iriseden\\.eu|\n                            videos\\.ubuntu-paris\\.org|\n                            peertube\\.mastodon\\.host|\n                            armstube\\.com|\n                            peertube\\.s2s\\.video|\n                            peertube\\.lol|\n                            tube\\.open-plug\\.eu|\n                            open\\.tube|\n                            peertube\\.ch|\n                            peertube\\.normandie-libre\\.fr|\n                            peertube\\.slat\\.org|\n                            video\\.lacaveatonton\\.ovh|\n                            peertube\\.uno|\n                            peertube\\.servebeer\\.com|\n                            peertube\\.fedi\\.quebec|\n                            tube\\.h3z\\.jp|\n                            tube\\.plus200\\.com|\n                            peertube\\.eric\\.ovh|\n                            tube\\.metadocs\\.cc|\n                            tube\\.unmondemeilleur\\.eu|\n                            gouttedeau\\.space|\n                            video\\.antirep\\.net|\n                            nrop\\.cant\\.at|\n                            tube\\.ksl-bmx\\.de|\n                            tube\\.plaf\\.fr|\n                            tube\\.tchncs\\.de|\n                            video\\.devinberg\\.com|\n                            hitchtube\\.fr|\n                            peertube\\.kosebamse\\.com|\n                            yunopeertube\\.myddns\\.me|\n                            peertube\\.varney\\.fr|\n                            peertube\\.anon-kenkai\\.com|\n                            tube\\.maiti\\.info|\n                            tubee\\.fr|\n                            videos\\.dinofly\\.com|\n                            toobnix\\.org|\n                            videotape\\.me|\n                            voca\\.tube|\n                            video\\.heromuster\\.com|\n                            video\\.lemediatv\\.fr|\n                            video\\.up\\.edu\\.ph|\n                            balafon\\.video|\n                            video\\.ivel\\.fr|\n                            thickrips\\.cloud|\n                            pt\\.laurentkruger\\.fr|\n                            video\\.monarch-pass\\.net|\n                            peertube\\.artica\\.center|\n                            video\\.alternanet\\.fr|\n                            indymotion\\.fr|\n                            fanvid\\.stopthatimp\\.net|\n                            video\\.farci\\.org|\n                            v\\.lesterpig\\.com|\n                            video\\.okaris\\.de|\n                            tube\\.pawelko\\.net|\n                            peertube\\.mablr\\.org|\n                            tube\\.fede\\.re|\n                            pytu\\.be|\n                            evertron\\.tv|\n                            devtube\\.dev-wiki\\.de|\n                            raptube\\.antipub\\.org|\n                            video\\.selea\\.se|\n                            peertube\\.mygaia\\.org|\n                            video\\.oh14\\.de|\n                            peertube\\.livingutopia\\.org|\n                            peertube\\.the-penguin\\.de|\n                            tube\\.thechangebook\\.org|\n                            tube\\.anjara\\.eu|\n                            pt\\.pube\\.tk|\n                            video\\.samedi\\.pm|\n                            mplayer\\.demouliere\\.eu|\n                            widemus\\.de|\n                            peertube\\.me|\n                            peertube\\.zapashcanon\\.fr|\n                            video\\.latavernedejohnjohn\\.fr|\n                            peertube\\.pcservice46\\.fr|\n                            peertube\\.mazzonetto\\.eu|\n                            video\\.irem\\.univ-paris-diderot\\.fr|\n                            video\\.livecchi\\.cloud|\n                            alttube\\.fr|\n                            video\\.coop\\.tools|\n                            video\\.cabane-libre\\.org|\n                            peertube\\.openstreetmap\\.fr|\n                            videos\\.alolise\\.org|\n                            irrsinn\\.video|\n                            video\\.antopie\\.org|\n                            scitech\\.video|\n                            tube2\\.nemsia\\.org|\n                            video\\.amic37\\.fr|\n                            peertube\\.freeforge\\.eu|\n                            video\\.arbitrarion\\.com|\n                            video\\.datsemultimedia\\.com|\n                            stoptrackingus\\.tv|\n                            peertube\\.ricostrongxxx\\.com|\n                            docker\\.videos\\.lecygnenoir\\.info|\n                            peertube\\.togart\\.de|\n                            tube\\.postblue\\.info|\n                            videos\\.domainepublic\\.net|\n                            peertube\\.cyber-tribal\\.com|\n                            video\\.gresille\\.org|\n                            peertube\\.dsmouse\\.net|\n                            cinema\\.yunohost\\.support|\n                            tube\\.theocevaer\\.fr|\n                            repro\\.video|\n                            tube\\.4aem\\.com|\n                            quaziinc\\.com|\n                            peertube\\.metawurst\\.space|\n                            videos\\.wakapo\\.com|\n                            video\\.ploud\\.fr|\n                            video\\.freeradical\\.zone|\n                            tube\\.valinor\\.fr|\n                            refuznik\\.video|\n                            pt\\.kircheneuenburg\\.de|\n                            peertube\\.asrun\\.eu|\n                            peertube\\.lagob\\.fr|\n                            videos\\.side-ways\\.net|\n                            91video\\.online|\n                            video\\.valme\\.io|\n                            video\\.taboulisme\\.com|\n                            videos-libr\\.es|\n                            tv\\.mooh\\.fr|\n                            nuage\\.acostey\\.fr|\n                            video\\.monsieur-a\\.fr|\n                            peertube\\.librelois\\.fr|\n                            videos\\.pair2jeux\\.tube|\n                            videos\\.pueseso\\.club|\n                            peer\\.mathdacloud\\.ovh|\n                            media\\.assassinate-you\\.net|\n                            vidcommons\\.org|\n                            ptube\\.rousset\\.nom\\.fr|\n                            tube\\.cyano\\.at|\n                            videos\\.squat\\.net|\n                            video\\.iphodase\\.fr|\n                            peertube\\.makotoworkshop\\.org|\n                            peertube\\.serveur\\.slv-valbonne\\.fr|\n                            vault\\.mle\\.party|\n                            hostyour\\.tv|\n                            videos\\.hack2g2\\.fr|\n                            libre\\.tube|\n                            pire\\.artisanlogiciel\\.net|\n                            videos\\.numerique-en-commun\\.fr|\n                            video\\.netsyms\\.com|\n                            video\\.die-partei\\.social|\n                            video\\.writeas\\.org|\n                            peertube\\.swarm\\.solvingmaz\\.es|\n                            tube\\.pericoloso\\.ovh|\n                            watching\\.cypherpunk\\.observer|\n                            videos\\.adhocmusic\\.com|\n                            tube\\.rfc1149\\.net|\n                            peertube\\.librelabucm\\.org|\n                            videos\\.numericoop\\.fr|\n                            peertube\\.koehn\\.com|\n                            peertube\\.anarchmusicall\\.net|\n                            tube\\.kampftoast\\.de|\n                            vid\\.y-y\\.li|\n                            peertube\\.xtenz\\.xyz|\n                            diode\\.zone|\n                            tube\\.egf\\.mn|\n                            peertube\\.nomagic\\.uk|\n                            visionon\\.tv|\n                            videos\\.koumoul\\.com|\n                            video\\.rastapuls\\.com|\n                            video\\.mantlepro\\.com|\n                            video\\.deadsuperhero\\.com|\n                            peertube\\.musicstudio\\.pro|\n                            peertube\\.we-keys\\.fr|\n                            artitube\\.artifaille\\.fr|\n                            peertube\\.ethernia\\.net|\n                            tube\\.midov\\.pl|\n                            peertube\\.fr|\n                            watch\\.snoot\\.tube|\n                            peertube\\.donnadieu\\.fr|\n                            argos\\.aquilenet\\.fr|\n                            tube\\.nemsia\\.org|\n                            tube\\.bruniau\\.net|\n                            videos\\.darckoune\\.moe|\n                            tube\\.traydent\\.info|\n                            dev\\.videos\\.lecygnenoir\\.info|\n                            peertube\\.nayya\\.org|\n                            peertube\\.live|\n                            peertube\\.mofgao\\.space|\n                            video\\.lequerrec\\.eu|\n                            peertube\\.amicale\\.net|\n                            aperi\\.tube|\n                            tube\\.ac-lyon\\.fr|\n                            video\\.lw1\\.at|\n                            www\\.yiny\\.org|\n                            videos\\.pofilo\\.fr|\n                            tube\\.lou\\.lt|\n                            choob\\.h\\.etbus\\.ch|\n                            tube\\.hoga\\.fr|\n                            peertube\\.heberge\\.fr|\n                            video\\.obermui\\.de|\n                            videos\\.cloudfrancois\\.fr|\n                            betamax\\.video|\n                            video\\.typica\\.us|\n                            tube\\.piweb\\.be|\n                            video\\.blender\\.org|\n                            peertube\\.cat|\n                            tube\\.kdy\\.ch|\n                            pe\\.ertu\\.be|\n                            peertube\\.social|\n                            videos\\.lescommuns\\.org|\n                            tv\\.datamol\\.org|\n                            videonaute\\.fr|\n                            dialup\\.express|\n                            peertube\\.nogafa\\.org|\n                            megatube\\.lilomoino\\.fr|\n                            peertube\\.tamanoir\\.foucry\\.net|\n                            peertube\\.devosi\\.org|\n                            peertube\\.1312\\.media|\n                            tube\\.bootlicker\\.party|\n                            skeptikon\\.fr|\n                            video\\.blueline\\.mg|\n                            tube\\.homecomputing\\.fr|\n                            tube\\.ouahpiti\\.info|\n                            video\\.tedomum\\.net|\n                            video\\.g3l\\.org|\n                            fontube\\.fr|\n                            peertube\\.gaialabs\\.ch|\n                            tube\\.kher\\.nl|\n                            peertube\\.qtg\\.fr|\n                            video\\.migennes\\.net|\n                            tube\\.p2p\\.legal|\n                            troll\\.tv|\n                            videos\\.iut-orsay\\.fr|\n                            peertube\\.solidev\\.net|\n                            videos\\.cemea\\.org|\n                            video\\.passageenseine\\.fr|\n                            videos\\.festivalparminous\\.org|\n                            peertube\\.touhoppai\\.moe|\n                            sikke\\.fi|\n                            peer\\.hostux\\.social|\n                            share\\.tube|\n                            peertube\\.walkingmountains\\.fr|\n                            videos\\.benpro\\.fr|\n                            peertube\\.parleur\\.net|\n                            peertube\\.heraut\\.eu|\n                            tube\\.aquilenet\\.fr|\n                            peertube\\.gegeweb\\.eu|\n                            framatube\\.org|\n                            thinkerview\\.video|\n                            tube\\.conferences-gesticulees\\.net|\n                            peertube\\.datagueule\\.tv|\n                            video\\.lqdn\\.fr|\n                            tube\\.mochi\\.academy|\n                            media\\.zat\\.im|\n                            video\\.colibris-outilslibres\\.org|\n                            tube\\.svnet\\.fr|\n                            peertube\\.video|\n                            peertube2\\.cpy\\.re|\n                            peertube3\\.cpy\\.re|\n                            videos\\.tcit\\.fr|\n                            peertube\\.cpy\\.re|\n                            canard\\.tube\n                        ))/(?:videos/(?:watch|embed)|api/v\\d/videos|w)/\n                    )\n                    (?P<id>[\\da-zA-Z]{22}|[\\da-fA-F]{8}-[\\da-fA-F]{4}-[\\da-fA-F]{4}-[\\da-fA-F]{4}-[\\da-fA-F]{12})\n                    '
    _RETURN_TYPE = 'video'


class PeerTubePlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.peertube'
    IE_NAME = 'PeerTube:Playlist'
    _VALID_URL = '(?x)\n                        https?://(?P<host>(?:\n                            # Taken from https://instances.joinpeertube.org/instances\n                            40two\\.tube|\n                            a\\.metube\\.ch|\n                            advtv\\.ml|\n                            algorithmic\\.tv|\n                            alimulama\\.com|\n                            arcana\\.fun|\n                            archive\\.vidicon\\.org|\n                            artefac-paris\\.tv|\n                            auf1\\.eu|\n                            battlepenguin\\.video|\n                            beertube\\.epgn\\.ch|\n                            befree\\.nohost\\.me|\n                            bideoak\\.argia\\.eus|\n                            birkeundnymphe\\.de|\n                            bitcointv\\.com|\n                            cattube\\.org|\n                            clap\\.nerv-project\\.eu|\n                            climatejustice\\.video|\n                            comf\\.tube|\n                            conspiracydistillery\\.com|\n                            darkvapor\\.nohost\\.me|\n                            daschauher\\.aksel\\.rocks|\n                            digitalcourage\\.video|\n                            dreiecksnebel\\.alex-detsch\\.de|\n                            eduvid\\.org|\n                            evangelisch\\.video|\n                            exo\\.tube|\n                            fair\\.tube|\n                            fediverse\\.tv|\n                            film\\.k-prod\\.fr|\n                            flim\\.txmn\\.tk|\n                            fotogramas\\.politicaconciencia\\.org|\n                            ftsi\\.ru|\n                            gary\\.vger\\.cloud|\n                            graeber\\.video|\n                            greatview\\.video|\n                            grypstube\\.uni-greifswald\\.de|\n                            highvoltage\\.tv|\n                            hpstube\\.fr|\n                            htp\\.live|\n                            hyperreal\\.tube|\n                            juggling\\.digital|\n                            kino\\.kompot\\.si|\n                            kino\\.schuerz\\.at|\n                            kinowolnosc\\.pl|\n                            kirche\\.peertube-host\\.de|\n                            kodcast\\.com|\n                            kolektiva\\.media|\n                            kraut\\.zone|\n                            kumi\\.tube|\n                            lastbreach\\.tv|\n                            lepetitmayennais\\.fr\\.nf|\n                            lexx\\.impa\\.me|\n                            libertynode\\.tv|\n                            libra\\.syntazia\\.org|\n                            libremedia\\.video|\n                            live\\.libratoi\\.org|\n                            live\\.nanao\\.moe|\n                            live\\.toobnix\\.org|\n                            livegram\\.net|\n                            lolitube\\.freedomchan\\.moe|\n                            lucarne\\.balsamine\\.be|\n                            maindreieck-tv\\.de|\n                            mani\\.tube|\n                            manicphase\\.me|\n                            media\\.fsfe\\.org|\n                            media\\.gzevd\\.de|\n                            media\\.inno3\\.cricket|\n                            media\\.kaitaia\\.life|\n                            media\\.krashboyz\\.org|\n                            media\\.over-world\\.org|\n                            media\\.skewed\\.de|\n                            media\\.undeadnetwork\\.de|\n                            medias\\.pingbase\\.net|\n                            melsungen\\.peertube-host\\.de|\n                            mirametube\\.fr|\n                            mojotube\\.net|\n                            monplaisirtube\\.ddns\\.net|\n                            mountaintown\\.video|\n                            my\\.bunny\\.cafe|\n                            myfreetube\\.de|\n                            mytube\\.kn-cloud\\.de|\n                            mytube\\.madzel\\.de|\n                            myworkoutarenapeertube\\.cf|\n                            nanawel-peertube\\.dyndns\\.org|\n                            nastub\\.cz|\n                            offenes\\.tv|\n                            orgdup\\.media|\n                            ovaltube\\.codinglab\\.ch|\n                            p2ptv\\.ru|\n                            p\\.eertu\\.be|\n                            p\\.lu|\n                            peer\\.azurs\\.fr|\n                            peertube1\\.zeteo\\.me|\n                            peertube\\.020\\.pl|\n                            peertube\\.0x5e\\.eu|\n                            peertube\\.alpharius\\.io|\n                            peertube\\.am-networks\\.fr|\n                            peertube\\.anduin\\.net|\n                            peertube\\.anzui\\.dev|\n                            peertube\\.arbleizez\\.bzh|\n                            peertube\\.art3mis\\.de|\n                            peertube\\.atilla\\.org|\n                            peertube\\.atsuchan\\.page|\n                            peertube\\.aukfood\\.net|\n                            peertube\\.aventer\\.biz|\n                            peertube\\.b38\\.rural-it\\.org|\n                            peertube\\.beeldengeluid\\.nl|\n                            peertube\\.be|\n                            peertube\\.bgzashtita\\.es|\n                            peertube\\.bitsandlinux\\.com|\n                            peertube\\.biz|\n                            peertube\\.boba\\.best|\n                            peertube\\.br0\\.fr|\n                            peertube\\.bridaahost\\.ynh\\.fr|\n                            peertube\\.bubbletea\\.dev|\n                            peertube\\.bubuit\\.net|\n                            peertube\\.cabaal\\.net|\n                            peertube\\.cats-home\\.net|\n                            peertube\\.chemnitz\\.freifunk\\.net|\n                            peertube\\.chevro\\.fr|\n                            peertube\\.chrisspiegl\\.com|\n                            peertube\\.chtisurel\\.net|\n                            peertube\\.cipherbliss\\.com|\n                            peertube\\.cloud\\.sans\\.pub|\n                            peertube\\.cpge-brizeux\\.fr|\n                            peertube\\.ctseuro\\.com|\n                            peertube\\.cuatrolibertades\\.org|\n                            peertube\\.cybercirujas\\.club|\n                            peertube\\.cythin\\.com|\n                            peertube\\.davigge\\.com|\n                            peertube\\.dc\\.pini\\.fr|\n                            peertube\\.debian\\.social|\n                            peertube\\.demonix\\.fr|\n                            peertube\\.designersethiques\\.org|\n                            peertube\\.desmu\\.fr|\n                            peertube\\.devloprog\\.org|\n                            peertube\\.devol\\.it|\n                            peertube\\.dtmf\\.ca|\n                            peertube\\.ecologie\\.bzh|\n                            peertube\\.eu\\.org|\n                            peertube\\.european-pirates\\.eu|\n                            peertube\\.euskarabildua\\.eus|\n                            peertube\\.fenarinarsa\\.com|\n                            peertube\\.fomin\\.site|\n                            peertube\\.forsud\\.be|\n                            peertube\\.francoispelletier\\.org|\n                            peertube\\.freenet\\.ru|\n                            peertube\\.freetalklive\\.com|\n                            peertube\\.functional\\.cafe|\n                            peertube\\.gardeludwig\\.fr|\n                            peertube\\.gargantia\\.fr|\n                            peertube\\.gcfamily\\.fr|\n                            peertube\\.genma\\.fr|\n                            peertube\\.get-racing\\.de|\n                            peertube\\.gidikroon\\.eu|\n                            peertube\\.gruezishop\\.ch|\n                            peertube\\.habets\\.house|\n                            peertube\\.hackerfraternity\\.org|\n                            peertube\\.ichigo\\.everydayimshuflin\\.com|\n                            peertube\\.ignifi\\.me|\n                            peertube\\.inapurna\\.org|\n                            peertube\\.informaction\\.info|\n                            peertube\\.interhop\\.org|\n                            peertube\\.iselfhost\\.com|\n                            peertube\\.it|\n                            peertube\\.jensdiemer\\.de|\n                            peertube\\.joffreyverd\\.fr|\n                            peertube\\.kalua\\.im|\n                            peertube\\.kathryl\\.fr|\n                            peertube\\.keazilla\\.net|\n                            peertube\\.klaewyss\\.fr|\n                            peertube\\.kodcast\\.com|\n                            peertube\\.kx\\.studio|\n                            peertube\\.lagvoid\\.com|\n                            peertube\\.lavallee\\.tech|\n                            peertube\\.le5emeaxe\\.fr|\n                            peertube\\.lestutosdeprocessus\\.fr|\n                            peertube\\.librenet\\.co\\.za|\n                            peertube\\.logilab\\.fr|\n                            peertube\\.louisematic\\.site|\n                            peertube\\.luckow\\.org|\n                            peertube\\.luga\\.at|\n                            peertube\\.lyceeconnecte\\.fr|\n                            peertube\\.manalejandro\\.com|\n                            peertube\\.marud\\.fr|\n                            peertube\\.mattone\\.net|\n                            peertube\\.maxweiss\\.io|\n                            peertube\\.monlycee\\.net|\n                            peertube\\.mxinfo\\.fr|\n                            peertube\\.myrasp\\.eu|\n                            peertube\\.nebelcloud\\.de|\n                            peertube\\.netzbegruenung\\.de|\n                            peertube\\.newsocial\\.tech|\n                            peertube\\.nicolastissot\\.fr|\n                            peertube\\.nz|\n                            peertube\\.offerman\\.com|\n                            peertube\\.opencloud\\.lu|\n                            peertube\\.orthus\\.link|\n                            peertube\\.patapouf\\.xyz|\n                            peertube\\.pi2\\.dev|\n                            peertube\\.plataformess\\.org|\n                            peertube\\.pl|\n                            peertube\\.portaesgnos\\.org|\n                            peertube\\.r2\\.enst\\.fr|\n                            peertube\\.r5c3\\.fr|\n                            peertube\\.radres\\.xyz|\n                            peertube\\.red|\n                            peertube\\.robonomics\\.network|\n                            peertube\\.rtnkv\\.cloud|\n                            peertube\\.runfox\\.tk|\n                            peertube\\.satoshishop\\.de|\n                            peertube\\.scic-tetris\\.org|\n                            peertube\\.securitymadein\\.lu|\n                            peertube\\.semweb\\.pro|\n                            peertube\\.social\\.my-wan\\.de|\n                            peertube\\.soykaf\\.org|\n                            peertube\\.stefofficiel\\.me|\n                            peertube\\.stream|\n                            peertube\\.su|\n                            peertube\\.swrs\\.net|\n                            peertube\\.takeko\\.cyou|\n                            peertube\\.tangentfox\\.com|\n                            peertube\\.taxinachtegel\\.de|\n                            peertube\\.thenewoil\\.xyz|\n                            peertube\\.ti-fr\\.com|\n                            peertube\\.tiennot\\.net|\n                            peertube\\.troback\\.com|\n                            peertube\\.tspu\\.edu\\.ru|\n                            peertube\\.tux\\.ovh|\n                            peertube\\.tv|\n                            peertube\\.tweb\\.tv|\n                            peertube\\.ucy\\.de|\n                            peertube\\.underworld\\.fr|\n                            peertube\\.us\\.to|\n                            peertube\\.ventresmous\\.fr|\n                            peertube\\.vlaki\\.cz|\n                            peertube\\.w\\.utnw\\.de|\n                            peertube\\.westring\\.digital|\n                            peertube\\.xwiki\\.com|\n                            peertube\\.zoz-serv\\.org|\n                            peervideo\\.ru|\n                            periscope\\.numenaute\\.org|\n                            perron-tube\\.de|\n                            petitlutinartube\\.fr|\n                            phijkchu\\.com|\n                            pierre\\.tube|\n                            piraten\\.space|\n                            play\\.rosano\\.ca|\n                            player\\.ojamajo\\.moe|\n                            plextube\\.nl|\n                            pocketnetpeertube1\\.nohost\\.me|\n                            pocketnetpeertube3\\.nohost\\.me|\n                            pocketnetpeertube4\\.nohost\\.me|\n                            pocketnetpeertube5\\.nohost\\.me|\n                            pocketnetpeertube6\\.nohost\\.me|\n                            pt\\.24-7\\.ro|\n                            pt\\.apathy\\.top|\n                            pt\\.diaspodon\\.fr|\n                            pt\\.fedi\\.tech|\n                            pt\\.maciej\\.website|\n                            ptb\\.lunarviews\\.net|\n                            ptmir1\\.inter21\\.net|\n                            ptmir2\\.inter21\\.net|\n                            ptmir3\\.inter21\\.net|\n                            ptmir4\\.inter21\\.net|\n                            ptmir5\\.inter21\\.net|\n                            ptube\\.horsentiers\\.fr|\n                            ptube\\.xmanifesto\\.club|\n                            queermotion\\.org|\n                            re-wizja\\.re-medium\\.com|\n                            regarder\\.sans\\.pub|\n                            ruraletv\\.ovh|\n                            s1\\.gegenstimme\\.tv|\n                            s2\\.veezee\\.tube|\n                            sdmtube\\.fr|\n                            sender-fm\\.veezee\\.tube|\n                            serv1\\.wiki-tube\\.de|\n                            serv3\\.wiki-tube\\.de|\n                            sickstream\\.net|\n                            sleepy\\.tube|\n                            sovran\\.video|\n                            spectra\\.video|\n                            stream\\.elven\\.pw|\n                            stream\\.k-prod\\.fr|\n                            stream\\.shahab\\.nohost\\.me|\n                            streamsource\\.video|\n                            studios\\.racer159\\.com|\n                            testtube\\.florimond\\.eu|\n                            tgi\\.hosted\\.spacebear\\.ee|\n                            thaitube\\.in\\.th|\n                            the\\.jokertv\\.eu|\n                            theater\\.ethernia\\.net|\n                            thecool\\.tube|\n                            tilvids\\.com|\n                            toob\\.bub\\.org|\n                            tpaw\\.video|\n                            truetube\\.media|\n                            tuba\\.lhub\\.pl|\n                            tube-aix-marseille\\.beta\\.education\\.fr|\n                            tube-amiens\\.beta\\.education\\.fr|\n                            tube-besancon\\.beta\\.education\\.fr|\n                            tube-bordeaux\\.beta\\.education\\.fr|\n                            tube-clermont-ferrand\\.beta\\.education\\.fr|\n                            tube-corse\\.beta\\.education\\.fr|\n                            tube-creteil\\.beta\\.education\\.fr|\n                            tube-dijon\\.beta\\.education\\.fr|\n                            tube-education\\.beta\\.education\\.fr|\n                            tube-grenoble\\.beta\\.education\\.fr|\n                            tube-lille\\.beta\\.education\\.fr|\n                            tube-limoges\\.beta\\.education\\.fr|\n                            tube-montpellier\\.beta\\.education\\.fr|\n                            tube-nancy\\.beta\\.education\\.fr|\n                            tube-nantes\\.beta\\.education\\.fr|\n                            tube-nice\\.beta\\.education\\.fr|\n                            tube-normandie\\.beta\\.education\\.fr|\n                            tube-orleans-tours\\.beta\\.education\\.fr|\n                            tube-outremer\\.beta\\.education\\.fr|\n                            tube-paris\\.beta\\.education\\.fr|\n                            tube-poitiers\\.beta\\.education\\.fr|\n                            tube-reims\\.beta\\.education\\.fr|\n                            tube-rennes\\.beta\\.education\\.fr|\n                            tube-strasbourg\\.beta\\.education\\.fr|\n                            tube-toulouse\\.beta\\.education\\.fr|\n                            tube-versailles\\.beta\\.education\\.fr|\n                            tube1\\.it\\.tuwien\\.ac\\.at|\n                            tube\\.abolivier\\.bzh|\n                            tube\\.ac-amiens\\.fr|\n                            tube\\.aerztefueraufklaerung\\.de|\n                            tube\\.alexx\\.ml|\n                            tube\\.amic37\\.fr|\n                            tube\\.anufrij\\.de|\n                            tube\\.apolut\\.net|\n                            tube\\.arkhalabs\\.io|\n                            tube\\.arthack\\.nz|\n                            tube\\.as211696\\.net|\n                            tube\\.avensio\\.de|\n                            tube\\.azbyka\\.ru|\n                            tube\\.azkware\\.net|\n                            tube\\.bachaner\\.fr|\n                            tube\\.bmesh\\.org|\n                            tube\\.borked\\.host|\n                            tube\\.bstly\\.de|\n                            tube\\.chaoszone\\.tv|\n                            tube\\.chatelet\\.ovh|\n                            tube\\.cloud-libre\\.eu|\n                            tube\\.cms\\.garden|\n                            tube\\.cowfee\\.moe|\n                            tube\\.cryptography\\.dog|\n                            tube\\.darknight-coffee\\.org|\n                            tube\\.dev\\.lhub\\.pl|\n                            tube\\.distrilab\\.fr|\n                            tube\\.dsocialize\\.net|\n                            tube\\.ebin\\.club|\n                            tube\\.fdn\\.fr|\n                            tube\\.florimond\\.eu|\n                            tube\\.foxarmy\\.ml|\n                            tube\\.foxden\\.party|\n                            tube\\.frischesicht\\.de|\n                            tube\\.futuretic\\.fr|\n                            tube\\.gnous\\.eu|\n                            tube\\.grap\\.coop|\n                            tube\\.graz\\.social|\n                            tube\\.grin\\.hu|\n                            tube\\.hackerscop\\.org|\n                            tube\\.hordearii\\.fr|\n                            tube\\.jeena\\.net|\n                            tube\\.kai-stuht\\.com|\n                            tube\\.kockatoo\\.org|\n                            tube\\.kotur\\.org|\n                            tube\\.lacaveatonton\\.ovh|\n                            tube\\.linkse\\.media|\n                            tube\\.lokad\\.com|\n                            tube\\.lucie-philou\\.com|\n                            tube\\.melonbread\\.xyz|\n                            tube\\.mfraters\\.net|\n                            tube\\.motuhake\\.xyz|\n                            tube\\.mrbesen\\.de|\n                            tube\\.nah\\.re|\n                            tube\\.nchoco\\.net|\n                            tube\\.novg\\.net|\n                            tube\\.nox-rhea\\.org|\n                            tube\\.nuagelibre\\.fr|\n                            tube\\.nx12\\.net|\n                            tube\\.octaplex\\.net|\n                            tube\\.odat\\.xyz|\n                            tube\\.oisux\\.org|\n                            tube\\.opportunis\\.me|\n                            tube\\.org\\.il|\n                            tube\\.ortion\\.xyz|\n                            tube\\.others\\.social|\n                            tube\\.picasoft\\.net|\n                            tube\\.plomlompom\\.com|\n                            tube\\.pmj\\.rocks|\n                            tube\\.portes-imaginaire\\.org|\n                            tube\\.pyngu\\.com|\n                            tube\\.rebellion\\.global|\n                            tube\\.rhythms-of-resistance\\.org|\n                            tube\\.rita\\.moe|\n                            tube\\.rsi\\.cnr\\.it|\n                            tube\\.s1gm4\\.eu|\n                            tube\\.saumon\\.io|\n                            tube\\.schleuss\\.online|\n                            tube\\.schule\\.social|\n                            tube\\.seditio\\.fr|\n                            tube\\.shanti\\.cafe|\n                            tube\\.shela\\.nu|\n                            tube\\.skrep\\.in|\n                            tube\\.sp-codes\\.de|\n                            tube\\.sp4ke\\.com|\n                            tube\\.superseriousbusiness\\.org|\n                            tube\\.systest\\.eu|\n                            tube\\.tappret\\.fr|\n                            tube\\.tardis\\.world|\n                            tube\\.toontoet\\.nl|\n                            tube\\.tpshd\\.de|\n                            tube\\.troopers\\.agency|\n                            tube\\.tylerdavis\\.xyz|\n                            tube\\.undernet\\.uy|\n                            tube\\.vigilian-consulting\\.nl|\n                            tube\\.vraphim\\.com|\n                            tube\\.wehost\\.lgbt|\n                            tube\\.wien\\.rocks|\n                            tube\\.wolfe\\.casa|\n                            tube\\.xd0\\.de|\n                            tube\\.xy-space\\.de|\n                            tube\\.yapbreak\\.fr|\n                            tubedu\\.org|\n                            tubes\\.jodh\\.us|\n                            tuktube\\.com|\n                            turkum\\.me|\n                            tututu\\.tube|\n                            tuvideo\\.encanarias\\.info|\n                            tv1\\.cocu\\.cc|\n                            tv1\\.gomntu\\.space|\n                            tv2\\.cocu\\.cc|\n                            tv\\.adn\\.life|\n                            tv\\.atmx\\.ca|\n                            tv\\.bitma\\.st|\n                            tv\\.generallyrubbish\\.net\\.au|\n                            tv\\.lumbung\\.space|\n                            tv\\.mattchristiansenmedia\\.com|\n                            tv\\.netwhood\\.online|\n                            tv\\.neue\\.city|\n                            tv\\.piejacker\\.net|\n                            tv\\.pirateradio\\.social|\n                            tv\\.undersco\\.re|\n                            tvox\\.ru|\n                            twctube\\.twc-zone\\.eu|\n                            unfilter\\.tube|\n                            v\\.basspistol\\.org|\n                            v\\.kisombrella\\.top|\n                            v\\.lastorder\\.xyz|\n                            v\\.lor\\.sh|\n                            v\\.phreedom\\.club|\n                            v\\.sil\\.sh|\n                            v\\.szy\\.io|\n                            v\\.xxxapex\\.com|\n                            veezee\\.tube|\n                            vid\\.dascoyote\\.xyz|\n                            vid\\.garwood\\.io|\n                            vid\\.ncrypt\\.at|\n                            vid\\.pravdastalina\\.info|\n                            vid\\.qorg11\\.net|\n                            vid\\.rajeshtaylor\\.com|\n                            vid\\.samtripoli\\.com|\n                            vid\\.werefox\\.dev|\n                            vid\\.wildeboer\\.net|\n                            video-cave-v2\\.de|\n                            video\\.076\\.ne\\.jp|\n                            video\\.1146\\.nohost\\.me|\n                            video\\.altertek\\.org|\n                            video\\.anartist\\.org|\n                            video\\.apps\\.thedoodleproject\\.net|\n                            video\\.artist\\.cx|\n                            video\\.asgardius\\.company|\n                            video\\.balsillie\\.net|\n                            video\\.bards\\.online|\n                            video\\.binarydad\\.com|\n                            video\\.blast-info\\.fr|\n                            video\\.catgirl\\.biz|\n                            video\\.cigliola\\.com|\n                            video\\.cm-en-transition\\.fr|\n                            video\\.cnt\\.social|\n                            video\\.coales\\.co|\n                            video\\.codingfield\\.com|\n                            video\\.comptoir\\.net|\n                            video\\.comune\\.trento\\.it|\n                            video\\.cpn\\.so|\n                            video\\.csc49\\.fr|\n                            video\\.cybre\\.town|\n                            video\\.demokratischer-sommer\\.de|\n                            video\\.discord-insoumis\\.fr|\n                            video\\.dolphincastle\\.com|\n                            video\\.dresden\\.network|\n                            video\\.ecole-89\\.com|\n                            video\\.elgrillolibertario\\.org|\n                            video\\.emergeheart\\.info|\n                            video\\.eradicatinglove\\.xyz|\n                            video\\.ethantheenigma\\.me|\n                            video\\.exodus-privacy\\.eu\\.org|\n                            video\\.fbxl\\.net|\n                            video\\.fhtagn\\.org|\n                            video\\.greenmycity\\.eu|\n                            video\\.guerredeclasse\\.fr|\n                            video\\.gyt\\.is|\n                            video\\.hackers\\.town|\n                            video\\.hardlimit\\.com|\n                            video\\.hooli\\.co|\n                            video\\.igem\\.org|\n                            video\\.internet-czas-dzialac\\.pl|\n                            video\\.islameye\\.com|\n                            video\\.kicik\\.fr|\n                            video\\.kuba-orlik\\.name|\n                            video\\.kyushojitsu\\.ca|\n                            video\\.lavolte\\.net|\n                            video\\.lespoesiesdheloise\\.fr|\n                            video\\.liberta\\.vip|\n                            video\\.liege\\.bike|\n                            video\\.linc\\.systems|\n                            video\\.linux\\.it|\n                            video\\.linuxtrent\\.it|\n                            video\\.lokal\\.social|\n                            video\\.lono\\.space|\n                            video\\.lunasqu\\.ee|\n                            video\\.lundi\\.am|\n                            video\\.marcorennmaus\\.de|\n                            video\\.mass-trespass\\.uk|\n                            video\\.mugoreve\\.fr|\n                            video\\.mundodesconocido\\.com|\n                            video\\.mycrowd\\.ca|\n                            video\\.nogafam\\.es|\n                            video\\.odayacres\\.farm|\n                            video\\.ozgurkon\\.org|\n                            video\\.p1ng0ut\\.social|\n                            video\\.p3x\\.de|\n                            video\\.pcf\\.fr|\n                            video\\.pony\\.gallery|\n                            video\\.potate\\.space|\n                            video\\.pourpenser\\.pro|\n                            video\\.progressiv\\.dev|\n                            video\\.resolutions\\.it|\n                            video\\.rw501\\.de|\n                            video\\.screamer\\.wiki|\n                            video\\.sdm-tools\\.net|\n                            video\\.sftblw\\.moe|\n                            video\\.shitposter\\.club|\n                            video\\.skyn3t\\.in|\n                            video\\.soi\\.ch|\n                            video\\.stuartbrand\\.co\\.uk|\n                            video\\.thinkof\\.name|\n                            video\\.toot\\.pt|\n                            video\\.triplea\\.fr|\n                            video\\.turbo\\.chat|\n                            video\\.vaku\\.org\\.ua|\n                            video\\.veloma\\.org|\n                            video\\.violoncello\\.ch|\n                            video\\.wilkie\\.how|\n                            video\\.wsf2021\\.info|\n                            videorelay\\.co|\n                            videos-passages\\.huma-num\\.fr|\n                            videos\\.3d-wolf\\.com|\n                            videos\\.ahp-numerique\\.fr|\n                            videos\\.alexandrebadalo\\.pt|\n                            videos\\.archigny\\.net|\n                            videos\\.benjaminbrady\\.ie|\n                            videos\\.buceoluegoexisto\\.com|\n                            videos\\.capas\\.se|\n                            videos\\.casually\\.cat|\n                            videos\\.cloudron\\.io|\n                            videos\\.coletivos\\.org|\n                            videos\\.danksquad\\.org|\n                            videos\\.denshi\\.live|\n                            videos\\.fromouter\\.space|\n                            videos\\.fsci\\.in|\n                            videos\\.globenet\\.org|\n                            videos\\.hauspie\\.fr|\n                            videos\\.hush\\.is|\n                            videos\\.john-livingston\\.fr|\n                            videos\\.jordanwarne\\.xyz|\n                            videos\\.lavoixdessansvoix\\.org|\n                            videos\\.leslionsfloorball\\.fr|\n                            videos\\.lucero\\.top|\n                            videos\\.martyn\\.berlin|\n                            videos\\.mastodont\\.cat|\n                            videos\\.monstro1\\.com|\n                            videos\\.npo\\.city|\n                            videos\\.optoutpod\\.com|\n                            videos\\.petch\\.rocks|\n                            videos\\.pzelawski\\.xyz|\n                            videos\\.rampin\\.org|\n                            videos\\.scanlines\\.xyz|\n                            videos\\.shmalls\\.pw|\n                            videos\\.sibear\\.fr|\n                            videos\\.stadtfabrikanten\\.org|\n                            videos\\.tankernn\\.eu|\n                            videos\\.testimonia\\.org|\n                            videos\\.thisishowidontdisappear\\.com|\n                            videos\\.traumaheilung\\.net|\n                            videos\\.trom\\.tf|\n                            videos\\.wakkerewereld\\.nu|\n                            videos\\.weblib\\.re|\n                            videos\\.yesil\\.club|\n                            vids\\.roshless\\.me|\n                            vids\\.tekdmn\\.me|\n                            vidz\\.dou\\.bet|\n                            vod\\.lumikko\\.dev|\n                            vs\\.uniter\\.network|\n                            vulgarisation-informatique\\.fr|\n                            watch\\.breadtube\\.tv|\n                            watch\\.deranalyst\\.ch|\n                            watch\\.ignorance\\.eu|\n                            watch\\.krazy\\.party|\n                            watch\\.libertaria\\.space|\n                            watch\\.rt4mn\\.org|\n                            watch\\.softinio\\.com|\n                            watch\\.tubelab\\.video|\n                            web-fellow\\.de|\n                            webtv\\.vandoeuvre\\.net|\n                            wechill\\.space|\n                            wikileaks\\.video|\n                            wiwi\\.video|\n                            worldofvids\\.com|\n                            wwtube\\.net|\n                            www4\\.mir\\.inter21\\.net|\n                            www\\.birkeundnymphe\\.de|\n                            www\\.captain-german\\.com|\n                            www\\.wiki-tube\\.de|\n                            xxivproduction\\.video|\n                            xxx\\.noho\\.st|\n\n                            # from youtube-dl\n                            peertube\\.rainbowswingers\\.net|\n                            tube\\.stanisic\\.nl|\n                            peer\\.suiri\\.us|\n                            medias\\.libox\\.fr|\n                            videomensoif\\.ynh\\.fr|\n                            peertube\\.travelpandas\\.eu|\n                            peertube\\.rachetjay\\.fr|\n                            peertube\\.montecsys\\.fr|\n                            tube\\.eskuero\\.me|\n                            peer\\.tube|\n                            peertube\\.umeahackerspace\\.se|\n                            tube\\.nx-pod\\.de|\n                            video\\.monsieurbidouille\\.fr|\n                            tube\\.openalgeria\\.org|\n                            vid\\.lelux\\.fi|\n                            video\\.anormallostpod\\.ovh|\n                            tube\\.crapaud-fou\\.org|\n                            peertube\\.stemy\\.me|\n                            lostpod\\.space|\n                            exode\\.me|\n                            peertube\\.snargol\\.com|\n                            vis\\.ion\\.ovh|\n                            videosdulib\\.re|\n                            v\\.mbius\\.io|\n                            videos\\.judrey\\.eu|\n                            peertube\\.osureplayviewer\\.xyz|\n                            peertube\\.mathieufamily\\.ovh|\n                            www\\.videos-libr\\.es|\n                            fightforinfo\\.com|\n                            peertube\\.fediverse\\.ru|\n                            peertube\\.oiseauroch\\.fr|\n                            video\\.nesven\\.eu|\n                            v\\.bearvideo\\.win|\n                            video\\.qoto\\.org|\n                            justporn\\.cc|\n                            video\\.vny\\.fr|\n                            peervideo\\.club|\n                            tube\\.taker\\.fr|\n                            peertube\\.chantierlibre\\.org|\n                            tube\\.ipfixe\\.info|\n                            tube\\.kicou\\.info|\n                            tube\\.dodsorf\\.as|\n                            videobit\\.cc|\n                            video\\.yukari\\.moe|\n                            videos\\.elbinario\\.net|\n                            hkvideo\\.live|\n                            pt\\.tux\\.tf|\n                            www\\.hkvideo\\.live|\n                            FIGHTFORINFO\\.com|\n                            pt\\.765racing\\.com|\n                            peertube\\.gnumeria\\.eu\\.org|\n                            nordenmedia\\.com|\n                            peertube\\.co\\.uk|\n                            tube\\.darfweb\\.eu|\n                            tube\\.kalah-france\\.org|\n                            0ch\\.in|\n                            vod\\.mochi\\.academy|\n                            film\\.node9\\.org|\n                            peertube\\.hatthieves\\.es|\n                            video\\.fitchfamily\\.org|\n                            peertube\\.ddns\\.net|\n                            video\\.ifuncle\\.kr|\n                            video\\.fdlibre\\.eu|\n                            tube\\.22decembre\\.eu|\n                            peertube\\.harmoniescreatives\\.com|\n                            tube\\.fabrigli\\.fr|\n                            video\\.thedwyers\\.co|\n                            video\\.bruitbruit\\.com|\n                            peertube\\.foxfam\\.club|\n                            peer\\.philoxweb\\.be|\n                            videos\\.bugs\\.social|\n                            peertube\\.malbert\\.xyz|\n                            peertube\\.bilange\\.ca|\n                            libretube\\.net|\n                            diytelevision\\.com|\n                            peertube\\.fedilab\\.app|\n                            libre\\.video|\n                            video\\.mstddntfdn\\.online|\n                            us\\.tv|\n                            peertube\\.sl-network\\.fr|\n                            peertube\\.dynlinux\\.io|\n                            peertube\\.david\\.durieux\\.family|\n                            peertube\\.linuxrocks\\.online|\n                            peerwatch\\.xyz|\n                            v\\.kretschmann\\.social|\n                            tube\\.otter\\.sh|\n                            yt\\.is\\.nota\\.live|\n                            tube\\.dragonpsi\\.xyz|\n                            peertube\\.boneheadmedia\\.com|\n                            videos\\.funkwhale\\.audio|\n                            watch\\.44con\\.com|\n                            peertube\\.gcaillaut\\.fr|\n                            peertube\\.icu|\n                            pony\\.tube|\n                            spacepub\\.space|\n                            tube\\.stbr\\.io|\n                            v\\.mom-gay\\.faith|\n                            tube\\.port0\\.xyz|\n                            peertube\\.simounet\\.net|\n                            play\\.jergefelt\\.se|\n                            peertube\\.zeteo\\.me|\n                            tube\\.danq\\.me|\n                            peertube\\.kerenon\\.com|\n                            tube\\.fab-l3\\.org|\n                            tube\\.calculate\\.social|\n                            peertube\\.mckillop\\.org|\n                            tube\\.netzspielplatz\\.de|\n                            vod\\.ksite\\.de|\n                            peertube\\.laas\\.fr|\n                            tube\\.govital\\.net|\n                            peertube\\.stephenson\\.cc|\n                            bistule\\.nohost\\.me|\n                            peertube\\.kajalinifi\\.de|\n                            video\\.ploud\\.jp|\n                            video\\.omniatv\\.com|\n                            peertube\\.ffs2play\\.fr|\n                            peertube\\.leboulaire\\.ovh|\n                            peertube\\.tronic-studio\\.com|\n                            peertube\\.public\\.cat|\n                            peertube\\.metalbanana\\.net|\n                            video\\.1000i100\\.fr|\n                            peertube\\.alter-nativ-voll\\.de|\n                            tube\\.pasa\\.tf|\n                            tube\\.worldofhauru\\.xyz|\n                            pt\\.kamp\\.site|\n                            peertube\\.teleassist\\.fr|\n                            videos\\.mleduc\\.xyz|\n                            conf\\.tube|\n                            media\\.privacyinternational\\.org|\n                            pt\\.forty-two\\.nl|\n                            video\\.halle-leaks\\.de|\n                            video\\.grosskopfgames\\.de|\n                            peertube\\.schaeferit\\.de|\n                            peertube\\.jackbot\\.fr|\n                            tube\\.extinctionrebellion\\.fr|\n                            peertube\\.f-si\\.org|\n                            video\\.subak\\.ovh|\n                            videos\\.koweb\\.fr|\n                            peertube\\.zergy\\.net|\n                            peertube\\.roflcopter\\.fr|\n                            peertube\\.floss-marketing-school\\.com|\n                            vloggers\\.social|\n                            peertube\\.iriseden\\.eu|\n                            videos\\.ubuntu-paris\\.org|\n                            peertube\\.mastodon\\.host|\n                            armstube\\.com|\n                            peertube\\.s2s\\.video|\n                            peertube\\.lol|\n                            tube\\.open-plug\\.eu|\n                            open\\.tube|\n                            peertube\\.ch|\n                            peertube\\.normandie-libre\\.fr|\n                            peertube\\.slat\\.org|\n                            video\\.lacaveatonton\\.ovh|\n                            peertube\\.uno|\n                            peertube\\.servebeer\\.com|\n                            peertube\\.fedi\\.quebec|\n                            tube\\.h3z\\.jp|\n                            tube\\.plus200\\.com|\n                            peertube\\.eric\\.ovh|\n                            tube\\.metadocs\\.cc|\n                            tube\\.unmondemeilleur\\.eu|\n                            gouttedeau\\.space|\n                            video\\.antirep\\.net|\n                            nrop\\.cant\\.at|\n                            tube\\.ksl-bmx\\.de|\n                            tube\\.plaf\\.fr|\n                            tube\\.tchncs\\.de|\n                            video\\.devinberg\\.com|\n                            hitchtube\\.fr|\n                            peertube\\.kosebamse\\.com|\n                            yunopeertube\\.myddns\\.me|\n                            peertube\\.varney\\.fr|\n                            peertube\\.anon-kenkai\\.com|\n                            tube\\.maiti\\.info|\n                            tubee\\.fr|\n                            videos\\.dinofly\\.com|\n                            toobnix\\.org|\n                            videotape\\.me|\n                            voca\\.tube|\n                            video\\.heromuster\\.com|\n                            video\\.lemediatv\\.fr|\n                            video\\.up\\.edu\\.ph|\n                            balafon\\.video|\n                            video\\.ivel\\.fr|\n                            thickrips\\.cloud|\n                            pt\\.laurentkruger\\.fr|\n                            video\\.monarch-pass\\.net|\n                            peertube\\.artica\\.center|\n                            video\\.alternanet\\.fr|\n                            indymotion\\.fr|\n                            fanvid\\.stopthatimp\\.net|\n                            video\\.farci\\.org|\n                            v\\.lesterpig\\.com|\n                            video\\.okaris\\.de|\n                            tube\\.pawelko\\.net|\n                            peertube\\.mablr\\.org|\n                            tube\\.fede\\.re|\n                            pytu\\.be|\n                            evertron\\.tv|\n                            devtube\\.dev-wiki\\.de|\n                            raptube\\.antipub\\.org|\n                            video\\.selea\\.se|\n                            peertube\\.mygaia\\.org|\n                            video\\.oh14\\.de|\n                            peertube\\.livingutopia\\.org|\n                            peertube\\.the-penguin\\.de|\n                            tube\\.thechangebook\\.org|\n                            tube\\.anjara\\.eu|\n                            pt\\.pube\\.tk|\n                            video\\.samedi\\.pm|\n                            mplayer\\.demouliere\\.eu|\n                            widemus\\.de|\n                            peertube\\.me|\n                            peertube\\.zapashcanon\\.fr|\n                            video\\.latavernedejohnjohn\\.fr|\n                            peertube\\.pcservice46\\.fr|\n                            peertube\\.mazzonetto\\.eu|\n                            video\\.irem\\.univ-paris-diderot\\.fr|\n                            video\\.livecchi\\.cloud|\n                            alttube\\.fr|\n                            video\\.coop\\.tools|\n                            video\\.cabane-libre\\.org|\n                            peertube\\.openstreetmap\\.fr|\n                            videos\\.alolise\\.org|\n                            irrsinn\\.video|\n                            video\\.antopie\\.org|\n                            scitech\\.video|\n                            tube2\\.nemsia\\.org|\n                            video\\.amic37\\.fr|\n                            peertube\\.freeforge\\.eu|\n                            video\\.arbitrarion\\.com|\n                            video\\.datsemultimedia\\.com|\n                            stoptrackingus\\.tv|\n                            peertube\\.ricostrongxxx\\.com|\n                            docker\\.videos\\.lecygnenoir\\.info|\n                            peertube\\.togart\\.de|\n                            tube\\.postblue\\.info|\n                            videos\\.domainepublic\\.net|\n                            peertube\\.cyber-tribal\\.com|\n                            video\\.gresille\\.org|\n                            peertube\\.dsmouse\\.net|\n                            cinema\\.yunohost\\.support|\n                            tube\\.theocevaer\\.fr|\n                            repro\\.video|\n                            tube\\.4aem\\.com|\n                            quaziinc\\.com|\n                            peertube\\.metawurst\\.space|\n                            videos\\.wakapo\\.com|\n                            video\\.ploud\\.fr|\n                            video\\.freeradical\\.zone|\n                            tube\\.valinor\\.fr|\n                            refuznik\\.video|\n                            pt\\.kircheneuenburg\\.de|\n                            peertube\\.asrun\\.eu|\n                            peertube\\.lagob\\.fr|\n                            videos\\.side-ways\\.net|\n                            91video\\.online|\n                            video\\.valme\\.io|\n                            video\\.taboulisme\\.com|\n                            videos-libr\\.es|\n                            tv\\.mooh\\.fr|\n                            nuage\\.acostey\\.fr|\n                            video\\.monsieur-a\\.fr|\n                            peertube\\.librelois\\.fr|\n                            videos\\.pair2jeux\\.tube|\n                            videos\\.pueseso\\.club|\n                            peer\\.mathdacloud\\.ovh|\n                            media\\.assassinate-you\\.net|\n                            vidcommons\\.org|\n                            ptube\\.rousset\\.nom\\.fr|\n                            tube\\.cyano\\.at|\n                            videos\\.squat\\.net|\n                            video\\.iphodase\\.fr|\n                            peertube\\.makotoworkshop\\.org|\n                            peertube\\.serveur\\.slv-valbonne\\.fr|\n                            vault\\.mle\\.party|\n                            hostyour\\.tv|\n                            videos\\.hack2g2\\.fr|\n                            libre\\.tube|\n                            pire\\.artisanlogiciel\\.net|\n                            videos\\.numerique-en-commun\\.fr|\n                            video\\.netsyms\\.com|\n                            video\\.die-partei\\.social|\n                            video\\.writeas\\.org|\n                            peertube\\.swarm\\.solvingmaz\\.es|\n                            tube\\.pericoloso\\.ovh|\n                            watching\\.cypherpunk\\.observer|\n                            videos\\.adhocmusic\\.com|\n                            tube\\.rfc1149\\.net|\n                            peertube\\.librelabucm\\.org|\n                            videos\\.numericoop\\.fr|\n                            peertube\\.koehn\\.com|\n                            peertube\\.anarchmusicall\\.net|\n                            tube\\.kampftoast\\.de|\n                            vid\\.y-y\\.li|\n                            peertube\\.xtenz\\.xyz|\n                            diode\\.zone|\n                            tube\\.egf\\.mn|\n                            peertube\\.nomagic\\.uk|\n                            visionon\\.tv|\n                            videos\\.koumoul\\.com|\n                            video\\.rastapuls\\.com|\n                            video\\.mantlepro\\.com|\n                            video\\.deadsuperhero\\.com|\n                            peertube\\.musicstudio\\.pro|\n                            peertube\\.we-keys\\.fr|\n                            artitube\\.artifaille\\.fr|\n                            peertube\\.ethernia\\.net|\n                            tube\\.midov\\.pl|\n                            peertube\\.fr|\n                            watch\\.snoot\\.tube|\n                            peertube\\.donnadieu\\.fr|\n                            argos\\.aquilenet\\.fr|\n                            tube\\.nemsia\\.org|\n                            tube\\.bruniau\\.net|\n                            videos\\.darckoune\\.moe|\n                            tube\\.traydent\\.info|\n                            dev\\.videos\\.lecygnenoir\\.info|\n                            peertube\\.nayya\\.org|\n                            peertube\\.live|\n                            peertube\\.mofgao\\.space|\n                            video\\.lequerrec\\.eu|\n                            peertube\\.amicale\\.net|\n                            aperi\\.tube|\n                            tube\\.ac-lyon\\.fr|\n                            video\\.lw1\\.at|\n                            www\\.yiny\\.org|\n                            videos\\.pofilo\\.fr|\n                            tube\\.lou\\.lt|\n                            choob\\.h\\.etbus\\.ch|\n                            tube\\.hoga\\.fr|\n                            peertube\\.heberge\\.fr|\n                            video\\.obermui\\.de|\n                            videos\\.cloudfrancois\\.fr|\n                            betamax\\.video|\n                            video\\.typica\\.us|\n                            tube\\.piweb\\.be|\n                            video\\.blender\\.org|\n                            peertube\\.cat|\n                            tube\\.kdy\\.ch|\n                            pe\\.ertu\\.be|\n                            peertube\\.social|\n                            videos\\.lescommuns\\.org|\n                            tv\\.datamol\\.org|\n                            videonaute\\.fr|\n                            dialup\\.express|\n                            peertube\\.nogafa\\.org|\n                            megatube\\.lilomoino\\.fr|\n                            peertube\\.tamanoir\\.foucry\\.net|\n                            peertube\\.devosi\\.org|\n                            peertube\\.1312\\.media|\n                            tube\\.bootlicker\\.party|\n                            skeptikon\\.fr|\n                            video\\.blueline\\.mg|\n                            tube\\.homecomputing\\.fr|\n                            tube\\.ouahpiti\\.info|\n                            video\\.tedomum\\.net|\n                            video\\.g3l\\.org|\n                            fontube\\.fr|\n                            peertube\\.gaialabs\\.ch|\n                            tube\\.kher\\.nl|\n                            peertube\\.qtg\\.fr|\n                            video\\.migennes\\.net|\n                            tube\\.p2p\\.legal|\n                            troll\\.tv|\n                            videos\\.iut-orsay\\.fr|\n                            peertube\\.solidev\\.net|\n                            videos\\.cemea\\.org|\n                            video\\.passageenseine\\.fr|\n                            videos\\.festivalparminous\\.org|\n                            peertube\\.touhoppai\\.moe|\n                            sikke\\.fi|\n                            peer\\.hostux\\.social|\n                            share\\.tube|\n                            peertube\\.walkingmountains\\.fr|\n                            videos\\.benpro\\.fr|\n                            peertube\\.parleur\\.net|\n                            peertube\\.heraut\\.eu|\n                            tube\\.aquilenet\\.fr|\n                            peertube\\.gegeweb\\.eu|\n                            framatube\\.org|\n                            thinkerview\\.video|\n                            tube\\.conferences-gesticulees\\.net|\n                            peertube\\.datagueule\\.tv|\n                            video\\.lqdn\\.fr|\n                            tube\\.mochi\\.academy|\n                            media\\.zat\\.im|\n                            video\\.colibris-outilslibres\\.org|\n                            tube\\.svnet\\.fr|\n                            peertube\\.video|\n                            peertube2\\.cpy\\.re|\n                            peertube3\\.cpy\\.re|\n                            videos\\.tcit\\.fr|\n                            peertube\\.cpy\\.re|\n                            canard\\.tube\n                        ))/(?P<type>(?:a|c|w/p))/\n                    (?P<id>[^/]+)\n                    '
    _RETURN_TYPE = 'playlist'


class PeerTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.peertv'
    IE_NAME = 'peer.tv'
    _VALID_URL = 'https?://(?:www\\.)?peer\\.tv/(?:de|it|en)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class PelotonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.peloton'
    IE_NAME = 'peloton'
    _VALID_URL = 'https?://members\\.onepeloton\\.com/classes/player/(?P<id>[a-f0-9]+)'
    _NETRC_MACHINE = 'peloton'
    _RETURN_TYPE = 'video'


class PelotonLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.peloton'
    IE_NAME = 'peloton:live'
    _VALID_URL = 'https?://members\\.onepeloton\\.com/player/live/(?P<id>[a-f0-9]+)'
    IE_DESC = 'Peloton Live'
    _RETURN_TYPE = 'video'


class PeopleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.people'
    IE_NAME = 'People'
    _VALID_URL = 'https?://(?:www\\.)?people\\.com/people/videos/0,,(?P<id>\\d+),00\\.html'
    _RETURN_TYPE = 'video'


class PerformGroupIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.performgroup'
    IE_NAME = 'PerformGroup'
    _VALID_URL = 'https?://player\\.performgroup\\.com/eplayer(?:/eplayer\\.html|\\.js)#/?(?P<id>[0-9a-f]{26})\\.(?P<auth_token>[0-9a-z]{26})'
    _RETURN_TYPE = 'video'


class PeriscopeBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.periscope'
    IE_NAME = 'PeriscopeBase'


class PeriscopeIE(PeriscopeBaseIE):
    _module = 'yt_dlp.extractor.periscope'
    IE_NAME = 'periscope'
    _VALID_URL = 'https?://(?:www\\.)?(?:periscope|pscp)\\.tv/[^/]+/(?P<id>[^/?#]+)'
    IE_DESC = 'Periscope'
    _RETURN_TYPE = 'video'


class PeriscopeUserIE(PeriscopeBaseIE):
    _module = 'yt_dlp.extractor.periscope'
    IE_NAME = 'periscope:user'
    _VALID_URL = 'https?://(?:www\\.)?(?:periscope|pscp)\\.tv/(?P<id>[^/]+)/?$'
    IE_DESC = 'Periscope user videos'
    _RETURN_TYPE = 'playlist'


class PGATourIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pgatour'
    IE_NAME = 'PGATour'
    _VALID_URL = 'https?://(?:www\\.)?pgatour\\.com/video/[\\w-]+/(?P<tc>T)?(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class PhilharmonieDeParisIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.philharmoniedeparis'
    IE_NAME = 'PhilharmonieDeParis'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            live\\.philharmoniedeparis\\.fr/(?:[Cc]oncert/|embed(?:app)?/|misc/Playlist\\.ashx\\?id=)|\n                            pad\\.philharmoniedeparis\\.fr/(?:doc/CIMU/|player\\.aspx\\?id=)|\n                            philharmoniedeparis\\.fr/fr/live/concert/|\n                            otoplayer\\.philharmoniedeparis\\.fr/fr/embed/\n                        )\n                        (?P<id>\\d+)\n                    '
    IE_DESC = 'Philharmonie de Paris'
    _RETURN_TYPE = 'any'


class ZDFBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zdf'
    IE_NAME = 'ZDFBase'


class PhoenixIE(ZDFBaseIE):
    _module = 'yt_dlp.extractor.phoenix'
    IE_NAME = 'phoenix.de'
    _VALID_URL = 'https?://(?:www\\.)?phoenix\\.de/(?:[^/]+/)*[^/?#&]*-a-(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class PhotobucketIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.photobucket'
    IE_NAME = 'Photobucket'
    _VALID_URL = 'https?://(?:[a-z0-9]+\\.)?photobucket\\.com/.*(([\\?\\&]current=)|_)(?P<id>.*)\\.(?P<ext>(flv)|(mp4))'
    _RETURN_TYPE = 'video'


class PiaproIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.piapro'
    IE_NAME = 'Piapro'
    _VALID_URL = 'https?://piapro\\.jp/t/(?P<id>\\w+)/?'
    _NETRC_MACHINE = 'piapro'
    _RETURN_TYPE = 'video'


class PicartoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.picarto'
    IE_NAME = 'Picarto'
    _VALID_URL = 'https?://(?:www.)?picarto\\.tv/(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if PicartoVodIE.suitable(url) else super(PicartoIE, cls).suitable(url)


class PicartoVodIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.picarto'
    IE_NAME = 'PicartoVod'
    _VALID_URL = 'https?://(?:www.)?picarto\\.tv/videopopout/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class PikselIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.piksel'
    IE_NAME = 'Piksel'
    _VALID_URL = '(?x)https?://\n        (?:\n            (?:\n                player\\.\n                    (?:\n                        olympusattelecom|\n                        vibebyvista\n                    )|\n                (?:api|player)\\.multicastmedia|\n                (?:api-ovp|player)\\.piksel\n            )\\.com|\n            (?:\n                mz-edge\\.stream\\.co|\n                movie-s\\.nhk\\.or\n            )\\.jp|\n            vidego\\.baltimorecity\\.gov\n        )/v/(?:refid/(?P<refid>[^/]+)/prefid/)?(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class PinkbikeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pinkbike'
    IE_NAME = 'Pinkbike'
    _VALID_URL = 'https?://(?:(?:www\\.)?pinkbike\\.com/video/|es\\.pinkbike\\.org/i/kvid/kvid-y5\\.swf\\?id=)(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class PinterestBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pinterest'
    IE_NAME = 'PinterestBase'


class PinterestIE(PinterestBaseIE):
    _module = 'yt_dlp.extractor.pinterest'
    IE_NAME = 'Pinterest'
    _VALID_URL = '(?x)\n        https?://(?:[^/]+\\.)?pinterest\\.(?:\n            com|fr|de|ch|jp|cl|ca|it|co\\.uk|nz|ru|com\\.au|at|pt|co\\.kr|es|com\\.mx|\n            dk|ph|th|com\\.uy|co|nl|info|kr|ie|vn|com\\.vn|ec|mx|in|pe|co\\.at|hu|\n            co\\.in|co\\.nz|id|com\\.ec|com\\.py|tw|be|uk|com\\.bo|com\\.pe)/pin/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class PinterestCollectionIE(PinterestBaseIE):
    _module = 'yt_dlp.extractor.pinterest'
    IE_NAME = 'PinterestCollection'
    _VALID_URL = '(?x)\n        https?://(?:[^/]+\\.)?pinterest\\.(?:\n            com|fr|de|ch|jp|cl|ca|it|co\\.uk|nz|ru|com\\.au|at|pt|co\\.kr|es|com\\.mx|\n            dk|ph|th|com\\.uy|co|nl|info|kr|ie|vn|com\\.vn|ec|mx|in|pe|co\\.at|hu|\n            co\\.in|co\\.nz|id|com\\.ec|com\\.py|tw|be|uk|com\\.bo|com\\.pe)/(?P<username>[^/]+)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if PinterestIE.suitable(url) else super(
            PinterestCollectionIE, cls).suitable(url)


class PixivSketchBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pixivsketch'
    IE_NAME = 'PixivSketchBase'


class PixivSketchIE(PixivSketchBaseIE):
    _module = 'yt_dlp.extractor.pixivsketch'
    IE_NAME = 'pixiv:sketch'
    _VALID_URL = 'https?://sketch\\.pixiv\\.net/@(?P<uploader_id>[a-zA-Z0-9_-]+)/lives/(?P<id>\\d+)/?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PixivSketchUserIE(PixivSketchBaseIE):
    _module = 'yt_dlp.extractor.pixivsketch'
    IE_NAME = 'pixiv:sketch:user'
    _VALID_URL = 'https?://sketch\\.pixiv\\.net/@(?P<id>[a-zA-Z0-9_-]+)/?'

    @classmethod
    def suitable(cls, url):
        return super(PixivSketchUserIE, cls).suitable(url) and not PixivSketchIE.suitable(url)


class PladformIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pladform'
    IE_NAME = 'Pladform'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:\n                                out\\.pladform\\.ru/player|\n                                static\\.pladform\\.ru/player\\.swf\n                            )\n                            \\?.*\\bvideoid=|\n                            video\\.pladform\\.ru/catalog/video/videoid/\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class PlanetMarathiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.planetmarathi'
    IE_NAME = 'PlanetMarathi'
    _VALID_URL = 'https?://(?:www\\.)?planetmarathi\\.com/titles/(?P<id>[^/#&?$]+)'
    _RETURN_TYPE = 'playlist'


class PlatziBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.platzi'
    IE_NAME = 'PlatziBase'
    _NETRC_MACHINE = 'platzi'


class PlatziIE(PlatziBaseIE):
    _module = 'yt_dlp.extractor.platzi'
    IE_NAME = 'Platzi'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            platzi\\.com/clases|           # es version\n                            courses\\.platzi\\.com/classes  # en version\n                        )/[^/]+/(?P<id>\\d+)-[^/?\\#&]+\n                    '
    _NETRC_MACHINE = 'platzi'
    _RETURN_TYPE = 'video'


class PlatziCourseIE(PlatziBaseIE):
    _module = 'yt_dlp.extractor.platzi'
    IE_NAME = 'PlatziCourse'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            platzi\\.com/clases|           # es version\n                            courses\\.platzi\\.com/classes  # en version\n                        )/(?P<id>[^/?\\#&]+)\n                    '
    _NETRC_MACHINE = 'platzi'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if PlatziIE.suitable(url) else super(PlatziCourseIE, cls).suitable(url)


class PlayFMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.playfm'
    IE_NAME = 'play.fm'
    _VALID_URL = 'https?://(?:www\\.)?play\\.fm/(?P<slug>(?:[^/]+/)+(?P<id>[^/]+))/?(?:$|[?#])'
    _RETURN_TYPE = 'video'


class PlayPlusTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.playplustv'
    IE_NAME = 'PlayPlusTV'
    _VALID_URL = 'https?://(?:www\\.)?playplus\\.(?:com|tv)/VOD/(?P<project_id>[0-9]+)/(?P<id>[0-9a-f]{32})'
    _NETRC_MACHINE = 'playplustv'
    _RETURN_TYPE = 'video'


class PlaysTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.plays'
    IE_NAME = 'PlaysTV'
    _VALID_URL = 'https?://(?:www\\.)?plays\\.tv/(?:video|embeds)/(?P<id>[0-9a-f]{18})'
    _RETURN_TYPE = 'video'


class PlayStuffIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.playstuff'
    IE_NAME = 'PlayStuff'
    _VALID_URL = 'https?://(?:www\\.)?play\\.stuff\\.co\\.nz/details/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class PlaySuisseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.playsuisse'
    IE_NAME = 'PlaySuisse'
    _VALID_URL = 'https?://(?:www\\.)?playsuisse\\.ch/(?:watch|detail)/(?:[^#]*[?&]episodeId=)?(?P<id>[0-9]+)'
    _RETURN_TYPE = 'any'


class PlaytvakIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.playtvak'
    IE_NAME = 'Playtvak'
    _VALID_URL = 'https?://(?:.+?\\.)?(?:playtvak|idnes|lidovky|metro)\\.cz/.*\\?(?:c|idvideo)=(?P<id>[^&]+)'
    IE_DESC = 'Playtvak.cz, iDNES.cz and Lidovky.cz'
    _RETURN_TYPE = 'video'


class PlayvidIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.playvid'
    IE_NAME = 'Playvid'
    _VALID_URL = 'https?://(?:www\\.)?playvid\\.com/watch(\\?v=|/)(?P<id>.+?)(?:#|$)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PlaywireIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.playwire'
    IE_NAME = 'Playwire'
    _VALID_URL = 'https?://(?:config|cdn)\\.playwire\\.com(?:/v2)?/(?P<publisher_id>\\d+)/(?:videos/v2|embed|config)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class PlutoTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.plutotv'
    IE_NAME = 'PlutoTV'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?pluto\\.tv(?:/[^/]+)?/on-demand\n        /(?P<video_type>movies|series)\n        /(?P<series_or_movie_slug>[^/]+)\n        (?:\n            (?:/seasons?/(?P<season_no>\\d+))?\n            (?:/episode/(?P<episode_slug>[^/]+))?\n        )?\n        /?(?:$|[#?])'
    _RETURN_TYPE = 'any'


class PluralsightBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pluralsight'
    IE_NAME = 'PluralsightBase'


class PluralsightIE(PluralsightBaseIE):
    _module = 'yt_dlp.extractor.pluralsight'
    IE_NAME = 'pluralsight'
    _VALID_URL = 'https?://(?:(?:www|app)\\.)?pluralsight\\.com/(?:training/)?player\\?'
    _NETRC_MACHINE = 'pluralsight'
    _RETURN_TYPE = 'video'


class PluralsightCourseIE(PluralsightBaseIE):
    _module = 'yt_dlp.extractor.pluralsight'
    IE_NAME = 'pluralsight:course'
    _VALID_URL = 'https?://(?:(?:www|app)\\.)?pluralsight\\.com/(?:library/)?courses/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class PodbayFMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.podbayfm'
    IE_NAME = 'PodbayFM'
    _VALID_URL = 'https?://podbay\\.fm/p/[^/]*/e/(?P<id>[^/]*)/?(?:[\\?#].*)?$'
    _RETURN_TYPE = 'video'


class PodbayFMChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.podbayfm'
    IE_NAME = 'PodbayFMChannel'
    _VALID_URL = 'https?://podbay\\.fm/p/(?P<id>[^/]*)/?(?:[\\?#].*)?$'
    _RETURN_TYPE = 'video'


class PodchaserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.podchaser'
    IE_NAME = 'Podchaser'
    _VALID_URL = 'https?://(?:www\\.)?podchaser\\.com/podcasts/[\\w-]+-(?P<podcast_id>\\d+)(?:/episodes/[\\w-]+-(?P<id>\\d+))?'
    _RETURN_TYPE = 'any'


class PodomaticIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.podomatic'
    IE_NAME = 'podomatic'
    _VALID_URL = '(?x)\n                    (?P<proto>https?)://\n                        (?:\n                            (?P<channel>[^.]+)\\.podomatic\\.com/entry|\n                            (?:www\\.)?podomatic\\.com/podcasts/(?P<channel_2>[^/]+)/episodes\n                        )/\n                        (?P<id>[^/?#&]+)\n                '
    _RETURN_TYPE = 'video'


class PokemonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pokemon'
    IE_NAME = 'Pokemon'
    _VALID_URL = 'https?://(?:www\\.)?pokemon\\.com/[a-z]{2}(?:.*?play=(?P<id>[a-z0-9]{32})|/(?:[^/]+/)+(?P<display_id>[^/?#&]+))'
    _RETURN_TYPE = 'video'


class PokemonWatchIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pokemon'
    IE_NAME = 'PokemonWatch'
    _VALID_URL = 'https?://watch\\.pokemon\\.com/[a-z]{2}-[a-z]{2}/(?:#/)?player(?:\\.html)?\\?id=(?P<id>[a-z0-9]{32})'
    _RETURN_TYPE = 'video'


class PokerGoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pokergo'
    IE_NAME = 'PokerGoBase'
    _NETRC_MACHINE = 'pokergo'


class PokerGoIE(PokerGoBaseIE):
    _module = 'yt_dlp.extractor.pokergo'
    IE_NAME = 'PokerGo'
    _VALID_URL = 'https?://(?:www\\.)?pokergo\\.com/videos/(?P<id>[^&$#/?]+)'
    _NETRC_MACHINE = 'pokergo'
    _RETURN_TYPE = 'video'


class PokerGoCollectionIE(PokerGoBaseIE):
    _module = 'yt_dlp.extractor.pokergo'
    IE_NAME = 'PokerGoCollection'
    _VALID_URL = 'https?://(?:www\\.)?pokergo\\.com/collections/(?P<id>[^&$#/?]+)'
    _NETRC_MACHINE = 'pokergo'
    _RETURN_TYPE = 'playlist'


class PolsatGoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.polsatgo'
    IE_NAME = 'PolsatGo'
    _VALID_URL = 'https?://(?:www\\.)?polsat(?:box)?go\\.pl/.+/(?P<id>[0-9a-fA-F]+)(?:[/#?]|$)'
    age_limit = 12
    _RETURN_TYPE = 'video'


class PolskieRadioBaseExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'PolskieRadioBaseExtract'


class PolskieRadioIE(PolskieRadioBaseExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'PolskieRadio'
    _VALID_URL = 'https?://(?:[^/]+\\.)?(?:polskieradio(?:24)?|radiokierowcow)\\.pl/artykul/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class PolskieRadioLegacyIE(PolskieRadioBaseExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'polskieradio:legacy'
    _VALID_URL = 'https?://(?:www\\.)?polskieradio(?:24)?\\.pl/\\d+/\\d+/[Aa]rtykul/(?P<id>\\d+)'
    _RETURN_TYPE = 'any'


class PolskieRadioAuditionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'polskieradio:audition'
    _VALID_URL = 'https?://(?:[^/]+\\.)?polskieradio\\.pl/audycj[ae]/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class PolskieRadioCategoryIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'polskieradio:category'
    _VALID_URL = 'https?://(?:www\\.)?polskieradio\\.pl/(?:\\d+(?:,[^/]+)?/|[^/]+/Tag)(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if PolskieRadioLegacyIE.suitable(url) else super().suitable(url)


class PolskieRadioPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'polskieradio:player'
    _VALID_URL = 'https?://player\\.polskieradio\\.pl/anteny/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class PolskieRadioPodcastBaseExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'PolskieRadioPodcastBaseExtract'


class PolskieRadioPodcastIE(PolskieRadioPodcastBaseExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'polskieradio:podcast'
    _VALID_URL = 'https?://podcasty\\.polskieradio\\.pl/track/(?P<id>[a-f\\d]{8}(?:-[a-f\\d]{4}){4}[a-f\\d]{8})'
    _RETURN_TYPE = 'video'


class PolskieRadioPodcastListIE(PolskieRadioPodcastBaseExtractor):
    _module = 'yt_dlp.extractor.polskieradio'
    IE_NAME = 'polskieradio:podcast:list'
    _VALID_URL = 'https?://podcasty\\.polskieradio\\.pl/podcast/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class PopcorntimesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.popcorntimes'
    IE_NAME = 'Popcorntimes'
    _VALID_URL = 'https?://popcorntimes\\.tv/[^/]+/m/(?P<id>[^/]+)/(?P<display_id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class PopcornTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.popcorntv'
    IE_NAME = 'PopcornTV'
    _VALID_URL = 'https?://[^/]+\\.popcorntv\\.it/guarda/(?P<display_id>[^/]+)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class Porn91IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.porn91'
    IE_NAME = '91porn'
    _VALID_URL = '(?:https?://)(?:www\\.|)91porn\\.com/view_video.php\\?([^#]+&)?viewkey=(?P<id>\\w+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornComIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.porncom'
    IE_NAME = 'PornCom'
    _VALID_URL = 'https?://(?:[a-zA-Z]+\\.)?porn\\.com/videos/(?:(?P<display_id>[^/]+)-)?(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornFlipIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pornflip'
    IE_NAME = 'PornFlip'
    _VALID_URL = 'https?://(?:www\\.)?pornflip\\.com/(?:(embed|sv|v)/)?(?P<id>[^/]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornHdIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pornhd'
    IE_NAME = 'PornHd'
    _VALID_URL = 'https?://(?:www\\.)?pornhd\\.com/(?:[a-z]{2,4}/)?videos/(?P<id>\\d+)(?:/(?P<display_id>.+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornHubBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHubBase'
    _NETRC_MACHINE = 'pornhub'


class PornHubIE(PornHubBaseIE):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHub'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:[^/]+\\.)?\n                            (?:(?P<host>pornhub(?:premium)?\\.(?:com|net|org))|pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd\\.onion)\n                            /(?:(?:view_video\\.php|video/show)\\?viewkey=|embed/)|\n                            (?:www\\.)?thumbzilla\\.com/video/\n                        )\n                        (?P<id>[\\da-z]+)\n                    '
    IE_DESC = 'PornHub and Thumbzilla'
    _NETRC_MACHINE = 'pornhub'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornHubPlaylistBaseIE(PornHubBaseIE):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHubPlaylistBase'
    _NETRC_MACHINE = 'pornhub'


class PornHubUserIE(PornHubPlaylistBaseIE):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHubUser'
    _VALID_URL = '(?P<url>https?://(?:[^/]+\\.)?(?:(?P<host>pornhub(?:premium)?\\.(?:com|net|org))|pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd\\.onion)/(?:(?:user|channel)s|model|pornstar)/(?P<id>[^/?#&]+))(?:[?#&]|/(?!videos)|$)'
    _NETRC_MACHINE = 'pornhub'
    _RETURN_TYPE = 'playlist'


class PornHubPlaylistIE(PornHubPlaylistBaseIE):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHubPlaylist'
    _VALID_URL = '(?P<url>https?://(?:[^/]+\\.)?(?:(?P<host>pornhub(?:premium)?\\.(?:com|net|org))|pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd\\.onion)/playlist/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'pornhub'
    _RETURN_TYPE = 'playlist'


class PornHubPagedPlaylistBaseIE(PornHubPlaylistBaseIE):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHubPagedPlaylistBase'
    _NETRC_MACHINE = 'pornhub'


class PornHubPagedVideoListIE(PornHubPagedPlaylistBaseIE):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHubPagedVideoList'
    _VALID_URL = 'https?://(?:[^/]+\\.)?(?:(?P<host>pornhub(?:premium)?\\.(?:com|net|org))|pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd\\.onion)/(?!playlist/)(?P<id>(?:[^/]+/)*[^/?#&]+)'
    _NETRC_MACHINE = 'pornhub'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False
                if PornHubIE.suitable(url) or PornHubUserIE.suitable(url) or PornHubUserVideosUploadIE.suitable(url)
                else super(PornHubPagedVideoListIE, cls).suitable(url))


class PornHubUserVideosUploadIE(PornHubPagedPlaylistBaseIE):
    _module = 'yt_dlp.extractor.pornhub'
    IE_NAME = 'PornHubUserVideosUpload'
    _VALID_URL = '(?P<url>https?://(?:[^/]+\\.)?(?:(?P<host>pornhub(?:premium)?\\.(?:com|net|org))|pornhubvybmsymdol4iibwgwtkpwmeyd6luq2gxajgjzfjvotyt5zhyd\\.onion)/(?:(?:user|channel)s|model|pornstar)/(?P<id>[^/]+)/videos/upload)'
    _NETRC_MACHINE = 'pornhub'
    _RETURN_TYPE = 'playlist'


class PornotubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pornotube'
    IE_NAME = 'Pornotube'
    _VALID_URL = 'https?://(?:\\w+\\.)?pornotube\\.com/(?:[^?#]*?)/video/(?P<id>[0-9]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornoVoisinesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pornovoisines'
    IE_NAME = 'PornoVoisines'
    _VALID_URL = 'https?://(?:www\\.)?pornovoisines\\.com/videos/show/(?P<id>\\d+)/(?P<display_id>[^/.]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornoXOIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pornoxo'
    IE_NAME = 'PornoXO'
    _VALID_URL = 'https?://(?:www\\.)?pornoxo\\.com/videos/(?P<id>\\d+)/(?P<display_id>[^/]+)\\.html'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornezIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pornez'
    IE_NAME = 'Pornez'
    _VALID_URL = 'https?://(?:www\\.)?pornez\\.net/(?:video(?P<id>\\w+)|watch)/'
    age_limit = 18
    _RETURN_TYPE = 'video'


class PuhuTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.puhutv'
    IE_NAME = 'puhutv'
    _VALID_URL = 'https?://(?:www\\.)?puhutv\\.com/(?P<id>[^/?#&]+)-izle'
    _RETURN_TYPE = 'video'


class PuhuTVSerieIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.puhutv'
    IE_NAME = 'puhutv:serie'
    _VALID_URL = 'https?://(?:www\\.)?puhutv\\.com/(?P<id>[^/?#&]+)-detay'
    _RETURN_TYPE = 'playlist'


class Pr0grammStaticIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pr0gramm'
    IE_NAME = 'Pr0grammStatic'
    _VALID_URL = 'https?://pr0gramm\\.com/static/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class Pr0grammIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pr0gramm'
    IE_NAME = 'Pr0gramm'
    _VALID_URL = 'https?:\\/\\/pr0gramm\\.com\\/(?!static/\\d+).+?\\/(?P<id>[\\d]+)(:|$)'
    _RETURN_TYPE = 'video'


class PrankCastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.prankcast'
    IE_NAME = 'PrankCast'
    _VALID_URL = 'https?://(?:www\\.)?prankcast\\.com/[^/?#]+/showreel/(?P<id>\\d+)-(?P<display_id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class PremiershipRugbyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.premiershiprugby'
    IE_NAME = 'PremiershipRugby'
    _VALID_URL = 'https?://(?:\\w+\\.)premiershiprugby\\.(?:com)/watch/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class PressTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.presstv'
    IE_NAME = 'PressTV'
    _VALID_URL = 'https?://(?:www\\.)?presstv\\.ir/[^/]+/(?P<y>\\d+)/(?P<m>\\d+)/(?P<d>\\d+)/(?P<id>\\d+)/(?P<display_id>[^/]+)?'
    _RETURN_TYPE = 'video'


class ProjectVeritasIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.projectveritas'
    IE_NAME = 'ProjectVeritas'
    _VALID_URL = 'https?://(?:www\\.)?projectveritas\\.com/(?P<type>news|video)/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class ProSiebenSat1BaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.prosiebensat1'
    IE_NAME = 'ProSiebenSat1Base'


class ProSiebenSat1IE(ProSiebenSat1BaseIE):
    _module = 'yt_dlp.extractor.prosiebensat1'
    IE_NAME = 'prosiebensat1'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?\n                        (?:\n                            (?:beta\\.)?\n                            (?:\n                                prosieben(?:maxx)?|sixx|sat1(?:gold)?|kabeleins(?:doku)?|the-voice-of-germany|advopedia\n                            )\\.(?:de|at|ch)|\n                            ran\\.de|fem\\.com|advopedia\\.de|galileo\\.tv/video\n                        )\n                        /(?P<id>.+)\n                    '
    IE_DESC = 'ProSiebenSat.1 Digital'
    _RETURN_TYPE = 'any'


class PRXBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.prx'
    IE_NAME = 'PRXBase'


class PRXStoryIE(PRXBaseIE):
    _module = 'yt_dlp.extractor.prx'
    IE_NAME = 'PRXStory'
    _VALID_URL = 'https?://(?:(?:beta|listen)\\.)?prx.org/stories/(?P<id>\\d+)'
    _RETURN_TYPE = 'any'


class PRXSeriesIE(PRXBaseIE):
    _module = 'yt_dlp.extractor.prx'
    IE_NAME = 'PRXSeries'
    _VALID_URL = 'https?://(?:(?:beta|listen)\\.)?prx.org/series/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class PRXAccountIE(PRXBaseIE):
    _module = 'yt_dlp.extractor.prx'
    IE_NAME = 'PRXAccount'
    _VALID_URL = 'https?://(?:(?:beta|listen)\\.)?prx.org/accounts/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class PRXStoriesSearchIE(PRXBaseIE, LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.prx'
    IE_NAME = 'prxstories:search'
    _VALID_URL = 'prxstories(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'PRX Stories Search'
    SEARCH_KEY = 'prxstories'
    _RETURN_TYPE = 'playlist'


class PRXSeriesSearchIE(PRXBaseIE, LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.prx'
    IE_NAME = 'prxseries:search'
    _VALID_URL = 'prxseries(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'PRX Series Search'
    SEARCH_KEY = 'prxseries'
    _RETURN_TYPE = 'playlist'


class Puls4IE(ProSiebenSat1BaseIE):
    _module = 'yt_dlp.extractor.puls4'
    IE_NAME = 'Puls4'
    _VALID_URL = 'https?://(?:www\\.)?puls4\\.com/(?P<id>[^?#&]+)'
    _RETURN_TYPE = 'video'


class PyvideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.pyvideo'
    IE_NAME = 'Pyvideo'
    _VALID_URL = 'https?://(?:www\\.)?pyvideo\\.org/(?P<category>[^/]+)/(?P<id>[^/?#&.]+)'
    _RETURN_TYPE = 'any'


class QDanceIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.qdance'
    IE_NAME = 'QDance'
    _VALID_URL = 'https?://(?:www\\.)?q-dance\\.com/network/(?:library|live)/(?P<id>\\d+)'
    _NETRC_MACHINE = 'qdance'
    _RETURN_TYPE = 'video'


class QingTingIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.qingting'
    IE_NAME = 'QingTing'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?(?:qingting\\.fm|qtfm\\.cn)/v?channels/(?P<channel>\\d+)/programs/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class QQMusicIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.qqmusic'
    IE_NAME = 'qqmusic'
    _VALID_URL = 'https?://y\\.qq\\.com/n/yqq/song/(?P<id>[0-9A-Za-z]+)\\.html'
    IE_DESC = 'QQ音乐'
    _RETURN_TYPE = 'video'


class QQPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.qqmusic'
    IE_NAME = 'QQPlaylistBase'


class QQMusicSingerIE(QQPlaylistBaseIE):
    _module = 'yt_dlp.extractor.qqmusic'
    IE_NAME = 'qqmusic:singer'
    _VALID_URL = 'https?://y\\.qq\\.com/n/yqq/singer/(?P<id>[0-9A-Za-z]+)\\.html'
    IE_DESC = 'QQ音乐 - 歌手'
    _RETURN_TYPE = 'playlist'


class QQMusicAlbumIE(QQPlaylistBaseIE):
    _module = 'yt_dlp.extractor.qqmusic'
    IE_NAME = 'qqmusic:album'
    _VALID_URL = 'https?://y\\.qq\\.com/n/yqq/album/(?P<id>[0-9A-Za-z]+)\\.html'
    IE_DESC = 'QQ音乐 - 专辑'
    _RETURN_TYPE = 'playlist'


class QQMusicToplistIE(QQPlaylistBaseIE):
    _module = 'yt_dlp.extractor.qqmusic'
    IE_NAME = 'qqmusic:toplist'
    _VALID_URL = 'https?://y\\.qq\\.com/n/yqq/toplist/(?P<id>[0-9]+)\\.html'
    IE_DESC = 'QQ音乐 - 排行榜'
    _RETURN_TYPE = 'playlist'


class QQMusicPlaylistIE(QQPlaylistBaseIE):
    _module = 'yt_dlp.extractor.qqmusic'
    IE_NAME = 'qqmusic:playlist'
    _VALID_URL = 'https?://y\\.qq\\.com/n/yqq/playlist/(?P<id>[0-9]+)\\.html'
    IE_DESC = 'QQ音乐 - 歌单'
    _RETURN_TYPE = 'playlist'


class R7IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.r7'
    IE_NAME = 'R7'
    _VALID_URL = '(?x)\n                        https?://\n                        (?:\n                            (?:[a-zA-Z]+)\\.r7\\.com(?:/[^/]+)+/idmedia/|\n                            noticias\\.r7\\.com(?:/[^/]+)+/[^/]+-|\n                            player\\.r7\\.com/video/i/\n                        )\n                        (?P<id>[\\da-f]{24})\n                    '
    _RETURN_TYPE = 'video'


class R7ArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.r7'
    IE_NAME = 'R7Article'
    _VALID_URL = 'https?://(?:[a-zA-Z]+)\\.r7\\.com/(?:[^/]+/)+[^/?#&]+-(?P<id>\\d+)'

    @classmethod
    def suitable(cls, url):
        return False if R7IE.suitable(url) else super(R7ArticleIE, cls).suitable(url)


class RadikoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiko'
    IE_NAME = 'RadikoBase'


class RadikoIE(RadikoBaseIE):
    _module = 'yt_dlp.extractor.radiko'
    IE_NAME = 'Radiko'
    _VALID_URL = 'https?://(?:www\\.)?radiko\\.jp/#!/ts/(?P<station>[A-Z0-9-]+)/(?P<id>\\d+)'


class RadikoRadioIE(RadikoBaseIE):
    _module = 'yt_dlp.extractor.radiko'
    IE_NAME = 'RadikoRadio'
    _VALID_URL = 'https?://(?:www\\.)?radiko\\.jp/#!/live/(?P<id>[A-Z0-9-]+)'


class RadioCanadaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiocanada'
    IE_NAME = 'radiocanada'
    _VALID_URL = '(?:radiocanada:|https?://ici\\.radio-canada\\.ca/widgets/mediaconsole/)(?P<app_code>[^:/]+)[:/](?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class RadioCanadaAudioVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiocanada'
    IE_NAME = 'radiocanada:audiovideo'
    _VALID_URL = 'https?://ici\\.radio-canada\\.ca/([^/]+/)*media-(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class RadioDeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiode'
    IE_NAME = 'radio.de'
    _VALID_URL = 'https?://(?P<id>.+?)\\.(?:radio\\.(?:de|at|fr|pt|es|pl|it)|rad\\.io)'
    _RETURN_TYPE = 'video'


class RadioJavanIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiojavan'
    IE_NAME = 'RadioJavan'
    _VALID_URL = 'https?://(?:www\\.)?radiojavan\\.com/videos/video/(?P<id>[^/]+)/?'
    _RETURN_TYPE = 'video'


class RadioBremenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiobremen'
    IE_NAME = 'radiobremen'
    _VALID_URL = 'http?://(?:www\\.)?radiobremen\\.de/mediathek/(?:index\\.html)?\\?id=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class FranceCultureIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiofrance'
    IE_NAME = 'FranceCulture'
    _VALID_URL = 'https?://(?:www\\.)?radiofrance\\.fr/(?:franceculture|fip|francemusique|mouv|franceinter)/podcasts/(?:[^?#]+/)?(?P<display_id>[^?#]+)-(?P<id>\\d+)($|[?#])'
    _RETURN_TYPE = 'video'


class RadioFranceIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiofrance'
    IE_NAME = 'radiofrance'
    _VALID_URL = '^https?://maison\\.radiofrance\\.fr/radiovisions/(?P<id>[^?#]+)'
    _RETURN_TYPE = 'video'


class RadioZetPodcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiozet'
    IE_NAME = 'RadioZetPodcast'
    _VALID_URL = 'https?://player\\.radiozet\\.pl\\/Podcasty/.*?/(?P<id>.+)'
    _RETURN_TYPE = 'video'


class RadioKapitalBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radiokapital'
    IE_NAME = 'RadioKapitalBase'


class RadioKapitalIE(RadioKapitalBaseIE):
    _module = 'yt_dlp.extractor.radiokapital'
    IE_NAME = 'radiokapital'
    _VALID_URL = 'https?://(?:www\\.)?radiokapital\\.pl/shows/[a-z\\d-]+/(?P<id>[a-z\\d-]+)'
    _RETURN_TYPE = 'video'


class RadioKapitalShowIE(RadioKapitalBaseIE):
    _module = 'yt_dlp.extractor.radiokapital'
    IE_NAME = 'radiokapital:show'
    _VALID_URL = 'https?://(?:www\\.)?radiokapital\\.pl/shows/(?P<id>[a-z\\d-]+)/?(?:$|[?#])'
    _RETURN_TYPE = 'playlist'


class RadLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.radlive'
    IE_NAME = 'radlive'
    _VALID_URL = 'https?://(?:www\\.)?rad\\.live/content/(?P<content_type>feature|episode)/(?P<id>[a-f0-9-]+)'
    _RETURN_TYPE = 'video'


class RadLiveChannelIE(RadLiveIE):
    _module = 'yt_dlp.extractor.radlive'
    IE_NAME = 'radlive:channel'
    _VALID_URL = 'https?://(?:www\\.)?rad\\.live/content/channel/(?P<id>[a-f0-9-]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if RadLiveIE.suitable(url) else super(RadLiveChannelIE, cls).suitable(url)


class RadLiveSeasonIE(RadLiveIE):
    _module = 'yt_dlp.extractor.radlive'
    IE_NAME = 'radlive:season'
    _VALID_URL = 'https?://(?:www\\.)?rad\\.live/content/season/(?P<id>[a-f0-9-]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if RadLiveIE.suitable(url) else super(RadLiveSeasonIE, cls).suitable(url)


class RaiBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiBase'


class RaiIE(RaiBaseIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'Rai'
    _VALID_URL = 'https?://[^/]+\\.(?:rai\\.(?:it|tv))/.+?-(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})(?:-.+?)?\\.html'
    _RETURN_TYPE = 'video'


class RaiPlayIE(RaiBaseIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiPlay'
    _VALID_URL = '(?P<base>https?://(?:www\\.)?raiplay\\.it/.+?-(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12}))\\.(?:html|json)'
    _RETURN_TYPE = 'video'


class RaiPlayLiveIE(RaiPlayIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiPlayLive'
    _VALID_URL = '(?P<base>https?://(?:www\\.)?raiplay\\.it/dirette/(?P<id>[^/?#&]+))'
    _RETURN_TYPE = 'video'


class RaiPlayPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiPlayPlaylist'
    _VALID_URL = '(?P<base>https?://(?:www\\.)?raiplay\\.it/programmi/(?P<id>[^/?#&]+))(?:/(?P<extra_id>[^?#&]+))?'
    _RETURN_TYPE = 'playlist'


class RaiPlaySoundIE(RaiBaseIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiPlaySound'
    _VALID_URL = '(?P<base>https?://(?:www\\.)?raiplaysound\\.it/.+?-(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12}))\\.(?:html|json)'
    _RETURN_TYPE = 'video'


class RaiPlaySoundLiveIE(RaiPlaySoundIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiPlaySoundLive'
    _VALID_URL = '(?P<base>https?://(?:www\\.)?raiplaysound\\.it/(?P<id>[^/?#&]+)$)'
    _RETURN_TYPE = 'video'


class RaiPlaySoundPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiPlaySoundPlaylist'
    _VALID_URL = '(?P<base>https?://(?:www\\.)?raiplaysound\\.it/(?:programmi|playlist|audiolibri)/(?P<id>[^/?#&]+))(?:/(?P<extra_id>[^?#&]+))?'
    _RETURN_TYPE = 'playlist'


class RaiNewsIE(RaiIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiNews'
    _VALID_URL = 'https?://(www\\.)?rainews\\.it/(?!articoli)[^?#]+-(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})(?:-[^/?#]+)?\\.html'
    _RETURN_TYPE = 'video'


class RaiCulturaIE(RaiNewsIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiCultura'
    _VALID_URL = 'https?://(www\\.)?raicultura\\.it/(?!articoli)[^?#]+-(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})(?:-[^/?#]+)?\\.html'
    _RETURN_TYPE = 'video'


class RaiSudtirolIE(RaiBaseIE):
    _module = 'yt_dlp.extractor.rai'
    IE_NAME = 'RaiSudtirol'
    _VALID_URL = 'https?://raisudtirol\\.rai\\.it/.+media=(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class RayWenderlichIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.raywenderlich'
    IE_NAME = 'RayWenderlich'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            videos\\.raywenderlich\\.com/courses|\n                            (?:www\\.)?raywenderlich\\.com\n                        )/\n                        (?P<course_id>[^/]+)/lessons/(?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class RayWenderlichCourseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.raywenderlich'
    IE_NAME = 'RayWenderlichCourse'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            videos\\.raywenderlich\\.com/courses|\n                            (?:www\\.)?raywenderlich\\.com\n                        )/\n                        (?P<id>[^/]+)\n                    '
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if RayWenderlichIE.suitable(url) else super(
            RayWenderlichCourseIE, cls).suitable(url)


class RBMARadioIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rbmaradio'
    IE_NAME = 'RBMARadio'
    _VALID_URL = 'https?://(?:www\\.)?(?:rbmaradio|redbullradio)\\.com/shows/(?P<show_id>[^/]+)/episodes/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class RbgTumIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rbgtum'
    IE_NAME = 'RbgTum'
    _VALID_URL = 'https://live\\.rbg\\.tum\\.de/w/(?P<id>.+)'
    _RETURN_TYPE = 'video'


class RbgTumCourseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rbgtum'
    IE_NAME = 'RbgTumCourse'
    _VALID_URL = 'https://live\\.rbg\\.tum\\.de/course/(?P<id>.+)'
    _RETURN_TYPE = 'playlist'


class RCSBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rcs'
    IE_NAME = 'RCSBase'


class RCSIE(RCSBaseIE):
    _module = 'yt_dlp.extractor.rcs'
    IE_NAME = 'RCS'
    _VALID_URL = '(?x)https?://(?P<vid>video|viaggi)\\.\n                    (?P<cdn>\n                    (?:\n                        corrieredelmezzogiorno\\.\n                        |corrieredelveneto\\.\n                        |corrieredibologna\\.\n                        |corrierefiorentino\\.\n                    )?corriere\\.it\n                    |(?:gazzanet\\.)?gazzetta\\.it)\n                    /(?!video-embed/)[^?#]+?/(?P<id>[^/\\?]+)(?=\\?|/$|$)'
    _RETURN_TYPE = 'video'


class RCSEmbedsIE(RCSBaseIE):
    _module = 'yt_dlp.extractor.rcs'
    IE_NAME = 'RCSEmbeds'
    _VALID_URL = '(?x)\n                    https?://(?P<vid>video)\\.\n                    (?P<cdn>\n                    (?:\n                        rcs|\n                        (?:corriere\\w+\\.)?corriere|\n                        (?:gazzanet\\.)?gazzetta\n                    )\\.it)\n                    /video-embed/(?P<id>[^/=&\\?]+?)(?:$|\\?)'
    _RETURN_TYPE = 'video'


class RCSVariousIE(RCSBaseIE):
    _module = 'yt_dlp.extractor.rcs'
    IE_NAME = 'RCSVarious'
    _VALID_URL = '(?x)https?://www\\.\n                    (?P<cdn>\n                        leitv\\.it|\n                        youreporter\\.it|\n                        amica\\.it\n                    )/(?:[^/]+/)?(?P<id>[^/]+?)(?:$|\\?|/)'
    _RETURN_TYPE = 'video'


class RCTIPlusBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rcti'
    IE_NAME = 'RCTIPlusBase'


class RCTIPlusIE(RCTIPlusBaseIE):
    _module = 'yt_dlp.extractor.rcti'
    IE_NAME = 'RCTIPlus'
    _VALID_URL = 'https://www\\.rctiplus\\.com/(?:programs/\\d+?/.*?/)?(?P<type>episode|clip|extra|live-event|missed-event)/(?P<id>\\d+)/(?P<display_id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class RCTIPlusSeriesIE(RCTIPlusBaseIE):
    _module = 'yt_dlp.extractor.rcti'
    IE_NAME = 'RCTIPlusSeries'
    _VALID_URL = 'https://www\\.rctiplus\\.com/programs/(?P<id>\\d+)/(?P<display_id>[^/?#&]+)(?:/(?P<type>episodes|extras|clips))?'
    age_limit = 2
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if RCTIPlusIE.suitable(url) else super(RCTIPlusSeriesIE, cls).suitable(url)


class RCTIPlusTVIE(RCTIPlusBaseIE):
    _module = 'yt_dlp.extractor.rcti'
    IE_NAME = 'RCTIPlusTV'
    _VALID_URL = 'https://www\\.rctiplus\\.com/((tv/(?P<tvname>\\w+))|(?P<eventname>live-event|missed-event))'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if RCTIPlusIE.suitable(url) else super(RCTIPlusTVIE, cls).suitable(url)


class RDSIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rds'
    IE_NAME = 'RDS'
    _VALID_URL = 'https?://(?:www\\.)?rds\\.ca/vid(?:[eé]|%C3%A9)os/(?:[^/]+/)*(?P<id>[^/]+)-\\d+\\.\\d+'
    IE_DESC = 'RDS.ca'
    _RETURN_TYPE = 'video'


class RecurbateIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.recurbate'
    IE_NAME = 'Recurbate'
    _VALID_URL = 'https?://(?:www\\.)?recurbate\\.com/play\\.php\\?video=(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class RedBeeBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.redbee'
    IE_NAME = 'RedBeeBase'


class ParliamentLiveUKIE(RedBeeBaseIE):
    _module = 'yt_dlp.extractor.redbee'
    IE_NAME = 'parliamentlive.tv'
    _VALID_URL = '(?i)https?://(?:www\\.)?parliamentlive\\.tv/Event/Index/(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'
    IE_DESC = 'UK parliament videos'
    _RETURN_TYPE = 'video'


class RTBFIE(RedBeeBaseIE):
    _module = 'yt_dlp.extractor.redbee'
    IE_NAME = 'RTBF'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?rtbf\\.be/\n        (?:\n            video/[^?]+\\?.*\\bid=|\n            ouftivi/(?:[^/]+/)*[^?]+\\?.*\\bvideoId=|\n            auvio/[^/]+\\?.*\\b(?P<live>l)?id=\n        )(?P<id>\\d+)'
    _NETRC_MACHINE = 'rtbf'
    _RETURN_TYPE = 'video'


class RedBullTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.redbulltv'
    IE_NAME = 'RedBullTV'
    _VALID_URL = 'https?://(?:www\\.)?redbull(?:\\.tv|\\.com(?:/[^/]+)?(?:/tv)?)(?:/events/[^/]+)?/(?:videos?|live|(?:film|episode)s)/(?P<id>AP-\\w+)'
    _RETURN_TYPE = 'video'


class RedBullEmbedIE(RedBullTVIE):
    _module = 'yt_dlp.extractor.redbulltv'
    IE_NAME = 'RedBullEmbed'
    _VALID_URL = 'https?://(?:www\\.)?redbull\\.com/embed/(?P<id>rrn:content:[^:]+:[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12}:[a-z]{2}-[A-Z]{2,3})'


class RedBullTVRrnContentIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.redbulltv'
    IE_NAME = 'RedBullTVRrnContent'
    _VALID_URL = 'https?://(?:www\\.)?redbull\\.com/(?P<region>[a-z]{2,3})-(?P<lang>[a-z]{2})/tv/(?:video|live|film)/(?P<id>rrn:content:[^:]+:[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'


class RedBullIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.redbulltv'
    IE_NAME = 'RedBull'
    _VALID_URL = 'https?://(?:www\\.)?redbull\\.com/(?P<region>[a-z]{2,3})-(?P<lang>[a-z]{2})/(?P<type>(?:episode|film|(?:(?:recap|trailer)-)?video)s|live)/(?!AP-|rrn:content:)(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class RedditIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.reddit'
    IE_NAME = 'Reddit'
    _VALID_URL = 'https?://(?P<host>(?:\\w+\\.)?reddit(?:media)?\\.com)/(?P<slug>(?:(?:r|user)/[^/]+/)?comments/(?P<id>[^/?#&]+))'
    _NETRC_MACHINE = 'reddit'
    _RETURN_TYPE = 'any'


class RedGifsBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.redgifs'
    IE_NAME = 'RedGifsBaseInfoExtract'


class RedGifsIE(RedGifsBaseInfoExtractor):
    _module = 'yt_dlp.extractor.redgifs'
    IE_NAME = 'RedGifs'
    _VALID_URL = 'https?://(?:(?:www\\.)?redgifs\\.com/watch/|thumbs2\\.redgifs\\.com/)(?P<id>[^-/?#\\.]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class RedGifsSearchIE(RedGifsBaseInfoExtractor):
    _module = 'yt_dlp.extractor.redgifs'
    IE_NAME = 'RedGifsSearch'
    _VALID_URL = 'https?://(?:www\\.)?redgifs\\.com/browse\\?(?P<query>[^#]+)'
    IE_DESC = 'Redgifs search'
    _RETURN_TYPE = 'playlist'


class RedGifsUserIE(RedGifsBaseInfoExtractor):
    _module = 'yt_dlp.extractor.redgifs'
    IE_NAME = 'RedGifsUser'
    _VALID_URL = 'https?://(?:www\\.)?redgifs\\.com/users/(?P<username>[^/?#]+)(?:\\?(?P<query>[^#]+))?'
    IE_DESC = 'Redgifs user'
    _RETURN_TYPE = 'playlist'


class RedTubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.redtube'
    IE_NAME = 'RedTube'
    _VALID_URL = 'https?://(?:(?:\\w+\\.)?redtube\\.com/|embed\\.redtube\\.com/\\?.*?\\bid=)(?P<id>[0-9]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class RegioTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.regiotv'
    IE_NAME = 'RegioTV'
    _VALID_URL = 'https?://(?:www\\.)?regio-tv\\.de/video/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class RENTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rentv'
    IE_NAME = 'RENTV'
    _VALID_URL = '(?:rentv:|https?://(?:www\\.)?ren\\.tv/(?:player|video/epizod)/)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class RENTVArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rentv'
    IE_NAME = 'RENTVArticle'
    _VALID_URL = 'https?://(?:www\\.)?ren\\.tv/novosti/\\d{4}-\\d{2}-\\d{2}/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class RestudyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.restudy'
    IE_NAME = 'Restudy'
    _VALID_URL = 'https?://(?:(?:www|portal)\\.)?restudy\\.dk/video/[^/]+/id/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class ReutersIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.reuters'
    IE_NAME = 'Reuters'
    _VALID_URL = 'https?://(?:www\\.)?reuters\\.com/.*?\\?.*?videoId=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class ReverbNationIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.reverbnation'
    IE_NAME = 'ReverbNation'
    _VALID_URL = '^https?://(?:www\\.)?reverbnation\\.com/.*?/song/(?P<id>\\d+).*?$'
    _RETURN_TYPE = 'video'


class RheinMainTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rheinmaintv'
    IE_NAME = 'RheinMainTV'
    _VALID_URL = 'https?://(?:www\\.)?rheinmaintv\\.de/sendungen/(?:[\\w-]+/)*(?P<video_id>(?P<display_id>[\\w-]+)/vom-\\d{2}\\.\\d{2}\\.\\d{4}(?:/\\d+)?)'
    _RETURN_TYPE = 'video'


class RICEIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rice'
    IE_NAME = 'RICE'
    _VALID_URL = 'https?://mediahub\\.rice\\.edu/app/[Pp]ortal/video\\.aspx\\?(?P<query>.+)'
    _RETURN_TYPE = 'video'


class RMCDecouverteIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rmcdecouverte'
    IE_NAME = 'RMCDecouverte'
    _VALID_URL = 'https?://rmcdecouverte\\.bfmtv\\.com/(?:[^?#]*_(?P<id>\\d+)|mediaplayer-direct)/?(?:[#?]|$)'
    _RETURN_TYPE = 'video'


class RockstarGamesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rockstargames'
    IE_NAME = 'RockstarGames'
    _VALID_URL = 'https?://(?:www\\.)?rockstargames\\.com/videos(?:/video/|#?/?\\?.*\\bvideo=)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class RokfinIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rokfin'
    IE_NAME = 'Rokfin'
    _VALID_URL = 'https?://(?:www\\.)?rokfin\\.com/(?P<id>(?P<type>post|stream)/\\d+)'
    _NETRC_MACHINE = 'rokfin'
    _RETURN_TYPE = 'video'


class RokfinPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rokfin'
    IE_NAME = 'RokfinPlaylistBase'


class RokfinStackIE(RokfinPlaylistBaseIE):
    _module = 'yt_dlp.extractor.rokfin'
    IE_NAME = 'rokfin:stack'
    _VALID_URL = 'https?://(?:www\\.)?rokfin\\.com/stack/(?P<id>[^/]+)'
    IE_DESC = 'Rokfin Stacks'
    _RETURN_TYPE = 'playlist'


class RokfinChannelIE(RokfinPlaylistBaseIE):
    _module = 'yt_dlp.extractor.rokfin'
    IE_NAME = 'rokfin:channel'
    _VALID_URL = 'https?://(?:www\\.)?rokfin\\.com/(?!((feed/?)|(discover/?)|(channels/?))$)(?P<id>[^/]+)/?$'
    IE_DESC = 'Rokfin Channels'
    _RETURN_TYPE = 'playlist'


class RokfinSearchIE(LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.rokfin'
    IE_NAME = 'rokfin:search'
    _VALID_URL = 'rkfnsearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'Rokfin Search'
    SEARCH_KEY = 'rkfnsearch'
    _RETURN_TYPE = 'playlist'


class RoosterTeethBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.roosterteeth'
    IE_NAME = 'RoosterTeethBase'
    _NETRC_MACHINE = 'roosterteeth'


class RoosterTeethIE(RoosterTeethBaseIE):
    _module = 'yt_dlp.extractor.roosterteeth'
    IE_NAME = 'RoosterTeeth'
    _VALID_URL = 'https?://(?:.+?\\.)?roosterteeth\\.com/(?:episode|watch)/(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'roosterteeth'
    _RETURN_TYPE = 'video'


class RoosterTeethSeriesIE(RoosterTeethBaseIE):
    _module = 'yt_dlp.extractor.roosterteeth'
    IE_NAME = 'RoosterTeethSeries'
    _VALID_URL = 'https?://(?:.+?\\.)?roosterteeth\\.com/series/(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'roosterteeth'
    _RETURN_TYPE = 'playlist'


class RottenTomatoesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rottentomatoes'
    IE_NAME = 'RottenTomatoes'
    _VALID_URL = 'https?://(?:www\\.)?rottentomatoes\\.com/m/(?P<playlist>[^/]+)(?:/(?P<tr>trailers)(?:/(?P<id>\\w+))?)?'
    _RETURN_TYPE = 'any'


class RozhlasIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rozhlas'
    IE_NAME = 'Rozhlas'
    _VALID_URL = 'https?://(?:www\\.)?prehravac\\.rozhlas\\.cz/audio/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class RozhlasBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rozhlas'
    IE_NAME = 'RozhlasBase'


class RozhlasVltavaIE(RozhlasBaseIE):
    _module = 'yt_dlp.extractor.rozhlas'
    IE_NAME = 'RozhlasVltava'
    _VALID_URL = 'https?://(?:\\w+\\.rozhlas|english\\.radio)\\.cz/[\\w-]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class MujRozhlasIE(RozhlasBaseIE):
    _module = 'yt_dlp.extractor.rozhlas'
    IE_NAME = 'MujRozhlas'
    _VALID_URL = 'https?://(?:www\\.)?mujrozhlas\\.cz/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'any'


class RteBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rte'
    IE_NAME = 'RteBase'


class RteIE(RteBaseIE):
    _module = 'yt_dlp.extractor.rte'
    IE_NAME = 'rte'
    _VALID_URL = 'https?://(?:www\\.)?rte\\.ie/player/[^/]{2,3}/show/[^/]+/(?P<id>[0-9]+)'
    IE_DESC = 'Raidió Teilifís Éireann TV'
    _RETURN_TYPE = 'video'


class RteRadioIE(RteBaseIE):
    _module = 'yt_dlp.extractor.rte'
    IE_NAME = 'rte:radio'
    _VALID_URL = 'https?://(?:www\\.)?rte\\.ie/radio/utils/radioplayer/rteradioweb\\.html#!rii=(?:b?[0-9]*)(?:%3A|:|%5F|_)(?P<id>[0-9]+)'
    IE_DESC = 'Raidió Teilifís Éireann radio'
    _RETURN_TYPE = 'video'


class RtlNlIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtlnl'
    IE_NAME = 'rtl.nl'
    _VALID_URL = '(?x)\n        https?://(?:(?:www|static)\\.)?\n        (?:\n            rtlxl\\.nl/(?:[^\\#]*\\#!|programma)/[^/]+/|\n            rtl\\.nl/(?:(?:system/videoplayer/(?:[^/]+/)+(?:video_)?embed\\.html|embed)\\b.+?\\buuid=|video/)|\n            embed\\.rtl\\.nl/\\#uuid=\n        )\n        (?P<id>[0-9a-f-]+)'
    IE_DESC = 'rtl.nl and rtlxl.nl'
    _RETURN_TYPE = 'video'


class RTLLuBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtlnl'
    IE_NAME = 'RTLLuBase'


class RTLLuTeleVODIE(RTLLuBaseIE):
    _module = 'yt_dlp.extractor.rtlnl'
    IE_NAME = 'rtl.lu:tele-vod'
    _VALID_URL = 'https?://(?:www\\.)?rtl\\.lu/(tele/(?P<slug>[\\w-]+)/v/|video/)(?P<id>\\d+)(\\.html)?'
    _RETURN_TYPE = 'video'


class RTLLuArticleIE(RTLLuBaseIE):
    _module = 'yt_dlp.extractor.rtlnl'
    IE_NAME = 'rtl.lu:article'
    _VALID_URL = 'https?://(?:(www|5minutes|today)\\.)rtl\\.lu/(?:[\\w-]+)/(?:[\\w-]+)/a/(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class RTLLuLiveIE(RTLLuBaseIE):
    _module = 'yt_dlp.extractor.rtlnl'
    IE_NAME = 'RTLLuLive'
    _VALID_URL = 'https?://www\\.rtl\\.lu/(?:tele|radio)/(?P<id>live(?:-\\d+)?|lauschteren)'
    _RETURN_TYPE = 'video'


class RTLLuRadioIE(RTLLuBaseIE):
    _module = 'yt_dlp.extractor.rtlnl'
    IE_NAME = 'RTLLuRadio'
    _VALID_URL = 'https?://www\\.rtl\\.lu/radio/(?:[\\w-]+)/s/(?P<id>\\d+)(\\.html)?'
    _RETURN_TYPE = 'video'


class RTL2IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtl2'
    IE_NAME = 'rtl2'
    _VALID_URL = 'https?://(?:www\\.)?rtl2\\.de/sendung/[^/]+/(?:video/(?P<vico_id>\\d+)[^/]+/(?P<vivi_id>\\d+)-|folge/)(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class RTL2YouBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtl2'
    IE_NAME = 'RTL2YouBase'


class RTL2YouIE(RTL2YouBaseIE):
    _module = 'yt_dlp.extractor.rtl2'
    IE_NAME = 'rtl2:you'
    _VALID_URL = 'http?://you\\.rtl2\\.de/(?:video/\\d+/|youplayer/index\\.html\\?.*?\\bvid=)(?P<id>\\d+)'
    age_limit = 12
    _RETURN_TYPE = 'video'


class RTL2YouSeriesIE(RTL2YouBaseIE):
    _module = 'yt_dlp.extractor.rtl2'
    IE_NAME = 'rtl2:you:series'
    _VALID_URL = 'http?://you\\.rtl2\\.de/videos/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class RTNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtnews'
    IE_NAME = 'RTNews'
    _VALID_URL = 'https?://(?:www\\.)?rt\\.com/[^/]+/(?:[^/]+/)?(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class RTDocumentryIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtnews'
    IE_NAME = 'RTDocumentry'
    _VALID_URL = 'https?://rtd\\.rt\\.com/(?:(?:series|shows)/[^/]+|films)/(?P<id>[^/?$&#]+)'
    _RETURN_TYPE = 'video'


class RTDocumentryPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtnews'
    IE_NAME = 'RTDocumentryPlaylist'
    _VALID_URL = 'https?://rtd\\.rt\\.com/(?:series|shows)/(?P<id>[^/]+)/$'
    _RETURN_TYPE = 'playlist'


class RuptlyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtnews'
    IE_NAME = 'Ruptly'
    _VALID_URL = 'https?://(?:www\\.)?ruptly\\.tv/[a-z]{2}/videos/(?P<id>\\d+-\\d+)'
    _RETURN_TYPE = 'video'


class RTPIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtp'
    IE_NAME = 'RTP'
    _VALID_URL = 'https?://(?:www\\.)?rtp\\.pt/play/p(?P<program_id>[0-9]+)/(?P<id>[^/?#]+)/?'
    _RETURN_TYPE = 'video'


class RTRFMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtrfm'
    IE_NAME = 'RTRFM'
    _VALID_URL = 'https?://(?:www\\.)?rtrfm\\.com\\.au/(?:shows|show-episode)/(?P<id>[^/?\\#&]+)'
    _RETURN_TYPE = 'video'


class RTVCPlayBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtvcplay'
    IE_NAME = 'RTVCPlayBase'


class RTVCPlayIE(RTVCPlayBaseIE):
    _module = 'yt_dlp.extractor.rtvcplay'
    IE_NAME = 'RTVCPlay'
    _VALID_URL = 'https?://(?:www\\.)?rtvcplay\\.co/(?P<category>(?!embed)[^/]+)/(?:[^?#]+/)?(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'any'


class RTVCPlayEmbedIE(RTVCPlayBaseIE):
    _module = 'yt_dlp.extractor.rtvcplay'
    IE_NAME = 'RTVCPlayEmbed'
    _VALID_URL = 'https?://(?:www\\.)?rtvcplay\\.co/embed/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class RTVCKalturaIE(RTVCPlayBaseIE):
    _module = 'yt_dlp.extractor.rtvcplay'
    IE_NAME = 'RTVCKaltura'
    _VALID_URL = 'https?://media\\.rtvc\\.gov\\.co/kalturartvc/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class RTVEALaCartaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtve'
    IE_NAME = 'rtve.es:alacarta'
    _VALID_URL = 'https?://(?:www\\.)?rtve\\.es/(m/)?(alacarta/videos|filmoteca)/[^/]+/[^/]+/(?P<id>\\d+)'
    IE_DESC = 'RTVE a la carta'
    _RETURN_TYPE = 'video'


class RTVEAudioIE(RTVEALaCartaIE):
    _module = 'yt_dlp.extractor.rtve'
    IE_NAME = 'rtve.es:audio'
    _VALID_URL = 'https?://(?:www\\.)?rtve\\.es/(alacarta|play)/audios/[^/]+/[^/]+/(?P<id>[0-9]+)'
    IE_DESC = 'RTVE audio'
    _RETURN_TYPE = 'video'


class RTVELiveIE(RTVEALaCartaIE):
    _module = 'yt_dlp.extractor.rtve'
    IE_NAME = 'rtve.es:live'
    _VALID_URL = 'https?://(?:www\\.)?rtve\\.es/directo/(?P<id>[a-zA-Z0-9-]+)'
    IE_DESC = 'RTVE.es live streams'
    _RETURN_TYPE = 'video'


class RTVEInfantilIE(RTVEALaCartaIE):
    _module = 'yt_dlp.extractor.rtve'
    IE_NAME = 'rtve.es:infantil'
    _VALID_URL = 'https?://(?:www\\.)?rtve\\.es/infantil/serie/[^/]+/video/[^/]+/(?P<id>[0-9]+)/'
    IE_DESC = 'RTVE infantil'
    _RETURN_TYPE = 'video'


class RTVETelevisionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtve'
    IE_NAME = 'rtve.es:television'
    _VALID_URL = 'https?://(?:www\\.)?rtve\\.es/television/[^/]+/[^/]+/(?P<id>\\d+).shtml'
    _RETURN_TYPE = 'video'


class RTVNHIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtvnh'
    IE_NAME = 'RTVNH'
    _VALID_URL = 'https?://(?:www\\.)?rtvnh\\.nl/video/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class RTVSIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtvs'
    IE_NAME = 'RTVS'
    _VALID_URL = 'https?://(?:www\\.)?rtvs\\.sk/(?:radio|televizia)/archiv(?:/\\d+)?/(?P<id>\\d+)/?(?:[#?]|$)'
    _RETURN_TYPE = 'video'


class RTVSLOIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rtvslo'
    IE_NAME = 'rtvslo.si'
    _VALID_URL = '(?x)\n        https?://(?:\n            (?:365|4d)\\.rtvslo.si/arhiv/[^/?#&;]+|\n            (?:www\\.)?rtvslo\\.si/rtv365/arhiv\n        )/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class RUHDIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ruhd'
    IE_NAME = 'RUHD'
    _VALID_URL = 'https?://(?:www\\.)?ruhd\\.ru/play\\.php\\?vid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class Rule34VideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rule34video'
    IE_NAME = 'Rule34Video'
    _VALID_URL = 'https?://(?:www\\.)?rule34video\\.com/videos/(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class RumbleEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rumble'
    IE_NAME = 'RumbleEmbed'
    _VALID_URL = 'https?://(?:www\\.)?rumble\\.com/embed/(?:[0-9a-z]+\\.)?(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class RumbleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rumble'
    IE_NAME = 'Rumble'
    _VALID_URL = 'https?://(?:www\\.)?rumble\\.com/(?P<id>v(?!ideos)[\\w.-]+)[^/]*$'
    _RETURN_TYPE = 'video'


class RumbleChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rumble'
    IE_NAME = 'RumbleChannel'
    _VALID_URL = '(?P<url>https?://(?:www\\.)?rumble\\.com/(?:c|user)/(?P<id>[^&?#$/]+))'
    _RETURN_TYPE = 'playlist'


class RutubeBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'RutubeBase'


class RutubeIE(RutubeBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'rutube'
    _VALID_URL = 'https?://rutube\\.ru/(?:video(?:/private)?|(?:play/)?embed)/(?P<id>[\\da-z]{32})'
    IE_DESC = 'Rutube videos'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if RutubePlaylistIE.suitable(url) else super(RutubeIE, cls).suitable(url)


class RutubePlaylistBaseIE(RutubeBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'RutubePlaylistBase'


class RutubeChannelIE(RutubePlaylistBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'rutube:channel'
    _VALID_URL = 'https?://rutube\\.ru/channel/(?P<id>\\d+)/videos'
    IE_DESC = 'Rutube channel'
    _RETURN_TYPE = 'playlist'


class RutubeEmbedIE(RutubeBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'rutube:embed'
    _VALID_URL = 'https?://rutube\\.ru/(?:video|play)/embed/(?P<id>[0-9]+)'
    IE_DESC = 'Rutube embedded videos'
    _RETURN_TYPE = 'video'


class RutubeMovieIE(RutubePlaylistBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'rutube:movie'
    _VALID_URL = 'https?://rutube\\.ru/metainfo/tv/(?P<id>\\d+)'
    IE_DESC = 'Rutube movies'


class RutubePersonIE(RutubePlaylistBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'rutube:person'
    _VALID_URL = 'https?://rutube\\.ru/video/person/(?P<id>\\d+)'
    IE_DESC = 'Rutube person videos'
    _RETURN_TYPE = 'playlist'


class RutubePlaylistIE(RutubePlaylistBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'rutube:playlist'
    _VALID_URL = 'https?://rutube\\.ru/(?:video|(?:play/)?embed)/[\\da-z]{32}/\\?.*?\\bpl_id=(?P<id>\\d+)'
    IE_DESC = 'Rutube playlists'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        from ..utils import int_or_none, parse_qs

        if not super(RutubePlaylistIE, cls).suitable(url):
            return False
        params = parse_qs(url)
        return params.get('pl_type', [None])[0] and int_or_none(params.get('pl_id', [None])[0])


class RutubeTagsIE(RutubePlaylistBaseIE):
    _module = 'yt_dlp.extractor.rutube'
    IE_NAME = 'rutube:tags'
    _VALID_URL = 'https?://rutube\\.ru/tags/video/(?P<id>\\d+)'
    IE_DESC = 'Rutube tags'
    _RETURN_TYPE = 'playlist'


class GlomexBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.glomex'
    IE_NAME = 'GlomexBase'


class GlomexIE(GlomexBaseIE):
    _module = 'yt_dlp.extractor.glomex'
    IE_NAME = 'glomex'
    _VALID_URL = 'https?://video\\.glomex\\.com/[^/]+/(?P<id>v-[^-]+)'
    IE_DESC = 'Glomex videos'
    _RETURN_TYPE = 'video'


class GlomexEmbedIE(GlomexBaseIE):
    _module = 'yt_dlp.extractor.glomex'
    IE_NAME = 'glomex:embed'
    _VALID_URL = 'https?://player\\.glomex\\.com/integration/[^/]/iframe\\-player\\.html\\?([^#]+&)?playlistId=(?P<id>[^#&]+)'
    IE_DESC = 'Glomex embedded videos'
    _RETURN_TYPE = 'any'


class MegaTVComBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.megatvcom'
    IE_NAME = 'MegaTVComBase'


class MegaTVComIE(MegaTVComBaseIE):
    _module = 'yt_dlp.extractor.megatvcom'
    IE_NAME = 'megatvcom'
    _VALID_URL = 'https?://(?:www\\.)?megatv\\.com/(?:\\d{4}/\\d{2}/\\d{2}|[^/]+/(?P<id>\\d+))/(?P<slug>[^/]+)'
    IE_DESC = 'megatv.com videos'
    _RETURN_TYPE = 'video'


class MegaTVComEmbedIE(MegaTVComBaseIE):
    _module = 'yt_dlp.extractor.megatvcom'
    IE_NAME = 'megatvcom:embed'
    _VALID_URL = '(?:https?:)?//(?:www\\.)?megatv\\.com/embed/?\\?p=(?P<id>\\d+)'
    IE_DESC = 'megatv.com embedded videos'
    _RETURN_TYPE = 'video'


class Ant1NewsGrBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ant1newsgr'
    IE_NAME = 'Ant1NewsGrBase'


class Ant1NewsGrWatchIE(Ant1NewsGrBaseIE):
    _module = 'yt_dlp.extractor.ant1newsgr'
    IE_NAME = 'ant1newsgr:watch'
    _VALID_URL = 'https?://(?P<netloc>(?:www\\.)?ant1news\\.gr)/watch/(?P<id>\\d+)/'
    IE_DESC = 'ant1news.gr videos'
    _RETURN_TYPE = 'video'


class Ant1NewsGrArticleIE(Ant1NewsGrBaseIE):
    _module = 'yt_dlp.extractor.ant1newsgr'
    IE_NAME = 'ant1newsgr:article'
    _VALID_URL = 'https?://(?:www\\.)?ant1news\\.gr/[^/]+/article/(?P<id>\\d+)/'
    IE_DESC = 'ant1news.gr articles'
    _RETURN_TYPE = 'any'


class Ant1NewsGrEmbedIE(Ant1NewsGrBaseIE):
    _module = 'yt_dlp.extractor.ant1newsgr'
    IE_NAME = 'ant1newsgr:embed'
    _VALID_URL = '(?:https?:)?//(?:[a-zA-Z0-9\\-]+\\.)?(?:antenna|ant1news)\\.gr/templates/pages/player\\?([^#]+&)?cid=(?P<id>[^#&]+)'
    IE_DESC = 'ant1news.gr embedded videos'
    _RETURN_TYPE = 'video'


class RUTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.rutv'
    IE_NAME = 'RUTV'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:test)?player\\.(?:rutv\\.ru|vgtrk\\.com)/\n                        (?P<path>\n                            flash\\d+v/container\\.swf\\?id=|\n                            iframe/(?P<type>swf|video|live)/id/|\n                            index/iframe/cast_id/\n                        )\n                        (?P<id>\\d+)\n                    '
    IE_DESC = 'RUTV.RU'
    _RETURN_TYPE = 'video'


class RuutuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ruutu'
    IE_NAME = 'Ruutu'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:www\\.)?(?:ruutu|supla)\\.fi/(?:video|supla|audio)/|\n                            static\\.nelonenmedia\\.fi/player/misc/embed_player\\.html\\?.*?\\bnid=\n                        )\n                        (?P<id>\\d+)\n                    '
    age_limit = 12
    _RETURN_TYPE = 'video'


class RuvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ruv'
    IE_NAME = 'Ruv'
    _VALID_URL = 'https?://(?:www\\.)?ruv\\.is/(?:sarpurinn/[^/]+|node)/(?P<id>[^/]+(?:/\\d+)?)'
    _RETURN_TYPE = 'video'


class RuvSpilaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ruv'
    IE_NAME = 'ruv.is:spila'
    _VALID_URL = 'https?://(?:www\\.)?ruv\\.is/(?:(?:sjon|ut)varp|(?:krakka|ung)ruv)/spila/.+/(?P<series_id>[0-9]+)/(?P<id>[a-z0-9]+)'
    _RETURN_TYPE = 'video'


class SafariBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.safari'
    IE_NAME = 'SafariBase'
    _NETRC_MACHINE = 'safari'


class SafariIE(SafariBaseIE):
    _module = 'yt_dlp.extractor.safari'
    IE_NAME = 'safari'
    _VALID_URL = '(?x)\n                        https?://\n                            (?:www\\.)?(?:safaribooksonline|(?:learning\\.)?oreilly)\\.com/\n                            (?:\n                                library/view/[^/]+/(?P<course_id>[^/]+)/(?P<part>[^/?\\#&]+)\\.html|\n                                videos/[^/]+/[^/]+/(?P<reference_id>[^-]+-[^/?\\#&]+)\n                            )\n                    '
    IE_DESC = 'safaribooksonline.com online video'
    _NETRC_MACHINE = 'safari'
    _RETURN_TYPE = 'video'


class SafariApiIE(SafariBaseIE):
    _module = 'yt_dlp.extractor.safari'
    IE_NAME = 'safari:api'
    _VALID_URL = 'https?://(?:www\\.)?(?:safaribooksonline|(?:learning\\.)?oreilly)\\.com/api/v1/book/(?P<course_id>[^/]+)/chapter(?:-content)?/(?P<part>[^/?#&]+)\\.html'
    _NETRC_MACHINE = 'safari'


class SafariCourseIE(SafariBaseIE):
    _module = 'yt_dlp.extractor.safari'
    IE_NAME = 'safari:course'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:www\\.)?(?:safaribooksonline|(?:learning\\.)?oreilly)\\.com/\n                            (?:\n                                library/view/[^/]+|\n                                api/v1/book|\n                                videos/[^/]+\n                            )|\n                            techbus\\.safaribooksonline\\.com\n                        )\n                        /(?P<id>[^/]+)\n                    '
    IE_DESC = 'safaribooksonline.com online courses'
    _NETRC_MACHINE = 'safari'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if SafariIE.suitable(url) or SafariApiIE.suitable(url)
                else super(SafariCourseIE, cls).suitable(url))


class SaitosanIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.saitosan'
    IE_NAME = 'Saitosan'
    _VALID_URL = 'https?://(?:www\\.)?saitosan\\.net/bview.html\\?id=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class SampleFocusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.samplefocus'
    IE_NAME = 'SampleFocus'
    _VALID_URL = 'https?://(?:www\\.)?samplefocus\\.com/samples/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class SapoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sapo'
    IE_NAME = 'Sapo'
    _VALID_URL = 'https?://(?:(?:v2|www)\\.)?videos\\.sapo\\.(?:pt|cv|ao|mz|tl)/(?P<id>[\\da-zA-Z]{20})'
    IE_DESC = 'SAPO Vídeos'
    _RETURN_TYPE = 'video'


class SaveFromIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.savefrom'
    IE_NAME = 'savefrom.net'
    _VALID_URL = 'https?://[^.]+\\.savefrom\\.net/\\#url=(?P<url>.*)$'
    _RETURN_TYPE = 'video'


class SBSIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sbs'
    IE_NAME = 'SBS'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?sbs\\.com\\.au/(?:\n            ondemand(?:\n                /video/(?:single/)?|\n                /(?:movie|tv-program)/[^/]+/|\n                /(?:tv|news)-series/(?:[^/]+/){3}|\n                .*?\\bplay=|/watch/\n            )|news/(?:embeds/)?video/\n        )(?P<id>[0-9]+)'
    IE_DESC = 'sbs.com.au'
    _RETURN_TYPE = 'video'


class Screen9IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.screen9'
    IE_NAME = 'Screen9'
    _VALID_URL = 'https?://(?:\\w+\\.screen9\\.(?:tv|com)|play\\.su\\.se)/(?:embed|media)/(?P<id>[^?#/]+)'
    _RETURN_TYPE = 'video'


class ScreencastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.screencast'
    IE_NAME = 'Screencast'
    _VALID_URL = 'https?://(?:www\\.)?screencast\\.com/t/(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'


class ScreencastifyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.screencastify'
    IE_NAME = 'Screencastify'
    _VALID_URL = 'https?://watch\\.screencastify\\.com/v/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class ScreencastOMaticIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.screencastomatic'
    IE_NAME = 'ScreencastOMatic'
    _VALID_URL = 'https?://screencast-o-matic\\.com/(?:(?:watch|player)/|embed\\?.*?\\bsc=)(?P<id>[0-9a-zA-Z]+)'
    _RETURN_TYPE = 'video'


class AWSIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.aws'
    IE_NAME = 'AWS'


class ScrippsNetworksWatchIE(AWSIE):
    _module = 'yt_dlp.extractor.scrippsnetworks'
    IE_NAME = 'scrippsnetworks:watch'
    _VALID_URL = '(?x)\n                    https?://\n                        watch\\.\n                        (?P<site>geniuskitchen)\\.com/\n                        (?:\n                            player\\.[A-Z0-9]+\\.html\\#|\n                            show/(?:[^/]+/){2}|\n                            player/\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class ScrippsNetworksIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.scrippsnetworks'
    IE_NAME = 'ScrippsNetworks'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>cookingchanneltv|discovery|(?:diy|food)network|hgtv|travelchannel)\\.com/videos/[0-9a-z-]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class SCTEBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.scte'
    IE_NAME = 'SCTEBase'
    _NETRC_MACHINE = 'scte'


class SCTEIE(SCTEBaseIE):
    _module = 'yt_dlp.extractor.scte'
    IE_NAME = 'SCTE'
    _VALID_URL = 'https?://learning\\.scte\\.org/mod/scorm/view\\.php?.*?\\bid=(?P<id>\\d+)'
    _NETRC_MACHINE = 'scte'
    _RETURN_TYPE = 'playlist'


class SCTECourseIE(SCTEBaseIE):
    _module = 'yt_dlp.extractor.scte'
    IE_NAME = 'SCTECourse'
    _VALID_URL = 'https?://learning\\.scte\\.org/(?:mod/sub)?course/view\\.php?.*?\\bid=(?P<id>\\d+)'
    _NETRC_MACHINE = 'scte'


class ScrolllerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.scrolller'
    IE_NAME = 'Scrolller'
    _VALID_URL = 'https?://(?:www\\.)?scrolller\\.com/(?P<id>[\\w-]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class SeekerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.seeker'
    IE_NAME = 'Seeker'
    _VALID_URL = 'https?://(?:www\\.)?seeker\\.com/(?P<display_id>.*)-(?P<article_id>\\d+)\\.html'
    _RETURN_TYPE = 'any'


class SenalColombiaLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.senalcolombia'
    IE_NAME = 'SenalColombiaLive'
    _VALID_URL = 'https?://(?:www\\.)?senalcolombia\\.tv/(?P<id>senal-en-vivo)'
    _RETURN_TYPE = 'video'


class SenateISVPIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.senategov'
    IE_NAME = 'SenateISVP'
    _VALID_URL = 'https?://(?:www\\.)?senate\\.gov/isvp/?\\?(?P<qs>.+)'
    _RETURN_TYPE = 'video'


class SenateGovIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.senategov'
    IE_NAME = 'SenateGov'
    _VALID_URL = 'https?:\\/\\/(?:www\\.)?(help|appropriations|judiciary|banking|armed-services|finance)\\.senate\\.gov'
    _RETURN_TYPE = 'video'


class SendtoNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sendtonews'
    IE_NAME = 'SendtoNews'
    _VALID_URL = 'https?://embed\\.sendtonews\\.com/player2/embedplayer\\.php\\?.*\\bSC=(?P<id>[0-9A-Za-z-]+)'
    _RETURN_TYPE = 'playlist'


class ServusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.servus'
    IE_NAME = 'Servus'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?\n                        (?:\n                            servus\\.com/(?:(?:at|de)/p/[^/]+|tv/videos)|\n                            (?:servustv|pm-wissen)\\.com/(?:[^/]+/)?v(?:ideos)?\n                        )\n                        /(?P<id>[aA]{2}-?\\w+|\\d+-\\d+)\n                    '
    _RETURN_TYPE = 'video'


class SevenPlusIE(BrightcoveNewBaseIE):
    _module = 'yt_dlp.extractor.sevenplus'
    IE_NAME = '7plus'
    _VALID_URL = 'https?://(?:www\\.)?7plus\\.com\\.au/(?P<path>[^?]+\\?.*?\\bepisode-id=(?P<id>[^&#]+))'
    _RETURN_TYPE = 'video'


class SexuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sexu'
    IE_NAME = 'Sexu'
    _VALID_URL = 'https?://(?:www\\.)?sexu\\.com/(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class SeznamZpravyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.seznamzpravy'
    IE_NAME = 'SeznamZpravy'
    _VALID_URL = 'https?://(?:www\\.)?seznamzpravy\\.cz/iframe/player\\?.*\\bsrc='
    _RETURN_TYPE = 'video'


class SeznamZpravyArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.seznamzpravy'
    IE_NAME = 'SeznamZpravyArticle'
    _VALID_URL = 'https?://(?:www\\.)?(?:seznam\\.cz/zpravy|seznamzpravy\\.cz)/clanek/(?:[^/?#&]+)-(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class ShahidBaseIE(AWSIE):
    _module = 'yt_dlp.extractor.shahid'
    IE_NAME = 'ShahidBase'


class ShahidIE(ShahidBaseIE):
    _module = 'yt_dlp.extractor.shahid'
    IE_NAME = 'Shahid'
    _VALID_URL = 'https?://shahid\\.mbc\\.net/[a-z]{2}/(?:serie|show|movie)s/[^/]+/(?P<type>episode|clip|movie)-(?P<id>\\d+)'
    _NETRC_MACHINE = 'shahid'
    _RETURN_TYPE = 'video'


class ShahidShowIE(ShahidBaseIE):
    _module = 'yt_dlp.extractor.shahid'
    IE_NAME = 'ShahidShow'
    _VALID_URL = 'https?://shahid\\.mbc\\.net/[a-z]{2}/(?:show|serie)s/[^/]+/(?:show|series)-(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class SharedBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.shared'
    IE_NAME = 'SharedBase'


class SharedIE(SharedBaseIE):
    _module = 'yt_dlp.extractor.shared'
    IE_NAME = 'Shared'
    _VALID_URL = 'https?://shared\\.sx/(?P<id>[\\da-z]{10})'
    IE_DESC = 'shared.sx'
    _RETURN_TYPE = 'video'


class VivoIE(SharedBaseIE):
    _module = 'yt_dlp.extractor.shared'
    IE_NAME = 'Vivo'
    _VALID_URL = 'https?://vivo\\.s[xt]/(?P<id>[\\da-z]{10})'
    IE_DESC = 'vivo.sx'
    _RETURN_TYPE = 'video'


class ShareVideosEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sharevideos'
    IE_NAME = 'ShareVideosEmbed'
    _VALID_URL = False


class SibnetEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sibnet'
    IE_NAME = 'SibnetEmbed'
    _VALID_URL = False


class ShemarooMeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.shemaroome'
    IE_NAME = 'ShemarooMe'
    _VALID_URL = 'https?://(?:www\\.)?shemaroome\\.com/(?:movies|shows)/(?P<id>[^?#]+)'
    _RETURN_TYPE = 'video'


class ShowRoomLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.showroomlive'
    IE_NAME = 'ShowRoomLive'
    _VALID_URL = 'https?://(?:www\\.)?showroom-live\\.com/(?!onlive|timetable|event|campaign|news|ranking|room)(?P<id>[^/?#&]+)'


class SimplecastBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.simplecast'
    IE_NAME = 'SimplecastBase'


class SimplecastIE(SimplecastBaseIE):
    _module = 'yt_dlp.extractor.simplecast'
    IE_NAME = 'simplecast'
    _VALID_URL = 'https?://(?:api\\.simplecast\\.com/episodes|player\\.simplecast\\.com)/(?P<id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class SimplecastEpisodeIE(SimplecastBaseIE):
    _module = 'yt_dlp.extractor.simplecast'
    IE_NAME = 'simplecast:episode'
    _VALID_URL = 'https?://(?!api\\.)[^/]+\\.simplecast\\.com/episodes/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class SimplecastPodcastIE(SimplecastBaseIE):
    _module = 'yt_dlp.extractor.simplecast'
    IE_NAME = 'simplecast:podcast'
    _VALID_URL = 'https?://(?!(?:api|cdn|embed|feeds|player)\\.)(?P<id>[^/]+)\\.simplecast\\.com(?!/episodes/[^/?&#]+)'
    _RETURN_TYPE = 'playlist'


class SinaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sina'
    IE_NAME = 'Sina'
    _VALID_URL = '(?x)https?://(?:.*?\\.)?video\\.sina\\.com\\.cn/\n                        (?:\n                            (?:view/|.*\\#)(?P<id>\\d+)|\n                            .+?/(?P<pseudo_id>[^/?#]+)(?:\\.s?html)|\n                            # This is used by external sites like Weibo\n                            api/sinawebApi/outplay.php/(?P<token>.+?)\\.swf\n                        )\n                  '
    _RETURN_TYPE = 'video'


class SixPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sixplay'
    IE_NAME = '6play'
    _VALID_URL = '(?:6play:|https?://(?:www\\.)?(?P<domain>6play\\.fr|rtlplay\\.be|play\\.rtl\\.hr|rtlmost\\.hu)/.+?-c_)(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class SkebIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.skeb'
    IE_NAME = 'Skeb'
    _VALID_URL = 'https?://skeb\\.jp/@[^/]+/works/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class SkyItPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.skyit'
    IE_NAME = 'player.sky.it'
    _VALID_URL = 'https?://player\\.sky\\.it/player/(?:external|social)\\.html\\?.*?\\bid=(?P<id>\\d+)'


class SkyItVideoIE(SkyItPlayerIE):
    _module = 'yt_dlp.extractor.skyit'
    IE_NAME = 'video.sky.it'
    _VALID_URL = 'https?://(?:masterchef|video|xfactor)\\.sky\\.it(?:/[^/]+)*/video/[0-9a-z-]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class SkyItVideoLiveIE(SkyItPlayerIE):
    _module = 'yt_dlp.extractor.skyit'
    IE_NAME = 'video.sky.it:live'
    _VALID_URL = 'https?://video\\.sky\\.it/diretta/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class SkyItIE(SkyItPlayerIE):
    _module = 'yt_dlp.extractor.skyit'
    IE_NAME = 'sky.it'
    _VALID_URL = 'https?://(?:sport|tg24)\\.sky\\.it(?:/[^/]+)*/\\d{4}/\\d{2}/\\d{2}/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class SkyItArteIE(SkyItIE):
    _module = 'yt_dlp.extractor.skyit'
    IE_NAME = 'arte.sky.it'
    _VALID_URL = 'https?://arte\\.sky\\.it/video/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class CieloTVItIE(SkyItIE):
    _module = 'yt_dlp.extractor.skyit'
    IE_NAME = 'cielotv.it'
    _VALID_URL = 'https?://(?:www\\.)?cielotv\\.it/video/(?P<id>[^.]+)\\.html'
    _RETURN_TYPE = 'video'


class TV8ItIE(SkyItVideoIE):
    _module = 'yt_dlp.extractor.skyit'
    IE_NAME = 'tv8.it'
    _VALID_URL = 'https?://(?:www\\.)?tv8\\.it/(?:show)?video/[0-9a-z-]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class SkylineWebcamsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.skylinewebcams'
    IE_NAME = 'SkylineWebcams'
    _VALID_URL = 'https?://(?:www\\.)?skylinewebcams\\.com/[^/]+/webcam/(?:[^/]+/)+(?P<id>[^/]+)\\.html'
    _RETURN_TYPE = 'video'


class SkyNewsArabiaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.skynewsarabia'
    IE_NAME = 'SkyNewsArabiaBase'


class SkyNewsArabiaIE(SkyNewsArabiaBaseIE):
    _module = 'yt_dlp.extractor.skynewsarabia'
    IE_NAME = 'skynewsarabia:video'
    _VALID_URL = 'https?://(?:www\\.)?skynewsarabia\\.com/web/video/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class SkyNewsArabiaArticleIE(SkyNewsArabiaBaseIE):
    _module = 'yt_dlp.extractor.skynewsarabia'
    IE_NAME = 'skynewsarabia:article'
    _VALID_URL = 'https?://(?:www\\.)?skynewsarabia\\.com/web/article/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'any'


class SkyNewsAUIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.skynewsau'
    IE_NAME = 'SkyNewsAU'
    _VALID_URL = 'https?://(?:www\\.)?skynews\\.com\\.au/[^/]+/[^/]+/[^/]+/video/(?P<id>[a-z0-9]+)'
    _RETURN_TYPE = 'video'


class SkyBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sky'
    IE_NAME = 'SkyBase'


class SkyNewsIE(SkyBaseIE):
    _module = 'yt_dlp.extractor.sky'
    IE_NAME = 'sky:news'
    _VALID_URL = 'https?://news\\.sky\\.com/video/[0-9a-z-]+-(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class SkyNewsStoryIE(SkyBaseIE):
    _module = 'yt_dlp.extractor.sky'
    IE_NAME = 'sky:news:story'
    _VALID_URL = 'https?://news\\.sky\\.com/story/[0-9a-z-]+-(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class SkySportsIE(SkyBaseIE):
    _module = 'yt_dlp.extractor.sky'
    IE_NAME = 'sky:sports'
    _VALID_URL = 'https?://(?:www\\.)?skysports\\.com/watch/video/([^/]+/)*(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class SkySportsNewsIE(SkyBaseIE):
    _module = 'yt_dlp.extractor.sky'
    IE_NAME = 'sky:sports:news'
    _VALID_URL = 'https?://(?:www\\.)?skysports\\.com/([^/]+/)*news/\\d+/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class SlideshareIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.slideshare'
    IE_NAME = 'Slideshare'
    _VALID_URL = 'https?://(?:www\\.)?slideshare\\.net/[^/]+?/(?P<title>.+?)($|\\?)'
    _RETURN_TYPE = 'video'


class SlidesLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.slideslive'
    IE_NAME = 'SlidesLive'
    _VALID_URL = 'https?://slideslive\\.com/(?:embed/(?:presentation/)?)?(?P<id>[0-9]+)'
    _RETURN_TYPE = 'any'


class SlutloadIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.slutload'
    IE_NAME = 'Slutload'
    _VALID_URL = 'https?://(?:\\w+\\.)?slutload\\.com/(?:video/[^/]+|embed_player|watch)/(?P<id>[^/]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class SmotrimIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.smotrim'
    IE_NAME = 'Smotrim'
    _VALID_URL = 'https?://smotrim\\.ru/(?P<type>brand|video|article|live)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class SnotrIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.snotr'
    IE_NAME = 'Snotr'
    _VALID_URL = 'http?://(?:www\\.)?snotr\\.com/video/(?P<id>\\d+)/([\\w]+)'
    _RETURN_TYPE = 'video'


class SohuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sohu'
    IE_NAME = 'Sohu'
    _VALID_URL = 'https?://(?P<mytv>my\\.)?tv\\.sohu\\.com/.+?/(?(mytv)|n)(?P<id>\\d+)\\.shtml.*?'
    _RETURN_TYPE = 'any'


class SonyLIVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sonyliv'
    IE_NAME = 'SonyLIV'
    _VALID_URL = '(?x)\n                     (?:\n                        sonyliv:|\n                        https?://(?:www\\.)?sonyliv\\.com/(?:s(?:how|port)s/[^/]+|movies|clip|trailer|music-videos)/[^/?#&]+-\n                    )\n                    (?P<id>\\d+)\n                  '
    _NETRC_MACHINE = 'sonyliv'
    _RETURN_TYPE = 'video'


class SonyLIVSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sonyliv'
    IE_NAME = 'SonyLIVSeries'
    _VALID_URL = 'https?://(?:www\\.)?sonyliv\\.com/shows/[^/?#&]+-(?P<id>\\d{10})$'
    _RETURN_TYPE = 'playlist'


class SoundcloudEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'SoundcloudEmbed'
    _VALID_URL = 'https?://(?:w|player|p)\\.soundcloud\\.com/player/?.*?\\burl=(?P<id>.+)'


class SoundcloudBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'SoundcloudBase'
    _NETRC_MACHINE = 'soundcloud'


class SoundcloudIE(SoundcloudBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud'
    _VALID_URL = '(?x)^(?:https?://)?\n                    (?:(?:(?:www\\.|m\\.)?soundcloud\\.com/\n                            (?!stations/track)\n                            (?P<uploader>[\\w\\d-]+)/\n                            (?!(?:tracks|albums|sets(?:/.+?)?|reposts|likes|spotlight)/?(?:$|[?#]))\n                            (?P<title>[\\w\\d-]+)\n                            (?:/(?P<token>(?!(?:albums|sets|recommended))[^?]+?))?\n                            (?:[?].*)?$)\n                       |(?:api(?:-v2)?\\.soundcloud\\.com/tracks/(?P<track_id>\\d+)\n                          (?:/?\\?secret_token=(?P<secret_token>[^&]+))?)\n                    )\n                    '
    _NETRC_MACHINE = 'soundcloud'
    _RETURN_TYPE = 'video'


class SoundcloudPlaylistBaseIE(SoundcloudBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'SoundcloudPlaylistBase'
    _NETRC_MACHINE = 'soundcloud'


class SoundcloudSetIE(SoundcloudPlaylistBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud:set'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)?soundcloud\\.com/(?P<uploader>[\\w\\d-]+)/sets/(?P<slug_title>[:\\w\\d-]+)(?:/(?P<token>[^?/]+))?'
    _NETRC_MACHINE = 'soundcloud'
    _RETURN_TYPE = 'playlist'


class SoundcloudPagedPlaylistBaseIE(SoundcloudBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'SoundcloudPagedPlaylistBase'
    _NETRC_MACHINE = 'soundcloud'


class SoundcloudRelatedIE(SoundcloudPagedPlaylistBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud:related'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)?soundcloud\\.com/(?P<slug>[\\w\\d-]+/[\\w\\d-]+)/(?P<relation>albums|sets|recommended)'
    _NETRC_MACHINE = 'soundcloud'
    _RETURN_TYPE = 'playlist'


class SoundcloudUserIE(SoundcloudPagedPlaylistBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud:user'
    _VALID_URL = '(?x)\n                        https?://\n                            (?:(?:www|m)\\.)?soundcloud\\.com/\n                            (?P<user>[^/]+)\n                            (?:/\n                                (?P<rsrc>tracks|albums|sets|reposts|likes|spotlight)\n                            )?\n                            /?(?:[?#].*)?$\n                    '
    _NETRC_MACHINE = 'soundcloud'
    _RETURN_TYPE = 'playlist'


class SoundcloudUserPermalinkIE(SoundcloudPagedPlaylistBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud:user:permalink'
    _VALID_URL = 'https?://api\\.soundcloud\\.com/users/(?P<id>\\d+)'
    _NETRC_MACHINE = 'soundcloud'
    _RETURN_TYPE = 'playlist'


class SoundcloudTrackStationIE(SoundcloudPagedPlaylistBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud:trackstation'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)?soundcloud\\.com/stations/track/[^/]+/(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'soundcloud'
    _RETURN_TYPE = 'playlist'


class SoundcloudPlaylistIE(SoundcloudPlaylistBaseIE):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud:playlist'
    _VALID_URL = 'https?://api(?:-v2)?\\.soundcloud\\.com/playlists/(?P<id>[0-9]+)(?:/?\\?secret_token=(?P<token>[^&]+?))?$'
    _NETRC_MACHINE = 'soundcloud'
    _RETURN_TYPE = 'playlist'


class SoundcloudSearchIE(SoundcloudBaseIE, LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.soundcloud'
    IE_NAME = 'soundcloud:search'
    _VALID_URL = 'scsearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'Soundcloud search'
    _NETRC_MACHINE = 'soundcloud'
    SEARCH_KEY = 'scsearch'
    _RETURN_TYPE = 'playlist'


class SoundgasmIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.soundgasm'
    IE_NAME = 'soundgasm'
    _VALID_URL = 'https?://(?:www\\.)?soundgasm\\.net/u/(?P<user>[0-9a-zA-Z_-]+)/(?P<display_id>[0-9a-zA-Z_-]+)'
    _RETURN_TYPE = 'video'


class SoundgasmProfileIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.soundgasm'
    IE_NAME = 'soundgasm:profile'
    _VALID_URL = 'https?://(?:www\\.)?soundgasm\\.net/u/(?P<id>[^/]+)/?(?:\\#.*)?$'
    _RETURN_TYPE = 'playlist'


class SouthParkIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.southpark'
    IE_NAME = 'southpark.cc.com'
    _VALID_URL = 'https?://(?:www\\.)?(?P<url>southpark(?:\\.cc|studios)\\.com/((?:video-)?clips|(?:full-)?episodes|collections)/(?P<id>.+?)(\\?|#|$))'
    _RETURN_TYPE = 'video'


class SouthParkDeIE(SouthParkIE):
    _module = 'yt_dlp.extractor.southpark'
    IE_NAME = 'southpark.de'
    _VALID_URL = 'https?://(?:www\\.)?(?P<url>southpark\\.de/(?:(en/(videoclip|collections|episodes|video-clips))|(videoclip|collections|folgen))/(?P<id>(?P<unique_id>.+?)/.+?)(?:\\?|#|$))'
    _RETURN_TYPE = 'video'


class SouthParkDkIE(SouthParkIE):
    _module = 'yt_dlp.extractor.southpark'
    IE_NAME = 'southparkstudios.dk'
    _VALID_URL = 'https?://(?:www\\.)?(?P<url>southparkstudios\\.(?:dk|nu)/(?:clips|full-episodes|collections)/(?P<id>.+?)(\\?|#|$))'
    _RETURN_TYPE = 'playlist'


class SouthParkEsIE(SouthParkIE):
    _module = 'yt_dlp.extractor.southpark'
    IE_NAME = 'southpark.cc.com:español'
    _VALID_URL = 'https?://(?:www\\.)?(?P<url>southpark\\.cc\\.com/es/episodios/(?P<id>.+?)(\\?|#|$))'
    _RETURN_TYPE = 'playlist'


class SouthParkLatIE(SouthParkIE):
    _module = 'yt_dlp.extractor.southpark'
    IE_NAME = 'southpark.lat'
    _VALID_URL = 'https?://(?:www\\.)?southpark\\.lat/(?:en/)?(?:video-?clips?|collections|episod(?:e|io)s)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class SouthParkNlIE(SouthParkIE):
    _module = 'yt_dlp.extractor.southpark'
    IE_NAME = 'southpark.nl'
    _VALID_URL = 'https?://(?:www\\.)?(?P<url>southpark\\.nl/(?:clips|(?:full-)?episodes|collections)/(?P<id>.+?)(\\?|#|$))'
    _RETURN_TYPE = 'playlist'


class SovietsClosetBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sovietscloset'
    IE_NAME = 'SovietsClosetBase'


class SovietsClosetIE(SovietsClosetBaseIE):
    _module = 'yt_dlp.extractor.sovietscloset'
    IE_NAME = 'SovietsCloset'
    _VALID_URL = 'https?://(?:www\\.)?sovietscloset\\.com/video/(?P<id>[0-9]+)/?'
    _RETURN_TYPE = 'video'


class SovietsClosetPlaylistIE(SovietsClosetBaseIE):
    _module = 'yt_dlp.extractor.sovietscloset'
    IE_NAME = 'SovietsClosetPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?sovietscloset\\.com/(?!video)(?P<id>[^#?]+)'
    _RETURN_TYPE = 'playlist'


class SpankBangIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spankbang'
    IE_NAME = 'SpankBang'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:[^/]+\\.)?spankbang\\.com/\n                        (?:\n                            (?P<id>[\\da-z]+)/(?:video|play|embed)\\b|\n                            [\\da-z]+-(?P<id_2>[\\da-z]+)/playlist/[^/?#&]+\n                        )\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class SpankBangPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spankbang'
    IE_NAME = 'SpankBangPlaylist'
    _VALID_URL = 'https?://(?:[^/]+\\.)?spankbang\\.com/(?P<id>[\\da-z]+)/playlist/(?P<display_id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class SpankwireIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spankwire'
    IE_NAME = 'Spankwire'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?spankwire\\.com/\n                        (?:\n                            [^/]+/video|\n                            EmbedPlayer\\.aspx/?\\?.*?\\bArticleId=\n                        )\n                        (?P<id>\\d+)\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class SpiegelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spiegel'
    IE_NAME = 'Spiegel'
    _VALID_URL = 'https?://(?:www\\.)?(?:spiegel|manager-magazin)\\.de(?:/[^/]+)+/[^/]*-(?P<id>[0-9]+|[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})(?:-embed|-iframe)?(?:\\.html)?(?:$|[#?])'
    _RETURN_TYPE = 'video'


class BellatorIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.spike'
    IE_NAME = 'Bellator'
    _VALID_URL = 'https?://(?:www\\.)?bellator\\.com/[^/]+/[\\da-z]{6}(?:[/?#&]|$)'
    _RETURN_TYPE = 'playlist'


class ParamountNetworkIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.spike'
    IE_NAME = 'ParamountNetwork'
    _VALID_URL = 'https?://(?:www\\.)?paramountnetwork\\.com/[^/]+/[\\da-z]{6}(?:[/?#&]|$)'
    _RETURN_TYPE = 'video'


class StagePlusVODConcertIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.stageplus'
    IE_NAME = 'StagePlusVODConcert'
    _VALID_URL = 'https?://(?:www\\.)?stage-plus\\.com/video/(?P<id>vod_concert_\\w+)'
    _NETRC_MACHINE = 'stageplus'
    _RETURN_TYPE = 'playlist'


class StarTrekIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.startrek'
    IE_NAME = 'StarTrek'
    _VALID_URL = '(?P<base>https?://(?:intl|www)\\.startrek\\.com)/videos/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class StitcherBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.stitcher'
    IE_NAME = 'StitcherBase'


class StitcherIE(StitcherBaseIE):
    _module = 'yt_dlp.extractor.stitcher'
    IE_NAME = 'Stitcher'
    _VALID_URL = 'https?://(?:www\\.)?stitcher\\.com/(?:podcast|show)/(?:[^/]+/)+e(?:pisode)?/(?:[^/#?&]+-)?(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class StitcherShowIE(StitcherBaseIE):
    _module = 'yt_dlp.extractor.stitcher'
    IE_NAME = 'StitcherShow'
    _VALID_URL = 'https?://(?:www\\.)?stitcher\\.com/(?:podcast|show)/(?P<id>[^/#?&]+)/?(?:[?#&]|$)'
    _RETURN_TYPE = 'playlist'


class Sport5IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sport5'
    IE_NAME = 'Sport5'
    _VALID_URL = 'https?://(?:www|vod)?\\.sport5\\.co\\.il/.*\\b(?:Vi|docID)=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class SportBoxIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sportbox'
    IE_NAME = 'SportBox'
    _VALID_URL = 'https?://(?:news\\.sportbox|matchtv)\\.ru/vdl/player(?:/[^/]+/|\\?.*?\\bn?id=)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class SportDeutschlandIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sportdeutschland'
    IE_NAME = 'SportDeutschland'
    _VALID_URL = 'https?://sportdeutschland\\.tv/(?P<id>(?:[^/]+/)?[^?#/&]+)'
    _RETURN_TYPE = 'any'


class SpotifyBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spotify'
    IE_NAME = 'SpotifyBase'
    _WORKING = False


class SpotifyIE(SpotifyBaseIE):
    _module = 'yt_dlp.extractor.spotify'
    IE_NAME = 'spotify'
    _VALID_URL = 'https?://open\\.spotify\\.com/(?:embed-podcast/|embed/|)episode/(?P<id>[^/?&#]+)'
    _WORKING = False
    IE_DESC = 'Spotify episodes'
    _RETURN_TYPE = 'video'


class SpotifyShowIE(SpotifyBaseIE):
    _module = 'yt_dlp.extractor.spotify'
    IE_NAME = 'spotify:show'
    _VALID_URL = 'https?://open\\.spotify\\.com/(?:embed-podcast/|embed/|)show/(?P<id>[^/?&#]+)'
    _WORKING = False
    IE_DESC = 'Spotify shows'
    _RETURN_TYPE = 'playlist'


class SpreakerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spreaker'
    IE_NAME = 'Spreaker'
    _VALID_URL = '(?x)\n                    https?://\n                        api\\.spreaker\\.com/\n                        (?:\n                            (?:download/)?episode|\n                            v2/episodes\n                        )/\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class SpreakerPageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spreaker'
    IE_NAME = 'SpreakerPage'
    _VALID_URL = 'https?://(?:www\\.)?spreaker\\.com/user/[^/]+/(?P<id>[^/?#&]+)'


class SpreakerShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spreaker'
    IE_NAME = 'SpreakerShow'
    _VALID_URL = 'https?://api\\.spreaker\\.com/show/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class SpreakerShowPageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.spreaker'
    IE_NAME = 'SpreakerShowPage'
    _VALID_URL = 'https?://(?:www\\.)?spreaker\\.com/show/(?P<id>[^/?#&]+)'


class SpringboardPlatformIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.springboardplatform'
    IE_NAME = 'SpringboardPlatform'
    _VALID_URL = '(?x)\n                    https?://\n                        cms\\.springboardplatform\\.com/\n                        (?:\n                            (?:previews|embed_iframe)/(?P<index>\\d+)/video/(?P<id>\\d+)|\n                            xml_feeds_advanced/index/(?P<index_2>\\d+)/rss3/(?P<id_2>\\d+)\n                        )\n                    '
    _RETURN_TYPE = 'video'


class SproutIE(AdobePassIE):
    _module = 'yt_dlp.extractor.sprout'
    IE_NAME = 'Sprout'
    _VALID_URL = 'https?://(?:www\\.)?(?:sproutonline|universalkids)\\.com/(?:watch|(?:[^/]+/)*videos)/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class SRGSSRIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.srgssr'
    IE_NAME = 'SRGSSR'
    _VALID_URL = '(?x)\n                    (?:\n                        https?://tp\\.srgssr\\.ch/p(?:/[^/]+)+\\?urn=urn|\n                        srgssr\n                    ):\n                    (?P<bu>\n                        srf|rts|rsi|rtr|swi\n                    ):(?:[^:]+:)?\n                    (?P<type>\n                        video|audio\n                    ):\n                    (?P<id>\n                        [0-9a-f\\-]{36}|\\d+\n                    )\n                    '


class RTSIE(SRGSSRIE):
    _module = 'yt_dlp.extractor.rts'
    IE_NAME = 'RTS'
    _VALID_URL = 'rts:(?P<rts_id>\\d+)|https?://(?:.+?\\.)?rts\\.ch/(?:[^/]+/){2,}(?P<id>[0-9]+)-(?P<display_id>.+?)\\.html'
    IE_DESC = 'RTS.ch'
    _RETURN_TYPE = 'any'


class SRGSSRPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.srgssr'
    IE_NAME = 'SRGSSRPlay'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:(?:www|play)\\.)?\n                        (?P<bu>srf|rts|rsi|rtr|swissinfo)\\.ch/play/(?:tv|radio)/\n                        (?:\n                            [^/]+/(?P<type>video|audio)/[^?]+|\n                            popup(?P<type_2>video|audio)player\n                        )\n                        \\?.*?\\b(?:id=|urn=urn:[^:]+:video:)(?P<id>[0-9a-f\\-]{36}|\\d+)\n                    '
    IE_DESC = 'srf.ch, rts.ch, rsi.ch, rtr.ch and swissinfo.ch play sites'
    _RETURN_TYPE = 'video'


class SRMediathekIE(ARDMediathekBaseIE):
    _module = 'yt_dlp.extractor.srmediathek'
    IE_NAME = 'sr:mediathek'
    _VALID_URL = 'https?://sr-mediathek(?:\\.sr-online)?\\.de/index\\.php\\?.*?&id=(?P<id>[0-9]+)'
    IE_DESC = 'Saarländischer Rundfunk'
    _RETURN_TYPE = 'video'


class WrestleUniverseBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wrestleuniverse'
    IE_NAME = 'WrestleUniverseBase'
    _NETRC_MACHINE = 'wrestleuniverse'


class StacommuBaseIE(WrestleUniverseBaseIE):
    _module = 'yt_dlp.extractor.stacommu'
    IE_NAME = 'StacommuBase'
    _NETRC_MACHINE = 'stacommu'


class StacommuLiveIE(StacommuBaseIE):
    _module = 'yt_dlp.extractor.stacommu'
    IE_NAME = 'StacommuLive'
    _VALID_URL = 'https?://www\\.stacommu\\.jp/live/(?P<id>[\\da-zA-Z]+)'
    _NETRC_MACHINE = 'stacommu'
    _RETURN_TYPE = 'video'


class StacommuVODIE(StacommuBaseIE):
    _module = 'yt_dlp.extractor.stacommu'
    IE_NAME = 'StacommuVOD'
    _VALID_URL = 'https?://www\\.stacommu\\.jp/videos/episodes/(?P<id>[\\da-zA-Z]+)'
    _NETRC_MACHINE = 'stacommu'
    _RETURN_TYPE = 'video'


class StanfordOpenClassroomIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.stanfordoc'
    IE_NAME = 'stanfordoc'
    _VALID_URL = 'https?://openclassroom\\.stanford\\.edu(?P<path>/?|(/MainFolder/(?:HomePage|CoursePage|VideoPage)\\.php([?]course=(?P<course>[^&]+)(&video=(?P<video>[^&]+))?(&.*)?)?))$'
    IE_DESC = 'Stanford Open ClassRoom'
    _RETURN_TYPE = 'video'


class StarTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.startv'
    IE_NAME = 'startv'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?startv\\.com\\.tr/\n        (?:\n            (?:dizi|program)/(?:[^/?#&]+)/(?:bolumler|fragmanlar|ekstralar)|\n            video/arsiv/(?:dizi|program)/(?:[^/?#&]+)\n        )/\n        (?P<id>[^/?#&]+)\n    '
    _RETURN_TYPE = 'video'


class SteamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.steam'
    IE_NAME = 'Steam'
    _VALID_URL = '(?x)\n        https?://(?:store\\.steampowered|steamcommunity)\\.com/\n            (?:agecheck/)?\n            (?P<urltype>video|app)/ #If the page is only for videos or for a game\n            (?P<gameID>\\d+)/?\n            (?P<videoID>\\d*)(?P<extra>\\??) # For urltype == video we sometimes get the videoID\n        |\n        https?://(?:www\\.)?steamcommunity\\.com/sharedfiles/filedetails/\\?id=(?P<fileID>[0-9]+)\n    '
    _RETURN_TYPE = 'any'


class SteamCommunityBroadcastIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.steam'
    IE_NAME = 'SteamCommunityBroadcast'
    _VALID_URL = 'https?://steamcommunity\\.(?:com)/broadcast/watch/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class StoryFireBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.storyfire'
    IE_NAME = 'StoryFireBase'


class StoryFireIE(StoryFireBaseIE):
    _module = 'yt_dlp.extractor.storyfire'
    IE_NAME = 'StoryFire'
    _VALID_URL = 'https?://(?:www\\.)?storyfire\\.com/video-details/(?P<id>[0-9a-f]{24})'
    _RETURN_TYPE = 'video'


class StoryFireUserIE(StoryFireBaseIE):
    _module = 'yt_dlp.extractor.storyfire'
    IE_NAME = 'StoryFireUser'
    _VALID_URL = 'https?://(?:www\\.)?storyfire\\.com/user/(?P<id>[^/]+)/video'
    _RETURN_TYPE = 'playlist'


class StoryFireSeriesIE(StoryFireBaseIE):
    _module = 'yt_dlp.extractor.storyfire'
    IE_NAME = 'StoryFireSeries'
    _VALID_URL = 'https?://(?:www\\.)?storyfire\\.com/write/series/stories/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'playlist'


class StreamableIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.streamable'
    IE_NAME = 'Streamable'
    _VALID_URL = 'https?://streamable\\.com/(?:[es]/)?(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class StreamanityIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.streamanity'
    IE_NAME = 'Streamanity'
    _VALID_URL = 'https?://(?:www\\.)?streamanity\\.com/video/(?P<id>[A-Za-z0-9]+)'
    _RETURN_TYPE = 'video'


class StreamcloudIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.streamcloud'
    IE_NAME = 'streamcloud.eu'
    _VALID_URL = 'https?://streamcloud\\.eu/(?P<id>[a-zA-Z0-9_-]+)(?:/(?P<fname>[^#?]*)\\.html)?'
    _RETURN_TYPE = 'video'


class StreamCZIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.streamcz'
    IE_NAME = 'StreamCZ'
    _VALID_URL = 'https?://(?:www\\.)?(?:stream|televizeseznam)\\.cz/[^?#]+/(?P<display_id>[^?#]+)-(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class StreamFFIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.streamff'
    IE_NAME = 'StreamFF'
    _VALID_URL = 'https?://(?:www\\.)?streamff\\.com/v/(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'


class StreetVoiceIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.streetvoice'
    IE_NAME = 'StreetVoice'
    _VALID_URL = 'https?://(?:.+?\\.)?streetvoice\\.com/[^/]+/songs/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class StretchInternetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.stretchinternet'
    IE_NAME = 'StretchInternet'
    _VALID_URL = 'https?://portal\\.stretchinternet\\.com/[^/]+/(?:portal|full)\\.htm\\?.*?\\beventId=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class StripchatIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.stripchat'
    IE_NAME = 'Stripchat'
    _VALID_URL = 'https?://stripchat\\.com/(?P<id>[^/?#]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class STVPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.stv'
    IE_NAME = 'stv:player'
    _VALID_URL = 'https?://player\\.stv\\.tv/(?P<type>episode|video)/(?P<id>[a-z0-9]{4})'
    _RETURN_TYPE = 'video'


class SubstackIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.substack'
    IE_NAME = 'Substack'
    _VALID_URL = 'https?://(?P<username>[\\w-]+)\\.substack\\.com/p/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class SunPornoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sunporno'
    IE_NAME = 'SunPorno'
    _VALID_URL = 'https?://(?:(?:www\\.)?sunporno\\.com/videos|embeds\\.sunporno\\.com/embed)/(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class SverigesRadioBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sverigesradio'
    IE_NAME = 'SverigesRadioBase'


class SverigesRadioEpisodeIE(SverigesRadioBaseIE):
    _module = 'yt_dlp.extractor.sverigesradio'
    IE_NAME = 'sverigesradio:episode'
    _VALID_URL = 'https?://(?:www\\.)?sverigesradio\\.se/(?:sida/)?avsnitt/(?:(?P<id>\\d+)|(?P<slug>[\\w-]+))(?:$|[#?])'
    _RETURN_TYPE = 'video'


class SverigesRadioPublicationIE(SverigesRadioBaseIE):
    _module = 'yt_dlp.extractor.sverigesradio'
    IE_NAME = 'sverigesradio:publication'
    _VALID_URL = 'https?://(?:www\\.)?sverigesradio\\.se/(?:sida/)?(?:artikel|gruppsida)(?:\\.aspx\\?.*?\\bartikel=(?P<id>[0-9]+)|/(?P<slug>[\\w-]+))'
    _RETURN_TYPE = 'video'


class SVTBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.svt'
    IE_NAME = 'SVTBase'


class SVTIE(SVTBaseIE):
    _module = 'yt_dlp.extractor.svt'
    IE_NAME = 'SVT'
    _VALID_URL = 'https?://(?:www\\.)?svt\\.se/wd\\?(?:.*?&)?widgetId=(?P<widget_id>\\d+)&.*?\\barticleId=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class SVTPageIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.svt'
    IE_NAME = 'SVTPage'
    _VALID_URL = 'https?://(?:www\\.)?svt\\.se/(?P<path>(?:[^/]+/)*(?P<id>[^/?&#]+))'
    _RETURN_TYPE = 'any'

    @classmethod
    def suitable(cls, url):
        return False if SVTIE.suitable(url) or SVTPlayIE.suitable(url) else super(SVTPageIE, cls).suitable(url)


class SVTPlayBaseIE(SVTBaseIE):
    _module = 'yt_dlp.extractor.svt'
    IE_NAME = 'SVTPlayBase'


class SVTPlayIE(SVTPlayBaseIE):
    _module = 'yt_dlp.extractor.svt'
    IE_NAME = 'SVTPlay'
    _VALID_URL = '(?x)\n                    (?:\n                        (?:\n                            svt:|\n                            https?://(?:www\\.)?svt\\.se/barnkanalen/barnplay/[^/]+/\n                        )\n                        (?P<svt_id>[^/?#&]+)|\n                        https?://(?:www\\.)?(?:svtplay|oppetarkiv)\\.se/(?:video|klipp|kanaler)/(?P<id>[^/?#&]+)\n                        (?:.*?(?:modalId|id)=(?P<modal_id>[\\da-zA-Z-]+))?\n                    )\n                    '
    IE_DESC = 'SVT Play and Öppet arkiv'
    _RETURN_TYPE = 'video'


class SVTSeriesIE(SVTPlayBaseIE):
    _module = 'yt_dlp.extractor.svt'
    IE_NAME = 'SVTSeries'
    _VALID_URL = 'https?://(?:www\\.)?svtplay\\.se/(?P<id>[^/?&#]+)(?:.+?\\btab=(?P<season_slug>[^&#]+))?'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if SVTIE.suitable(url) or SVTPlayIE.suitable(url) else super(SVTSeriesIE, cls).suitable(url)


class SwearnetEpisodeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.swearnet'
    IE_NAME = 'SwearnetEpisode'
    _VALID_URL = 'https?://www\\.swearnet\\.com/shows/(?P<id>[\\w-]+)/seasons/(?P<season_num>\\d+)/episodes/(?P<episode_num>\\d+)'
    _RETURN_TYPE = 'video'


class SWRMediathekIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.swrmediathek'
    IE_NAME = 'SWRMediathek'
    _VALID_URL = 'https?://(?:www\\.)?swrmediathek\\.de/(?:content/)?player\\.htm\\?show=(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class SYVDKIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.syvdk'
    IE_NAME = 'SYVDK'
    _VALID_URL = 'https?://(?:www\\.)?24syv\\.dk/episode/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class SyfyIE(AdobePassIE):
    _module = 'yt_dlp.extractor.syfy'
    IE_NAME = 'Syfy'
    _VALID_URL = 'https?://(?:www\\.)?syfy\\.com/(?:[^/]+/)?videos/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class SztvHuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.sztvhu'
    IE_NAME = 'SztvHu'
    _VALID_URL = 'https?://(?:(?:www\\.)?sztv\\.hu|www\\.tvszombathely\\.hu)/(?:[^/]+)/.+-(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class TagesschauIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tagesschau'
    IE_NAME = 'Tagesschau'
    _VALID_URL = 'https?://(?:www\\.)?tagesschau\\.de/(?P<path>[^/]+/(?:[^/]+/)*?(?P<id>[^/#?]+?(?:-?[0-9]+)?))(?:~_?[^/#?]+?)?\\.html'
    _RETURN_TYPE = 'any'


class TassIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tass'
    IE_NAME = 'Tass'
    _VALID_URL = 'https?://(?:tass\\.ru|itar-tass\\.com)/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TBSIE(TurnerBaseIE):
    _module = 'yt_dlp.extractor.tbs'
    IE_NAME = 'TBS'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>tbs|tntdrama)\\.com(?P<path>/(?:movies|watchtnt|watchtbs|shows/[^/]+/(?:clips|season-\\d+/episode-\\d+))/(?P<id>[^/?#]+))'
    _RETURN_TYPE = 'video'


class TDSLifewayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tdslifeway'
    IE_NAME = 'TDSLifeway'
    _VALID_URL = 'https?://tds\\.lifeway\\.com/v1/trainingdeliverysystem/courses/(?P<id>\\d+)/index\\.html'
    _RETURN_TYPE = 'video'


class TeachableBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.teachable'
    IE_NAME = 'TeachableBase'
    _NETRC_MACHINE = 'teachable'


class TeachableIE(TeachableBaseIE):
    _module = 'yt_dlp.extractor.teachable'
    IE_NAME = 'Teachable'
    _VALID_URL = '(?x)\n                    (?:\n                        teachable:https?://(?P<site_t>[^/]+)|\n                        https?://(?:www\\.)?(?P<site>v1\\.upskillcourses\\.com|gns3\\.teachable\\.com|academyhacker\\.com|stackskills\\.com|market\\.saleshacker\\.com|learnability\\.org|edurila\\.com|courses\\.workitdaily\\.com)\n                    )\n                    /courses/[^/]+/lectures/(?P<id>\\d+)\n                    '
    _NETRC_MACHINE = 'teachable'
    _RETURN_TYPE = 'video'


class TeachableCourseIE(TeachableBaseIE):
    _module = 'yt_dlp.extractor.teachable'
    IE_NAME = 'TeachableCourse'
    _VALID_URL = '(?x)\n                        (?:\n                            teachable:https?://(?P<site_t>[^/]+)|\n                            https?://(?:www\\.)?(?P<site>v1\\.upskillcourses\\.com|gns3\\.teachable\\.com|academyhacker\\.com|stackskills\\.com|market\\.saleshacker\\.com|learnability\\.org|edurila\\.com|courses\\.workitdaily\\.com)\n                        )\n                        /(?:courses|p)/(?:enrolled/)?(?P<id>[^/?#&]+)\n                    '
    _NETRC_MACHINE = 'teachable'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if TeachableIE.suitable(url) else super(
            TeachableCourseIE, cls).suitable(url)


class TeacherTubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.teachertube'
    IE_NAME = 'teachertube'
    _VALID_URL = 'https?://(?:www\\.)?teachertube\\.com/(viewVideo\\.php\\?video_id=|music\\.php\\?music_id=|video/(?:[\\da-z-]+-)?|audio/)(?P<id>\\d+)'
    IE_DESC = 'teachertube.com videos'
    _RETURN_TYPE = 'video'


class TeacherTubeUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.teachertube'
    IE_NAME = 'teachertube:user:collection'
    _VALID_URL = 'https?://(?:www\\.)?teachertube\\.com/(user/profile|collection)/(?P<user>[0-9a-zA-Z]+)/?'
    IE_DESC = 'teachertube.com user and collection videos'
    _RETURN_TYPE = 'playlist'


class TeachingChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.teachingchannel'
    IE_NAME = 'TeachingChannel'
    _VALID_URL = 'https?://(?:www\\.)?teachingchannel\\.org/videos?/(?P<id>[^/?&#]+)'
    _RETURN_TYPE = 'video'


class TeamcocoBaseIE(TurnerBaseIE):
    _module = 'yt_dlp.extractor.teamcoco'
    IE_NAME = 'TeamcocoBase'


class TeamcocoIE(TeamcocoBaseIE):
    _module = 'yt_dlp.extractor.teamcoco'
    IE_NAME = 'Teamcoco'
    _VALID_URL = 'https?://(?:www\\.)?teamcoco\\.com/(?P<id>([^/]+/)*[^/?#]+)'
    _RETURN_TYPE = 'video'


class ConanClassicIE(TeamcocoBaseIE):
    _module = 'yt_dlp.extractor.teamcoco'
    IE_NAME = 'ConanClassic'
    _VALID_URL = 'https?://(?:(?:www\\.)?conanclassic|conan25\\.teamcoco)\\.com/(?P<id>([^/]+/)*[^/?#]+)'
    _RETURN_TYPE = 'video'


class TeamTreeHouseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.teamtreehouse'
    IE_NAME = 'TeamTreeHouse'
    _VALID_URL = 'https?://(?:www\\.)?teamtreehouse\\.com/library/(?P<id>[^/]+)'
    _NETRC_MACHINE = 'teamtreehouse'
    _RETURN_TYPE = 'any'


class TechTalksIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.techtalks'
    IE_NAME = 'TechTalks'
    _VALID_URL = 'https?://techtalks\\.tv/talks/(?:[^/]+/)?(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class TedEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ted'
    IE_NAME = 'TedEmbed'
    _VALID_URL = 'https?://embed(?:-ssl)?\\.ted\\.com/'
    _RETURN_TYPE = 'video'


class TedBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ted'
    IE_NAME = 'TedBase'


class TedPlaylistIE(TedBaseIE):
    _module = 'yt_dlp.extractor.ted'
    IE_NAME = 'TedPlaylist'
    _VALID_URL = 'https?://www\\.ted\\.com/(?:playlists(?:/\\d+)?)(?:/lang/[^/#?]+)?/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class TedSeriesIE(TedBaseIE):
    _module = 'yt_dlp.extractor.ted'
    IE_NAME = 'TedSeries'
    _VALID_URL = 'https?://www\\.ted\\.com/(?:series)(?:/lang/[^/#?]+)?/(?P<id>[\\w-]+)(?:#season_(?P<season>\\d+))?'
    _RETURN_TYPE = 'playlist'


class TedTalkIE(TedBaseIE):
    _module = 'yt_dlp.extractor.ted'
    IE_NAME = 'TedTalk'
    _VALID_URL = 'https?://www\\.ted\\.com/(?:talks)(?:/lang/[^/#?]+)?/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class Tele5IE(DPlayIE):
    _module = 'yt_dlp.extractor.tele5'
    IE_NAME = 'Tele5'
    _VALID_URL = 'https?://(?:www\\.)?tele5\\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class Tele13IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tele13'
    IE_NAME = 'Tele13'
    _VALID_URL = '^https?://(?:www\\.)?t13\\.cl/videos(?:/[^/]+)+/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class TeleBruxellesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telebruxelles'
    IE_NAME = 'TeleBruxelles'
    _VALID_URL = 'https?://(?:www\\.)?(?:telebruxelles|bx1)\\.be/(?:[^/]+/)*(?P<id>[^/#?]+)'
    _RETURN_TYPE = 'video'


class TelecaribePlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telecaribe'
    IE_NAME = 'TelecaribePlay'
    _VALID_URL = 'https?://(?:www\\.)?play\\.telecaribe\\.co/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'any'


class TelecincoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telecinco'
    IE_NAME = 'Telecinco'
    _VALID_URL = 'https?://(?:www\\.)?(?:telecinco\\.es|cuatro\\.com|mediaset\\.es)/(?:[^/]+/)+(?P<id>.+?)\\.html'
    IE_DESC = 'telecinco.es, cuatro.com and mediaset.es'
    _RETURN_TYPE = 'any'


class MiTeleIE(TelecincoIE):
    _module = 'yt_dlp.extractor.mitele'
    IE_NAME = 'MiTele'
    _VALID_URL = 'https?://(?:www\\.)?mitele\\.es/(?:[^/]+/)+(?P<id>[^/]+)/player'
    IE_DESC = 'mitele.es'
    age_limit = 16
    _RETURN_TYPE = 'video'


class TelegraafIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telegraaf'
    IE_NAME = 'Telegraaf'
    _VALID_URL = 'https?://(?:www\\.)?telegraaf\\.nl/video/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TelegramEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telegram'
    IE_NAME = 'telegram:embed'
    _VALID_URL = 'https?://t\\.me/(?P<channel_id>[^/]+)/(?P<id>\\d+)'
    _RETURN_TYPE = 'any'


class TeleMBIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telemb'
    IE_NAME = 'TeleMB'
    _VALID_URL = 'https?://(?:www\\.)?telemb\\.be/(?P<display_id>.+?)_d_(?P<id>\\d+)\\.html'
    _RETURN_TYPE = 'video'


class TelemundoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telemundo'
    IE_NAME = 'Telemundo'
    _VALID_URL = 'https?:\\/\\/(?:www\\.)?telemundo\\.com\\/.+?video\\/[^\\/]+(?P<id>tmvo\\d{7})'
    _RETURN_TYPE = 'video'


class TeleQuebecBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telequebec'
    IE_NAME = 'TeleQuebecBase'


class TeleQuebecIE(TeleQuebecBaseIE):
    _module = 'yt_dlp.extractor.telequebec'
    IE_NAME = 'TeleQuebec'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            zonevideo\\.telequebec\\.tv/media|\n                            coucou\\.telequebec\\.tv/videos\n                        )/(?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class TeleQuebecSquatIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telequebec'
    IE_NAME = 'TeleQuebecSquat'
    _VALID_URL = 'https://squat\\.telequebec\\.tv/videos/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TeleQuebecEmissionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telequebec'
    IE_NAME = 'TeleQuebecEmission'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            [^/]+\\.telequebec\\.tv/emissions/|\n                            (?:www\\.)?telequebec\\.tv/\n                        )\n                        (?P<id>[^?#&]+)\n                    '
    _RETURN_TYPE = 'video'


class TeleQuebecLiveIE(TeleQuebecBaseIE):
    _module = 'yt_dlp.extractor.telequebec'
    IE_NAME = 'TeleQuebecLive'
    _VALID_URL = 'https?://zonevideo\\.telequebec\\.tv/(?P<id>endirect)'
    _RETURN_TYPE = 'video'


class TeleQuebecVideoIE(TeleQuebecBaseIE):
    _module = 'yt_dlp.extractor.telequebec'
    IE_NAME = 'TeleQuebecVideo'
    _VALID_URL = 'https?://video\\.telequebec\\.tv/player(?:-live)?/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TeleTaskIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.teletask'
    IE_NAME = 'TeleTask'
    _VALID_URL = 'https?://(?:www\\.)?tele-task\\.de/archive/video/html5/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'playlist'


class TelewebionIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.telewebion'
    IE_NAME = 'Telewebion'
    _VALID_URL = 'https?://(?:www\\.)?telewebion\\.com/#!/episode/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TempoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tempo'
    IE_NAME = 'Tempo'
    _VALID_URL = 'https?://video\\.tempo\\.co/\\w+/\\d+/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class IVXPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tempo'
    IE_NAME = 'IVXPlayer'
    _VALID_URL = 'ivxplayer:(?P<video_id>\\d+):(?P<player_key>\\w+)'
    _RETURN_TYPE = 'video'


class TencentBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'TencentBase'


class WeTvBaseIE(TencentBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'WeTvBase'


class IflixBaseIE(WeTvBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'IflixBase'


class IflixEpisodeIE(IflixBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'iflix:episode'
    _VALID_URL = 'https?://(?:www\\.)?iflix\\.com/(?:[^?#]+/)?play/(?P<series_id>\\w+)(?:-[^?#]+)?/(?P<id>\\w+)(?:-[^?#]+)?'
    _RETURN_TYPE = 'video'


class IflixSeriesIE(IflixBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'IflixSeries'
    _VALID_URL = 'https?://(?:www\\.)?iflix\\.com/(?:[^?#]+/)?play/(?P<id>\\w+)(?:-[^/?#]+)?/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class VQQBaseIE(TencentBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'VQQBase'


class VQQSeriesIE(VQQBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'vqq:series'
    _VALID_URL = 'https?://v\\.qq\\.com/x/cover/(?P<id>\\w+)\\.html/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class VQQVideoIE(VQQBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'vqq:video'
    _VALID_URL = 'https?://v\\.qq\\.com/x/(?:page|cover/(?P<series_id>\\w+))/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class WeTvEpisodeIE(WeTvBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'wetv:episode'
    _VALID_URL = 'https?://(?:www\\.)?wetv\\.vip/(?:[^?#]+/)?play/(?P<series_id>\\w+)(?:-[^?#]+)?/(?P<id>\\w+)(?:-[^?#]+)?'
    _RETURN_TYPE = 'video'


class WeTvSeriesIE(WeTvBaseIE):
    _module = 'yt_dlp.extractor.tencent'
    IE_NAME = 'WeTvSeries'
    _VALID_URL = 'https?://(?:www\\.)?wetv\\.vip/(?:[^?#]+/)?play/(?P<id>\\w+)(?:-[^/?#]+)?/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class TennisTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tennistv'
    IE_NAME = 'TennisTV'
    _VALID_URL = 'https?://(?:www\\.)?tennistv\\.com/videos/(?P<id>[-a-z0-9]+)'
    _NETRC_MACHINE = 'tennistv'
    _RETURN_TYPE = 'video'


class TenPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tenplay'
    IE_NAME = 'TenPlay'
    _VALID_URL = 'https?://(?:www\\.)?10play\\.com\\.au/(?:[^/]+/)+(?P<id>tpv\\d{6}[a-z]{5})'
    _NETRC_MACHINE = '10play'
    age_limit = 15
    _RETURN_TYPE = 'video'


class TestURLIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.testurl'
    IE_NAME = 'TestURL'
    _VALID_URL = 'test(?:url)?:(?P<extractor>.*?)(?:_(?P<num>\\d+|all))?$'
    IE_DESC = False


class TF1IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tf1'
    IE_NAME = 'TF1'
    _VALID_URL = 'https?://(?:www\\.)?tf1\\.fr/[^/]+/(?P<program_slug>[^/]+)/videos/(?P<id>[^/?&#]+)\\.html'
    _RETURN_TYPE = 'video'


class TFOIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tfo'
    IE_NAME = 'TFO'
    _VALID_URL = 'https?://(?:www\\.)?tfo\\.org/(?:en|fr)/(?:[^/]+/){2}(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TheHoleTvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.theholetv'
    IE_NAME = 'TheHoleTv'
    _VALID_URL = 'https?://(?:www\\.)?the-hole\\.tv/episodes/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class TheInterceptIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.theintercept'
    IE_NAME = 'TheIntercept'
    _VALID_URL = 'https?://theintercept\\.com/fieldofvision/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class ThePlatformIE(ThePlatformBaseIE, AdobePassIE):
    _module = 'yt_dlp.extractor.theplatform'
    IE_NAME = 'ThePlatform'
    _VALID_URL = '(?x)\n        (?:https?://(?:link|player)\\.theplatform\\.com/[sp]/(?P<provider_id>[^/]+)/\n           (?:(?:(?:[^/]+/)+select/)?(?P<media>media/(?:guid/\\d+/)?)?|(?P<config>(?:[^/\\?]+/(?:swf|config)|onsite)/select/))?\n         |theplatform:)(?P<id>[^/\\?&]+)'
    _RETURN_TYPE = 'video'


class AENetworksBaseIE(ThePlatformIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'AENetworksBase'
    _VALID_URL = '(?x)\n        (?:https?://(?:link|player)\\.theplatform\\.com/[sp]/(?P<provider_id>[^/]+)/\n           (?:(?:(?:[^/]+/)+select/)?(?P<media>media/(?:guid/\\d+/)?)?|(?P<config>(?:[^/\\?]+/(?:swf|config)|onsite)/select/))?\n         |theplatform:)(?P<id>[^/\\?&]+)'


class AENetworksListBaseIE(AENetworksBaseIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'AENetworksListBase'
    _VALID_URL = '(?x)\n        (?:https?://(?:link|player)\\.theplatform\\.com/[sp]/(?P<provider_id>[^/]+)/\n           (?:(?:(?:[^/]+/)+select/)?(?P<media>media/(?:guid/\\d+/)?)?|(?P<config>(?:[^/\\?]+/(?:swf|config)|onsite)/select/))?\n         |theplatform:)(?P<id>[^/\\?&]+)'


class AENetworksIE(AENetworksBaseIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'aenetworks'
    _VALID_URL = '(?x)https?://\n        (?:(?:www|play|watch)\\.)?\n        (?P<domain>\n            (?:history(?:vault)?|aetv|mylifetime|lifetimemovieclub)\\.com|\n            fyi\\.tv\n        )/(?P<id>\n        shows/[^/]+/season-\\d+/episode-\\d+|\n        (?:\n            (?:movie|special)s/[^/]+|\n            (?:shows/[^/]+/)?videos\n        )/[^/?#&]+\n    )'
    IE_DESC = 'A+E Networks: A&E, Lifetime, History.com, FYI Network and History Vault'
    _RETURN_TYPE = 'video'


class AENetworksCollectionIE(AENetworksListBaseIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'aenetworks:collection'
    _VALID_URL = '(?x)https?://\n        (?:(?:www|play|watch)\\.)?\n        (?P<domain>\n            (?:history(?:vault)?|aetv|mylifetime|lifetimemovieclub)\\.com|\n            fyi\\.tv\n        )/(?:[^/]+/)*(?:list|collections)/(?P<id>[^/?#&]+)/?(?:[?#&]|$)'
    _RETURN_TYPE = 'playlist'


class AENetworksShowIE(AENetworksListBaseIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'aenetworks:show'
    _VALID_URL = '(?x)https?://\n        (?:(?:www|play|watch)\\.)?\n        (?P<domain>\n            (?:history(?:vault)?|aetv|mylifetime|lifetimemovieclub)\\.com|\n            fyi\\.tv\n        )/shows/(?P<id>[^/?#&]+)/?(?:[?#&]|$)'
    _RETURN_TYPE = 'playlist'


class HistoryTopicIE(AENetworksBaseIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'history:topic'
    _VALID_URL = 'https?://(?:www\\.)?history\\.com/topics/[^/]+/(?P<id>[\\w+-]+?)-video'
    IE_DESC = 'History.com Topic'
    _RETURN_TYPE = 'video'


class HistoryPlayerIE(AENetworksBaseIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'history:player'
    _VALID_URL = 'https?://(?:www\\.)?(?P<domain>(?:history|biography)\\.com)/player/(?P<id>\\d+)'


class BiographyIE(AENetworksBaseIE):
    _module = 'yt_dlp.extractor.aenetworks'
    IE_NAME = 'Biography'
    _VALID_URL = 'https?://(?:www\\.)?biography\\.com/video/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class AMCNetworksIE(ThePlatformIE):
    _module = 'yt_dlp.extractor.amcnetworks'
    IE_NAME = 'AMCNetworks'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>amc|bbcamerica|ifc|(?:we|sundance)tv)\\.com/(?P<id>(?:movies|shows(?:/[^/]+)+)/[^/?#&]+)'
    _RETURN_TYPE = 'video'


class NBCIE(ThePlatformIE):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'NBC'
    _VALID_URL = 'https?(?P<permalink>://(?:www\\.)?nbc\\.com/(?:classic-tv/)?[^/]+/video/[^/]+/(?P<id>(?:NBCE|n)?\\d+))'
    _RETURN_TYPE = 'video'


class NBCNewsIE(ThePlatformIE):
    _module = 'yt_dlp.extractor.nbc'
    IE_NAME = 'NBCNews'
    _VALID_URL = '(?x)https?://(?:www\\.)?(?:nbcnews|today|msnbc)\\.com/([^/]+/)*(?:.*-)?(?P<id>[^/?]+)'
    _RETURN_TYPE = 'video'


class ThePlatformFeedIE(ThePlatformBaseIE):
    _module = 'yt_dlp.extractor.theplatform'
    IE_NAME = 'ThePlatformFeed'
    _VALID_URL = 'https?://feed\\.theplatform\\.com/f/(?P<provider_id>[^/]+)/(?P<feed_id>[^?/]+)\\?(?:[^&]+&)*(?P<filter>by(?:Gui|I)d=(?P<id>[^&]+))'
    _RETURN_TYPE = 'video'


class CBSBaseIE(ThePlatformFeedIE):
    _module = 'yt_dlp.extractor.cbs'
    IE_NAME = 'CBSBase'
    _VALID_URL = 'https?://feed\\.theplatform\\.com/f/(?P<provider_id>[^/]+)/(?P<feed_id>[^?/]+)\\?(?:[^&]+&)*(?P<filter>by(?:Gui|I)d=(?P<id>[^&]+))'


class CBSIE(CBSBaseIE):
    _module = 'yt_dlp.extractor.cbs'
    IE_NAME = 'CBS'
    _VALID_URL = '(?x)\n        (?:\n            cbs:|\n            https?://(?:www\\.)?(?:\n                cbs\\.com/(?:shows|movies)/(?:video|[^/]+/video|[^/]+)/|\n                colbertlateshow\\.com/(?:video|podcasts)/)\n        )(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class CBSInteractiveIE(CBSIE):
    _module = 'yt_dlp.extractor.cbsinteractive'
    IE_NAME = 'CBSInteractive'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>cnet|zdnet)\\.com/(?:videos|video(?:/share)?)/(?P<id>[^/?]+)'
    _RETURN_TYPE = 'video'


class CorusIE(ThePlatformFeedIE):
    _module = 'yt_dlp.extractor.corus'
    IE_NAME = 'Corus'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?\n                        (?P<domain>\n                            (?:\n                                globaltv|\n                                etcanada|\n                                seriesplus|\n                                wnetwork|\n                                ytv\n                            )\\.com|\n                            (?:\n                                hgtv|\n                                foodnetwork|\n                                slice|\n                                history|\n                                showcase|\n                                bigbrothercanada|\n                                abcspark|\n                                disney(?:channel|lachaine)\n                            )\\.ca\n                        )\n                        /(?:[^/]+/)*\n                        (?:\n                            video\\.html\\?.*?\\bv=|\n                            videos?/(?:[^/]+/)*(?:[a-z0-9-]+-)?\n                        )\n                        (?P<id>\n                            [\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12}|\n                            (?:[A-Z]{4})?\\d{12,20}\n                        )\n                    '
    _RETURN_TYPE = 'video'


class ParamountPlusIE(CBSBaseIE):
    _module = 'yt_dlp.extractor.paramountplus'
    IE_NAME = 'ParamountPlus'
    _VALID_URL = '(?x)\n        (?:\n            paramountplus:|\n            https?://(?:www\\.)?(?:\n                paramountplus\\.com/(?:shows|movies)/(?:video|[^/]+/video|[^/]+)/\n        )(?P<id>[\\w-]+))'
    _RETURN_TYPE = 'video'


class TheStarIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.thestar'
    IE_NAME = 'TheStar'
    _VALID_URL = 'https?://(?:www\\.)?thestar\\.com/(?:[^/]+/)*(?P<id>.+)\\.html'
    _RETURN_TYPE = 'video'


class TheSunIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.thesun'
    IE_NAME = 'TheSun'
    _VALID_URL = 'https?://(?:www\\.)?the-?sun(\\.co\\.uk|\\.com)/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class ThetaVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.theta'
    IE_NAME = 'ThetaVideo'
    _VALID_URL = 'https?://(?:www\\.)?theta\\.tv/video/(?P<id>vid[a-z0-9]+)'
    _RETURN_TYPE = 'video'


class ThetaStreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.theta'
    IE_NAME = 'ThetaStream'
    _VALID_URL = 'https?://(?:www\\.)?theta\\.tv/(?!video/)(?P<id>[a-z0-9-]+)'
    _RETURN_TYPE = 'video'


class TheWeatherChannelIE(ThePlatformIE):
    _module = 'yt_dlp.extractor.theweatherchannel'
    IE_NAME = 'TheWeatherChannel'
    _VALID_URL = 'https?://(?:www\\.)?weather\\.com(?P<asset_name>(?:/(?P<locale>[a-z]{2}-[A-Z]{2}))?/(?:[^/]+/)*video/(?P<id>[^/?#]+))'
    _RETURN_TYPE = 'video'


class ThisAmericanLifeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.thisamericanlife'
    IE_NAME = 'ThisAmericanLife'
    _VALID_URL = 'https?://(?:www\\.)?thisamericanlife\\.org/(?:radio-archives/episode/|play_full\\.php\\?play=)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ThisAVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.thisav'
    IE_NAME = 'ThisAV'
    _VALID_URL = 'https?://(?:www\\.)?thisav\\.com/video/(?P<id>[0-9]+)/.*'
    _RETURN_TYPE = 'video'


class ThisOldHouseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.thisoldhouse'
    IE_NAME = 'ThisOldHouse'
    _VALID_URL = 'https?://(?:www\\.)?thisoldhouse\\.com/(?:watch|how-to|tv-episode|(?:[^/]+/)?\\d+)/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class ThisVidIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.thisvid'
    IE_NAME = 'ThisVid'
    _VALID_URL = 'https?://(?:www\\.)?thisvid\\.com/(?P<type>videos|embed)/(?P<id>[A-Za-z0-9-]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class ThisVidPlaylistBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.thisvid'
    IE_NAME = 'ThisVidPlaylistBase'


class ThisVidMemberIE(ThisVidPlaylistBaseIE):
    _module = 'yt_dlp.extractor.thisvid'
    IE_NAME = 'ThisVidMember'
    _VALID_URL = 'https?://thisvid\\.com/members/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class ThisVidPlaylistIE(ThisVidPlaylistBaseIE):
    _module = 'yt_dlp.extractor.thisvid'
    IE_NAME = 'ThisVidPlaylist'
    _VALID_URL = 'https?://thisvid\\.com/playlist/(?P<id>\\d+)/video/(?P<video_id>[A-Za-z0-9-]+)'
    age_limit = 18
    _RETURN_TYPE = 'any'


class ThreeSpeakIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.threespeak'
    IE_NAME = 'ThreeSpeak'
    _VALID_URL = 'https?://(?:www\\.)?3speak\\.tv/watch\\?v\\=[^/]+/(?P<id>[^/$&#?]+)'
    _RETURN_TYPE = 'video'


class ThreeSpeakUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.threespeak'
    IE_NAME = 'ThreeSpeakUser'
    _VALID_URL = 'https?://(?:www\\.)?3speak\\.tv/user/(?P<id>[^/$&?#]+)'
    _RETURN_TYPE = 'playlist'


class ThreeQSDNIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.threeqsdn'
    IE_NAME = '3qsdn'
    _VALID_URL = 'https?://playout\\.3qsdn\\.com/(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'
    IE_DESC = '3Q SDN'
    _RETURN_TYPE = 'video'


class TikTokBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'TikTokBase'


class TikTokIE(TikTokBaseIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'TikTok'
    _VALID_URL = 'https?://www\\.tiktok\\.com/(?:embed|@(?P<user_id>[\\w\\.-]+)?/video)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TikTokUserIE(TikTokBaseIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'tiktok:user'
    _VALID_URL = 'https?://(?:www\\.)?tiktok\\.com/@(?P<id>[\\w\\.-]+)/?(?:$|[#?])'
    _WORKING = False
    _RETURN_TYPE = 'playlist'


class TikTokBaseListIE(TikTokBaseIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'TikTokBaseList'


class TikTokSoundIE(TikTokBaseListIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'tiktok:sound'
    _VALID_URL = 'https?://(?:www\\.)?tiktok\\.com/music/[\\w\\.-]+-(?P<id>[\\d]+)[/?#&]?'
    _WORKING = False
    _RETURN_TYPE = 'playlist'


class TikTokEffectIE(TikTokBaseListIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'tiktok:effect'
    _VALID_URL = 'https?://(?:www\\.)?tiktok\\.com/sticker/[\\w\\.-]+-(?P<id>[\\d]+)[/?#&]?'
    _WORKING = False
    _RETURN_TYPE = 'playlist'


class TikTokTagIE(TikTokBaseListIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'tiktok:tag'
    _VALID_URL = 'https?://(?:www\\.)?tiktok\\.com/tag/(?P<id>[^/?#&]+)'
    _WORKING = False
    _RETURN_TYPE = 'playlist'


class TikTokVMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'vm.tiktok'
    _VALID_URL = 'https?://(?:(?:vm|vt)\\.tiktok\\.com|(?:www\\.)tiktok\\.com/t)/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class TikTokLiveIE(TikTokBaseIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'tiktok:live'
    _VALID_URL = '(?x)https?://(?:\n        (?:www\\.)?tiktok\\.com/@(?P<uploader>[\\w.-]+)/live|\n        m\\.tiktok\\.com/share/live/(?P<id>\\d+)\n    )'
    _RETURN_TYPE = 'video'


class DouyinIE(TikTokBaseIE):
    _module = 'yt_dlp.extractor.tiktok'
    IE_NAME = 'Douyin'
    _VALID_URL = 'https?://(?:www\\.)?douyin\\.com/video/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class TinyPicIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tinypic'
    IE_NAME = 'tinypic'
    _VALID_URL = 'https?://(?:.+?\\.)?tinypic\\.com/player\\.php\\?v=(?P<id>[^&]+)&s=\\d+'
    IE_DESC = 'tinypic.com videos'
    _RETURN_TYPE = 'video'


class TMZIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tmz'
    IE_NAME = 'TMZ'
    _VALID_URL = 'https?://(?:www\\.)?tmz\\.com/.*'
    _RETURN_TYPE = 'video'


class TNAFlixNetworkBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tnaflix'
    IE_NAME = 'TNAFlixNetworkBase'


class TNAFlixNetworkEmbedIE(TNAFlixNetworkBaseIE):
    _module = 'yt_dlp.extractor.tnaflix'
    IE_NAME = 'TNAFlixNetworkEmbed'
    _VALID_URL = 'https?://player\\.(?P<host>tnaflix|empflix)\\.com/video/(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class TNAEMPFlixBaseIE(TNAFlixNetworkBaseIE):
    _module = 'yt_dlp.extractor.tnaflix'
    IE_NAME = 'TNAEMPFlixBase'


class TNAFlixIE(TNAEMPFlixBaseIE):
    _module = 'yt_dlp.extractor.tnaflix'
    IE_NAME = 'TNAFlix'
    _VALID_URL = 'https?://(?:www\\.)?(?P<host>tnaflix)\\.com/[^/]+/(?P<display_id>[^/]+)/video(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class EMPFlixIE(TNAEMPFlixBaseIE):
    _module = 'yt_dlp.extractor.tnaflix'
    IE_NAME = 'EMPFlix'
    _VALID_URL = 'https?://(?:www\\.)?(?P<host>empflix)\\.com/(?:videos/(?P<display_id>.+?)-|[^/]+/(?P<display_id_2>[^/]+)/video)(?P<id>[0-9]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class MovieFapIE(TNAFlixNetworkBaseIE):
    _module = 'yt_dlp.extractor.tnaflix'
    IE_NAME = 'MovieFap'
    _VALID_URL = 'https?://(?:www\\.)?(?P<host>moviefap)\\.com/videos/(?P<id>[0-9a-f]+)/(?P<display_id>[^/]+)\\.html'
    age_limit = 18
    _RETURN_TYPE = 'video'


class ToggleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.toggle'
    IE_NAME = 'toggle'
    _VALID_URL = '(?:https?://(?:(?:www\\.)?mewatch|video\\.toggle)\\.sg/(?:en|zh)/(?:[^/]+/){2,}|toggle:)(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class MeWatchIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.toggle'
    IE_NAME = 'mewatch'
    _VALID_URL = 'https?://(?:(?:www|live)\\.)?mewatch\\.sg/watch/[^/?#&]+-(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class ToggoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.toggo'
    IE_NAME = 'toggo'
    _VALID_URL = 'https?://(?:www\\.)?toggo\\.de/(?:toggolino/)?[^/?#]+/(?:folge|video)/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class TokentubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tokentube'
    IE_NAME = 'Tokentube'
    _VALID_URL = 'https?://(?:www\\.)?tokentube\\.net/(?:view\\?[vl]=|[vl]/)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TokentubeChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tokentube'
    IE_NAME = 'Tokentube:channel'
    _VALID_URL = 'https?://(?:www\\.)?tokentube\\.net/channel/(?P<id>\\d+)/[^/]+(?:/videos)?'
    _RETURN_TYPE = 'playlist'


class TOnlineIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tonline'
    IE_NAME = 't-online.de'
    _VALID_URL = 'https?://(?:www\\.)?t-online\\.de/tv/(?:[^/]+/)*id_(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ToonGogglesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.toongoggles'
    IE_NAME = 'ToonGoggles'
    _VALID_URL = 'https?://(?:www\\.)?toongoggles\\.com/shows/(?P<show_id>\\d+)(?:/[^/]+/episodes/(?P<episode_id>\\d+))?'
    _RETURN_TYPE = 'any'


class TouTvIE(RadioCanadaIE):
    _module = 'yt_dlp.extractor.toutv'
    IE_NAME = 'tou.tv'
    _VALID_URL = 'https?://ici\\.tou\\.tv/(?P<id>[a-zA-Z0-9_-]+(?:/S[0-9]+[EC][0-9]+)?)'
    _NETRC_MACHINE = 'toutv'
    _RETURN_TYPE = 'video'


class ToypicsUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.toypics'
    IE_NAME = 'ToypicsUser'
    _VALID_URL = 'https?://videos\\.toypics\\.net/(?!view)(?P<id>[^/?#&]+)'
    IE_DESC = 'Toypics user profile'
    _RETURN_TYPE = 'playlist'


class ToypicsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.toypics'
    IE_NAME = 'Toypics'
    _VALID_URL = 'https?://videos\\.toypics\\.net/view/(?P<id>[0-9]+)'
    IE_DESC = 'Toypics video'
    age_limit = 18
    _RETURN_TYPE = 'video'


class TrailerAddictIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.traileraddict'
    IE_NAME = 'TrailerAddict'
    _VALID_URL = '(?:https?://)?(?:www\\.)?traileraddict\\.com/(?:trailer|clip)/(?P<movie>.+?)/(?P<trailer_name>.+)'
    _WORKING = False
    _RETURN_TYPE = 'video'


class TrillerBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.triller'
    IE_NAME = 'TrillerBase'
    _NETRC_MACHINE = 'triller'


class TrillerIE(TrillerBaseIE):
    _module = 'yt_dlp.extractor.triller'
    IE_NAME = 'Triller'
    _VALID_URL = '(?x)\n            https?://(?:www\\.)?triller\\.co/\n            @(?P<username>[\\w.]+)/video/(?P<id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})\n        '
    _NETRC_MACHINE = 'triller'
    _RETURN_TYPE = 'video'


class TrillerUserIE(TrillerBaseIE):
    _module = 'yt_dlp.extractor.triller'
    IE_NAME = 'TrillerUser'
    _VALID_URL = 'https?://(?:www\\.)?triller\\.co/@(?P<id>[\\w.]+)/?(?:$|[#?])'
    _NETRC_MACHINE = 'triller'
    _RETURN_TYPE = 'playlist'


class TrillerShortIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.triller'
    IE_NAME = 'TrillerShort'
    _VALID_URL = 'https?://v\\.triller\\.co/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class TriluliluIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.trilulilu'
    IE_NAME = 'Trilulilu'
    _VALID_URL = 'https?://(?:(?:www|m)\\.)?trilulilu\\.ro/(?:[^/]+/)?(?P<id>[^/#\\?]+)'
    _RETURN_TYPE = 'video'


class TrovoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.trovo'
    IE_NAME = 'TrovoBase'


class TrovoIE(TrovoBaseIE):
    _module = 'yt_dlp.extractor.trovo'
    IE_NAME = 'Trovo'
    _VALID_URL = 'https?://(?:www\\.)?trovo\\.live/(?:s/)?(?!(?:clip|video)/)(?P<id>(?!s/)[^/?&#]+(?![^#]+[?&]vid=))'
    _RETURN_TYPE = 'video'


class TrovoVodIE(TrovoBaseIE):
    _module = 'yt_dlp.extractor.trovo'
    IE_NAME = 'TrovoVod'
    _VALID_URL = 'https?://(?:www\\.)?trovo\\.live/(?:clip|video|s)/(?:[^/]+/\\d+[^#]*[?&]vid=)?(?P<id>(?<!/s/)[^/?&#]+)'
    _RETURN_TYPE = 'video'


class TrovoChannelBaseIE(TrovoBaseIE):
    _module = 'yt_dlp.extractor.trovo'
    IE_NAME = 'TrovoChannelBase'


class TrovoChannelVodIE(TrovoChannelBaseIE):
    _module = 'yt_dlp.extractor.trovo'
    IE_NAME = 'TrovoChannelVod'
    _VALID_URL = 'trovovod:(?P<id>[^\\s]+)'
    IE_DESC = 'All VODs of a trovo.live channel; "trovovod:" prefix'
    _RETURN_TYPE = 'playlist'


class TrovoChannelClipIE(TrovoChannelBaseIE):
    _module = 'yt_dlp.extractor.trovo'
    IE_NAME = 'TrovoChannelClip'
    _VALID_URL = 'trovoclip:(?P<id>[^\\s]+)'
    IE_DESC = 'All Clips of a trovo.live channel; "trovoclip:" prefix'
    _RETURN_TYPE = 'playlist'


class TrtCocukVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.trtcocuk'
    IE_NAME = 'TrtCocukVideo'
    _VALID_URL = 'https?://www\\.trtcocuk\\.net\\.tr/video/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class TrueIDIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.trueid'
    IE_NAME = 'TrueID'
    _VALID_URL = 'https?://(?P<domain>vn\\.trueid\\.net|trueid\\.(?:id|ph))/(?:movie|series/[^/]+)/(?P<id>[^/?#&]+)'
    age_limit = 13
    _RETURN_TYPE = 'video'


class TruNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.trunews'
    IE_NAME = 'TruNews'
    _VALID_URL = 'https?://(?:www\\.)?trunews\\.com/stream/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class TruthIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.truth'
    IE_NAME = 'Truth'
    _VALID_URL = 'https?://truthsocial\\.com/@[^/]+/posts/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TruTVIE(TurnerBaseIE):
    _module = 'yt_dlp.extractor.trutv'
    IE_NAME = 'TruTV'
    _VALID_URL = 'https?://(?:www\\.)?trutv\\.com/(?:shows|full-episodes)/(?P<series_slug>[0-9A-Za-z-]+)/(?:videos/(?P<clip_slug>[0-9A-Za-z-]+)|(?P<id>\\d+))'
    _RETURN_TYPE = 'video'


class Tube8IE(KeezMoviesIE):
    _module = 'yt_dlp.extractor.tube8'
    IE_NAME = 'Tube8'
    _VALID_URL = 'https?://(?:www\\.)?tube8\\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class TubeTuGrazBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tubetugraz'
    IE_NAME = 'TubeTuGrazBase'
    _NETRC_MACHINE = 'tubetugraz'


class TubeTuGrazIE(TubeTuGrazBaseIE):
    _module = 'yt_dlp.extractor.tubetugraz'
    IE_NAME = 'TubeTuGraz'
    _VALID_URL = '(?x)\n        https?://tube\\.tugraz\\.at/paella/ui/watch.html\\?id=\n        (?P<id>[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})\n    '
    IE_DESC = 'tube.tugraz.at'
    _NETRC_MACHINE = 'tubetugraz'
    _RETURN_TYPE = 'video'


class TubeTuGrazSeriesIE(TubeTuGrazBaseIE):
    _module = 'yt_dlp.extractor.tubetugraz'
    IE_NAME = 'TubeTuGrazSeries'
    _VALID_URL = '(?x)\n        https?://tube\\.tugraz\\.at/paella/ui/browse\\.html\\?series=\n        (?P<id>[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})\n    '
    _NETRC_MACHINE = 'tubetugraz'
    _RETURN_TYPE = 'playlist'


class TubiTvIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tubitv'
    IE_NAME = 'TubiTv'
    _VALID_URL = '(?x)\n                    (?:\n                        tubitv:|\n                        https?://(?:www\\.)?tubitv\\.com/(?:video|movies|tv-shows)/\n                    )\n                    (?P<id>[0-9]+)'
    _NETRC_MACHINE = 'tubitv'
    _RETURN_TYPE = 'video'


class TubiTvShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tubitv'
    IE_NAME = 'TubiTvShow'
    _VALID_URL = 'https?://(?:www\\.)?tubitv\\.com/series/[0-9]+/(?P<show_name>[^/?#]+)'
    _RETURN_TYPE = 'playlist'


class TumblrIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tumblr'
    IE_NAME = 'Tumblr'
    _VALID_URL = 'https?://(?P<blog_name>[^/?#&]+)\\.tumblr\\.com/(?:post|video)/(?P<id>[0-9]+)(?:$|[/?#])'
    _NETRC_MACHINE = 'tumblr'
    age_limit = 18
    _RETURN_TYPE = 'video'


class TuneInBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tunein'
    IE_NAME = 'TuneInBase'


class TuneInStationIE(TuneInBaseIE):
    _module = 'yt_dlp.extractor.tunein'
    IE_NAME = 'TuneInStation'
    _VALID_URL = 'https?://(?:www\\.)?tunein\\.com(?:/radio/[^?#]+-|/embed/player/)(?P<id>s\\d+)'
    _RETURN_TYPE = 'video'


class TuneInPodcastIE(TuneInBaseIE):
    _module = 'yt_dlp.extractor.tunein'
    IE_NAME = 'TuneInPodcast'
    _VALID_URL = 'https?://(?:www\\.)?tunein\\.com/(?:podcasts/[^?#]+-|embed/player/)(?P<id>p\\d+)/?(?:#|$)'
    _RETURN_TYPE = 'playlist'


class TuneInPodcastEpisodeIE(TuneInBaseIE):
    _module = 'yt_dlp.extractor.tunein'
    IE_NAME = 'TuneInPodcastEpisode'
    _VALID_URL = 'https?://(?:www\\.)?tunein\\.com/podcasts/(?:[^?&]+-)?(?P<podcast_id>p\\d+)/?\\?topicId=(?P<id>\\w\\d+)'
    _RETURN_TYPE = 'video'


class TuneInShortenerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tunein'
    IE_NAME = 'tunein:shortener'
    _VALID_URL = 'https?://tun\\.in/(?P<id>[A-Za-z0-9]+)'
    IE_DESC = False
    _RETURN_TYPE = 'video'


class TunePkIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tunepk'
    IE_NAME = 'TunePk'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:www\\.)?tune\\.pk/(?:video/|player/embed_player.php?.*?\\bvid=)|\n                            embed\\.tune\\.pk/play/\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class TurboIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.turbo'
    IE_NAME = 'Turbo'
    _VALID_URL = 'https?://(?:www\\.)?turbo\\.fr/videos-voiture/(?P<id>[0-9]+)-'
    _RETURN_TYPE = 'video'


class TV2IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2'
    IE_NAME = 'TV2'
    _VALID_URL = 'https?://(?:www\\.)?tv2\\.no/v(?:ideo)?\\d*/(?:[^?#]+/)*(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TV2ArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2'
    IE_NAME = 'TV2Article'
    _VALID_URL = 'https?://(?:www\\.)?tv2\\.no/(?!v(?:ideo)?\\d*/)[^?#]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class KatsomoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2'
    IE_NAME = 'Katsomo'
    _VALID_URL = 'https?://(?:www\\.)?(?:katsomo|mtv(uutiset)?)\\.fi/(?:sarja/[0-9a-z-]+-\\d+/[0-9a-z-]+-|(?:#!/)?jakso/(?:\\d+/[^/]+/)?|video/prog)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class MTVUutisetArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2'
    IE_NAME = 'MTVUutisetArticle'
    _VALID_URL = 'https?://(?:www\\.)mtvuutiset\\.fi/artikkeli/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TV24UAVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv24ua'
    IE_NAME = '24tv.ua'
    _VALID_URL = 'https?://24tv\\.ua/news/showPlayer\\.do.*?(?:\\?|&)objectId=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TV2DKIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2dk'
    IE_NAME = 'TV2DK'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?\n                        (?:\n                            tvsyd|\n                            tv2ostjylland|\n                            tvmidtvest|\n                            tv2fyn|\n                            tv2east|\n                            tv2lorry|\n                            tv2nord\n                        )\\.dk/\n                        (:[^/]+/)*\n                        (?P<id>[^/?\\#&]+)\n                    '
    _RETURN_TYPE = 'video'


class TV2DKBornholmPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2dk'
    IE_NAME = 'TV2DKBornholmPlay'
    _VALID_URL = 'https?://play\\.tv2bornholm\\.dk/\\?.*?\\bid=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TV2HuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2hu'
    IE_NAME = 'tv2play.hu'
    _VALID_URL = 'https?://(?:www\\.)?tv2play\\.hu/(?!szalag/)(?P<id>[^#&?]+)'
    _RETURN_TYPE = 'video'


class TV2HuSeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv2hu'
    IE_NAME = 'tv2playseries.hu'
    _VALID_URL = 'https?://(?:www\\.)?tv2play\\.hu/szalag/(?P<id>[^#&?]+)'
    _RETURN_TYPE = 'playlist'


class TV4IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv4'
    IE_NAME = 'TV4'
    _VALID_URL = '(?x)https?://(?:www\\.)?\n        (?:\n            tv4\\.se/(?:[^/]+)/klipp/(?:.*)-|\n            tv4play\\.se/\n            (?:\n                (?:program|barn)/(?:(?:[^/]+/){1,2}|(?:[^\\?]+)\\?video_id=)|\n                iframe/video/|\n                film/|\n                sport/|\n            )\n        )(?P<id>[0-9]+)'
    IE_DESC = 'tv4.se and tv4play.se'
    _RETURN_TYPE = 'video'


class TV5MondePlusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv5mondeplus'
    IE_NAME = 'TV5MondePlus'
    _VALID_URL = 'https?://(?:www\\.)?(?:tv5mondeplus|revoir\\.tv5monde)\\.com/toutes-les-videos/[^/]+/(?P<id>[^/?#]+)'
    IE_DESC = 'TV5MONDE+'
    _RETURN_TYPE = 'video'


class TV5UnisBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tv5unis'
    IE_NAME = 'TV5UnisBase'


class TV5UnisVideoIE(TV5UnisBaseIE):
    _module = 'yt_dlp.extractor.tv5unis'
    IE_NAME = 'tv5unis:video'
    _VALID_URL = 'https?://(?:www\\.)?tv5unis\\.ca/videos/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TV5UnisIE(TV5UnisBaseIE):
    _module = 'yt_dlp.extractor.tv5unis'
    IE_NAME = 'tv5unis'
    _VALID_URL = 'https?://(?:www\\.)?tv5unis\\.ca/videos/(?P<id>[^/]+)(?:/saisons/(?P<season_number>\\d+)/episodes/(?P<episode_number>\\d+))?/?(?:[?#&]|$)'
    age_limit = 8
    _RETURN_TYPE = 'video'


class TVAIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tva'
    IE_NAME = 'TVA'
    _VALID_URL = 'https?://videos?\\.tva\\.ca/details/_(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class QubIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tva'
    IE_NAME = 'Qub'
    _VALID_URL = 'https?://(?:www\\.)?qub\\.ca/(?:[^/]+/)*[0-9a-z-]+-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TVANouvellesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvanouvelles'
    IE_NAME = 'TVANouvelles'
    _VALID_URL = 'https?://(?:www\\.)?tvanouvelles\\.ca/videos/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TVANouvellesArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvanouvelles'
    IE_NAME = 'TVANouvellesArticle'
    _VALID_URL = 'https?://(?:www\\.)?tvanouvelles\\.ca/(?:[^/]+/)+(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if TVANouvellesIE.suitable(url) else super(TVANouvellesArticleIE, cls).suitable(url)


class TVCIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvc'
    IE_NAME = 'TVC'
    _VALID_URL = 'https?://(?:www\\.)?tvc\\.ru/video/iframe/id/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TVCArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvc'
    IE_NAME = 'TVCArticle'
    _VALID_URL = 'https?://(?:www\\.)?tvc\\.ru/(?!video/iframe/id/)(?P<id>[^?#]+)'
    _RETURN_TYPE = 'video'


class TVerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tver'
    IE_NAME = 'TVer'
    _VALID_URL = 'https?://(?:www\\.)?tver\\.jp/(?:(?P<type>lp|corner|series|episodes?|feature|tokyo2020/video)/)+(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'


class TvigleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvigle'
    IE_NAME = 'tvigle'
    _VALID_URL = 'https?://(?:www\\.)?(?:tvigle\\.ru/(?:[^/]+/)+(?P<display_id>[^/]+)/$|cloud\\.tvigle\\.ru/video/(?P<id>\\d+))'
    IE_DESC = 'Интернет-телевидение Tvigle.ru'
    age_limit = 12
    _RETURN_TYPE = 'video'


class TVIPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tviplayer'
    IE_NAME = 'TVIPlayer'
    _VALID_URL = 'https?://tviplayer\\.iol\\.pt(/programa/[\\w-]+/[a-f0-9]+)?/\\w+/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class TVLandIE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.tvland'
    IE_NAME = 'tvland.com'
    _VALID_URL = 'https?://(?:www\\.)?tvland\\.com/(?:video-clips|(?:full-)?episodes)/(?P<id>[^/?#.]+)'
    _RETURN_TYPE = 'any'


class TVN24IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvn24'
    IE_NAME = 'TVN24'
    _VALID_URL = 'https?://(?:(?:[^/]+)\\.)?tvn24(?:bis)?\\.pl/(?:[^/]+/)*(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class TVNetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvnet'
    IE_NAME = 'TVNet'
    _VALID_URL = 'https?://(?:[^/]+)\\.tvnet\\.gov\\.vn/[^/]+/(?:\\d+/)?(?P<id>\\d+)(?:/|$)'
    _RETURN_TYPE = 'video'


class TVNoeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvnoe'
    IE_NAME = 'TVNoe'
    _VALID_URL = 'https?://(?:www\\.)?tvnoe\\.cz/video/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class TVNowBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowBase'


class TVNowIE(TVNowBaseIE):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNow'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?tvnow\\.(?:de|at|ch)/(?P<station>[^/]+)/\n                        (?P<show_id>[^/]+)/\n                        (?!(?:list|jahr)(?:/|$))(?P<id>[^/?\\#&]+)\n                    '
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return (False if TVNowNewIE.suitable(url) or TVNowSeasonIE.suitable(url) or TVNowAnnualIE.suitable(url) or TVNowShowIE.suitable(url)
                else super(TVNowIE, cls).suitable(url))


class TVNowFilmIE(TVNowBaseIE):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowFilm'
    _VALID_URL = '(?x)\n                    (?P<base_url>https?://\n                        (?:www\\.)?tvnow\\.(?:de|at|ch)/\n                        (?:filme))/\n                        (?P<title>[^/?$&]+)-(?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class TVNowNewIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowNew'
    _VALID_URL = '(?x)\n                    (?P<base_url>https?://\n                        (?:www\\.)?tvnow\\.(?:de|at|ch)/\n                        (?:shows|serien))/\n                        (?P<show>[^/]+)-\\d+/\n                        [^/]+/\n                        episode-\\d+-(?P<episode>[^/?$&]+)-(?P<id>\\d+)\n                    '


class TVNowNewBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowNewBase'


class TVNowListBaseIE(TVNowNewBaseIE):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowListBase'

    @classmethod
    def suitable(cls, url):
        return (False if TVNowNewIE.suitable(url)
                else super(TVNowListBaseIE, cls).suitable(url))


class TVNowSeasonIE(TVNowListBaseIE):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowSeason'
    _VALID_URL = '(?x)\n                    (?P<base_url>\n                        https?://\n                            (?:www\\.)?tvnow\\.(?:de|at|ch)/(?:shows|serien)/\n                            [^/?#&]+-(?P<show_id>\\d+)\n                    )\n                    /staffel-(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if TVNowNewIE.suitable(url)
                else super(TVNowListBaseIE, cls).suitable(url))


class TVNowAnnualIE(TVNowListBaseIE):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowAnnual'
    _VALID_URL = '(?x)\n                    (?P<base_url>\n                        https?://\n                            (?:www\\.)?tvnow\\.(?:de|at|ch)/(?:shows|serien)/\n                            [^/?#&]+-(?P<show_id>\\d+)\n                    )\n                    /(?P<year>\\d{4})-(?P<month>\\d{2})'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if TVNowNewIE.suitable(url)
                else super(TVNowListBaseIE, cls).suitable(url))


class TVNowShowIE(TVNowListBaseIE):
    _module = 'yt_dlp.extractor.tvnow'
    IE_NAME = 'TVNowShow'
    _VALID_URL = '(?x)\n                    (?P<base_url>\n                        https?://\n                            (?:www\\.)?tvnow\\.(?:de|at|ch)/(?:shows|serien)/\n                            [^/?#&]+-(?P<show_id>\\d+)\n                    )\n                    '
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if TVNowNewIE.suitable(url) or TVNowSeasonIE.suitable(url) or TVNowAnnualIE.suitable(url)
                else super(TVNowShowIE, cls).suitable(url))


class TVOpenGrBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvopengr'
    IE_NAME = 'TVOpenGrBase'


class TVOpenGrWatchIE(TVOpenGrBaseIE):
    _module = 'yt_dlp.extractor.tvopengr'
    IE_NAME = 'tvopengr:watch'
    _VALID_URL = 'https?://(?P<netloc>(?:www\\.)?(?:tvopen|ethnos)\\.gr)/watch/(?P<id>\\d+)/(?P<slug>[^/]+)'
    IE_DESC = 'tvopen.gr (and ethnos.gr) videos'
    _RETURN_TYPE = 'video'


class TVOpenGrEmbedIE(TVOpenGrBaseIE):
    _module = 'yt_dlp.extractor.tvopengr'
    IE_NAME = 'tvopengr:embed'
    _VALID_URL = '(?:https?:)?//(?:www\\.|cdn\\.|)(?:tvopen|ethnos).gr/embed/(?P<id>\\d+)'
    IE_DESC = 'tvopen.gr embedded videos'
    _RETURN_TYPE = 'video'


class TVPEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvp'
    IE_NAME = 'tvp:embed'
    _VALID_URL = '(?x)\n        (?:\n            tvp:\n            |https?://\n                (?:[^/]+\\.)?\n                (?:tvp(?:parlament)?\\.pl|tvp\\.info|tvpworld\\.com|swipeto\\.pl)/\n                (?:sess/\n                        (?:tvplayer\\.php\\?.*?object_id\n                        |TVPlayer2/(?:embed|api)\\.php\\?.*[Ii][Dd])\n                    |shared/details\\.php\\?.*?object_id)\n                =)\n        (?P<id>\\d+)\n    '
    IE_DESC = 'Telewizja Polska'
    age_limit = 12
    _RETURN_TYPE = 'video'


class TVPIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvp'
    IE_NAME = 'tvp'
    _VALID_URL = 'https?://(?:[^/]+\\.)?(?:tvp(?:parlament)?\\.(?:pl|info)|tvpworld\\.com|swipeto\\.pl)/(?:(?!\\d+/)[^/]+/)*(?P<id>\\d+)'
    IE_DESC = 'Telewizja Polska'
    age_limit = 12
    _RETURN_TYPE = 'any'


class TVPStreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvp'
    IE_NAME = 'tvp:stream'
    _VALID_URL = '(?:tvpstream:|https?://(?:tvpstream\\.vod|stream)\\.tvp\\.pl/(?:\\?(?:[^&]+[&;])*channel_id=)?)(?P<id>\\d*)'


class TVPVODBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvp'
    IE_NAME = 'TVPVODBase'


class TVPVODSeriesIE(TVPVODBaseIE):
    _module = 'yt_dlp.extractor.tvp'
    IE_NAME = 'tvp:vod:series'
    _VALID_URL = 'https?://vod\\.tvp\\.pl/[a-z\\d-]+,\\d+/[a-z\\d-]+-odcinki,(?P<id>\\d+)(?:\\?[^#]+)?(?:#.+)?$'
    age_limit = 12
    _RETURN_TYPE = 'playlist'


class TVPVODVideoIE(TVPVODBaseIE):
    _module = 'yt_dlp.extractor.tvp'
    IE_NAME = 'tvp:vod'
    _VALID_URL = 'https?://vod\\.tvp\\.pl/[a-z\\d-]+,\\d+/[a-z\\d-]+(?<!-odcinki)(?:-odcinki,\\d+/odcinek-\\d+,S\\d+E\\d+)?,(?P<id>\\d+)(?:\\?[^#]+)?(?:#.+)?$'
    age_limit = 16
    _RETURN_TYPE = 'video'


class TVPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvplay'
    IE_NAME = 'mtg'
    _VALID_URL = '(?x)\n                    (?:\n                        mtg:|\n                        https?://\n                            (?:www\\.)?\n                            (?:\n                                tvplay(?:\\.skaties)?\\.lv(?:/parraides)?|\n                                (?:tv3play|play\\.tv3)\\.lt(?:/programos)?|\n                                tv3play(?:\\.tv3)?\\.ee/sisu\n                            )\n                            /(?:[^/]+/)+\n                        )\n                        (?P<id>\\d+)\n                    '
    IE_DESC = 'MTG services'
    _RETURN_TYPE = 'video'


class TVPlayHomeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvplay'
    IE_NAME = 'TVPlayHome'
    _VALID_URL = '(?x)\n            https?://\n            (?:tv3?)?\n            play\\.(?:tv3|skaties)\\.(?P<country>lv|lt|ee)/\n            (?P<live>lives/)?\n            [^?#&]+(?:episode|programme|clip)-(?P<id>\\d+)\n    '
    _RETURN_TYPE = 'video'


class TVPlayerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tvplayer'
    IE_NAME = 'TVPlayer'
    _VALID_URL = 'https?://(?:www\\.)?tvplayer\\.com/watch/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class TweakersIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.tweakers'
    IE_NAME = 'Tweakers'
    _VALID_URL = 'https?://tweakers\\.net/video/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TwentyFourVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twentyfourvideo'
    IE_NAME = '24video'
    _VALID_URL = '(?x)\n                    https?://\n                        (?P<host>\n                            (?:(?:www|porno?)\\.)?24video\\.\n                            (?:net|me|xxx|sexy?|tube|adult|site|vip)\n                        )/\n                        (?:\n                            video/(?:(?:view|xml)/)?|\n                            player/new24_play\\.swf\\?id=\n                        )\n                        (?P<id>\\d+)\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class TwentyMinutenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twentymin'
    IE_NAME = '20min'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:www\\.)?20min\\.ch/\n                        (?:\n                            videotv/*\\?.*?\\bvid=|\n                            videoplayer/videoplayer\\.html\\?.*?\\bvideoId@\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class TwentyThreeVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twentythreevideo'
    IE_NAME = '23video'
    _VALID_URL = 'https?://(?P<domain>[^.]+\\.(?:twentythree\\.net|23video\\.com|filmweb\\.no))/v\\.ihtml/player\\.html\\?(?P<query>.*?\\bphoto(?:_|%5f)id=(?P<id>\\d+).*)'
    _RETURN_TYPE = 'video'


class TwitCastingIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twitcasting'
    IE_NAME = 'TwitCasting'
    _VALID_URL = 'https?://(?:[^/]+\\.)?twitcasting\\.tv/(?P<uploader_id>[^/]+)/(?:movie|twplayer)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TwitCastingLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twitcasting'
    IE_NAME = 'TwitCastingLive'
    _VALID_URL = 'https?://(?:[^/]+\\.)?twitcasting\\.tv/(?P<id>[^/]+)/?(?:[#?]|$)'


class TwitCastingUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twitcasting'
    IE_NAME = 'TwitCastingUser'
    _VALID_URL = 'https?://(?:[^/]+\\.)?twitcasting\\.tv/(?P<id>[^/]+)/show/?(?:[#?]|$)'


class TwitchBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'TwitchBase'
    _NETRC_MACHINE = 'twitch'


class TwitchVodIE(TwitchBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'twitch:vod'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:(?:www|go|m)\\.)?twitch\\.tv/(?:[^/]+/v(?:ideo)?|videos)/|\n                            player\\.twitch\\.tv/\\?.*?\\bvideo=v?|\n                            www\\.twitch\\.tv/[^/]+/schedule\\?vodID=\n                        )\n                        (?P<id>\\d+)\n                    '
    _NETRC_MACHINE = 'twitch'
    _RETURN_TYPE = 'video'


class TwitchCollectionIE(TwitchBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'TwitchCollection'
    _VALID_URL = 'https?://(?:(?:www|go|m)\\.)?twitch\\.tv/collections/(?P<id>[^/]+)'
    _NETRC_MACHINE = 'twitch'
    _RETURN_TYPE = 'playlist'


class TwitchPlaylistBaseIE(TwitchBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'TwitchPlaylistBase'
    _NETRC_MACHINE = 'twitch'


class TwitchVideosIE(TwitchPlaylistBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'TwitchVideos'
    _VALID_URL = 'https?://(?:(?:www|go|m)\\.)?twitch\\.tv/(?P<id>[^/]+)/(?:videos|profile)'
    _NETRC_MACHINE = 'twitch'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False
                if any(ie.suitable(url) for ie in (
                    TwitchVideosClipsIE,
                    TwitchVideosCollectionsIE))
                else super(TwitchVideosIE, cls).suitable(url))


class TwitchVideosClipsIE(TwitchPlaylistBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'TwitchVideosClips'
    _VALID_URL = 'https?://(?:(?:www|go|m)\\.)?twitch\\.tv/(?P<id>[^/]+)/(?:clips|videos/*?\\?.*?\\bfilter=clips)'
    _NETRC_MACHINE = 'twitch'
    _RETURN_TYPE = 'playlist'


class TwitchVideosCollectionsIE(TwitchPlaylistBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'TwitchVideosCollections'
    _VALID_URL = 'https?://(?:(?:www|go|m)\\.)?twitch\\.tv/(?P<id>[^/]+)/videos/*?\\?.*?\\bfilter=collections'
    _NETRC_MACHINE = 'twitch'
    _RETURN_TYPE = 'playlist'


class TwitchStreamIE(TwitchBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'twitch:stream'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:(?:www|go|m)\\.)?twitch\\.tv/|\n                            player\\.twitch\\.tv/\\?.*?\\bchannel=\n                        )\n                        (?P<id>[^/#?]+)\n                    '
    _NETRC_MACHINE = 'twitch'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return (False
                if any(ie.suitable(url) for ie in (
                    TwitchVodIE,
                    TwitchCollectionIE,
                    TwitchVideosIE,
                    TwitchVideosClipsIE,
                    TwitchVideosCollectionsIE,
                    TwitchClipsIE))
                else super(TwitchStreamIE, cls).suitable(url))


class TwitchClipsIE(TwitchBaseIE):
    _module = 'yt_dlp.extractor.twitch'
    IE_NAME = 'twitch:clips'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            clips\\.twitch\\.tv/(?:embed\\?.*?\\bclip=|(?:[^/]+/)*)|\n                            (?:(?:www|go|m)\\.)?twitch\\.tv/(?:[^/]+/)?clip/\n                        )\n                        (?P<id>[^/?#&]+)\n                    '
    _NETRC_MACHINE = 'twitch'
    _RETURN_TYPE = 'video'


class TwitterCardIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twitter'
    IE_NAME = 'twitter:card'
    _VALID_URL = 'https?://(?:(?:www|m(?:obile)?)\\.)?(?:twitter\\.com|twitter3e4tixl4xyajtrzo62zg5vztmjuricljdp2c5kshju4avyoid\\.onion)/i/(?:cards/tfw/v1|videos(?:/tweet)?)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class TwitterBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.twitter'
    IE_NAME = 'TwitterBase'
    _NETRC_MACHINE = 'twitter'


class TwitterIE(TwitterBaseIE):
    _module = 'yt_dlp.extractor.twitter'
    IE_NAME = 'twitter'
    _VALID_URL = 'https?://(?:(?:www|m(?:obile)?)\\.)?(?:twitter\\.com|twitter3e4tixl4xyajtrzo62zg5vztmjuricljdp2c5kshju4avyoid\\.onion)/(?:(?:i/web|[^/]+)/status|statuses)/(?P<id>\\d+)(?:/(?:video|photo)/(?P<index>\\d+))?'
    _NETRC_MACHINE = 'twitter'
    age_limit = 18
    _RETURN_TYPE = 'any'


class TwitterAmplifyIE(TwitterBaseIE):
    _module = 'yt_dlp.extractor.twitter'
    IE_NAME = 'twitter:amplify'
    _VALID_URL = 'https?://amp\\.twimg\\.com/v/(?P<id>[0-9a-f\\-]{36})'
    _NETRC_MACHINE = 'twitter'
    _RETURN_TYPE = 'video'


class TwitterBroadcastIE(TwitterBaseIE, PeriscopeBaseIE):
    _module = 'yt_dlp.extractor.twitter'
    IE_NAME = 'twitter:broadcast'
    _VALID_URL = 'https?://(?:(?:www|m(?:obile)?)\\.)?(?:twitter\\.com|twitter3e4tixl4xyajtrzo62zg5vztmjuricljdp2c5kshju4avyoid\\.onion)/i/broadcasts/(?P<id>[0-9a-zA-Z]{13})'
    _NETRC_MACHINE = 'twitter'
    _RETURN_TYPE = 'video'


class TwitterSpacesIE(TwitterBaseIE):
    _module = 'yt_dlp.extractor.twitter'
    IE_NAME = 'twitter:spaces'
    _VALID_URL = 'https?://(?:(?:www|m(?:obile)?)\\.)?(?:twitter\\.com|twitter3e4tixl4xyajtrzo62zg5vztmjuricljdp2c5kshju4avyoid\\.onion)/i/spaces/(?P<id>[0-9a-zA-Z]{13})'
    _NETRC_MACHINE = 'twitter'
    _RETURN_TYPE = 'video'


class TwitterShortenerIE(TwitterBaseIE):
    _module = 'yt_dlp.extractor.twitter'
    IE_NAME = 'twitter:shortener'
    _VALID_URL = 'https?://t.co/(?P<id>[^?]+)|tco:(?P<eid>[^?]+)'
    _NETRC_MACHINE = 'twitter'


class TxxxIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.txxx'
    IE_NAME = 'Txxx'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?(?P<host>hclips\\.com|hdzog\\.com|hdzog\\.tube|hotmovs\\.com|hotmovs\\.tube|inporn\\.com|privatehomeclips\\.com|tubepornclassic\\.com|txxx\\.com|txxx\\.tube|upornia\\.com|upornia\\.tube|vjav\\.com|vjav\\.tube|vxxx\\.com|voyeurhit\\.com|voyeurhit\\.tube)/\n        (?:videos?[/-]|embed/)(?P<id>\\d+)(?:/(?P<display_id>[^/?#]+))?\n    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class PornTopIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.txxx'
    IE_NAME = 'PornTop'
    _VALID_URL = 'https?://(?P<host>(?:www\\.)?porntop\\.com)/video/(?P<id>\\d+)(?:/(?P<display_id>[^/?]+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class UdemyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.udemy'
    IE_NAME = 'udemy'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:[^/]+\\.)?udemy\\.com/\n                        (?:\n                            [^#]+\\#/lecture/|\n                            lecture/view/?\\?lectureId=|\n                            [^/]+/learn/v4/t/lecture/\n                        )\n                        (?P<id>\\d+)\n                    '
    _NETRC_MACHINE = 'udemy'
    _RETURN_TYPE = 'video'


class UdemyCourseIE(UdemyIE):
    _module = 'yt_dlp.extractor.udemy'
    IE_NAME = 'udemy:course'
    _VALID_URL = 'https?://(?:[^/]+\\.)?udemy\\.com/(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'udemy'

    @classmethod
    def suitable(cls, url):
        return False if UdemyIE.suitable(url) else super(UdemyCourseIE, cls).suitable(url)


class UDNEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.udn'
    IE_NAME = 'UDNEmbed'
    _VALID_URL = 'https?://video\\.udn\\.com/(?:embed|play)/news/(?P<id>\\d+)'
    IE_DESC = '聯合影音'
    _RETURN_TYPE = 'video'


class ImgGamingBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.imggaming'
    IE_NAME = 'ImgGamingBase'


class UFCTVIE(ImgGamingBaseIE):
    _module = 'yt_dlp.extractor.ufctv'
    IE_NAME = 'UFCTV'
    _VALID_URL = 'https?://(?P<domain>(?:(?:app|www)\\.)?(?:ufc\\.tv|(?:ufc)?fightpass\\.com)|ufcfightpass\\.img(?:dge|gaming)\\.com)/(?P<type>live|playlist|video)/(?P<id>\\d+)(?:\\?.*?\\bplaylistId=(?P<playlist_id>\\d+))?'
    _NETRC_MACHINE = 'ufctv'


class UFCArabiaIE(ImgGamingBaseIE):
    _module = 'yt_dlp.extractor.ufctv'
    IE_NAME = 'UFCArabia'
    _VALID_URL = 'https?://(?P<domain>(?:(?:app|www)\\.)?ufcarabia\\.(?:ae|com))/(?P<type>live|playlist|video)/(?P<id>\\d+)(?:\\?.*?\\bplaylistId=(?P<playlist_id>\\d+))?'
    _NETRC_MACHINE = 'ufcarabia'


class UkColumnIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ukcolumn'
    IE_NAME = 'ukcolumn'
    _VALID_URL = '(?i)https?://(?:www\\.)?ukcolumn\\.org(/index\\.php)?/(?:video|ukcolumn-news)/(?P<id>[-a-z0-9]+)'
    _RETURN_TYPE = 'video'


class UKTVPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.uktvplay'
    IE_NAME = 'UKTVPlay'
    _VALID_URL = 'https?://uktvplay\\.(?:uktv\\.)?co\\.uk/(?:.+?\\?.*?\\bvideo=|([^/]+/)*)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class DigitekaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.digiteka'
    IE_NAME = 'Digiteka'
    _VALID_URL = '(?x)\n        https?://(?:www\\.)?(?:digiteka\\.net|ultimedia\\.com)/\n        (?:\n            deliver/\n            (?P<embed_type>\n                generic|\n                musique\n            )\n            (?:/[^/]+)*/\n            (?:\n                src|\n                article\n            )|\n            default/index/video\n            (?P<site_type>\n                generic|\n                music\n            )\n            /id\n        )/(?P<id>[\\d+a-z]+)'
    _RETURN_TYPE = 'video'


class DLiveVODIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dlive'
    IE_NAME = 'dlive:vod'
    _VALID_URL = 'https?://(?:www\\.)?dlive\\.tv/p/(?P<uploader_id>.+?)\\+(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class DLiveStreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.dlive'
    IE_NAME = 'dlive:stream'
    _VALID_URL = 'https?://(?:www\\.)?dlive\\.tv/(?!p/)(?P<id>[\\w.-]+)'


class DroobleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.drooble'
    IE_NAME = 'Drooble'
    _VALID_URL = '(?x)https?://drooble\\.com/(?:\n        (?:(?P<user>[^/]+)/)?(?P<kind>song|videos|music/albums)/(?P<id>\\d+)|\n        (?P<user_2>[^/]+)/(?P<kind_2>videos|music))\n    '
    _RETURN_TYPE = 'any'


class UMGDeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.umg'
    IE_NAME = 'umg:de'
    _VALID_URL = 'https?://(?:www\\.)?universal-music\\.de/[^/]+/videos/[^/?#]+-(?P<id>\\d+)'
    IE_DESC = 'Universal Music Deutschland'
    _RETURN_TYPE = 'video'


class UnistraIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.unistra'
    IE_NAME = 'Unistra'
    _VALID_URL = 'https?://utv\\.unistra\\.fr/(?:index|video)\\.php\\?id_video\\=(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class UnityIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.unity'
    IE_NAME = 'Unity'
    _VALID_URL = 'https?://(?:www\\.)?unity3d\\.com/learn/tutorials/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class UnscriptedNewsVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.unscripted'
    IE_NAME = 'UnscriptedNewsVideo'
    _VALID_URL = 'https?://www\\.unscripted\\.news/videos/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class UnsupportedInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.unsupported'
    IE_NAME = 'UnsupportedInfoExtract'
    _VALID_URL = 'https?://(?:www\\.)?(?:)'
    IE_DESC = False


class KnownDRMIE(UnsupportedInfoExtractor):
    _module = 'yt_dlp.extractor.unsupported'
    IE_NAME = 'DRM'
    _VALID_URL = 'https?://(?:www\\.)?(?:play\\.hbomax\\.com|channel(?:4|5)\\.com|peacocktv\\.com|(?:[\\w\\.]+\\.)?disneyplus\\.com|open\\.spotify\\.com/(?:track|playlist|album|artist)|tvnz\\.co\\.nz|oneplus\\.ch|artstation\\.com/learning/courses|philo\\.com|(?:[\\w\\.]+\\.)?mech-plus\\.com|aha\\.video|mubi\\.com|vootkids\\.com|nowtv\\.it/watch|tv\\.apple\\.com)'
    IE_DESC = False


class KnownPiracyIE(UnsupportedInfoExtractor):
    _module = 'yt_dlp.extractor.unsupported'
    IE_NAME = 'Piracy'
    _VALID_URL = 'https?://(?:www\\.)?(?:dood\\.(?:to|watch|so|pm|wf|re)|viewsb\\.com|filemoon\\.sx|hentai\\.animestigma\\.com)'
    IE_DESC = False


class UOLIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.uol'
    IE_NAME = 'uol.com.br'
    _VALID_URL = 'https?://(?:.+?\\.)?uol\\.com\\.br/.*?(?:(?:mediaId|v)=|view/(?:[a-z0-9]+/)?|video(?:=|/(?:\\d{4}/\\d{2}/\\d{2}/)?))(?P<id>\\d+|[\\w-]+-[A-Z0-9]+)'
    _RETURN_TYPE = 'video'


class UplynkBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.uplynk'
    IE_NAME = 'UplynkBase'


class UplynkIE(UplynkBaseIE):
    _module = 'yt_dlp.extractor.uplynk'
    IE_NAME = 'uplynk'
    _VALID_URL = '(?x)\n        https?://[\\w-]+\\.uplynk\\.com/(?P<path>\n            ext/[0-9a-f]{32}/(?P<external_id>[^/?&]+)|\n            (?P<id>[0-9a-f]{32})\n        )\\.(?:m3u8|json)\n        (?:.*?\\bpbs=(?P<session_id>[^&]+))?'
    _RETURN_TYPE = 'video'


class UplynkPreplayIE(UplynkBaseIE):
    _module = 'yt_dlp.extractor.uplynk'
    IE_NAME = 'uplynk:preplay'
    _VALID_URL = 'https?://[\\w-]+\\.uplynk\\.com/preplay2?/(?P<path>ext/[0-9a-f]{32}/(?P<external_id>[^/?&]+)|(?P<id>[0-9a-f]{32}))\\.json'


class UrortIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.urort'
    IE_NAME = 'Urort'
    _VALID_URL = 'https?://(?:www\\.)?urort\\.p3\\.no/#!/Band/(?P<id>[^/]+)$'
    IE_DESC = 'NRK P3 Urørt'
    _RETURN_TYPE = 'video'


class URPlayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.urplay'
    IE_NAME = 'URPlay'
    _VALID_URL = 'https?://(?:www\\.)?ur(?:play|skola)\\.se/(?:program|Produkter)/(?P<id>[0-9]+)'
    age_limit = 15
    _RETURN_TYPE = 'video'


class USANetworkIE(NBCIE):
    _module = 'yt_dlp.extractor.usanetwork'
    IE_NAME = 'USANetwork'
    _VALID_URL = 'https?(?P<permalink>://(?:www\\.)?usanetwork\\.com/(?:[^/]+/videos?|movies?)/(?:[^/]+/)?(?P<id>\\d+))'
    _RETURN_TYPE = 'video'


class USATodayIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.usatoday'
    IE_NAME = 'USAToday'
    _VALID_URL = 'https?://(?:www\\.)?usatoday\\.com/(?:[^/]+/)*(?P<id>[^?/#]+)'
    _RETURN_TYPE = 'video'


class UstreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ustream'
    IE_NAME = 'ustream'
    _VALID_URL = 'https?://(?:www\\.)?(?:ustream\\.tv|video\\.ibm\\.com)/(?P<type>recorded|embed|embed/recorded)/(?P<id>\\d+)'
    _RETURN_TYPE = 'any'


class UstreamChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ustream'
    IE_NAME = 'ustream:channel'
    _VALID_URL = 'https?://(?:www\\.)?ustream\\.tv/channel/(?P<slug>.+)'
    _RETURN_TYPE = 'playlist'


class UstudioIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ustudio'
    IE_NAME = 'ustudio'
    _VALID_URL = 'https?://(?:(?:www|v1)\\.)?ustudio\\.com/video/(?P<id>[^/]+)/(?P<display_id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class UstudioEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ustudio'
    IE_NAME = 'ustudio:embed'
    _VALID_URL = 'https?://(?:(?:app|embed)\\.)?ustudio\\.com/embed/(?P<uid>[^/]+)/(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class UtreonIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.utreon'
    IE_NAME = 'Utreon'
    _VALID_URL = 'https?://(?:www\\.)?utreon.com/v/(?P<id>[a-zA-Z0-9_-]+)'
    _RETURN_TYPE = 'video'


class Varzesh3IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.varzesh3'
    IE_NAME = 'Varzesh3'
    _VALID_URL = 'https?://(?:www\\.)?video\\.varzesh3\\.com/(?:[^/]+/)+(?P<id>[^/]+)/?'
    _RETURN_TYPE = 'video'


class Vbox7IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vbox7'
    IE_NAME = 'Vbox7'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:[^/]+\\.)?vbox7\\.com/\n                        (?:\n                            play:|\n                            (?:\n                                emb/external\\.php|\n                                player/ext\\.swf\n                            )\\?.*?\\bvid=\n                        )\n                        (?P<id>[\\da-fA-F]+)\n                    '
    _RETURN_TYPE = 'video'


class VeeHDIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.veehd'
    IE_NAME = 'VeeHD'
    _VALID_URL = 'https?://veehd\\.com/video/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class VeoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.veo'
    IE_NAME = 'Veo'
    _VALID_URL = 'https?://app\\.veo\\.co/matches/(?P<id>[0-9A-Za-z-_]+)'
    _RETURN_TYPE = 'video'


class VeohIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.veoh'
    IE_NAME = 'Veoh'
    _VALID_URL = 'https?://(?:www\\.)?veoh\\.com/(?:watch|videos|embed|iphone/#_Watch)/(?P<id>(?:v|e|yapi-)[\\da-zA-Z]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class VeohUserIE(VeohIE):
    _module = 'yt_dlp.extractor.veoh'
    IE_NAME = 'veoh:user'
    _VALID_URL = 'https?://(?:www\\.)?veoh\\.com/users/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'playlist'


class VestiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vesti'
    IE_NAME = 'Vesti'
    _VALID_URL = 'https?://(?:.+?\\.)?vesti\\.ru/(?P<id>.+)'
    IE_DESC = 'Вести.Ru'
    _RETURN_TYPE = 'video'


class VevoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vevo'
    IE_NAME = 'VevoBase'


class VevoIE(VevoBaseIE):
    _module = 'yt_dlp.extractor.vevo'
    IE_NAME = 'Vevo'
    _VALID_URL = '(?x)\n        (?:https?://(?:www\\.)?vevo\\.com/watch/(?!playlist|genre)(?:[^/]+/(?:[^/]+/)?)?|\n           https?://cache\\.vevo\\.com/m/html/embed\\.html\\?video=|\n           https?://videoplayer\\.vevo\\.com/embed/embedded\\?videoId=|\n           https?://embed\\.vevo\\.com/.*?[?&]isrc=|\n           https?://tv\\.vevo\\.com/watch/artist/(?:[^/]+)/|\n           vevo:)\n        (?P<id>[^&?#]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class VevoPlaylistIE(VevoBaseIE):
    _module = 'yt_dlp.extractor.vevo'
    IE_NAME = 'VevoPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?vevo\\.com/watch/(?P<kind>playlist|genre)/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class BTArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vgtv'
    IE_NAME = 'bt:article'
    _VALID_URL = 'https?://(?:www\\.)?bt\\.no/(?:[^/]+/)+(?P<id>[^/]+)-\\d+\\.html'
    IE_DESC = 'Bergens Tidende Articles'
    _RETURN_TYPE = 'video'


class BTVestlendingenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vgtv'
    IE_NAME = 'bt:vestlendingen'
    _VALID_URL = 'https?://(?:www\\.)?bt\\.no/spesial/vestlendingen/#!/(?P<id>\\d+)'
    IE_DESC = 'Bergens Tidende - Vestlendingen'
    _RETURN_TYPE = 'video'


class VH1IE(MTVServicesInfoExtractor):
    _module = 'yt_dlp.extractor.vh1'
    IE_NAME = 'vh1.com'
    _VALID_URL = 'https?://(?:www\\.)?vh1\\.com/(?:video-clips|episodes)/(?P<id>[^/?#.]+)'
    _RETURN_TYPE = 'any'


class ViceBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vice'
    IE_NAME = 'ViceBase'


class ViceIE(ViceBaseIE, AdobePassIE):
    _module = 'yt_dlp.extractor.vice'
    IE_NAME = 'vice'
    _VALID_URL = 'https?://(?:(?:video|vms)\\.vice|(?:www\\.)?vice(?:land|tv))\\.com/(?P<locale>[^/]+)/(?:video/[^/]+|embed)/(?P<id>[\\da-f]{24})'
    age_limit = 14
    _RETURN_TYPE = 'video'


class ViceArticleIE(ViceBaseIE):
    _module = 'yt_dlp.extractor.vice'
    IE_NAME = 'vice:article'
    _VALID_URL = 'https://(?:www\\.)?vice\\.com/(?P<locale>[^/]+)/article/(?:[0-9a-z]{6}/)?(?P<id>[^?#]+)'
    age_limit = 17
    _RETURN_TYPE = 'video'


class ViceShowIE(ViceBaseIE):
    _module = 'yt_dlp.extractor.vice'
    IE_NAME = 'vice:show'
    _VALID_URL = 'https?://(?:video\\.vice|(?:www\\.)?vice(?:land|tv))\\.com/(?P<locale>[^/]+)/show/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class VidbitIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vidbit'
    IE_NAME = 'Vidbit'
    _VALID_URL = 'https?://(?:www\\.)?vidbit\\.co/(?:watch|embed)\\?.*?\\bv=(?P<id>[\\da-zA-Z]+)'
    _RETURN_TYPE = 'video'


class ViddlerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viddler'
    IE_NAME = 'Viddler'
    _VALID_URL = 'https?://(?:www\\.)?viddler\\.com/(?:v|embed|player)/(?P<id>[a-z0-9]+)(?:.+?\\bsecret=(\\d+))?'
    _RETURN_TYPE = 'video'


class VideaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videa'
    IE_NAME = 'Videa'
    _VALID_URL = '(?x)\n                    https?://\n                        videa(?:kid)?\\.hu/\n                        (?:\n                            videok/(?:[^/]+/)*[^?#&]+-|\n                            (?:videojs_)?player\\?.*?\\bv=|\n                            player/v/\n                        )\n                        (?P<id>[^?#&]+)\n                    '
    _RETURN_TYPE = 'video'


class VideocampusSachsenIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videocampus_sachsen'
    IE_NAME = 'ViMP'
    _VALID_URL = '(?x)https?://(?P<host>bergauf\\.tv|campus\\.demo\\.vimp\\.com|corporate\\.demo\\.vimp\\.com|dancehalldatabase\\.com|drehzahl\\.tv|educhannel\\.hs\\-gesundheit\\.de|emedia\\.ls\\.haw\\-hamburg\\.de|globale\\-evolution\\.net|hohu\\.tv|htvideos\\.hightechhigh\\.org|k210039\\.vimp\\.mivitec\\.net|media\\.cmslegal\\.com|media\\.hs\\-furtwangen\\.de|media\\.hwr\\-berlin\\.de|mediathek\\.dkfz\\.de|mediathek\\.htw\\-berlin\\.de|mediathek\\.polizei\\-bw\\.de|medien\\.hs\\-merseburg\\.de|mportal\\.europa\\-uni\\.de|pacific\\.demo\\.vimp\\.com|slctv\\.com|streaming\\.prairiesouth\\.ca|tube\\.isbonline\\.cn|univideo\\.uni\\-kassel\\.de|ursula2\\.genetics\\.emory\\.edu|ursulablicklevideoarchiv\\.com|v\\.agrarumweltpaedagogik\\.at|video\\.eplay\\-tv\\.de|video\\.fh\\-dortmund\\.de|video\\.hs\\-offenburg\\.de|video\\.hs\\-pforzheim\\.de|video\\.hspv\\.nrw\\.de|video\\.irtshdf\\.fr|video\\.pareygo\\.de|video\\.tu\\-freiberg\\.de|videocampus\\.sachsen\\.de|videoportal\\.uni\\-freiburg\\.de|videoportal\\.vm\\.uni\\-freiburg\\.de|videos\\.duoc\\.cl|videos\\.uni\\-paderborn\\.de|vimp\\-bemus\\.udk\\-berlin\\.de|vimp\\.aekwl\\.de|vimp\\.hs\\-mittweida\\.de|vimp\\.oth\\-regensburg\\.de|vimp\\.ph\\-heidelberg\\.de|vimp\\.sma\\-events\\.com|vimp\\.weka\\-fachmedien\\.de|webtv\\.univ\\-montp3\\.fr|www\\.b\\-tu\\.de/media|www\\.bergauf\\.tv|www\\.bigcitytv\\.de|www\\.cad\\-videos\\.de|www\\.drehzahl\\.tv|www\\.fh\\-bielefeld\\.de/medienportal|www\\.hohu\\.tv|www\\.orvovideo\\.com|www\\.rwe\\.tv|www\\.salzi\\.tv|www\\.wenglor\\-media\\.com|www2\\.univ\\-sba\\.dz)/(?:\n        m/(?P<tmp_id>[0-9a-f]+)|\n        (?:category/)?video/(?P<display_id>[\\w-]+)/(?P<id>[0-9a-f]{32})|\n        media/embed.*(?:\\?|&)key=(?P<embed_id>[0-9a-f]{32}&?)\n    )'
    _RETURN_TYPE = 'video'


class ViMPPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videocampus_sachsen'
    IE_NAME = 'ViMP:Playlist'
    _VALID_URL = '(?x)(?P<host>https?://(?:bergauf\\.tv|campus\\.demo\\.vimp\\.com|corporate\\.demo\\.vimp\\.com|dancehalldatabase\\.com|drehzahl\\.tv|educhannel\\.hs\\-gesundheit\\.de|emedia\\.ls\\.haw\\-hamburg\\.de|globale\\-evolution\\.net|hohu\\.tv|htvideos\\.hightechhigh\\.org|k210039\\.vimp\\.mivitec\\.net|media\\.cmslegal\\.com|media\\.hs\\-furtwangen\\.de|media\\.hwr\\-berlin\\.de|mediathek\\.dkfz\\.de|mediathek\\.htw\\-berlin\\.de|mediathek\\.polizei\\-bw\\.de|medien\\.hs\\-merseburg\\.de|mportal\\.europa\\-uni\\.de|pacific\\.demo\\.vimp\\.com|slctv\\.com|streaming\\.prairiesouth\\.ca|tube\\.isbonline\\.cn|univideo\\.uni\\-kassel\\.de|ursula2\\.genetics\\.emory\\.edu|ursulablicklevideoarchiv\\.com|v\\.agrarumweltpaedagogik\\.at|video\\.eplay\\-tv\\.de|video\\.fh\\-dortmund\\.de|video\\.hs\\-offenburg\\.de|video\\.hs\\-pforzheim\\.de|video\\.hspv\\.nrw\\.de|video\\.irtshdf\\.fr|video\\.pareygo\\.de|video\\.tu\\-freiberg\\.de|videocampus\\.sachsen\\.de|videoportal\\.uni\\-freiburg\\.de|videoportal\\.vm\\.uni\\-freiburg\\.de|videos\\.duoc\\.cl|videos\\.uni\\-paderborn\\.de|vimp\\-bemus\\.udk\\-berlin\\.de|vimp\\.aekwl\\.de|vimp\\.hs\\-mittweida\\.de|vimp\\.oth\\-regensburg\\.de|vimp\\.ph\\-heidelberg\\.de|vimp\\.sma\\-events\\.com|vimp\\.weka\\-fachmedien\\.de|webtv\\.univ\\-montp3\\.fr|www\\.b\\-tu\\.de/media|www\\.bergauf\\.tv|www\\.bigcitytv\\.de|www\\.cad\\-videos\\.de|www\\.drehzahl\\.tv|www\\.fh\\-bielefeld\\.de/medienportal|www\\.hohu\\.tv|www\\.orvovideo\\.com|www\\.rwe\\.tv|www\\.salzi\\.tv|www\\.wenglor\\-media\\.com|www2\\.univ\\-sba\\.dz))/(?:\n        album/view/aid/(?P<album_id>[0-9]+)|\n        (?P<mode>category|channel)/(?P<name>[\\w-]+)/(?P<id>[0-9]+)\n    )'
    _RETURN_TYPE = 'playlist'


class VideoDetectiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videodetective'
    IE_NAME = 'VideoDetective'
    _VALID_URL = 'https?://(?:www\\.)?videodetective\\.com/[^/]+/[^/]+/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class VideofyMeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videofyme'
    IE_NAME = 'videofy.me'
    _VALID_URL = 'https?://(?:www\\.videofy\\.me/.+?|p\\.videofy\\.me/v)/(?P<id>\\d+)(&|#|$)'
    _RETURN_TYPE = 'video'


class VideoKenBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videoken'
    IE_NAME = 'VideoKenBase'


class VideoKenIE(VideoKenBaseIE):
    _module = 'yt_dlp.extractor.videoken'
    IE_NAME = 'VideoKen'
    _VALID_URL = 'https?://(?P<host>videos\\.icts\\.res\\.in|videos\\.cncf\\.io|videos\\.neurips\\.cc)/(?:(?:topic|category)/[^/#?]+/)?video/(?P<id>[\\w-]+)'
    _RETURN_TYPE = 'video'


class VideoKenPlayerIE(VideoKenBaseIE):
    _module = 'yt_dlp.extractor.videoken'
    IE_NAME = 'VideoKenPlayer'
    _VALID_URL = 'https?://player\\.videoken\\.com/embed/slideslive-(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class VideoKenPlaylistIE(VideoKenBaseIE):
    _module = 'yt_dlp.extractor.videoken'
    IE_NAME = 'VideoKenPlaylist'
    _VALID_URL = 'https?://(?P<host>videos\\.icts\\.res\\.in|videos\\.cncf\\.io|videos\\.neurips\\.cc)/(?:category/\\d+/)?playlist/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class VideoKenCategoryIE(VideoKenBaseIE):
    _module = 'yt_dlp.extractor.videoken'
    IE_NAME = 'VideoKenCategory'
    _VALID_URL = 'https?://(?P<host>videos\\.icts\\.res\\.in|videos\\.cncf\\.io|videos\\.neurips\\.cc)/category/(?P<id>\\d+)/?(?:$|[?#])'
    _RETURN_TYPE = 'playlist'


class VideoKenTopicIE(VideoKenBaseIE):
    _module = 'yt_dlp.extractor.videoken'
    IE_NAME = 'VideoKenTopic'
    _VALID_URL = 'https?://(?P<host>videos\\.icts\\.res\\.in|videos\\.cncf\\.io|videos\\.neurips\\.cc)/topic/(?P<id>[^/#?]+)/?(?:$|[?#])'
    _RETURN_TYPE = 'playlist'


class VideomoreIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videomore'
    IE_NAME = 'videomore'
    _VALID_URL = '(?x)\n                    videomore:(?P<sid>\\d+)$|\n                    https?://\n                        (?:\n                            videomore\\.ru/\n                            (?:\n                                embed|\n                                [^/]+/[^/]+\n                            )/|\n                            (?:\n                                (?:player\\.)?videomore\\.ru|\n                                siren\\.more\\.tv/player\n                            )/[^/]*\\?.*?\\btrack_id=|\n                            odysseus\\.more.tv/player/(?P<partner_id>\\d+)/\n                        )\n                        (?P<id>\\d+)\n                        (?:[/?#&]|\\.(?:xml|json)|$)\n                    '
    age_limit = 16
    _RETURN_TYPE = 'video'


class VideomoreBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videomore'
    IE_NAME = 'VideomoreBase'


class VideomoreVideoIE(VideomoreBaseIE):
    _module = 'yt_dlp.extractor.videomore'
    IE_NAME = 'videomore:video'
    _VALID_URL = 'https?://(?:videomore\\.ru|more\\.tv)/(?P<id>(?:(?:[^/]+/){2})?[^/?#&]+)(?:/*|[?#&].*?)$'
    age_limit = 16
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return False if VideomoreIE.suitable(url) else super(VideomoreVideoIE, cls).suitable(url)


class VideomoreSeasonIE(VideomoreBaseIE):
    _module = 'yt_dlp.extractor.videomore'
    IE_NAME = 'videomore:season'
    _VALID_URL = 'https?://(?:videomore\\.ru|more\\.tv)/(?!embed)(?P<id>[^/]+/[^/?#&]+)(?:/*|[?#&].*?)$'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return (False if (VideomoreIE.suitable(url) or VideomoreVideoIE.suitable(url))
                else super(VideomoreSeasonIE, cls).suitable(url))


class VideoPressIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.videopress'
    IE_NAME = 'VideoPress'
    _VALID_URL = 'https?://video(?:\\.word)?press\\.com/embed/(?P<id>[\\da-zA-Z]{8})'
    _RETURN_TYPE = 'video'


class VidioBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vidio'
    IE_NAME = 'VidioBase'
    _NETRC_MACHINE = 'vidio'


class VidioIE(VidioBaseIE):
    _module = 'yt_dlp.extractor.vidio'
    IE_NAME = 'Vidio'
    _VALID_URL = 'https?://(?:www\\.)?vidio\\.com/(watch|embed)/(?P<id>\\d+)-(?P<display_id>[^/?#&]+)'
    _NETRC_MACHINE = 'vidio'
    _RETURN_TYPE = 'video'


class VidioPremierIE(VidioBaseIE):
    _module = 'yt_dlp.extractor.vidio'
    IE_NAME = 'VidioPremier'
    _VALID_URL = 'https?://(?:www\\.)?vidio\\.com/premier/(?P<id>\\d+)/(?P<display_id>[^/?#&]+)'
    _NETRC_MACHINE = 'vidio'
    _RETURN_TYPE = 'playlist'


class VidioLiveIE(VidioBaseIE):
    _module = 'yt_dlp.extractor.vidio'
    IE_NAME = 'VidioLive'
    _VALID_URL = 'https?://(?:www\\.)?vidio\\.com/live/(?P<id>\\d+)-(?P<display_id>[^/?#&]+)'
    _NETRC_MACHINE = 'vidio'
    _RETURN_TYPE = 'video'


class VidLiiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vidlii'
    IE_NAME = 'VidLii'
    _VALID_URL = 'https?://(?:www\\.)?vidlii\\.com/(?:watch|embed)\\?.*?\\bv=(?P<id>[0-9A-Za-z_-]{11})'
    _RETURN_TYPE = 'video'


class ViewLiftBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viewlift'
    IE_NAME = 'ViewLiftBase'


class ViewLiftIE(ViewLiftBaseIE):
    _module = 'yt_dlp.extractor.viewlift'
    IE_NAME = 'viewlift'
    _VALID_URL = 'https?://(?:www\\.)?(?P<domain>(?:(?:main\\.)?snagfilms|snagxtreme|funnyforfree|kiddovid|winnersview|(?:monumental|lax)sportsnetwork|vayafilm|failarmy|ftfnext|lnppass\\.legapallacanestro|moviespree|app\\.myoutdoortv|neoufitness|pflmma|theidentitytb)\\.com|(?:hoichoi|app\\.horseandcountry|kronon|marquee|supercrosslive)\\.tv)(?P<path>(?:/(?:films/title|show|(?:news/)?videos?|watch))?/(?P<id>[^?#]+))'
    age_limit = 17
    _RETURN_TYPE = 'any'

    @classmethod
    def suitable(cls, url):
        return False if ViewLiftEmbedIE.suitable(url) else super(ViewLiftIE, cls).suitable(url)


class ViewLiftEmbedIE(ViewLiftBaseIE):
    _module = 'yt_dlp.extractor.viewlift'
    IE_NAME = 'viewlift:embed'
    _VALID_URL = 'https?://(?:(?:www|embed)\\.)?(?P<domain>(?:(?:main\\.)?snagfilms|snagxtreme|funnyforfree|kiddovid|winnersview|(?:monumental|lax)sportsnetwork|vayafilm|failarmy|ftfnext|lnppass\\.legapallacanestro|moviespree|app\\.myoutdoortv|neoufitness|pflmma|theidentitytb)\\.com|(?:hoichoi|app\\.horseandcountry|kronon|marquee|supercrosslive)\\.tv)/embed/player\\?.*\\bfilmId=(?P<id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class ViideaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viidea'
    IE_NAME = 'Viidea'
    _VALID_URL = '(?x)https?://(?:www\\.)?(?:\n            videolectures\\.net|\n            flexilearn\\.viidea\\.net|\n            presentations\\.ocwconsortium\\.org|\n            video\\.travel-zoom\\.si|\n            video\\.pomp-forum\\.si|\n            tv\\.nil\\.si|\n            video\\.hekovnik.com|\n            video\\.szko\\.si|\n            kpk\\.viidea\\.com|\n            inside\\.viidea\\.net|\n            video\\.kiberpipa\\.org|\n            bvvideo\\.si|\n            kongres\\.viidea\\.net|\n            edemokracija\\.viidea\\.com\n        )(?:/lecture)?/(?P<id>[^/]+)(?:/video/(?P<part>\\d+))?/*(?:[#?].*)?$'
    _RETURN_TYPE = 'any'


class VimeoBaseInfoExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'VimeoBaseInfoExtract'
    _NETRC_MACHINE = 'vimeo'


class VimeoIE(VimeoBaseInfoExtractor):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo'
    _VALID_URL = '(?x)\n                     https?://\n                         (?:\n                             (?:\n                                 www|\n                                 player\n                             )\n                             \\.\n                         )?\n                         vimeo\\.com/\n                         (?:\n                             (?P<u>user)|\n                             (?!(?:channels|album|showcase)/[^/?#]+/?(?:$|[?#])|[^/]+/review/|ondemand/)\n                             (?:.*?/)??\n                             (?P<q>\n                                 (?:\n                                     play_redirect_hls|\n                                     moogaloop\\.swf)\\?clip_id=\n                             )?\n                             (?:videos?/)?\n                         )\n                         (?P<id>[0-9]+)\n                         (?(u)\n                             /(?!videos|likes)[^/?#]+/?|\n                             (?(q)|/(?P<unlisted_hash>[\\da-f]{10}))?\n                         )\n                         (?:(?(q)[&]|(?(u)|/?)[?]).*?)?(?:[#].*)?$\n                 '
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'video'


class VimeoAlbumIE(VimeoBaseInfoExtractor):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:album'
    _VALID_URL = 'https://vimeo\\.com/(?:album|showcase)/(?P<id>\\d+)(?:$|[?#]|/(?!video))'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'playlist'


class VimeoChannelIE(VimeoBaseInfoExtractor):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:channel'
    _VALID_URL = 'https://vimeo\\.com/channels/(?P<id>[^/?#]+)/?(?:$|[?#])'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'playlist'


class VimeoGroupsIE(VimeoChannelIE):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:group'
    _VALID_URL = 'https://vimeo\\.com/groups/(?P<id>[^/]+)(?:/(?!videos?/\\d+)|$)'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'playlist'


class VimeoLikesIE(VimeoChannelIE):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:likes'
    _VALID_URL = 'https://(?:www\\.)?vimeo\\.com/(?P<id>[^/]+)/likes/?(?:$|[?#]|sort:)'
    IE_DESC = 'Vimeo user likes'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'playlist'


class VimeoOndemandIE(VimeoIE):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:ondemand'
    _VALID_URL = 'https?://(?:www\\.)?vimeo\\.com/ondemand/(?:[^/]+/)?(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'video'


class VimeoProIE(VimeoBaseInfoExtractor):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:pro'
    _VALID_URL = 'https?://(?:www\\.)?vimeopro\\.com/[^/?#]+/(?P<slug>[^/?#]+)(?:(?:/videos?/(?P<id>[0-9]+)))?'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'video'


class VimeoReviewIE(VimeoBaseInfoExtractor):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:review'
    _VALID_URL = '(?P<url>https://vimeo\\.com/[^/]+/review/(?P<id>[^/]+)/[0-9a-f]{10})'
    IE_DESC = 'Review pages on vimeo'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'video'


class VimeoUserIE(VimeoChannelIE):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:user'
    _VALID_URL = 'https://vimeo\\.com/(?!(?:[0-9]+|watchlater)(?:$|[?#/]))(?P<id>[^/]+)(?:/videos)?/?(?:$|[?#])'
    _NETRC_MACHINE = 'vimeo'
    _RETURN_TYPE = 'playlist'


class VimeoWatchLaterIE(VimeoChannelIE):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vimeo:watchlater'
    _VALID_URL = 'https://vimeo\\.com/(?:home/)?watchlater|:vimeowatchlater'
    IE_DESC = 'Vimeo watch later list, ":vimeowatchlater" keyword (requires authentication)'
    _NETRC_MACHINE = 'vimeo'


class VHXEmbedIE(VimeoBaseInfoExtractor):
    _module = 'yt_dlp.extractor.vimeo'
    IE_NAME = 'vhx:embed'
    _VALID_URL = 'https?://embed\\.vhx\\.tv/videos/(?P<id>\\d+)'
    _NETRC_MACHINE = 'vimeo'


class VimmIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vimm'
    IE_NAME = 'Vimm:stream'
    _VALID_URL = 'https?://(?:www\\.)?vimm\\.tv/(?:c/)?(?P<id>[0-9a-z-]+)$'
    _RETURN_TYPE = 'video'


class VimmRecordingIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vimm'
    IE_NAME = 'Vimm:recording'
    _VALID_URL = 'https?://(?:www\\.)?vimm\\.tv/c/(?P<channel_id>[0-9a-z-]+)\\?v=(?P<video_id>[0-9A-Za-z]+)'
    _RETURN_TYPE = 'video'


class VimpleIE(SprutoBaseIE):
    _module = 'yt_dlp.extractor.vimple'
    IE_NAME = 'Vimple'
    _VALID_URL = 'https?://(?:player\\.vimple\\.(?:ru|co)/iframe|vimple\\.(?:ru|co))/(?P<id>[\\da-f-]{32,36})'
    IE_DESC = 'Vimple - one-click video hosting'
    _RETURN_TYPE = 'video'


class VineIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vine'
    IE_NAME = 'Vine'
    _VALID_URL = 'https?://(?:www\\.)?vine\\.co/(?:v|oembed)/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class VineUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vine'
    IE_NAME = 'vine:user'
    _VALID_URL = 'https?://vine\\.co/(?P<u>u/)?(?P<user>[^/]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if VineIE.suitable(url) else super(VineUserIE, cls).suitable(url)


class VikiBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viki'
    IE_NAME = 'VikiBase'
    _NETRC_MACHINE = 'viki'


class VikiIE(VikiBaseIE):
    _module = 'yt_dlp.extractor.viki'
    IE_NAME = 'viki'
    _VALID_URL = 'https?://(?:www\\.)?viki\\.(?:com|net|mx|jp|fr)/(?:videos|player)/(?P<id>[0-9]+v)'
    _NETRC_MACHINE = 'viki'
    age_limit = 13
    _RETURN_TYPE = 'video'


class VikiChannelIE(VikiBaseIE):
    _module = 'yt_dlp.extractor.viki'
    IE_NAME = 'viki:channel'
    _VALID_URL = 'https?://(?:www\\.)?viki\\.(?:com|net|mx|jp|fr)/(?:tv|news|movies|artists)/(?P<id>[0-9]+c)'
    _NETRC_MACHINE = 'viki'
    _RETURN_TYPE = 'playlist'


class ViqeoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viqeo'
    IE_NAME = 'Viqeo'
    _VALID_URL = '(?x)\n                        (?:\n                            viqeo:|\n                            https?://cdn\\.viqeo\\.tv/embed/*\\?.*?\\bvid=|\n                            https?://api\\.viqeo\\.tv/v\\d+/data/startup?.*?\\bvideo(?:%5B%5D|\\[\\])=\n                        )\n                        (?P<id>[\\da-f]+)\n                    '
    _RETURN_TYPE = 'video'


class ViuBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viu'
    IE_NAME = 'ViuBase'


class ViuIE(ViuBaseIE):
    _module = 'yt_dlp.extractor.viu'
    IE_NAME = 'Viu'
    _VALID_URL = '(?:viu:|https?://[^/]+\\.viu\\.com/[a-z]{2}/media/)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ViuPlaylistIE(ViuBaseIE):
    _module = 'yt_dlp.extractor.viu'
    IE_NAME = 'viu:playlist'
    _VALID_URL = 'https?://www\\.viu\\.com/[^/]+/listing/playlist-(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class ViuOTTIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viu'
    IE_NAME = 'viu:ott'
    _VALID_URL = 'https?://(?:www\\.)?viu\\.com/ott/(?P<country_code>[a-z]{2})/(?P<lang_code>[a-z]{2}-[a-z]{2})/vod/(?P<id>\\d+)'
    _NETRC_MACHINE = 'viu'
    _RETURN_TYPE = 'any'


class ViuOTTIndonesiaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.viu'
    IE_NAME = 'ViuOTTIndonesiaBase'


class ViuOTTIndonesiaIE(ViuOTTIndonesiaBaseIE):
    _module = 'yt_dlp.extractor.viu'
    IE_NAME = 'ViuOTTIndonesia'
    _VALID_URL = 'https?://www\\.viu\\.com/ott/\\w+/\\w+/all/video-[\\w-]+-(?P<id>\\d+)'
    age_limit = 13
    _RETURN_TYPE = 'video'


class VKBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vk'
    IE_NAME = 'VKBase'
    _NETRC_MACHINE = 'vk'


class VKIE(VKBaseIE):
    _module = 'yt_dlp.extractor.vk'
    IE_NAME = 'vk'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:\n                                (?:(?:m|new)\\.)?vk\\.com/video_|\n                                (?:www\\.)?daxab.com/\n                            )\n                            ext\\.php\\?(?P<embed_query>.*?\\boid=(?P<oid>-?\\d+).*?\\bid=(?P<id>\\d+).*)|\n                            (?:\n                                (?:(?:m|new)\\.)?vk\\.com/(?:.+?\\?.*?z=)?(?:video|clip)|\n                                (?:www\\.)?daxab.com/embed/\n                            )\n                            (?P<videoid>-?\\d+_\\d+)(?:.*\\blist=(?P<list_id>([\\da-f]+)|(ln-[\\da-zA-Z]+)))?\n                        )\n                    '
    IE_DESC = 'VK'
    _NETRC_MACHINE = 'vk'
    _RETURN_TYPE = 'video'


class VKUserVideosIE(VKBaseIE):
    _module = 'yt_dlp.extractor.vk'
    IE_NAME = 'vk:uservideos'
    _VALID_URL = 'https?://(?:(?:m|new)\\.)?vk\\.com/video/(?:playlist/)?(?P<id>[^?$#/&]+)(?!\\?.*\\bz=video)(?:[/?#&](?:.*?\\bsection=(?P<section>\\w+))?|$)'
    IE_DESC = "VK - User's Videos"
    _NETRC_MACHINE = 'vk'
    _RETURN_TYPE = 'playlist'


class VKWallPostIE(VKBaseIE):
    _module = 'yt_dlp.extractor.vk'
    IE_NAME = 'vk:wallpost'
    _VALID_URL = 'https?://(?:(?:(?:(?:m|new)\\.)?vk\\.com/(?:[^?]+\\?.*\\bw=)?wall(?P<id>-?\\d+_\\d+)))'
    _NETRC_MACHINE = 'vk'
    _RETURN_TYPE = 'playlist'


class VKPlayBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vk'
    IE_NAME = 'VKPlayBase'


class VKPlayIE(VKPlayBaseIE):
    _module = 'yt_dlp.extractor.vk'
    IE_NAME = 'VKPlay'
    _VALID_URL = 'https?://vkplay\\.live/(?P<username>[^/]+)/record/(?P<id>[a-f0-9\\-]+)'
    _RETURN_TYPE = 'video'


class VKPlayLiveIE(VKPlayBaseIE):
    _module = 'yt_dlp.extractor.vk'
    IE_NAME = 'VKPlayLive'
    _VALID_URL = 'https?://vkplay\\.live/(?P<id>[^/]+)/?(?:[#?]|$)'
    _RETURN_TYPE = 'video'


class VocarooIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vocaroo'
    IE_NAME = 'Vocaroo'
    _VALID_URL = 'https?://(?:www\\.)?(?:vocaroo\\.com|voca\\.ro)/(?:embed/)?(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class VodlockerIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vodlocker'
    IE_NAME = 'Vodlocker'
    _VALID_URL = 'https?://(?:www\\.)?vodlocker\\.(?:com|city)/(?:embed-)?(?P<id>[0-9a-zA-Z]+)(?:\\..*?)?'
    _RETURN_TYPE = 'video'


class VODPlIE(OnetBaseIE):
    _module = 'yt_dlp.extractor.vodpl'
    IE_NAME = 'VODPl'
    _VALID_URL = 'https?://vod\\.pl/(?:[^/]+/)+(?P<id>[0-9a-zA-Z]+)'
    _RETURN_TYPE = 'video'


class VODPlatformIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vodplatform'
    IE_NAME = 'VODPlatform'
    _VALID_URL = 'https?://(?:(?:www\\.)?vod-platform\\.net|embed\\.kwikmotion\\.com)/[eE]mbed/(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'video'


class VoiceRepublicIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.voicerepublic'
    IE_NAME = 'VoiceRepublic'
    _VALID_URL = 'https?://voicerepublic\\.com/(?:talks|embed)/(?P<id>[0-9a-z-]+)'
    _RETURN_TYPE = 'video'


class VoicyBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.voicy'
    IE_NAME = 'VoicyBase'


class VoicyIE(VoicyBaseIE):
    _module = 'yt_dlp.extractor.voicy'
    IE_NAME = 'voicy'
    _VALID_URL = 'https?://voicy\\.jp/channel/(?P<channel_id>\\d+)/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'


class VoicyChannelIE(VoicyBaseIE):
    _module = 'yt_dlp.extractor.voicy'
    IE_NAME = 'voicy:channel'
    _VALID_URL = 'https?://voicy\\.jp/channel/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return not VoicyIE.suitable(url) and super().suitable(url)


class VolejTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.volejtv'
    IE_NAME = 'VolejTV'
    _VALID_URL = 'https?://volej\\.tv/video/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class VootBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.voot'
    IE_NAME = 'VootBase'
    _NETRC_MACHINE = 'voot'


class VootIE(VootBaseIE):
    _module = 'yt_dlp.extractor.voot'
    IE_NAME = 'Voot'
    _VALID_URL = '(?x)\n                    (?:\n                        voot:|\n                        https?://(?:www\\.)?voot\\.com/?\n                        (?:\n                            movies?/[^/]+/|\n                            (?:shows|kids)/(?:[^/]+/){4}\n                        )\n                     )\n                    (?P<id>\\d{3,})\n                    '
    _NETRC_MACHINE = 'voot'
    age_limit = 13
    _RETURN_TYPE = 'video'


class VootSeriesIE(VootBaseIE):
    _module = 'yt_dlp.extractor.voot'
    IE_NAME = 'VootSeries'
    _VALID_URL = 'https?://(?:www\\.)?voot\\.com/shows/[^/]+/(?P<id>\\d{3,})'
    _NETRC_MACHINE = 'voot'
    _RETURN_TYPE = 'playlist'


class VoxMediaVolumeIE(OnceIE):
    _module = 'yt_dlp.extractor.voxmedia'
    IE_NAME = 'VoxMediaVolume'
    _VALID_URL = 'https?://volume\\.vox-cdn\\.com/embed/(?P<id>[0-9a-f]{9})'


class VoxMediaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.voxmedia'
    IE_NAME = 'VoxMedia'
    _VALID_URL = 'https?://(?:www\\.)?(?:(?:theverge|vox|sbnation|eater|polygon|curbed|racked|funnyordie)\\.com|recode\\.net)/(?:[^/]+/)*(?P<id>[^/?]+)'
    _RETURN_TYPE = 'any'


class GigyaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.gigya'
    IE_NAME = 'GigyaBase'


class VRTBaseIE(GigyaBaseIE):
    _module = 'yt_dlp.extractor.vrt'
    IE_NAME = 'VRTBase'


class VRTIE(VRTBaseIE):
    _module = 'yt_dlp.extractor.vrt'
    IE_NAME = 'VRT'
    _VALID_URL = 'https?://(?:www\\.)?(?P<site>vrt\\.be/vrtnws|sporza\\.be)/[a-z]{2}/\\d{4}/\\d{2}/\\d{2}/(?P<id>[^/?&#]+)'
    IE_DESC = 'VRT NWS, Flanders News, Flandern Info and Sporza'
    _RETURN_TYPE = 'video'


class VrtNUIE(VRTBaseIE):
    _module = 'yt_dlp.extractor.vrt'
    IE_NAME = 'VrtNU'
    _VALID_URL = 'https?://(?:www\\.)?vrt\\.be/vrtnu/a-z/(?:[^/]+/){2}(?P<id>[^/?#&]+)'
    IE_DESC = 'VRT MAX'
    _NETRC_MACHINE = 'vrtnu'
    age_limit = 12
    _RETURN_TYPE = 'video'


class KetnetIE(VRTBaseIE):
    _module = 'yt_dlp.extractor.vrt'
    IE_NAME = 'Ketnet'
    _VALID_URL = 'https?://(?:www\\.)?ketnet\\.be/(?P<id>(?:[^/]+/)*[^/?#&]+)'
    _RETURN_TYPE = 'video'


class DagelijkseKostIE(VRTBaseIE):
    _module = 'yt_dlp.extractor.vrt'
    IE_NAME = 'DagelijkseKost'
    _VALID_URL = 'https?://dagelijksekost\\.een\\.be/gerechten/(?P<id>[^/?#&]+)'
    IE_DESC = 'dagelijksekost.een.be'
    _RETURN_TYPE = 'video'


class VrakIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vrak'
    IE_NAME = 'Vrak'
    _VALID_URL = 'https?://(?:www\\.)?vrak\\.tv/videos\\?.*?\\btarget=(?P<id>[\\d.]+)'
    age_limit = 8
    _RETURN_TYPE = 'video'


class VRVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vrv'
    IE_NAME = 'VRVBase'


class VRVIE(VRVBaseIE):
    _module = 'yt_dlp.extractor.vrv'
    IE_NAME = 'vrv'
    _VALID_URL = 'https?://(?:www\\.)?vrv\\.co/watch/(?P<id>[A-Z0-9]+)'
    _NETRC_MACHINE = 'vrv'
    _RETURN_TYPE = 'any'


class VRVSeriesIE(VRVBaseIE):
    _module = 'yt_dlp.extractor.vrv'
    IE_NAME = 'vrv:series'
    _VALID_URL = 'https?://(?:www\\.)?vrv\\.co/series/(?P<id>[A-Z0-9]+)'
    _RETURN_TYPE = 'playlist'


class VShareIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vshare'
    IE_NAME = 'VShare'
    _VALID_URL = 'https?://(?:www\\.)?vshare\\.io/[dv]/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class VTMIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vtm'
    IE_NAME = 'VTM'
    _VALID_URL = 'https?://(?:www\\.)?vtm\\.be/([^/?&#]+)~v(?P<id>[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})'
    _RETURN_TYPE = 'video'


class MedialaanIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.medialaan'
    IE_NAME = 'Medialaan'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:embed\\.)?mychannels.video/embed/|\n                            embed\\.mychannels\\.video/(?:s(?:dk|cript)/)?production/|\n                            (?:www\\.)?(?:\n                                (?:\n                                    7sur7|\n                                    demorgen|\n                                    hln|\n                                    joe|\n                                    qmusic\n                                )\\.be|\n                                (?:\n                                    [abe]d|\n                                    bndestem|\n                                    destentor|\n                                    gelderlander|\n                                    pzc|\n                                    tubantia|\n                                    volkskrant\n                                )\\.nl\n                            )/video/(?:[^/]+/)*[^/?&#]+~p\n                        )\n                        (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class VuClipIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vuclip'
    IE_NAME = 'VuClip'
    _VALID_URL = 'https?://(?:m\\.)?vuclip\\.com/w\\?.*?cid=(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class VuploadIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vupload'
    IE_NAME = 'Vupload'
    _VALID_URL = 'https://vupload\\.com/v/(?P<id>[a-z0-9]+)'
    _RETURN_TYPE = 'video'


class VVVVIDIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vvvvid'
    IE_NAME = 'VVVVID'
    _VALID_URL = 'https?://(?:www\\.)?vvvvid\\.it/(?:#!)?(?:show|anime|film|series)/(?P<show_id>\\d+)/[^/]+/(?P<season_id>\\d+)/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class VVVVIDShowIE(VVVVIDIE):
    _module = 'yt_dlp.extractor.vvvvid'
    IE_NAME = 'VVVVIDShow'
    _VALID_URL = '(?P<base_url>https?://(?:www\\.)?vvvvid\\.it/(?:#!)?(?:show|anime|film|series)/(?P<id>\\d+)(?:/(?P<show_title>[^/?&#]+))?)/?(?:[?#&]|$)'
    _RETURN_TYPE = 'playlist'


class VyboryMosIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vyborymos'
    IE_NAME = 'VyboryMos'
    _VALID_URL = 'https?://vybory\\.mos\\.ru/(?:#precinct/|account/channels\\?.*?\\bstation_id=)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class VzaarIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.vzaar'
    IE_NAME = 'Vzaar'
    _VALID_URL = 'https?://(?:(?:www|view)\\.)?vzaar\\.com/(?:videos/)?(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class WakanimIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wakanim'
    IE_NAME = 'Wakanim'
    _VALID_URL = 'https://(?:www\\.)?wakanim\\.tv/[^/]+/v2/catalogue/episode/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class WallaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.walla'
    IE_NAME = 'Walla'
    _VALID_URL = 'https?://vod\\.walla\\.co\\.il/[^/]+/(?P<id>\\d+)/(?P<display_id>.+)'
    _RETURN_TYPE = 'video'


class WashingtonPostIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.washingtonpost'
    IE_NAME = 'washingtonpost'
    _VALID_URL = '(?:washingtonpost:|https?://(?:www\\.)?washingtonpost\\.com/(?:video|posttv)/(?:[^/]+/)*)(?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class WashingtonPostArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.washingtonpost'
    IE_NAME = 'washingtonpost:article'
    _VALID_URL = 'https?://(?:www\\.)?washingtonpost\\.com/(?:[^/]+/)*(?P<id>[^/?#]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if WashingtonPostIE.suitable(url) else super(WashingtonPostArticleIE, cls).suitable(url)


class WASDTVBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wasdtv'
    IE_NAME = 'WASDTVBase'


class WASDTVStreamIE(WASDTVBaseIE):
    _module = 'yt_dlp.extractor.wasdtv'
    IE_NAME = 'wasdtv:stream'
    _VALID_URL = 'https?://wasd\\.tv/(?P<id>[^/#?]+)$'
    _RETURN_TYPE = 'video'


class WASDTVRecordIE(WASDTVBaseIE):
    _module = 'yt_dlp.extractor.wasdtv'
    IE_NAME = 'wasdtv:record'
    _VALID_URL = 'https?://wasd\\.tv/[^/#?]+(?:/videos)?\\?record=(?P<id>\\d+)$'
    _RETURN_TYPE = 'video'


class WASDTVClipIE(WASDTVBaseIE):
    _module = 'yt_dlp.extractor.wasdtv'
    IE_NAME = 'wasdtv:clip'
    _VALID_URL = 'https?://wasd\\.tv/[^/#?]+/clips\\?clip=(?P<id>\\d+)$'
    _RETURN_TYPE = 'video'


class WatIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wat'
    IE_NAME = 'wat.tv'
    _VALID_URL = '(?:wat:|https?://(?:www\\.)?wat\\.tv/video/.*-)(?P<id>[0-9a-z]+)'
    _RETURN_TYPE = 'video'


class WatchBoxIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.watchbox'
    IE_NAME = 'WatchBox'
    _VALID_URL = 'https?://(?:www\\.)?watchbox\\.de/(?P<kind>serien|filme)/(?:[^/]+/)*[^/]+-(?P<id>\\d+)'
    age_limit = 16
    _RETURN_TYPE = 'video'


class WatchIndianPornIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.watchindianporn'
    IE_NAME = 'WatchIndianPorn'
    _VALID_URL = 'https?://(?:www\\.)?watchindianporn\\.net/(?:[^/]+/)*video/(?P<display_id>[^/]+)-(?P<id>[a-zA-Z0-9]+)\\.html'
    IE_DESC = 'Watch Indian Porn'
    age_limit = 18
    _RETURN_TYPE = 'video'


class WDRIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wdr'
    IE_NAME = 'WDR'
    _VALID_URL = '(?x)https?://\n        (?:deviceids-medp\\.wdr\\.de/ondemand/\\d+/|\n           kinder\\.wdr\\.de/(?!mediathek/)[^#?]+-)\n        (?P<id>\\d+)\\.(?:js|assetjsonp)\n    '
    _RETURN_TYPE = 'video'


class WDRPageIE(WDRIE):
    _module = 'yt_dlp.extractor.wdr'
    IE_NAME = 'WDRPage'
    _VALID_URL = 'https?://(?:www\\d?\\.)?(?:(?:kinder\\.)?wdr\\d?|sportschau)\\.de/(?:mediathek/)?(?:[^/]+/)*(?P<display_id>[^/]+)\\.html|https?://(?:www\\.)wdrmaus.de/(?:[^/]+/)*?(?P<maus_id>[^/?#.]+)(?:/?|/index\\.php5|\\.php5)$'
    _RETURN_TYPE = 'any'


class WDRElefantIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wdr'
    IE_NAME = 'WDRElefant'
    _VALID_URL = 'https?://(?:www\\.)wdrmaus\\.de/elefantenseite/#(?P<id>.+)'
    _RETURN_TYPE = 'video'


class WDRMobileIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wdr'
    IE_NAME = 'wdr:mobile'
    _VALID_URL = '(?x)\n        https?://mobile-ondemand\\.wdr\\.de/\n        .*?/fsk(?P<age_limit>[0-9]+)\n        /[0-9]+/[0-9]+/\n        (?P<id>[0-9]+)_(?P<title>[0-9]+)'
    _WORKING = False
    _RETURN_TYPE = 'video'


class WebcameraplIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.webcamerapl'
    IE_NAME = 'Webcamerapl'
    _VALID_URL = 'https?://(?P<id>[\\w-]+)\\.webcamera\\.pl'
    _RETURN_TYPE = 'video'


class WebcasterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.webcaster'
    IE_NAME = 'Webcaster'
    _VALID_URL = 'https?://bl\\.webcaster\\.pro/(?:quote|media)/start/free_(?P<id>[^/]+)'
    _RETURN_TYPE = 'video'


class WebcasterFeedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.webcaster'
    IE_NAME = 'WebcasterFeed'
    _VALID_URL = 'https?://bl\\.webcaster\\.pro/feed/start/free_(?P<id>[^/]+)'


class WebOfStoriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.webofstories'
    IE_NAME = 'WebOfStories'
    _VALID_URL = 'https?://(?:www\\.)?webofstories\\.com/play/(?:[^/]+/)?(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class WebOfStoriesPlaylistIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.webofstories'
    IE_NAME = 'WebOfStoriesPlaylist'
    _VALID_URL = 'https?://(?:www\\.)?webofstories\\.com/playAll/(?P<id>[^/]+)'
    _RETURN_TYPE = 'playlist'


class WeiboIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.weibo'
    IE_NAME = 'Weibo'
    _VALID_URL = 'https?://(?:www\\.)?weibo\\.com/[0-9]+/(?P<id>[a-zA-Z0-9]+)'
    _RETURN_TYPE = 'video'


class WeiboMobileIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.weibo'
    IE_NAME = 'WeiboMobile'
    _VALID_URL = 'https?://m\\.weibo\\.cn/status/(?P<id>[0-9]+)(\\?.+)?'
    _RETURN_TYPE = 'video'


class WeiqiTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.weiqitv'
    IE_NAME = 'WeiqiTV'
    _VALID_URL = 'https?://(?:www\\.)?weiqitv\\.com/index/video_play\\?videoId=(?P<id>[A-Za-z0-9]+)'
    IE_DESC = 'WQTV'
    _RETURN_TYPE = 'video'


class WeverseBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'WeverseBase'
    _NETRC_MACHINE = 'weverse'


class WeverseIE(WeverseBaseIE):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'Weverse'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?weverse.io/(?P<artist>[^/?#]+)/live/(?P<id>[\\d-]+)'
    _NETRC_MACHINE = 'weverse'
    _RETURN_TYPE = 'video'


class WeverseMediaIE(WeverseBaseIE):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'WeverseMedia'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?weverse.io/(?P<artist>[^/?#]+)/media/(?P<id>[\\d-]+)'
    _NETRC_MACHINE = 'weverse'
    _RETURN_TYPE = 'video'


class WeverseMomentIE(WeverseBaseIE):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'WeverseMoment'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?weverse.io/(?P<artist>[^/?#]+)/moment/(?P<uid>[\\da-f]+)/post/(?P<id>[\\d-]+)'
    _NETRC_MACHINE = 'weverse'
    _RETURN_TYPE = 'video'


class WeverseTabBaseIE(WeverseBaseIE):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'WeverseTabBase'
    _NETRC_MACHINE = 'weverse'


class WeverseLiveTabIE(WeverseTabBaseIE):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'WeverseLiveTab'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?weverse.io/(?P<id>[^/?#]+)/live/?(?:[?#]|$)'
    _NETRC_MACHINE = 'weverse'
    _RETURN_TYPE = 'playlist'


class WeverseMediaTabIE(WeverseTabBaseIE):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'WeverseMediaTab'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?weverse.io/(?P<id>[^/?#]+)/media(?:/|/all|/new)?(?:[?#]|$)'
    _NETRC_MACHINE = 'weverse'
    _RETURN_TYPE = 'playlist'


class WeverseLiveIE(WeverseBaseIE):
    _module = 'yt_dlp.extractor.weverse'
    IE_NAME = 'WeverseLive'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?weverse.io/(?P<id>[^/?#]+)/?(?:[?#]|$)'
    _NETRC_MACHINE = 'weverse'
    _RETURN_TYPE = 'video'


class WeVidiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wevidi'
    IE_NAME = 'WeVidi'
    _VALID_URL = 'https?://(?:www\\.)?wevidi\\.net/watch/(?P<id>[\\w-]{11})'
    _RETURN_TYPE = 'video'


class WeyyakIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.weyyak'
    IE_NAME = 'Weyyak'
    _VALID_URL = 'https?://weyyak\\.com/(?P<lang>\\w+)/(?:player/)?(?P<type>episode|movie)/(?P<id>\\d+)'
    age_limit = 15
    _RETURN_TYPE = 'video'


class WhypIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.whyp'
    IE_NAME = 'Whyp'
    _VALID_URL = 'https?://(?:www\\.)?whyp\\.it/tracks/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class WikimediaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wikimedia'
    IE_NAME = 'wikimedia.org'
    _VALID_URL = 'https?://commons\\.wikimedia\\.org/wiki/File:(?P<id>[^/#?]+)\\.\\w+'
    _RETURN_TYPE = 'video'


class WillowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.willow'
    IE_NAME = 'Willow'
    _VALID_URL = 'https?://(www\\.)?willow\\.tv/videos/(?P<id>[0-9a-z-_]+)'
    _RETURN_TYPE = 'video'


class WimTVIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wimtv'
    IE_NAME = 'WimTV'
    _VALID_URL = '(?x:\n        https?://platform.wim.tv/\n        (?:\n            (?:embed/)?\\?\n            |\\#/webtv/.+?/\n        )\n        (?P<type>vod|live|cast)[=/]\n        (?P<id>[\\da-f]{8}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{4}-[\\da-f]{12}).*?)'
    _RETURN_TYPE = 'video'


class WhoWatchIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.whowatch'
    IE_NAME = 'whowatch'
    _VALID_URL = 'https?://whowatch\\.tv/viewer/(?P<id>\\d+)'


class WistiaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wistia'
    IE_NAME = 'WistiaBase'


class WistiaIE(WistiaBaseIE):
    _module = 'yt_dlp.extractor.wistia'
    IE_NAME = 'Wistia'
    _VALID_URL = '(?:wistia:|https?://(?:\\w+\\.)?wistia\\.(?:net|com)/(?:embed/)?(?:iframe|medias)/)(?P<id>[a-z0-9]{10})'
    _RETURN_TYPE = 'video'


class WistiaPlaylistIE(WistiaBaseIE):
    _module = 'yt_dlp.extractor.wistia'
    IE_NAME = 'WistiaPlaylist'
    _VALID_URL = 'https?://(?:\\w+\\.)?wistia\\.(?:net|com)/(?:embed/)?playlists/(?P<id>[a-z0-9]{10})'
    _RETURN_TYPE = 'playlist'


class WistiaChannelIE(WistiaBaseIE):
    _module = 'yt_dlp.extractor.wistia'
    IE_NAME = 'WistiaChannel'
    _VALID_URL = '(?:wistiachannel:|https?://(?:\\w+\\.)?wistia\\.(?:net|com)/(?:embed/)?channel/)(?P<id>[a-z0-9]{10})'
    _RETURN_TYPE = 'any'


class WordpressPlaylistEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wordpress'
    IE_NAME = 'wordpress:playlist'
    _VALID_URL = False


class WordpressMiniAudioPlayerEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wordpress'
    IE_NAME = 'wordpress:mb.miniAudioPlayer'
    _VALID_URL = False


class WorldStarHipHopIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.worldstarhiphop'
    IE_NAME = 'WorldStarHipHop'
    _VALID_URL = 'https?://(?:www|m)\\.worldstar(?:candy|hiphop)\\.com/(?:videos|android)/video\\.php\\?.*?\\bv=(?P<id>[^&]+)'
    _RETURN_TYPE = 'video'


class WPPilotBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wppilot'
    IE_NAME = 'WPPilotBase'


class WPPilotIE(WPPilotBaseIE):
    _module = 'yt_dlp.extractor.wppilot'
    IE_NAME = 'wppilot'
    _VALID_URL = '(?:https?://pilot\\.wp\\.pl/tv/?#|wppilot:)(?P<id>[a-z\\d-]+)'
    _RETURN_TYPE = 'video'


class WPPilotChannelsIE(WPPilotBaseIE):
    _module = 'yt_dlp.extractor.wppilot'
    IE_NAME = 'wppilot:channels'
    _VALID_URL = '(?:https?://pilot\\.wp\\.pl/(?:tv/?)?(?:\\?[^#]*)?#?|wppilot:)$'
    _RETURN_TYPE = 'playlist'


class WrestleUniverseVODIE(WrestleUniverseBaseIE):
    _module = 'yt_dlp.extractor.wrestleuniverse'
    IE_NAME = 'WrestleUniverseVOD'
    _VALID_URL = 'https?://(?:www\\.)?wrestle-universe\\.com/(?:(?P<lang>\\w{2})/)?videos/(?P<id>\\w+)'
    _NETRC_MACHINE = 'wrestleuniverse'
    _RETURN_TYPE = 'video'


class WrestleUniversePPVIE(WrestleUniverseBaseIE):
    _module = 'yt_dlp.extractor.wrestleuniverse'
    IE_NAME = 'WrestleUniversePPV'
    _VALID_URL = 'https?://(?:www\\.)?wrestle-universe\\.com/(?:(?P<lang>\\w{2})/)?lives/(?P<id>\\w+)'
    _NETRC_MACHINE = 'wrestleuniverse'
    _RETURN_TYPE = 'video'


class WSJIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wsj'
    IE_NAME = 'WSJ'
    _VALID_URL = '(?x)\n                        (?:\n                            https?://video-api\\.wsj\\.com/api-video/player/iframe\\.html\\?.*?\\bguid=|\n                            https?://(?:www\\.)?(?:wsj|barrons)\\.com/video/(?:[^/]+/)+|\n                            wsj:\n                        )\n                        (?P<id>[a-fA-F0-9-]{36})\n                    '
    IE_DESC = 'Wall Street Journal'
    _RETURN_TYPE = 'video'


class WSJArticleIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wsj'
    IE_NAME = 'WSJArticle'
    _VALID_URL = '(?i)https?://(?:www\\.)?wsj\\.com/articles/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class WWEBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wwe'
    IE_NAME = 'WWEBase'


class WWEIE(WWEBaseIE):
    _module = 'yt_dlp.extractor.wwe'
    IE_NAME = 'WWE'
    _VALID_URL = 'https?://(?:[^/]+\\.)?wwe\\.com/(?:[^/]+/)*videos/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class WykopBaseExtractor(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.wykop'
    IE_NAME = 'WykopBaseExtract'


class WykopDigIE(WykopBaseExtractor):
    _module = 'yt_dlp.extractor.wykop'
    IE_NAME = 'wykop:dig'
    _VALID_URL = 'https?://(?:www\\.)?wykop\\.pl/link/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return cls._match_valid_url(url) and not WykopDigCommentIE.suitable(url)


class WykopDigCommentIE(WykopBaseExtractor):
    _module = 'yt_dlp.extractor.wykop'
    IE_NAME = 'wykop:dig:comment'
    _VALID_URL = 'https?://(?:www\\.)?wykop\\.pl/link/(?P<dig_id>\\d+)/[^/]+/komentarz/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class WykopPostIE(WykopBaseExtractor):
    _module = 'yt_dlp.extractor.wykop'
    IE_NAME = 'wykop:post'
    _VALID_URL = 'https?://(?:www\\.)?wykop\\.pl/wpis/(?P<id>\\d+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return cls._match_valid_url(url) and not WykopPostCommentIE.suitable(url)


class WykopPostCommentIE(WykopBaseExtractor):
    _module = 'yt_dlp.extractor.wykop'
    IE_NAME = 'wykop:post:comment'
    _VALID_URL = 'https?://(?:www\\.)?wykop\\.pl/wpis/(?P<post_id>\\d+)/[^/#]+#(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class XanimuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xanimu'
    IE_NAME = 'Xanimu'
    _VALID_URL = 'https?://(?:www\\.)?xanimu\\.com/(?P<id>[^/]+)/?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class XBefIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xbef'
    IE_NAME = 'XBef'
    _VALID_URL = 'https?://(?:www\\.)?xbef\\.com/video/(?P<id>[0-9]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class XboxClipsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xboxclips'
    IE_NAME = 'XboxClips'
    _VALID_URL = 'https?://(?:www\\.)?(?:xboxclips\\.com|gameclips\\.io)/(?:video\\.php\\?.*vid=|[^/]+/)(?P<id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})'
    _RETURN_TYPE = 'video'


class XFileShareIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xfileshare'
    IE_NAME = 'XFileShare'
    _VALID_URL = 'https?://(?:www\\.)?(?P<host>aparat\\.cam|clipwatching\\.com|gounlimited\\.to|govid\\.me|holavid\\.com|streamty\\.com|thevideobee\\.to|uqload\\.com|vidbom\\.com|vidlo\\.us|vidlocker\\.xyz|vidshare\\.tv|vup\\.to|wolfstream\\.tv|xvideosharing\\.com)/(?:embed-)?(?P<id>[0-9a-zA-Z]+)'
    IE_DESC = 'XFileShare based sites: Aparat, ClipWatching, GoUnlimited, GoVid, HolaVid, Streamty, TheVideoBee, Uqload, VidBom, vidlo, VidLocker, VidShare, VUp, WolfStream, XVideoSharing'
    _RETURN_TYPE = 'video'


class XHamsterIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xhamster'
    IE_NAME = 'XHamster'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:.+?\\.)?(?:xhamster\\.(?:com|one|desi)|xhms\\.pro|xhamster\\d+\\.com|xhday\\.com|xhvid\\.com)/\n                        (?:\n                            movies/(?P<id>[\\dA-Za-z]+)/(?P<display_id>[^/]*)\\.html|\n                            videos/(?P<display_id_2>[^/]*)-(?P<id_2>[\\dA-Za-z]+)\n                        )\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class XHamsterEmbedIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xhamster'
    IE_NAME = 'XHamsterEmbed'
    _VALID_URL = 'https?://(?:.+?\\.)?(?:xhamster\\.(?:com|one|desi)|xhms\\.pro|xhamster\\d+\\.com|xhday\\.com|xhvid\\.com)/xembed\\.php\\?video=(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class XHamsterUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xhamster'
    IE_NAME = 'XHamsterUser'
    _VALID_URL = 'https?://(?:.+?\\.)?(?:xhamster\\.(?:com|one|desi)|xhms\\.pro|xhamster\\d+\\.com|xhday\\.com|xhvid\\.com)/users/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'


class XimalayaBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ximalaya'
    IE_NAME = 'XimalayaBase'


class XimalayaIE(XimalayaBaseIE):
    _module = 'yt_dlp.extractor.ximalaya'
    IE_NAME = 'ximalaya'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?ximalaya\\.com/(:?(?P<uid>\\d+)/)?sound/(?P<id>[0-9]+)'
    IE_DESC = '喜马拉雅FM'
    _RETURN_TYPE = 'video'


class XimalayaAlbumIE(XimalayaBaseIE):
    _module = 'yt_dlp.extractor.ximalaya'
    IE_NAME = 'ximalaya:album'
    _VALID_URL = 'https?://(?:www\\.|m\\.)?ximalaya\\.com/(?:\\d+/)?album/(?P<id>[0-9]+)'
    IE_DESC = '喜马拉雅FM 专辑'
    _RETURN_TYPE = 'playlist'


class XinpianchangIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xinpianchang'
    IE_NAME = 'xinpianchang'
    _VALID_URL = 'https?://www\\.xinpianchang\\.com/(?P<id>[^/]+?)(?:\\D|$)'
    IE_DESC = 'xinpianchang.com'
    _RETURN_TYPE = 'video'


class XMinusIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xminus'
    IE_NAME = 'XMinus'
    _VALID_URL = 'https?://(?:www\\.)?x-minus\\.org/track/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class XNXXIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xnxx'
    IE_NAME = 'XNXX'
    _VALID_URL = 'https?://(?:video|www)\\.xnxx3?\\.com/video-?(?P<id>[0-9a-z]+)/'
    age_limit = 18
    _RETURN_TYPE = 'video'


class XstreamIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xstream'
    IE_NAME = 'Xstream'
    _VALID_URL = '(?x)\n                    (?:\n                        xstream:|\n                        https?://frontend\\.xstream\\.(?:dk|net)/\n                    )\n                    (?P<partner_id>[^/]+)\n                    (?:\n                        :|\n                        /feed/video/\\?.*?\\bid=\n                    )\n                    (?P<id>\\d+)\n                    '
    _RETURN_TYPE = 'video'


class VGTVIE(XstreamIE):
    _module = 'yt_dlp.extractor.vgtv'
    IE_NAME = 'VGTV'
    _VALID_URL = '(?x)\n                    (?:https?://(?:www\\.)?\n                    (?P<host>\n                        tv.vg.no|vgtv.no|bt.no/tv|aftenbladet.no/tv|fvn.no/fvntv|aftenposten.no/webtv|ap.vgtv.no/webtv|tv.aftonbladet.se|tv.aftonbladet.se/abtv|www.aftonbladet.se/tv\n                    )\n                    /?\n                    (?:\n                        (?:\\#!/)?(?:video|live)/|\n                        embed?.*id=|\n                        a(?:rticles)?/\n                    )|\n                    (?P<appname>\n                        vgtv|bttv|satv|fvntv|aptv|abtv\n                    ):)\n                    (?P<id>\\d+)\n                    '
    IE_DESC = 'VGTV, BTTV, FTV, Aftenposten and Aftonbladet'
    _RETURN_TYPE = 'video'


class XTubeUserIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xtube'
    IE_NAME = 'XTubeUser'
    _VALID_URL = 'https?://(?:www\\.)?xtube\\.com/profile/(?P<id>[^/]+-\\d+)'
    IE_DESC = 'XTube user profile'
    age_limit = 18
    _RETURN_TYPE = 'playlist'


class XTubeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xtube'
    IE_NAME = 'XTube'
    _VALID_URL = '(?x)\n                        (?:\n                            xtube:|\n                            https?://(?:www\\.)?xtube\\.com/(?:watch\\.php\\?.*\\bv=|video-watch/(?:embedded/)?(?P<display_id>[^/]+)-)\n                        )\n                        (?P<id>[^/?&#]+)\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class XuiteIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xuite'
    IE_NAME = 'Xuite'
    _VALID_URL = 'https?://vlog\\.xuite\\.net/(?:play|embed)/(?P<id>(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?)'
    IE_DESC = '隨意窩Xuite影音'
    _RETURN_TYPE = 'video'


class XVideosIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xvideos'
    IE_NAME = 'XVideos'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            (?:[^/]+\\.)?xvideos2?\\.com/video|\n                            (?:www\\.)?xvideos\\.es/video|\n                            (?:www|flashservice)\\.xvideos\\.com/embedframe/|\n                            static-hw\\.xvideos\\.com/swf/xv-player\\.swf\\?.*?\\bid_video=\n                        )\n                        (?P<id>[0-9]+)\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class XVideosQuickiesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xvideos'
    IE_NAME = 'xvideos:quickies'
    _VALID_URL = 'https?://(?P<domain>(?:[^/]+\\.)?xvideos2?\\.com)/amateur-channels/[^#]+#quickies/a/(?P<id>\\d+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class XXXYMoviesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.xxxymovies'
    IE_NAME = 'XXXYMovies'
    _VALID_URL = 'https?://(?:www\\.)?xxxymovies\\.com/videos/(?P<id>\\d+)/(?P<display_id>[^/]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class YahooIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yahoo'
    IE_NAME = 'Yahoo'
    _VALID_URL = '(?P<url>https?://(?:(?P<country>[a-zA-Z]{2}(?:-[a-zA-Z]{2})?|malaysia)\\.)?(?:[\\da-zA-Z_-]+\\.)?yahoo\\.com/(?:[^/]+/)*(?P<id>[^?&#]*-[0-9]+(?:-[a-z]+)?)\\.html)'
    IE_DESC = 'Yahoo screen and movies'
    _RETURN_TYPE = 'any'


class AolIE(YahooIE):
    _module = 'yt_dlp.extractor.aol'
    IE_NAME = 'aol.com'
    _VALID_URL = '(?:aol-video:|https?://(?:www\\.)?aol\\.(?:com|ca|co\\.uk|de|jp)/video/(?:[^/]+/)*)(?P<id>\\d{9}|[0-9a-f]{24}|[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})'
    IE_DESC = 'Yahoo screen and movies'
    _RETURN_TYPE = 'video'


class YahooSearchIE(LazyLoadSearchExtractor):
    _module = 'yt_dlp.extractor.yahoo'
    IE_NAME = 'screen.yahoo:search'
    _VALID_URL = 'yvsearch(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\\s\\S]+)'
    IE_DESC = 'Yahoo screen search'
    SEARCH_KEY = 'yvsearch'
    _RETURN_TYPE = 'playlist'


class YahooJapanNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yahoo'
    IE_NAME = 'yahoo:japannews'
    _VALID_URL = 'https?://news\\.yahoo\\.co\\.jp/(?:articles|feature)/(?P<id>[a-zA-Z0-9]+)'
    IE_DESC = 'Yahoo! Japan News'
    _RETURN_TYPE = 'video'


class YandexDiskIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yandexdisk'
    IE_NAME = 'YandexDisk'
    _VALID_URL = '(?x)https?://\n        (?P<domain>\n            yadi\\.sk|\n            disk\\.yandex\\.\n                (?:\n                    az|\n                    by|\n                    co(?:m(?:\\.(?:am|ge|tr))?|\\.il)|\n                    ee|\n                    fr|\n                    k[gz]|\n                    l[tv]|\n                    md|\n                    t[jm]|\n                    u[az]|\n                    ru\n                )\n        )/(?:[di]/|public.*?\\bhash=)(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'


class YandexMusicBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'YandexMusicBase'


class YandexMusicTrackIE(YandexMusicBaseIE):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'yandexmusic:track'
    _VALID_URL = 'https?://music\\.yandex\\.(?P<tld>ru|kz|ua|by|com)/album/(?P<album_id>\\d+)/track/(?P<id>\\d+)'
    IE_DESC = 'Яндекс.Музыка - Трек'
    _RETURN_TYPE = 'video'


class YandexMusicPlaylistBaseIE(YandexMusicBaseIE):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'YandexMusicPlaylistBase'


class YandexMusicAlbumIE(YandexMusicPlaylistBaseIE):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'yandexmusic:album'
    _VALID_URL = 'https?://music\\.yandex\\.(?P<tld>ru|kz|ua|by|com)/album/(?P<id>\\d+)'
    IE_DESC = 'Яндекс.Музыка - Альбом'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if YandexMusicTrackIE.suitable(url) else super(YandexMusicAlbumIE, cls).suitable(url)


class YandexMusicPlaylistIE(YandexMusicPlaylistBaseIE):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'yandexmusic:playlist'
    _VALID_URL = 'https?://music\\.yandex\\.(?P<tld>ru|kz|ua|by|com)/users/(?P<user>[^/]+)/playlists/(?P<id>\\d+)'
    IE_DESC = 'Яндекс.Музыка - Плейлист'
    _RETURN_TYPE = 'playlist'


class YandexMusicArtistBaseIE(YandexMusicPlaylistBaseIE):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'YandexMusicArtistBase'


class YandexMusicArtistTracksIE(YandexMusicArtistBaseIE):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'yandexmusic:artist:tracks'
    _VALID_URL = 'https?://music\\.yandex\\.(?P<tld>ru|kz|ua|by|com)/artist/(?P<id>\\d+)/tracks'
    IE_DESC = 'Яндекс.Музыка - Артист - Треки'
    _RETURN_TYPE = 'playlist'


class YandexMusicArtistAlbumsIE(YandexMusicArtistBaseIE):
    _module = 'yt_dlp.extractor.yandexmusic'
    IE_NAME = 'yandexmusic:artist:albums'
    _VALID_URL = 'https?://music\\.yandex\\.(?P<tld>ru|kz|ua|by|com)/artist/(?P<id>\\d+)/albums'
    IE_DESC = 'Яндекс.Музыка - Артист - Альбомы'
    _RETURN_TYPE = 'playlist'


class YandexVideoIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yandexvideo'
    IE_NAME = 'YandexVideo'
    _VALID_URL = '(?x)\n                    https?://\n                        (?:\n                            yandex\\.ru(?:/(?:portal/(?:video|efir)|efir))?/?\\?.*?stream_id=|\n                            frontend\\.vh\\.yandex\\.ru/player/\n                        )\n                        (?P<id>(?:[\\da-f]{32}|[\\w-]{12}))\n                    '
    age_limit = 18
    _RETURN_TYPE = 'video'


class YandexVideoPreviewIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yandexvideo'
    IE_NAME = 'YandexVideoPreview'
    _VALID_URL = 'https?://(?:www\\.)?yandex\\.\\w{2,3}(?:\\.(?:am|ge|il|tr))?/video/preview(?:/?\\?.*?filmId=|/)(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ZenYandexIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yandexvideo'
    IE_NAME = 'ZenYandex'
    _VALID_URL = 'https?://(zen\\.yandex|dzen)\\.ru(?:/video)?/(media|watch)/(?:(?:id/[^/]+/|[^/]+/)(?:[a-z0-9-]+)-)?(?P<id>[a-z0-9-]+)'
    _RETURN_TYPE = 'video'


class ZenYandexChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yandexvideo'
    IE_NAME = 'ZenYandexChannel'
    _VALID_URL = 'https?://(zen\\.yandex|dzen)\\.ru/(?!media|video)(?:id/)?(?P<id>[a-z0-9-_]+)'
    _RETURN_TYPE = 'playlist'


class YapFilesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yapfiles'
    IE_NAME = 'YapFiles'
    _VALID_URL = 'https?://(?:(?:www|api)\\.)?yapfiles\\.ru/get_player/*\\?.*?\\bv=(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class YappyIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yappy'
    IE_NAME = 'Yappy'
    _VALID_URL = 'https?://yappy\\.media/video/(?P<id>\\w+)'
    _RETURN_TYPE = 'video'


class YappyProfileIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yappy'
    IE_NAME = 'YappyProfile'
    _VALID_URL = 'https?://yappy\\.media/profile/(?P<id>\\w+)'
    _RETURN_TYPE = 'playlist'


class YesJapanIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yesjapan'
    IE_NAME = 'YesJapan'
    _VALID_URL = 'https?://(?:www\\.)?yesjapan\\.com/video/(?P<slug>[A-Za-z0-9\\-]*)_(?P<id>[A-Za-z0-9]+)\\.html'
    _RETURN_TYPE = 'video'


class YinYueTaiIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yinyuetai'
    IE_NAME = 'yinyuetai:video'
    _VALID_URL = 'https?://v\\.yinyuetai\\.com/video(?:/h5)?/(?P<id>[0-9]+)'
    IE_DESC = '音悦Tai'
    _RETURN_TYPE = 'video'


class YleAreenaIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yle_areena'
    IE_NAME = 'YleAreena'
    _VALID_URL = 'https?://areena\\.yle\\.fi/(?P<id>[\\d-]+)'
    age_limit = 7
    _RETURN_TYPE = 'video'


class YnetIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.ynet'
    IE_NAME = 'Ynet'
    _VALID_URL = 'https?://(?:.+?\\.)?ynet\\.co\\.il/(?:.+?/)?0,7340,(?P<id>L(?:-[0-9]+)+),00\\.html'
    _RETURN_TYPE = 'video'


class YouJizzIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youjizz'
    IE_NAME = 'YouJizz'
    _VALID_URL = 'https?://(?:\\w+\\.)?youjizz\\.com/videos/(?:[^/#?]*-(?P<id>\\d+)\\.html|embed/(?P<embed_id>\\d+))'
    age_limit = 18
    _RETURN_TYPE = 'video'


class YoukuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youku'
    IE_NAME = 'youku'
    _VALID_URL = '(?x)\n        (?:\n            https?://(\n                (?:v|player)\\.youku\\.com/(?:v_show/id_|player\\.php/sid/)|\n                video\\.tudou\\.com/v/)|\n            youku:)\n        (?P<id>[A-Za-z0-9]+)(?:\\.html|/v\\.swf|)\n    '
    IE_DESC = '优酷'
    _RETURN_TYPE = 'video'


class YoukuShowIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youku'
    IE_NAME = 'youku:show'
    _VALID_URL = 'https?://list\\.youku\\.com/show/id_(?P<id>[0-9a-z]+)\\.html'
    _RETURN_TYPE = 'playlist'


class YouNowLiveIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.younow'
    IE_NAME = 'YouNowLive'
    _VALID_URL = 'https?://(?:www\\.)?younow\\.com/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return (False
                if YouNowChannelIE.suitable(url) or YouNowMomentIE.suitable(url)
                else super(YouNowLiveIE, cls).suitable(url))


class YouNowChannelIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.younow'
    IE_NAME = 'YouNowChannel'
    _VALID_URL = 'https?://(?:www\\.)?younow\\.com/(?P<id>[^/]+)/channel'
    _RETURN_TYPE = 'playlist'


class YouNowMomentIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.younow'
    IE_NAME = 'YouNowMoment'
    _VALID_URL = 'https?://(?:www\\.)?younow\\.com/[^/]+/(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'video'

    @classmethod
    def suitable(cls, url):
        return (False
                if YouNowChannelIE.suitable(url)
                else super(YouNowMomentIE, cls).suitable(url))


class YouPornIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.youporn'
    IE_NAME = 'YouPorn'
    _VALID_URL = 'https?://(?:www\\.)?youporn\\.com/(?:watch|embed)/(?P<id>\\d+)(?:/(?P<display_id>[^/?#&]+))?'
    age_limit = 18
    _RETURN_TYPE = 'video'


class YourPornIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yourporn'
    IE_NAME = 'YourPorn'
    _VALID_URL = 'https?://(?:www\\.)?sxyprn\\.com/post/(?P<id>[^/?#&.]+)'
    age_limit = 18
    _RETURN_TYPE = 'video'


class YourUploadIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.yourupload'
    IE_NAME = 'YourUpload'
    _VALID_URL = 'https?://(?:www\\.)?(?:yourupload\\.com/(?:watch|embed)|embed\\.yourupload\\.com)/(?P<id>[A-Za-z0-9]+)'
    _RETURN_TYPE = 'video'


class ZaikoBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zaiko'
    IE_NAME = 'ZaikoBase'


class ZaikoIE(ZaikoBaseIE):
    _module = 'yt_dlp.extractor.zaiko'
    IE_NAME = 'Zaiko'
    _VALID_URL = 'https?://(?:[\\w-]+\\.)?zaiko\\.io/event/(?P<id>\\d+)/stream(?:/\\d+)+'
    _RETURN_TYPE = 'video'


class ZaikoETicketIE(ZaikoBaseIE):
    _module = 'yt_dlp.extractor.zaiko'
    IE_NAME = 'ZaikoETicket'
    _VALID_URL = 'https?://(?:www.)?zaiko\\.io/account/eticket/(?P<id>[\\w=-]{49})'
    _RETURN_TYPE = 'playlist'


class ZapiksIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zapiks'
    IE_NAME = 'Zapiks'
    _VALID_URL = 'https?://(?:www\\.)?zapiks\\.(?:fr|com)/(?:(?:[a-z]{2}/)?(?P<display_id>.+?)\\.html|index\\.php\\?.*\\bmedia_id=(?P<id>\\d+))'
    _RETURN_TYPE = 'video'


class ZattooPlatformBaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'ZattooPlatformBase'


class BBVTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'BBVTVBase'
    _NETRC_MACHINE = 'bbvtv'


class BBVTVIE(BBVTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'BBVTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?bbv\\-tv\\.net/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'bbvtv'


class BBVTVLiveIE(BBVTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'BBVTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?bbv\\-tv\\.net/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'bbvtv'

    @classmethod
    def suitable(cls, url):
        return False if BBVTVIE.suitable(url) else super().suitable(url)


class BBVTVRecordingsIE(BBVTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'BBVTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?bbv\\-tv\\.net/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'bbvtv'


class EinsUndEinsTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EinsUndEinsTVBase'
    _NETRC_MACHINE = '1und1tv'


class EinsUndEinsTVIE(EinsUndEinsTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EinsUndEinsTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?1und1\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = '1und1tv'


class EinsUndEinsTVLiveIE(EinsUndEinsTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EinsUndEinsTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?1und1\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = '1und1tv'

    @classmethod
    def suitable(cls, url):
        return False if EinsUndEinsTVIE.suitable(url) else super().suitable(url)


class EinsUndEinsTVRecordingsIE(EinsUndEinsTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EinsUndEinsTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?1und1\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = '1und1tv'


class EWETVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EWETVBase'
    _NETRC_MACHINE = 'ewetv'


class EWETVIE(EWETVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EWETV'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvonline\\.ewe\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'ewetv'


class EWETVLiveIE(EWETVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EWETVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvonline\\.ewe\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'ewetv'

    @classmethod
    def suitable(cls, url):
        return False if EWETVIE.suitable(url) else super().suitable(url)


class EWETVRecordingsIE(EWETVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'EWETVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvonline\\.ewe\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'ewetv'


class GlattvisionTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'GlattvisionTVBase'
    _NETRC_MACHINE = 'glattvisiontv'


class GlattvisionTVIE(GlattvisionTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'GlattvisionTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?iptv\\.glattvision\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'glattvisiontv'


class GlattvisionTVLiveIE(GlattvisionTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'GlattvisionTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?iptv\\.glattvision\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'glattvisiontv'

    @classmethod
    def suitable(cls, url):
        return False if GlattvisionTVIE.suitable(url) else super().suitable(url)


class GlattvisionTVRecordingsIE(GlattvisionTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'GlattvisionTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?iptv\\.glattvision\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'glattvisiontv'


class MNetTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'MNetTVBase'
    _NETRC_MACHINE = 'mnettv'


class MNetTVIE(MNetTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'MNetTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvplus\\.m\\-net\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'mnettv'


class MNetTVLiveIE(MNetTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'MNetTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvplus\\.m\\-net\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'mnettv'

    @classmethod
    def suitable(cls, url):
        return False if MNetTVIE.suitable(url) else super().suitable(url)


class MNetTVRecordingsIE(MNetTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'MNetTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvplus\\.m\\-net\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'mnettv'


class NetPlusTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'NetPlusTVBase'
    _NETRC_MACHINE = 'netplus'


class NetPlusTVIE(NetPlusTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'NetPlusTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?netplus\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'netplus'


class NetPlusTVLiveIE(NetPlusTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'NetPlusTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?netplus\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'netplus'

    @classmethod
    def suitable(cls, url):
        return False if NetPlusTVIE.suitable(url) else super().suitable(url)


class NetPlusTVRecordingsIE(NetPlusTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'NetPlusTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?netplus\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'netplus'


class OsnatelTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'OsnatelTVBase'
    _NETRC_MACHINE = 'osnateltv'


class OsnatelTVIE(OsnatelTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'OsnatelTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvonline\\.osnatel\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'osnateltv'


class OsnatelTVLiveIE(OsnatelTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'OsnatelTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvonline\\.osnatel\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'osnateltv'

    @classmethod
    def suitable(cls, url):
        return False if OsnatelTVIE.suitable(url) else super().suitable(url)


class OsnatelTVRecordingsIE(OsnatelTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'OsnatelTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?tvonline\\.osnatel\\.de/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'osnateltv'


class QuantumTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'QuantumTVBase'
    _NETRC_MACHINE = 'quantumtv'


class QuantumTVIE(QuantumTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'QuantumTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?quantum\\-tv\\.com/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'quantumtv'


class QuantumTVLiveIE(QuantumTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'QuantumTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?quantum\\-tv\\.com/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'quantumtv'

    @classmethod
    def suitable(cls, url):
        return False if QuantumTVIE.suitable(url) else super().suitable(url)


class QuantumTVRecordingsIE(QuantumTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'QuantumTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?quantum\\-tv\\.com/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'quantumtv'


class SaltTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SaltTVBase'
    _NETRC_MACHINE = 'salttv'


class SaltTVIE(SaltTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SaltTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?tv\\.salt\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'salttv'


class SaltTVLiveIE(SaltTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SaltTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?tv\\.salt\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'salttv'

    @classmethod
    def suitable(cls, url):
        return False if SaltTVIE.suitable(url) else super().suitable(url)


class SaltTVRecordingsIE(SaltTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SaltTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?tv\\.salt\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'salttv'


class SAKTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SAKTVBase'
    _NETRC_MACHINE = 'saktv'


class SAKTVIE(SAKTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SAKTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?saktv\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'saktv'


class SAKTVLiveIE(SAKTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SAKTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?saktv\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'saktv'

    @classmethod
    def suitable(cls, url):
        return False if SAKTVIE.suitable(url) else super().suitable(url)


class SAKTVRecordingsIE(SAKTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'SAKTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?saktv\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'saktv'


class VTXTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'VTXTVBase'
    _NETRC_MACHINE = 'vtxtv'


class VTXTVIE(VTXTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'VTXTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?vtxtv\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'vtxtv'


class VTXTVLiveIE(VTXTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'VTXTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?vtxtv\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'vtxtv'

    @classmethod
    def suitable(cls, url):
        return False if VTXTVIE.suitable(url) else super().suitable(url)


class VTXTVRecordingsIE(VTXTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'VTXTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?vtxtv\\.ch/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'vtxtv'


class WalyTVBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'WalyTVBase'
    _NETRC_MACHINE = 'walytv'


class WalyTVIE(WalyTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'WalyTV'
    _VALID_URL = '(?x)https?://(?:www\\.)?player\\.waly\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'walytv'


class WalyTVLiveIE(WalyTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'WalyTVLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?player\\.waly\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'walytv'

    @classmethod
    def suitable(cls, url):
        return False if WalyTVIE.suitable(url) else super().suitable(url)


class WalyTVRecordingsIE(WalyTVBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'WalyTVRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?player\\.waly\\.tv/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'walytv'


class ZattooBaseIE(ZattooPlatformBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'ZattooBase'
    _NETRC_MACHINE = 'zattoo'


class ZattooIE(ZattooBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'Zattoo'
    _VALID_URL = '(?x)https?://(?:www\\.)?zattoo\\.com/(?:\n        [^?#]+\\?(?:[^#]+&)?program=(?P<vid2>\\d+)\n        |(?:program|watch)/[^/]+/(?P<vid1>\\d+)\n    )'
    _NETRC_MACHINE = 'zattoo'
    _RETURN_TYPE = 'video'


class ZattooLiveIE(ZattooBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'ZattooLive'
    _VALID_URL = '(?x)https?://(?:www\\.)?zattoo\\.com/(?:\n        [^?#]+\\?(?:[^#]+&)?channel=(?P<vid2>[^/?&#]+)\n        |live/(?P<vid1>[^/?&#]+)\n    )'
    _NETRC_MACHINE = 'zattoo'

    @classmethod
    def suitable(cls, url):
        return False if ZattooIE.suitable(url) else super().suitable(url)


class ZattooMoviesIE(ZattooBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'ZattooMovies'
    _VALID_URL = '(?x)https?://(?:www\\.)?zattoo\\.com/(?:\n        [^?#]+\\?(?:[^#]+&)?movie_id=(?P<vid2>\\w+)\n        |vod/movies/(?P<vid1>\\w+)\n    )'
    _NETRC_MACHINE = 'zattoo'


class ZattooRecordingsIE(ZattooBaseIE):
    _module = 'yt_dlp.extractor.zattoo'
    IE_NAME = 'ZattooRecordings'
    _VALID_URL = '(?x)https?://(?:www\\.)?zattoo\\.com/(?:\n        [^?#]+\\?(?:[^#]+&)?recording=(?P<vid2>\\d+)\n        (?P<vid1>)\n    )'
    _NETRC_MACHINE = 'zattoo'


class ZDFIE(ZDFBaseIE):
    _module = 'yt_dlp.extractor.zdf'
    IE_NAME = 'ZDF'
    _VALID_URL = 'https?://www\\.zdf\\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)\\.html'
    _RETURN_TYPE = 'video'


class DreiSatIE(ZDFIE):
    _module = 'yt_dlp.extractor.dreisat'
    IE_NAME = '3sat'
    _VALID_URL = 'https?://(?:www\\.)?3sat\\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)\\.html'
    _RETURN_TYPE = 'video'


class ZDFChannelIE(ZDFBaseIE):
    _module = 'yt_dlp.extractor.zdf'
    IE_NAME = 'ZDFChannel'
    _VALID_URL = 'https?://www\\.zdf\\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _RETURN_TYPE = 'playlist'

    @classmethod
    def suitable(cls, url):
        return False if ZDFIE.suitable(url) else super(ZDFChannelIE, cls).suitable(url)


class Zee5IE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zee5'
    IE_NAME = 'Zee5'
    _VALID_URL = '(?x)\n                     (?:\n                        zee5:|\n                        https?://(?:www\\.)?zee5\\.com/(?:[^#?]+/)?\n                        (?:\n                            (?:tv-shows|kids|web-series|zee5originals)(?:/[^#/?]+){3}\n                            |(?:movies|kids|videos|news|music-videos)/(?!kids-shows)[^#/?]+\n                        )/(?P<display_id>[^#/?]+)/\n                     )\n                     (?P<id>[^#/?]+)/?(?:$|[?#])\n                     '
    _NETRC_MACHINE = 'zee5'
    _RETURN_TYPE = 'video'


class Zee5SeriesIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zee5'
    IE_NAME = 'zee5:series'
    _VALID_URL = '(?x)\n                     (?:\n                        zee5:series:|\n                        https?://(?:www\\.)?zee5\\.com/(?:[^#?]+/)?\n                        (?:tv-shows|web-series|kids|zee5originals)/(?!kids-movies)(?:[^#/?]+/){2}\n                     )\n                     (?P<id>[^#/?]+)(?:/episodes)?/?(?:$|[?#])\n                     '
    _RETURN_TYPE = 'playlist'


class ZeeNewsIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zeenews'
    IE_NAME = 'ZeeNews'
    _VALID_URL = 'https?://zeenews\\.india\\.com/[^#?]+/video/(?P<display_id>[^#/?]+)/(?P<id>\\d+)'
    _RETURN_TYPE = 'video'


class ZhihuIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zhihu'
    IE_NAME = 'Zhihu'
    _VALID_URL = 'https?://(?:www\\.)?zhihu\\.com/zvideo/(?P<id>[0-9]+)'
    _RETURN_TYPE = 'video'


class ZingMp3BaseIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'ZingMp3Base'


class ZingMp3IE(ZingMp3BaseIE):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'zingmp3'
    _VALID_URL = 'https?://(?:mp3\\.zing|zingmp3)\\.vn/(?P<type>(?:bai-hat|video-clip|embed))/[^/?#]+/(?P<id>\\w+)(?:\\.html|\\?)'
    IE_DESC = 'zingmp3.vn'
    _RETURN_TYPE = 'video'


class ZingMp3AlbumIE(ZingMp3BaseIE):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'zingmp3:album'
    _VALID_URL = 'https?://(?:mp3\\.zing|zingmp3)\\.vn/(?P<type>(?:album|playlist))/[^/?#]+/(?P<id>\\w+)(?:\\.html|\\?)'
    _RETURN_TYPE = 'playlist'


class ZingMp3ChartHomeIE(ZingMp3BaseIE):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'zingmp3:chart-home'
    _VALID_URL = 'https?://(?:mp3\\.zing|zingmp3)\\.vn/(?P<id>(?:zing-chart|moi-phat-hanh))/?(?:[#?]|$)'
    _RETURN_TYPE = 'playlist'


class ZingMp3WeekChartIE(ZingMp3BaseIE):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'zingmp3:week-chart'
    _VALID_URL = 'https?://(?:mp3\\.zing|zingmp3)\\.vn/(?P<type>(?:zing-chart-tuan))/[^/?#]+/(?P<id>\\w+)(?:\\.html|\\?)'
    _RETURN_TYPE = 'playlist'


class ZingMp3ChartMusicVideoIE(ZingMp3BaseIE):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'zingmp3:chart-music-video'
    _VALID_URL = 'https?://(?:mp3\\.zing|zingmp3)\\.vn/(?P<type>the-loai-video)/(?P<regions>[^/]+)/(?P<id>[^\\.]+)'
    _RETURN_TYPE = 'playlist'


class ZingMp3UserIE(ZingMp3BaseIE):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'zingmp3:user'
    _VALID_URL = 'https?://(?:mp3\\.zing|zingmp3)\\.vn/(?P<user>[^/]+)/(?P<type>bai-hat|single|album|video)/?(?:[?#]|$)'
    _RETURN_TYPE = 'playlist'


class ZingMp3HubIE(ZingMp3BaseIE):
    _module = 'yt_dlp.extractor.zingmp3'
    IE_NAME = 'zingmp3:hub'
    _VALID_URL = 'https?://(?:mp3\\.zing|zingmp3)\\.vn/(?P<type>hub)/(?P<regions>[^/]+)/(?P<id>[^\\.]+)'
    _RETURN_TYPE = 'playlist'


class ZoomIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zoom'
    IE_NAME = 'zoom'
    _VALID_URL = '(?P<base_url>https?://(?:[^.]+\\.)?zoom.us/)rec(?:ording)?/(?P<type>play|share)/(?P<id>[A-Za-z0-9_.-]+)'
    _RETURN_TYPE = 'video'


class ZypeIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.zype'
    IE_NAME = 'Zype'
    _VALID_URL = 'https?://player\\.zype\\.com/embed/(?P<id>[\\da-fA-F]+)\\.(?:js|json|html)\\?.*?(?:access_token|(?:ap[ip]|player)_key)=[^&]+'
    _RETURN_TYPE = 'video'


class GenericIE(LazyLoadExtractor):
    _module = 'yt_dlp.extractor.generic'
    IE_NAME = 'generic'
    _VALID_URL = '.*'
    IE_DESC = 'Generic downloader that works on some sites'
    _NETRC_MACHINE = False
    age_limit = 18
    _RETURN_TYPE = 'any'


_ALL_CLASSES = [YoutubeIE, YoutubeClipIE, YoutubeFavouritesIE, YoutubeNotificationsIE, YoutubeHistoryIE, YoutubeTabIE, YoutubeLivestreamEmbedIE, YoutubePlaylistIE, YoutubeRecommendedIE, YoutubeSearchDateIE, YoutubeSearchIE, YoutubeSearchURLIE, YoutubeMusicSearchURLIE, YoutubeSubscriptionsIE, YoutubeTruncatedIDIE, YoutubeTruncatedURLIE, YoutubeYtBeIE, YoutubeYtUserIE, YoutubeWatchLaterIE, YoutubeShortsAudioPivotIE, YoutubeConsentRedirectIE, ABCIE, ABCIViewIE, ABCIViewShowSeriesIE, AbcNewsIE, AbcNewsVideoIE, ABCOTVSIE, ABCOTVSClipsIE, AbemaTVIE, AbemaTVTitleIE, AcademicEarthCourseIE, ACastIE, ACastChannelIE, AcFunVideoIE, AcFunBangumiIE, ADNIE, AdobeConnectIE, AdobeTVEmbedIE, AdobeTVIE, AdobeTVShowIE, AdobeTVChannelIE, AdobeTVVideoIE, AdultSwimIE, AeonCoIE, AfreecaTVIE, AfreecaTVLiveIE, AfreecaTVUserIE, TokFMAuditionIE, TokFMPodcastIE, WyborczaPodcastIE, WyborczaVideoIE, AirMozillaIE, AirTVIE, AitubeKZVideoIE, AlJazeeraIE, AlphaPornoIE, AmaraIE, AluraIE, AluraCourseIE, AmazonStoreIE, AmazonReviewsIE, AmazonMiniTVIE, AmazonMiniTVSeasonIE, AmazonMiniTVSeriesIE, AmericasTestKitchenIE, AmericasTestKitchenSeasonIE, AnchorFMEpisodeIE, AngelIE, AnvatoIE, AllocineIE, AliExpressLiveIE, Alsace20TVIE, Alsace20TVEmbedIE, APAIE, AparatIE, AppleConnectIE, AppleTrailersIE, AppleTrailersSectionIE, ApplePodcastsIE, ArchiveOrgIE, YoutubeWebArchiveIE, VLiveWebArchiveIE, ArcPublishingIE, ArkenaIE, ARDBetaMediathekIE, ARDIE, ARDMediathekIE, ArteTVIE, ArteTVEmbedIE, ArteTVPlaylistIE, ArteTVCategoryIE, ArnesIE, AsianCrushIE, AsianCrushPlaylistIE, AtresPlayerIE, AtScaleConfEventIE, ATTTechChannelIE, ATVAtIE, AudiMediaIE, AudioBoomIE, AudiodraftCustomIE, AudiodraftGenericIE, AudiomackIE, AudiomackAlbumIE, AudiusIE, AudiusTrackIE, AudiusPlaylistIE, AudiusProfileIE, AWAANIE, AWAANVideoIE, AWAANLiveIE, AWAANSeasonIE, AZMedienIE, BaiduVideoIE, BanByeIE, BanByeChannelIE, BandaiChannelIE, BandcampIE, BandcampAlbumIE, BandcampWeeklyIE, BandcampUserIE, BannedVideoIE, BBCCoUkIE, BBCCoUkArticleIE, BBCCoUkIPlayerEpisodesIE, BBCCoUkIPlayerGroupIE, BBCCoUkPlaylistIE, BBCIE, BeegIE, BehindKinkIE, BellMediaIE, BeatBumpVideoIE, BeatBumpPlaylistIE, BeatportIE, BerufeTVIE, BetIE, BFIPlayerIE, BFMTVIE, BFMTVLiveIE, BFMTVArticleIE, BibelTVLiveIE, BibelTVSeriesIE, BibelTVVideoIE, BigflixIE, BigoIE, BildIE, BiliBiliIE, BiliBiliBangumiIE, BiliBiliBangumiMediaIE, BiliBiliSearchIE, BilibiliCategoryIE, BilibiliAudioIE, BilibiliAudioAlbumIE, BiliBiliPlayerIE, BilibiliSpaceVideoIE, BilibiliSpaceAudioIE, BilibiliSpacePlaylistIE, BiliIntlIE, BiliIntlSeriesIE, BiliLiveIE, BioBioChileTVIE, BitChuteIE, BitChuteChannelIE, BitwaveReplayIE, BitwaveStreamIE, BIQLEIE, BlackboardCollaborateIE, BleacherReportIE, BleacherReportCMSIE, BlerpIE, BloggerIE, BloombergIE, BokeCCIE, BongaCamsIE, BostonGlobeIE, BoxIE, BoxCastVideoIE, BpbIE, BRIE, BRMediathekIE, BravoTVIE, BrainPOPIE, BrainPOPJrIE, BrainPOPELLIE, BrainPOPEspIE, BrainPOPFrIE, BrainPOPIlIE, BreakIE, BreitBartIE, BrightcoveLegacyIE, BrightcoveNewIE, BusinessInsiderIE, BundesligaIE, BuzzFeedIE, BYUtvIE, C56IE, CableAVIE, CallinIE, CaltransIE, CAM4IE, CamdemyIE, CamdemyFolderIE, CamFMEpisodeIE, CamFMShowIE, CamModelsIE, CamsodaIE, CamtasiaEmbedIE, CamWithHerIE, CanalAlphaIE, CanalplusIE, Canalc2IE, CarambaTVIE, CarambaTVPageIE, CartoonNetworkIE, CBCIE, CBCPlayerIE, CBCGemIE, CBCGemPlaylistIE, CBCGemLiveIE, ParamountPressExpressIE, CBSNewsEmbedIE, CBSNewsIE, CBSLocalIE, CBSLocalArticleIE, CBSLocalLiveIE, CBSNewsLiveIE, CBSNewsLiveVideoIE, CBSSportsEmbedIE, CBSSportsIE, TwentyFourSevenSportsIE, CCCIE, CCCPlaylistIE, CCMAIE, CCTVIE, CDAIE, CellebriteIE, CeskaTelevizeIE, CGTNIE, Channel9IE, CharlieRoseIE, ChaturbateIE, ChilloutzoneIE, ChingariIE, ChingariUserIE, ChirbitIE, ChirbitProfileIE, CinchcastIE, CinemaxIE, CinetecaMilanoIE, CiscoLiveSessionIE, CiscoLiveSearchIE, CiscoWebexIE, CJSWIE, ClipchampIE, CliphunterIE, ClippitIE, ClipRsIE, ClipsyndicateIE, CloserToTruthIE, CloudflareStreamIE, CloudyIE, ClubicIE, ClypIE, CNBCIE, CNBCVideoIE, CNNIE, CNNBlogsIE, CNNArticleIE, CNNIndonesiaIE, CoubIE, ComedyCentralIE, ComedyCentralTVIE, CommonMistakesIE, UnicodeBOMIE, MmsIE, RtmpIE, ViewSourceIE, CondeNastIE, CONtvIE, CPACIE, CPACPlaylistIE, CozyTVIE, CrackedIE, CrackleIE, CraftsyIE, CrooksAndLiarsIE, CrowdBunkerIE, CrowdBunkerChannelIE, CrtvgIE, CrunchyrollBetaIE, CrunchyrollBetaShowIE, CrunchyrollMusicIE, CrunchyrollArtistIE, CSpanIE, CSpanCongressIE, CtsNewsIE, CTVIE, CTVNewsIE, CultureUnpluggedIE, CuriosityStreamIE, CuriosityStreamCollectionsIE, CuriosityStreamSeriesIE, CWTVIE, CybraryIE, CybraryCourseIE, DacastVODIE, DacastPlaylistIE, DaftsexIE, DailyMailIE, DailymotionIE, DailymotionPlaylistIE, DailymotionUserIE, DailyWireIE, DailyWirePodcastIE, DamtomoRecordIE, DamtomoVideoIE, DaumIE, DaumClipIE, DaumPlaylistIE, DaumUserIE, DaystarClipIE, DBTVIE, DctpTvIE, DeezerPlaylistIE, DeezerAlbumIE, DemocracynowIE, DetikEmbedIE, DLFIE, DLFCorpusIE, DFBIE, DHMIE, DiggIE, DotsubIE, DouyuShowIE, DouyuTVIE, DPlayIE, DiscoveryPlusIE, HGTVDeIE, GoDiscoveryIE, TravelChannelIE, CookingChannelIE, HGTVUsaIE, FoodNetworkIE, InvestigationDiscoveryIE, DestinationAmericaIE, AmHistoryChannelIE, ScienceChannelIE, DIYNetworkIE, DiscoveryLifeIE, AnimalPlanetIE, TLCIE, MotorTrendIE, MotorTrendOnDemandIE, DiscoveryPlusIndiaIE, DiscoveryNetworksDeIE, DiscoveryPlusItalyIE, DiscoveryPlusItalyShowIE, DiscoveryPlusIndiaShowIE, GlobalCyclingNetworkPlusIE, DRBonanzaIE, DrTuberIE, DRTVIE, DRTVLiveIE, DRTVSeasonIE, DRTVSeriesIE, DTubeIE, DVTVIE, DubokuIE, DubokuPlaylistIE, DumpertIE, DefenseGouvFrIE, DeuxMIE, DeuxMNewsIE, DigitalConcertHallIE, DiscogsReleasePlaylistIE, DiscoveryIE, DisneyIE, DigitallySpeakingIE, DropboxIE, DropoutSeasonIE, DropoutIE, DWIE, DWArticleIE, EaglePlatformIE, ClipYouEmbedIE, EbaumsWorldIE, EbayIE, EchoMskIE, EggheadCourseIE, EggheadLessonIE, EHowIE, EightTracksIE, EinthusanIE, EitbIE, ElevenSportsIE, EllenTubeIE, EllenTubeVideoIE, EllenTubePlaylistIE, ElonetIE, ElPaisIE, EmbedlyIE, EngadgetIE, EpiconIE, EpiconSeriesIE, EpochIE, EpornerIE, EroProfileIE, EroProfileAlbumIE, ERTFlixCodenameIE, ERTFlixIE, ERTWebtvEmbedIE, EscapistIE, ESPNIE, WatchESPNIE, ESPNArticleIE, FiveThirtyEightIE, ESPNCricInfoIE, EsriVideoIE, EttuTvIE, EuropaIE, EuroParlWebstreamIE, EuropeanTourIE, EurosportIE, EUScreenIE, ExpoTVIE, ExpressenIE, EyedoTVIE, FacebookIE, FacebookPluginsVideoIE, FacebookRedirectURLIE, FacebookReelIE, FancodeVodIE, FancodeLiveIE, FazIE, FC2IE, FC2EmbedIE, FC2LiveIE, FczenitIE, FifaIE, FilmmoduIE, FilmOnIE, FilmOnChannelIE, FilmwebIE, FirstTVIE, FiveTVIE, FlickrIE, FolketingetIE, FootyRoomIE, Formula1IE, FourTubeIE, PornTubeIE, PornerBrosIE, FuxIE, FourZeroStudioArchiveIE, FourZeroStudioClipIE, FOXIE, FOX9IE, FOX9NewsIE, FoxgayIE, FoxNewsIE, FoxNewsArticleIE, FoxNewsVideoIE, FoxSportsIE, FptplayIE, FranceInterIE, FranceTVIE, FranceTVSiteIE, FranceTVInfoIE, FreesoundIE, FreespeechIE, FrontendMastersIE, FrontendMastersLessonIE, FrontendMastersCourseIE, FreeTvIE, FreeTvMoviesIE, FujiTVFODPlus7IE, FunimationIE, FunimationPageIE, FunimationShowIE, FunkIE, Funker530IE, FusionIE, FuyinTVIE, GabTVIE, GabIE, GaiaIE, GameInformerIE, GameJoltIE, GameJoltUserIE, GameJoltGameIE, GameJoltGameSoundtrackIE, GameJoltCommunityIE, GameJoltSearchIE, GameSpotIE, GameStarIE, GaskrankIE, GazetaIE, GDCVaultIE, GediDigitalIE, GeniusIE, GeniusLyricsIE, GettrIE, GettrStreamingIE, GfycatIE, GiantBombIE, GigaIE, GlideIE, GlobalPlayerLiveIE, GlobalPlayerLivePlaylistIE, GlobalPlayerAudioIE, GlobalPlayerAudioEpisodeIE, GlobalPlayerVideoIE, GloboIE, GloboArticleIE, GMANetworkVideoIE, GoIE, GodTubeIE, GofileIE, GolemIE, GoodGameIE, GoogleDriveIE, GoogleDriveFolderIE, GooglePodcastsIE, GooglePodcastsFeedIE, GoogleSearchIE, GoProIE, GoPlayIE, GoshgayIE, GoToStageIE, GPUTechConfIE, GronkhIE, GronkhFeedIE, GronkhVodsIE, GrouponIE, HarpodeonIE, HBOIE, HearThisAtIE, HeiseIE, HellPornoIE, HelsinkiIE, HGTVComShowIE, HKETVIE, HiDiveIE, HistoricFilmsIE, HitboxIE, HitboxLiveIE, HitRecordIE, HollywoodReporterIE, HollywoodReporterPlaylistIE, HolodexIE, HotNewHipHopIE, HotStarIE, HotStarPrefixIE, HotStarPlaylistIE, HotStarSeasonIE, HotStarSeriesIE, HowcastIE, HowStuffWorksIE, HrefLiRedirectIE, HRFernsehenIE, HRTiIE, HRTiPlaylistIE, HSEShowIE, HSEProductIE, HTML5MediaEmbedIE, QuotedHTMLIE, HuajiaoIE, HuyaLiveIE, HuffPostIE, HungamaIE, HungamaSongIE, HungamaAlbumPlaylistIE, HypemIE, MonsterSirenHypergryphMusicIE, HytaleIE, IcareusIE, IchinanaLiveIE, IchinanaLiveClipIE, IdolPlusIE, IGNIE, IGNVideoIE, IGNArticleIE, IHeartRadioIE, IHeartRadioPodcastIE, IltalehtiIE, ImdbIE, ImdbListIE, ImgurIE, ImgurGalleryIE, ImgurAlbumIE, InaIE, IncIE, IndavideoEmbedIE, InfoQIE, InstagramIE, InstagramIOSIE, InstagramUserIE, InstagramTagIE, InstagramStoryIE, InternazionaleIE, InternetVideoArchiveIE, IPrimaIE, IPrimaCNNIE, IqiyiIE, IqIE, IqAlbumIE, IslamChannelIE, IslamChannelSeriesIE, IsraelNationalNewsIE, ITProTVIE, ITProTVCourseIE, ITVIE, ITVBTCCIE, IviIE, IviCompilationIE, IvideonIE, IwaraIE, IwaraPlaylistIE, IwaraUserIE, IxiguaIE, IzleseneIE, JableIE, JablePlaylistIE, JamendoIE, JamendoAlbumIE, ShugiinItvLiveIE, ShugiinItvLiveRoomIE, ShugiinItvVodIE, SangiinInstructionIE, SangiinIE, JeuxVideoIE, JoveIE, JojIE, JStreamIE, JWPlatformIE, KakaoIE, KalturaIE, Kanal2IE, KankaNewsIE, KaraoketvIE, KarriereVideosIE, KeezMoviesIE, ExtremeTubeIE, KelbyOneIE, KhanAcademyIE, KhanAcademyUnitIE, KickIE, KickVODIE, KickerIE, KickStarterIE, KinjaEmbedIE, KinoPoiskIE, KommunetvIE, KompasVideoIE, KonserthusetPlayIE, KooIE, KTHIE, KrasViewIE, Ku6IE, KUSIIE, KuwoIE, KuwoAlbumIE, KuwoChartIE, KuwoSingerIE, KuwoCategoryIE, KuwoMvIE, LA7IE, LA7PodcastEpisodeIE, LA7PodcastIE, Laola1TvEmbedIE, Laola1TvIE, EHFTVIE, ITTFIE, LastFMIE, LastFMPlaylistIE, LastFMUserIE, LBRYIE, LBRYChannelIE, LCIIE, LcpPlayIE, LcpIE, Lecture2GoIE, LecturioIE, LecturioCourseIE, LecturioDeCourseIE, LeIE, LePlaylistIE, LetvCloudIE, LeFigaroVideoEmbedIE, LeFigaroVideoSectionIE, LEGOIE, LemondeIE, LentaIE, LibraryOfCongressIE, LibsynIE, LifeNewsIE, LifeEmbedIE, LikeeIE, LikeeUserIE, LimelightMediaIE, LimelightChannelIE, LimelightChannelListIE, LinkedInIE, LinkedInLearningIE, LinkedInLearningCourseIE, LinuxAcademyIE, Liputan6IE, ListenNotesIE, LiTVIE, LiveJournalIE, LivestreamIE, LivestreamOriginalIE, LivestreamShortenerIE, LivestreamfailsIE, LnkGoIE, LnkIE, LocalNews8IE, LoveHomePornIE, LRTVODIE, LRTStreamIE, LumniIE, LyndaIE, LyndaCourseIE, M6IE, MagentaMusik360IE, MailRuIE, MailRuMusicIE, MailRuMusicSearchIE, MainStreamingIE, MallTVIE, MangomoloVideoIE, MangomoloLiveIE, ManotoTVIE, ManotoTVShowIE, ManotoTVLiveIE, ManyVidsIE, MaoriTVIE, MarkizaIE, MarkizaPageIE, MassengeschmackTVIE, MastersIE, MatchTVIE, MDRIE, MedalTVIE, MediaiteIE, MediaKlikkIE, MediasetIE, MediasetShowIE, MediasiteIE, MediasiteCatalogIE, MediasiteNamedCatalogIE, MediaStreamIE, WinSportsVideoIE, MediaWorksNZVODIE, MediciIE, MegaphoneIE, MeipaiIE, MelonVODIE, METAIE, MetacafeIE, MetacriticIE, MgoonIE, MGTVIE, MiaoPaiIE, MicrosoftStreamIE, MicrosoftVirtualAcademyIE, MicrosoftVirtualAcademyCourseIE, MicrosoftEmbedIE, MildomIE, MildomVodIE, MildomClipIE, MildomUserVodIE, MindsIE, MindsChannelIE, MindsGroupIE, MinistryGridIE, MinotoIE, MioMioIE, MirrativIE, MirrativUserIE, MirrorCoUKIE, TechTVMITIE, OCWMITIE, MixchIE, MixchArchiveIE, MixcloudIE, MixcloudUserIE, MixcloudPlaylistIE, MLBIE, MLBVideoIE, MLBTVIE, MLBArticleIE, MLSSoccerIE, MnetIE, MochaVideoIE, MoeVideoIE, MofosexIE, MofosexEmbedIE, MojvideoIE, MorningstarIE, MotherlessIE, MotherlessGroupIE, MotherlessGalleryIE, MotorsportIE, MovieClipsIE, MoviepilotIE, MoviewPlayIE, MoviezineIE, MovingImageIE, MSNIE, MTVIE, CMTIE, MTVVideoIE, MTVServicesEmbeddedIE, MTVDEIE, MTVJapanIE, MTVItaliaIE, MTVItaliaProgrammaIE, MuenchenTVIE, MurrtubeIE, MurrtubeUserIE, MuseScoreIE, MusicdexSongIE, MusicdexAlbumIE, MusicdexArtistIE, MusicdexPlaylistIE, MwaveIE, MwaveMeetGreetIE, MxplayerIE, MxplayerShowIE, MyChannelsIE, MySpaceIE, MySpaceAlbumIE, MySpassIE, MyviIE, MyviEmbedIE, MyVideoGeIE, MyVidsterIE, MzaaloIE, N1InfoAssetIE, N1InfoIIE, NateIE, NateProgramIE, NationalGeographicVideoIE, NationalGeographicTVIE, NaverIE, NaverLiveIE, NaverNowIE, NBAWatchEmbedIE, NBAWatchIE, NBAWatchCollectionIE, NBAEmbedIE, NBAIE, NBAChannelIE, NBCOlympicsIE, NBCOlympicsStreamIE, NBCSportsIE, NBCSportsStreamIE, NBCSportsVPlayerIE, NBCStationsIE, NDRIE, NJoyIE, NDREmbedBaseIE, NDREmbedIE, NJoyEmbedIE, NDTVIE, NebulaIE, NebulaSubscriptionsIE, NebulaChannelIE, NekoHackerIE, NerdCubedFeedIE, NetzkinoIE, NetEaseMusicIE, NetEaseMusicAlbumIE, NetEaseMusicSingerIE, NetEaseMusicListIE, NetEaseMusicMvIE, NetEaseMusicProgramIE, NetEaseMusicDjRadioIE, NetverseIE, NetversePlaylistIE, NetverseSearchIE, NewgroundsIE, NewgroundsPlaylistIE, NewgroundsUserIE, NewsPicksIE, NewstubeIE, NewsyIE, NextMediaIE, NextMediaActionNewsIE, AppleDailyIE, NextTVIE, NexxIE, NexxEmbedIE, NFBIE, NFHSNetworkIE, NFLIE, NFLArticleIE, NFLPlusEpisodeIE, NFLPlusReplayIE, NhkVodIE, NhkVodProgramIE, NhkForSchoolBangumiIE, NhkForSchoolSubjectIE, NhkForSchoolProgramListIE, NhkRadioNewsPageIE, NhkRadiruIE, NhkRadiruLiveIE, NHLIE, NickIE, NickBrIE, NickDeIE, NickNightIE, NickRuIE, NiconicoIE, NiconicoPlaylistIE, NiconicoUserIE, NiconicoSeriesIE, NiconicoHistoryIE, NicovideoSearchDateIE, NicovideoSearchIE, NicovideoSearchURLIE, NicovideoTagURLIE, NiconicoLiveIE, NineCNineMediaIE, CPTwentyFourIE, NineGagIE, NineNowIE, NintendoIE, NitterIE, NJPWWorldIE, NobelPrizeIE, NoicePodcastIE, NonkTubeIE, NoodleMagazineIE, NoovoIE, NormalbootsIE, NosVideoIE, NOSNLArticleIE, NovaEmbedIE, NovaIE, NovaPlayIE, NownessIE, NownessPlaylistIE, NownessSeriesIE, NozIE, NPOIE, AndereTijdenIE, NPOLiveIE, NPORadioIE, NPORadioFragmentIE, SchoolTVIE, HetKlokhuisIE, VPROIE, WNLIE, NprIE, NRKIE, NRKPlaylistIE, NRKSkoleIE, NRKTVIE, NRKTVDirekteIE, NRKRadioPodkastIE, NRKTVEpisodeIE, NRKTVEpisodesIE, NRKTVSeasonIE, NRKTVSeriesIE, NRLTVIE, NTVCoJpCUIE, NTVDeIE, NTVRuIE, NubilesPornIE, NYTimesIE, NYTimesArticleIE, NYTimesCookingIE, NuvidIE, NZHeraldIE, NZOnScreenIE, NZZIE, OdaTVIE, OnDemandChinaEpisodeIE, OdnoklassnikiIE, OfTVIE, OfTVPlaylistIE, OktoberfestTVIE, OlympicsReplayIE, On24IE, OnDemandKoreaIE, OneFootballIE, OneNewsNZIE, OnePlacePodcastIE, OnetIE, OnetChannelIE, OnetMVPIE, OnetPlIE, OnionStudiosIE, OoyalaIE, OoyalaExternalIE, OpencastIE, OpencastPlaylistIE, OpenRecIE, OpenRecCaptureIE, OpenRecMovieIE, OraTVIE, ORFTVthekIE, ORFFM4StoryIE, ORFRadioIE, ORFIPTVIE, OutsideTVIE, OwnCloudIE, PacktPubIE, PacktPubCourseIE, PalcoMP3IE, PalcoMP3ArtistIE, PalcoMP3VideoIE, PandoraTVIE, PanoptoIE, PanoptoListIE, PanoptoPlaylistIE, ParamountPlusSeriesIE, ParlerIE, ParlviewIE, PatreonIE, PatreonCampaignIE, PBSIE, PearVideoIE, PeekVidsIE, PlayVidsIE, PeerTubeIE, PeerTubePlaylistIE, PeerTVIE, PelotonIE, PelotonLiveIE, PeopleIE, PerformGroupIE, PeriscopeIE, PeriscopeUserIE, PGATourIE, PhilharmonieDeParisIE, PhoenixIE, PhotobucketIE, PiaproIE, PicartoIE, PicartoVodIE, PikselIE, PinkbikeIE, PinterestIE, PinterestCollectionIE, PixivSketchIE, PixivSketchUserIE, PladformIE, PlanetMarathiIE, PlatziIE, PlatziCourseIE, PlayFMIE, PlayPlusTVIE, PlaysTVIE, PlayStuffIE, PlaySuisseIE, PlaytvakIE, PlayvidIE, PlaywireIE, PlutoTVIE, PluralsightIE, PluralsightCourseIE, PodbayFMIE, PodbayFMChannelIE, PodchaserIE, PodomaticIE, PokemonIE, PokemonWatchIE, PokerGoIE, PokerGoCollectionIE, PolsatGoIE, PolskieRadioIE, PolskieRadioLegacyIE, PolskieRadioAuditionIE, PolskieRadioCategoryIE, PolskieRadioPlayerIE, PolskieRadioPodcastIE, PolskieRadioPodcastListIE, PopcorntimesIE, PopcornTVIE, Porn91IE, PornComIE, PornFlipIE, PornHdIE, PornHubIE, PornHubUserIE, PornHubPlaylistIE, PornHubPagedVideoListIE, PornHubUserVideosUploadIE, PornotubeIE, PornoVoisinesIE, PornoXOIE, PornezIE, PuhuTVIE, PuhuTVSerieIE, Pr0grammStaticIE, Pr0grammIE, PrankCastIE, PremiershipRugbyIE, PressTVIE, ProjectVeritasIE, ProSiebenSat1IE, PRXStoryIE, PRXSeriesIE, PRXAccountIE, PRXStoriesSearchIE, PRXSeriesSearchIE, Puls4IE, PyvideoIE, QDanceIE, QingTingIE, QQMusicIE, QQMusicSingerIE, QQMusicAlbumIE, QQMusicToplistIE, QQMusicPlaylistIE, R7IE, R7ArticleIE, RadikoIE, RadikoRadioIE, RadioCanadaIE, RadioCanadaAudioVideoIE, RadioDeIE, RadioJavanIE, RadioBremenIE, FranceCultureIE, RadioFranceIE, RadioZetPodcastIE, RadioKapitalIE, RadioKapitalShowIE, RadLiveIE, RadLiveChannelIE, RadLiveSeasonIE, RaiIE, RaiPlayIE, RaiPlayLiveIE, RaiPlayPlaylistIE, RaiPlaySoundIE, RaiPlaySoundLiveIE, RaiPlaySoundPlaylistIE, RaiNewsIE, RaiCulturaIE, RaiSudtirolIE, RayWenderlichIE, RayWenderlichCourseIE, RBMARadioIE, RbgTumIE, RbgTumCourseIE, RCSIE, RCSEmbedsIE, RCSVariousIE, RCTIPlusIE, RCTIPlusSeriesIE, RCTIPlusTVIE, RDSIE, RecurbateIE, ParliamentLiveUKIE, RTBFIE, RedBullTVIE, RedBullEmbedIE, RedBullTVRrnContentIE, RedBullIE, RedditIE, RedGifsIE, RedGifsSearchIE, RedGifsUserIE, RedTubeIE, RegioTVIE, RENTVIE, RENTVArticleIE, RestudyIE, ReutersIE, ReverbNationIE, RheinMainTVIE, RICEIE, RMCDecouverteIE, RockstarGamesIE, RokfinIE, RokfinStackIE, RokfinChannelIE, RokfinSearchIE, RoosterTeethIE, RoosterTeethSeriesIE, RottenTomatoesIE, RozhlasIE, RozhlasVltavaIE, MujRozhlasIE, RteIE, RteRadioIE, RtlNlIE, RTLLuTeleVODIE, RTLLuArticleIE, RTLLuLiveIE, RTLLuRadioIE, RTL2IE, RTL2YouIE, RTL2YouSeriesIE, RTNewsIE, RTDocumentryIE, RTDocumentryPlaylistIE, RuptlyIE, RTPIE, RTRFMIE, RTVCPlayIE, RTVCPlayEmbedIE, RTVCKalturaIE, RTVEALaCartaIE, RTVEAudioIE, RTVELiveIE, RTVEInfantilIE, RTVETelevisionIE, RTVNHIE, RTVSIE, RTVSLOIE, RUHDIE, Rule34VideoIE, RumbleEmbedIE, RumbleIE, RumbleChannelIE, RutubeIE, RutubeChannelIE, RutubeEmbedIE, RutubeMovieIE, RutubePersonIE, RutubePlaylistIE, RutubeTagsIE, GlomexIE, GlomexEmbedIE, MegaTVComIE, MegaTVComEmbedIE, Ant1NewsGrWatchIE, Ant1NewsGrArticleIE, Ant1NewsGrEmbedIE, RUTVIE, RuutuIE, RuvIE, RuvSpilaIE, SafariIE, SafariApiIE, SafariCourseIE, SaitosanIE, SampleFocusIE, SapoIE, SaveFromIE, SBSIE, Screen9IE, ScreencastIE, ScreencastifyIE, ScreencastOMaticIE, ScrippsNetworksWatchIE, ScrippsNetworksIE, SCTEIE, SCTECourseIE, ScrolllerIE, SeekerIE, SenalColombiaLiveIE, SenateISVPIE, SenateGovIE, SendtoNewsIE, ServusIE, SevenPlusIE, SexuIE, SeznamZpravyIE, SeznamZpravyArticleIE, ShahidIE, ShahidShowIE, SharedIE, VivoIE, ShareVideosEmbedIE, SibnetEmbedIE, ShemarooMeIE, ShowRoomLiveIE, SimplecastIE, SimplecastEpisodeIE, SimplecastPodcastIE, SinaIE, SixPlayIE, SkebIE, SkyItPlayerIE, SkyItVideoIE, SkyItVideoLiveIE, SkyItIE, SkyItArteIE, CieloTVItIE, TV8ItIE, SkylineWebcamsIE, SkyNewsArabiaIE, SkyNewsArabiaArticleIE, SkyNewsAUIE, SkyNewsIE, SkyNewsStoryIE, SkySportsIE, SkySportsNewsIE, SlideshareIE, SlidesLiveIE, SlutloadIE, SmotrimIE, SnotrIE, SohuIE, SonyLIVIE, SonyLIVSeriesIE, SoundcloudEmbedIE, SoundcloudIE, SoundcloudSetIE, SoundcloudRelatedIE, SoundcloudUserIE, SoundcloudUserPermalinkIE, SoundcloudTrackStationIE, SoundcloudPlaylistIE, SoundcloudSearchIE, SoundgasmIE, SoundgasmProfileIE, SouthParkIE, SouthParkDeIE, SouthParkDkIE, SouthParkEsIE, SouthParkLatIE, SouthParkNlIE, SovietsClosetIE, SovietsClosetPlaylistIE, SpankBangIE, SpankBangPlaylistIE, SpankwireIE, SpiegelIE, BellatorIE, ParamountNetworkIE, StagePlusVODConcertIE, StarTrekIE, StitcherIE, StitcherShowIE, Sport5IE, SportBoxIE, SportDeutschlandIE, SpotifyIE, SpotifyShowIE, SpreakerIE, SpreakerPageIE, SpreakerShowIE, SpreakerShowPageIE, SpringboardPlatformIE, SproutIE, SRGSSRIE, RTSIE, SRGSSRPlayIE, SRMediathekIE, StacommuLiveIE, StacommuVODIE, StanfordOpenClassroomIE, StarTVIE, SteamIE, SteamCommunityBroadcastIE, StoryFireIE, StoryFireUserIE, StoryFireSeriesIE, StreamableIE, StreamanityIE, StreamcloudIE, StreamCZIE, StreamFFIE, StreetVoiceIE, StretchInternetIE, StripchatIE, STVPlayerIE, SubstackIE, SunPornoIE, SverigesRadioEpisodeIE, SverigesRadioPublicationIE, SVTIE, SVTPageIE, SVTPlayIE, SVTSeriesIE, SwearnetEpisodeIE, SWRMediathekIE, SYVDKIE, SyfyIE, SztvHuIE, TagesschauIE, TassIE, TBSIE, TDSLifewayIE, TeachableIE, TeachableCourseIE, TeacherTubeIE, TeacherTubeUserIE, TeachingChannelIE, TeamcocoIE, ConanClassicIE, TeamTreeHouseIE, TechTalksIE, TedEmbedIE, TedPlaylistIE, TedSeriesIE, TedTalkIE, Tele5IE, Tele13IE, TeleBruxellesIE, TelecaribePlayIE, TelecincoIE, MiTeleIE, TelegraafIE, TelegramEmbedIE, TeleMBIE, TelemundoIE, TeleQuebecIE, TeleQuebecSquatIE, TeleQuebecEmissionIE, TeleQuebecLiveIE, TeleQuebecVideoIE, TeleTaskIE, TelewebionIE, TempoIE, IVXPlayerIE, IflixEpisodeIE, IflixSeriesIE, VQQSeriesIE, VQQVideoIE, WeTvEpisodeIE, WeTvSeriesIE, TennisTVIE, TenPlayIE, TestURLIE, TF1IE, TFOIE, TheHoleTvIE, TheInterceptIE, ThePlatformIE, AENetworksIE, AENetworksCollectionIE, AENetworksShowIE, HistoryTopicIE, HistoryPlayerIE, BiographyIE, AMCNetworksIE, NBCIE, NBCNewsIE, ThePlatformFeedIE, CBSIE, CBSInteractiveIE, CorusIE, ParamountPlusIE, TheStarIE, TheSunIE, ThetaVideoIE, ThetaStreamIE, TheWeatherChannelIE, ThisAmericanLifeIE, ThisAVIE, ThisOldHouseIE, ThisVidIE, ThisVidMemberIE, ThisVidPlaylistIE, ThreeSpeakIE, ThreeSpeakUserIE, ThreeQSDNIE, TikTokIE, TikTokUserIE, TikTokSoundIE, TikTokEffectIE, TikTokTagIE, TikTokVMIE, TikTokLiveIE, DouyinIE, TinyPicIE, TMZIE, TNAFlixNetworkEmbedIE, TNAFlixIE, EMPFlixIE, MovieFapIE, ToggleIE, MeWatchIE, ToggoIE, TokentubeIE, TokentubeChannelIE, TOnlineIE, ToonGogglesIE, TouTvIE, ToypicsUserIE, ToypicsIE, TrailerAddictIE, TrillerIE, TrillerUserIE, TrillerShortIE, TriluliluIE, TrovoIE, TrovoVodIE, TrovoChannelVodIE, TrovoChannelClipIE, TrtCocukVideoIE, TrueIDIE, TruNewsIE, TruthIE, TruTVIE, Tube8IE, TubeTuGrazIE, TubeTuGrazSeriesIE, TubiTvIE, TubiTvShowIE, TumblrIE, TuneInStationIE, TuneInPodcastIE, TuneInPodcastEpisodeIE, TuneInShortenerIE, TunePkIE, TurboIE, TV2IE, TV2ArticleIE, KatsomoIE, MTVUutisetArticleIE, TV24UAVideoIE, TV2DKIE, TV2DKBornholmPlayIE, TV2HuIE, TV2HuSeriesIE, TV4IE, TV5MondePlusIE, TV5UnisVideoIE, TV5UnisIE, TVAIE, QubIE, TVANouvellesIE, TVANouvellesArticleIE, TVCIE, TVCArticleIE, TVerIE, TvigleIE, TVIPlayerIE, TVLandIE, TVN24IE, TVNetIE, TVNoeIE, TVNowIE, TVNowFilmIE, TVNowNewIE, TVNowSeasonIE, TVNowAnnualIE, TVNowShowIE, TVOpenGrWatchIE, TVOpenGrEmbedIE, TVPEmbedIE, TVPIE, TVPStreamIE, TVPVODSeriesIE, TVPVODVideoIE, TVPlayIE, TVPlayHomeIE, TVPlayerIE, TweakersIE, TwentyFourVideoIE, TwentyMinutenIE, TwentyThreeVideoIE, TwitCastingIE, TwitCastingLiveIE, TwitCastingUserIE, TwitchVodIE, TwitchCollectionIE, TwitchVideosIE, TwitchVideosClipsIE, TwitchVideosCollectionsIE, TwitchStreamIE, TwitchClipsIE, TwitterCardIE, TwitterIE, TwitterAmplifyIE, TwitterBroadcastIE, TwitterSpacesIE, TwitterShortenerIE, TxxxIE, PornTopIE, UdemyIE, UdemyCourseIE, UDNEmbedIE, UFCTVIE, UFCArabiaIE, UkColumnIE, UKTVPlayIE, DigitekaIE, DLiveVODIE, DLiveStreamIE, DroobleIE, UMGDeIE, UnistraIE, UnityIE, UnscriptedNewsVideoIE, KnownDRMIE, KnownPiracyIE, UOLIE, UplynkIE, UplynkPreplayIE, UrortIE, URPlayIE, USANetworkIE, USATodayIE, UstreamIE, UstreamChannelIE, UstudioIE, UstudioEmbedIE, UtreonIE, Varzesh3IE, Vbox7IE, VeeHDIE, VeoIE, VeohIE, VeohUserIE, VestiIE, VevoIE, VevoPlaylistIE, BTArticleIE, BTVestlendingenIE, VH1IE, ViceIE, ViceArticleIE, ViceShowIE, VidbitIE, ViddlerIE, VideaIE, VideocampusSachsenIE, ViMPPlaylistIE, VideoDetectiveIE, VideofyMeIE, VideoKenIE, VideoKenPlayerIE, VideoKenPlaylistIE, VideoKenCategoryIE, VideoKenTopicIE, VideomoreIE, VideomoreVideoIE, VideomoreSeasonIE, VideoPressIE, VidioIE, VidioPremierIE, VidioLiveIE, VidLiiIE, ViewLiftIE, ViewLiftEmbedIE, ViideaIE, VimeoIE, VimeoAlbumIE, VimeoChannelIE, VimeoGroupsIE, VimeoLikesIE, VimeoOndemandIE, VimeoProIE, VimeoReviewIE, VimeoUserIE, VimeoWatchLaterIE, VHXEmbedIE, VimmIE, VimmRecordingIE, VimpleIE, VineIE, VineUserIE, VikiIE, VikiChannelIE, ViqeoIE, ViuIE, ViuPlaylistIE, ViuOTTIE, ViuOTTIndonesiaIE, VKIE, VKUserVideosIE, VKWallPostIE, VKPlayIE, VKPlayLiveIE, VocarooIE, VodlockerIE, VODPlIE, VODPlatformIE, VoiceRepublicIE, VoicyIE, VoicyChannelIE, VolejTVIE, VootIE, VootSeriesIE, VoxMediaVolumeIE, VoxMediaIE, VRTIE, VrtNUIE, KetnetIE, DagelijkseKostIE, VrakIE, VRVIE, VRVSeriesIE, VShareIE, VTMIE, MedialaanIE, VuClipIE, VuploadIE, VVVVIDIE, VVVVIDShowIE, VyboryMosIE, VzaarIE, WakanimIE, WallaIE, WashingtonPostIE, WashingtonPostArticleIE, WASDTVStreamIE, WASDTVRecordIE, WASDTVClipIE, WatIE, WatchBoxIE, WatchIndianPornIE, WDRIE, WDRPageIE, WDRElefantIE, WDRMobileIE, WebcameraplIE, WebcasterIE, WebcasterFeedIE, WebOfStoriesIE, WebOfStoriesPlaylistIE, WeiboIE, WeiboMobileIE, WeiqiTVIE, WeverseIE, WeverseMediaIE, WeverseMomentIE, WeverseLiveTabIE, WeverseMediaTabIE, WeverseLiveIE, WeVidiIE, WeyyakIE, WhypIE, WikimediaIE, WillowIE, WimTVIE, WhoWatchIE, WistiaIE, WistiaPlaylistIE, WistiaChannelIE, WordpressPlaylistEmbedIE, WordpressMiniAudioPlayerEmbedIE, WorldStarHipHopIE, WPPilotIE, WPPilotChannelsIE, WrestleUniverseVODIE, WrestleUniversePPVIE, WSJIE, WSJArticleIE, WWEIE, WykopDigIE, WykopDigCommentIE, WykopPostIE, WykopPostCommentIE, XanimuIE, XBefIE, XboxClipsIE, XFileShareIE, XHamsterIE, XHamsterEmbedIE, XHamsterUserIE, XimalayaIE, XimalayaAlbumIE, XinpianchangIE, XMinusIE, XNXXIE, XstreamIE, VGTVIE, XTubeUserIE, XTubeIE, XuiteIE, XVideosIE, XVideosQuickiesIE, XXXYMoviesIE, YahooIE, AolIE, YahooSearchIE, YahooJapanNewsIE, YandexDiskIE, YandexMusicTrackIE, YandexMusicAlbumIE, YandexMusicPlaylistIE, YandexMusicArtistTracksIE, YandexMusicArtistAlbumsIE, YandexVideoIE, YandexVideoPreviewIE, ZenYandexIE, ZenYandexChannelIE, YapFilesIE, YappyIE, YappyProfileIE, YesJapanIE, YinYueTaiIE, YleAreenaIE, YnetIE, YouJizzIE, YoukuIE, YoukuShowIE, YouNowLiveIE, YouNowChannelIE, YouNowMomentIE, YouPornIE, YourPornIE, YourUploadIE, ZaikoIE, ZaikoETicketIE, ZapiksIE, BBVTVIE, BBVTVLiveIE, BBVTVRecordingsIE, EinsUndEinsTVIE, EinsUndEinsTVLiveIE, EinsUndEinsTVRecordingsIE, EWETVIE, EWETVLiveIE, EWETVRecordingsIE, GlattvisionTVIE, GlattvisionTVLiveIE, GlattvisionTVRecordingsIE, MNetTVIE, MNetTVLiveIE, MNetTVRecordingsIE, NetPlusTVIE, NetPlusTVLiveIE, NetPlusTVRecordingsIE, OsnatelTVIE, OsnatelTVLiveIE, OsnatelTVRecordingsIE, QuantumTVIE, QuantumTVLiveIE, QuantumTVRecordingsIE, SaltTVIE, SaltTVLiveIE, SaltTVRecordingsIE, SAKTVIE, SAKTVLiveIE, SAKTVRecordingsIE, VTXTVIE, VTXTVLiveIE, VTXTVRecordingsIE, WalyTVIE, WalyTVLiveIE, WalyTVRecordingsIE, ZattooIE, ZattooLiveIE, ZattooMoviesIE, ZattooRecordingsIE, ZDFIE, DreiSatIE, ZDFChannelIE, Zee5IE, Zee5SeriesIE, ZeeNewsIE, ZhihuIE, ZingMp3IE, ZingMp3AlbumIE, ZingMp3ChartHomeIE, ZingMp3WeekChartIE, ZingMp3ChartMusicVideoIE, ZingMp3UserIE, ZingMp3HubIE, ZoomIE, ZypeIE, GenericIE]
