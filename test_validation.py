from validation import CONTAINERFILE_TMPL


def test_containerfile_has_from_instruction():
    assert 'FROM' in CONTAINERFILE_TMPL
