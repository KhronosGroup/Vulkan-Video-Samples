"""
Unit tests for the encode feedback file validation.

Copyright 2026 Igalia S.L.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pytest

from tests.libs.video_test_feedback_validation import (
    FeedbackExpectations,
    validate_feedback_text,
)

PARTITION_ARGS = ["--enablePerPartitionFeedback",
                  "--maxPerPartitionFeedbackEntries", "16", "--slices", "4"]

PARTITION_TEXT = """\
frame 0 status=1 bs_offset=0 bs_size=17311 pic_partition_count=4
partition 0 status=1 offset=0 size=4344
partition 1 status=1 offset=4344 size=6462
partition 2 status=1 offset=10806 size=1569
partition 3 status=1 offset=12375 size=4936
frame 1 status=1 bs_offset=0 bs_size=127 pic_partition_count=4
partition 0 status=1 offset=0 size=57
partition 1 status=1 offset=57 size=24
partition 2 status=1 offset=81 size=23
partition 3 status=1 offset=104 size=23
"""

QP_TEXT = """\
frame 0 status=1 bs_offset=0 bs_size=17125 avgqp=23 minqp=22 maxqp=25
frame 1 status=1 bs_offset=0 bs_size=88 avgqp=30 minqp=30 maxqp=33
"""

PIXEL_TEXT = """\
frame 0 status=1 bs_offset=0 bs_size=17125 intra=101376 inter=0 skipped=0
frame 1 status=1 bs_offset=0 bs_size=88 intra=0 inter=101376 skipped=900
"""


def expectations(args, codec="h264"):
    """Expectations for a 352x288 test with the given extra arguments"""
    return FeedbackExpectations(codec=codec, extra_args=args,
                                width=352, height=288)


class TestExpectations:
    """Tests for FeedbackExpectations"""

    def test_no_feedback_argument(self):
        """A test without feedback arguments expects no feedback file"""
        assert not expectations(["--slices", "4"]).enabled

    def test_per_partition_arguments(self):
        """Per-partition arguments are picked up with their values"""
        expected = expectations(PARTITION_ARGS)
        assert expected.enabled
        assert expected.per_partition
        assert not expected.picture
        assert expected.max_partition_entries == 16
        assert expected.slices == 4

    def test_default_partition_entries(self):
        """The encoder asks for a single entry by default"""
        expected = expectations(["--enablePerPartitionFeedback"])
        assert expected.max_partition_entries == 1
        assert expected.slices is None


class TestValidFeedback:
    """Feedback files that must be accepted"""

    def test_per_partition(self):
        """Per-partition output as written by the encoder"""
        assert not validate_feedback_text(PARTITION_TEXT,
                                          expectations(PARTITION_ARGS))

    def test_qp(self):
        """QP output as written by the encoder"""
        assert not validate_feedback_text(
            QP_TEXT, expectations(["--pictureFeedback"]))

    def test_qp_without_min_max(self):
        """Min/max QP are optional, the encoder drops them if unsupported"""
        text = "frame 0 status=1 bs_offset=0 bs_size=10 avgqp=23\n"
        assert not validate_feedback_text(
            text, expectations(["--pictureFeedback"]))

    def test_av1_qp_range(self):
        """AV1 quantizer indices go up to 255"""
        text = "frame 0 status=1 bs_offset=0 bs_size=10 avgqp=180\n"
        assert not validate_feedback_text(
            text, expectations(["--pictureFeedback"], codec="av1"))

    def test_pixel_counts(self):
        """Pixel counts as written by the encoder"""
        args = ["--pixelCountFeedback", "--skippedPixelCountFeedback"]
        assert not validate_feedback_text(PIXEL_TEXT, expectations(args))

    def test_entries_limited_by_max(self):
        """Only the requested number of entries is written"""
        text = ("frame 0 status=1 bs_offset=0 bs_size=100 "
                "pic_partition_count=4\n"
                "partition 0 status=1 offset=0 size=20\n")
        assert not validate_feedback_text(
            text, expectations(["--enablePerPartitionFeedback"]))


@pytest.mark.parametrize("args,text,expected_error", [
    (["--pictureFeedback"], "", "no frame feedback"),
    (["--pictureFeedback"], "garbage\n", "cannot parse"),
    (["--pictureFeedback"],
     QP_TEXT.replace("frame 1 status=1", "frame 1 status=-1"),
     "frame 1: status is -1"),
    (["--pictureFeedback"],
     QP_TEXT.replace("frame 1", "frame 0"), "more than once"),
    (["--pictureFeedback"],
     QP_TEXT.replace("frame 1", "frame 2"), "frame 1: not reported"),
    (["--pictureFeedback"],
     QP_TEXT.replace("bs_size=88", "bs_size=0"), "bs_size is 0"),
    (["--pictureFeedback"],
     "frame 0 status=1 bs_offset=0 bs_size=10\n", "avgqp is missing"),
    (["--pictureFeedback"],
     QP_TEXT.replace("avgqp=23", "avgqp=52"), "avgqp 52 is outside"),
    (["--pictureFeedback"],
     QP_TEXT.replace("minqp=22", "minqp=24"),
     "minqp 24 is greater than avgqp 23"),
    (["--pixelCountFeedback"],
     "frame 0 status=1 bs_offset=0 bs_size=10 intra=5\n",
     "inter pixel count is missing"),
    (["--pixelCountFeedback"],
     PIXEL_TEXT.replace("intra=101376", "intra=999999"),
     "intra pixel count 999999 is outside"),
    (["--pixelCountFeedback"],
     PIXEL_TEXT.replace("intra=101376", "intra=0"),
     "no pixel was reported"),
    (["--skippedPixelCountFeedback"],
     "frame 0 status=1 bs_offset=0 bs_size=10\n",
     "skipped pixel count is missing"),
    (PARTITION_ARGS,
     "frame 0 status=1 bs_offset=0 bs_size=10\n",
     "pic_partition_count is missing"),
    (PARTITION_ARGS,
     PARTITION_TEXT.replace("pic_partition_count=4",
                            "pic_partition_count=3"),
     "expected 4 slices"),
    (["--enablePerPartitionFeedback"],
     PARTITION_TEXT,
     "4 partition entries, expected between 1 and 1"),
    (PARTITION_ARGS,
     PARTITION_TEXT.replace("partition 2 status=1 offset=10806",
                            "partition 2 status=-1 offset=10806"),
     "partition 2: status is -1"),
    (PARTITION_ARGS,
     PARTITION_TEXT.replace("offset=81 size=23", "offset=81 size=0"),
     "partition 2: size is 0"),
    (PARTITION_ARGS,
     PARTITION_TEXT.replace("offset=4344 size=6462",
                            "offset=4000 size=6462"),
     "overlaps"),
    (PARTITION_ARGS,
     PARTITION_TEXT.replace("bs_size=127", "bs_size=100"),
     "outside the frame range [0, 100]"),
])
def test_rejected_feedback(args, text, expected_error):
    """Each broken file reports the matching problem"""
    errors = validate_feedback_text(text, expectations(args))
    assert any(expected_error in error for error in errors), errors
