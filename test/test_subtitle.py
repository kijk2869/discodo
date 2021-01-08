import os.path

from discodo.source import SubtitleSource

__DIRNAME = os.path.dirname(os.path.abspath(__file__))


def testSmi() -> None:
    with open(os.path.join(__DIRNAME, "testdata", "test.smi")) as fp:
        Source = SubtitleSource.smi(fp.read())

    assert Source.TextElements == {
        0.0: {
            "start": 0.0,
            "text": "Hello, World!",
            "markdown": "Hello, World!",
            "end": 5.0,
            "duration": 5,
        }
    }
    assert Source.duration == 5.0


def testSrv1() -> None:
    with open(os.path.join(__DIRNAME, "testdata", "test.srv1.xml")) as fp:
        Source = SubtitleSource.srv1(fp.read())

    assert Source.TextElements == {
        0.0: {
            "start": 0.0,
            "text": "Hello, World!",
            "markdown": "Hello, World!",
            "end": 5.0,
            "duration": 5,
        }
    }
    assert Source.duration == 5.0
