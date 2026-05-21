import pytest

from pman.errors import AIError, ConfigError, PDFError, PMANError, ValidationError


class TestCustomExceptions:
    def test_pman_error_is_exception(self):
        with pytest.raises(PMANError):
            raise PMANError("test")

    def test_pdf_error_is_pman_error(self):
        with pytest.raises(PMANError):
            raise PDFError("bad pdf")

    def test_ai_error_is_pman_error(self):
        with pytest.raises(PMANError):
            raise AIError("ai failed")

    def test_config_error_is_pman_error(self):
        with pytest.raises(PMANError):
            raise ConfigError("bad config")

    def test_validation_error_is_pman_error(self):
        with pytest.raises(PMANError):
            raise ValidationError("invalid")
