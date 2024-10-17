class EmbedConfig:

    # Camel casing is used for the member variables as they are going to be serialized and camel case is standard for JSON keys

    tokenId = None
    accessToken = None
    tokenExpiry = None
    reportConfig = None

    def __init__(self, tokenId, token, expiration, reports):
        self.tokenId = tokenId
        self.accessToken = token
        self.tokenExpiry = expiration
        self.reportConfig = reports
