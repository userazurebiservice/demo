# models/embedtoken.py
class EmbedToken:

    def __init__(self, token_id, token, expiration):
        self.tokenId = token_id
        self.token = token
        self.expiration = expiration