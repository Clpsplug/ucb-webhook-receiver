import hashlib
import hmac

import os


def verify_signature(body: bytes, signature: str) -> bool:
    """
    Calculates the HMAC SHA-256 signature for this payload and compares it with the header.

    :param body: given body
    :param signature: signature in header
    :return: true if the signature is good.
    :raises KeyError: If the signature is not set in environment. Use dotenv to set one.
    """

    try:
        token = os.environ['UCB_TOKEN']
        calculated_signature = (
            hmac.new(bytes(token, 'utf-8'), body, digestmod=hashlib.sha256).hexdigest().upper()
        )
        return signature.upper() == calculated_signature
    except KeyError:
        print('[FATAL] TOKEN not set in env')
        raise
