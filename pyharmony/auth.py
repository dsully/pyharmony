import asyncio
import logging
import re

from xml.etree import cElementTree as ET

from .xmpp import BaseXMPPClient

log = logging.getLogger(__name__)


class SessionTokenClient(BaseXMPPClient):
    """An XMPP Client for getting a session token given a login token for a Harmony Hub device."""

    @classmethod
    def login(cls, hostname, port=5222):
        """Performs a login to Logitech, returning a session token from the local device.

        :param str hostname: The hostname (or IP) of the local Harmony device.
        :param int port: The port of the Harmony device. Defaults to 5222.

        :returns: The session token from Logitech.
        :rtype: str
        """

        client = cls('guest@connect.logitech.com/gatorade', 'guest')
        token = asyncio.Future()

        async def start(event):
            token.set_result(await client.get_token())
            client.disconnect()

        client.add_event_handler('session_start', start)
        client.connect(address=(hostname, port), disable_starttls=True, use_ssl=False)
        client.process(forever=False)

        return token.result()

    async def get_token(self):
        """Get the login token for a client session."""

        iq_cmd = self.Iq()
        iq_cmd['type'] = 'get'

        action_cmd = ET.Element('oa')
        action_cmd.attrib['xmlns'] = 'connect.logitech.com'
        action_cmd.attrib['mime'] = 'vnd.logitech.connect/vnd.logitech.pair'
        action_cmd.text = 'method=pair:name=%s' % 'pyharmony#iOS10.1#iPhone'

        iq_cmd.set_payload(action_cmd)

        result = await iq_cmd.send()
        payload = result.get_payload()

        assert len(payload) == 1
        oa_response = payload[0]

        assert oa_response.attrib['errorcode'] == '200'

        match = re.search(r'identity=(?P<uuid>[\w-]+):status', oa_response.text)

        if not match:
          raise ValueError('Could not get a session token!')

        uuid = match.group('uuid')

        log.debug('Received UUID from device: %s', uuid)

        return uuid
