import typing as t
from pathlib import Path

import pytest
import pytest_check as check
from idaqpy import UnsupportedLogFile
from idaqpy.models import iDAQ
from pytest_mock.plugin import MockFixture


class UnsupportedFileTestCase(t.NamedTuple):
    """Represent unsupported file test cases & whether the file name should yield an error."""

    file_name: str
    should_raise: bool


UNSUPPORTED_FILE_CASES = (
    UnsupportedFileTestCase(file_name="file.exe", should_raise=True),
    UnsupportedFileTestCase(file_name="file.mat", should_raise=True),
    UnsupportedFileTestCase(file_name="LOG.001", should_raise=False),
    UnsupportedFileTestCase(file_name="file.idaq", should_raise=False),
    UnsupportedFileTestCase(file_name="file.csv", should_raise=False),
)


@pytest.mark.parametrize("file_name, should_raise", UNSUPPORTED_FILE_CASES)
def test_unsupported_raise(
    file_name: str, should_raise: bool, tmp_path: Path, mocker: MockFixture
) -> None:
    """
    Test that an error is appropriately raised for unsupported file types.

    A temporary directory is provided by Pytest as a fixture to create a dummy file to bypass
    log existence check.
    """
    # Create a temporary dummy file
    tempfile = tmp_path / file_name
    tempfile.write_text("")

    # Mock the data parsing methods since they're not relevant to this test
    mocker.patch("idaqpy.models.iDAQ.parse_raw_log")
    mocker.patch("idaqpy.models.iDAQ.parse_log_csv")

    if should_raise:
        with pytest.raises(UnsupportedLogFile):
            _ = iDAQ(tempfile)
    else:
        _ = iDAQ(tempfile)


def test_os_specific_logdecoder_path(mocker: MockFixture) -> None:
    """
    Test that the path to the logdecoder is appropriately set per OS.

    On Windows, the logdecoder will need an `*.exe` extension, all others will not.
    """
    # Mock the log parsing chain since we're only concerned about the log
    mocker.patch("idaqpy.models.iDAQ.parse_log_file")
    test_idaq = iDAQ(Path())

    failure_msg = "logdecoder path test failed for platform '{platform}'"
    for platform in ("win32", "cygwin"):
        mocker.patch("sys.platform", platform)
        check.equal(
            test_idaq.logdecoder_path.suffix, ".exe", msg=failure_msg.format(platform=platform)
        )

    for platform in ("darwin", "linux"):
        mocker.patch("sys.platform", platform)
        check.equal(test_idaq.logdecoder_path.suffix, "", msg=failure_msg.format(platform=platform))
