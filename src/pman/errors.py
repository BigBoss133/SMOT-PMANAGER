class PMANError(Exception):
    pass


class PDFError(PMANError):
    pass


class AIError(PMANError):
    pass


class ConfigError(PMANError):
    pass


class ValidationError(PMANError):
    pass
