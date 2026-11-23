"""
Vulkan Video Encoder Feedback Validation
Checks the text file the encoder writes when encode feedback2 is requested.

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

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

FEEDBACK_FILE_SUFFIX = ".feedback.txt"

PICTURE_FEEDBACK_ARG = "--pictureFeedback"
PIXEL_COUNT_FEEDBACK_ARG = "--pixelCountFeedback"
SKIPPED_PIXEL_COUNT_FEEDBACK_ARG = "--skippedPixelCountFeedback"
PER_PARTITION_FEEDBACK_ARG = "--enablePerPartitionFeedback"
MAX_PARTITION_ENTRIES_ARG = "--maxPerPartitionFeedbackEntries"
SLICES_ARG = "--slices"

# VK_QUERY_RESULT_STATUS_COMPLETE_KHR
QUERY_STATUS_COMPLETE = 1

# 8-bit quantizer ranges: qp for H.264/H.265, base_q_idx for AV1.
QP_RANGE = {"h264": (0, 51), "h265": (0, 51), "av1": (0, 255)}
SLICE_CODECS = ("h264", "h265")
# Largest coding block the coded extent is padded to (AV1 superblock).
CODED_EXTENT_ALIGNMENT = 128
# The encoder requests a single per-partition entry unless told otherwise.
DEFAULT_MAX_PARTITION_ENTRIES = 1


@dataclass
class FeedbackExpectations:
    """What the feedback file must contain, derived from the test arguments"""
    codec: str
    extra_args: List[str] = field(default_factory=list)
    width: int = 0
    height: int = 0

    @property
    def picture(self) -> bool:
        """True when QP feedback is requested"""
        return PICTURE_FEEDBACK_ARG in self.extra_args

    @property
    def pixel_count(self) -> bool:
        """True when intra/inter pixel counts are requested"""
        return (PIXEL_COUNT_FEEDBACK_ARG in self.extra_args
                or self.skipped_pixel_count)

    @property
    def skipped_pixel_count(self) -> bool:
        """True when the skipped pixel count is requested"""
        return SKIPPED_PIXEL_COUNT_FEEDBACK_ARG in self.extra_args

    @property
    def per_partition(self) -> bool:
        """True when per-partition feedback is requested"""
        return PER_PARTITION_FEEDBACK_ARG in self.extra_args

    @property
    def max_partition_entries(self) -> int:
        """Number of per-partition entries the encoder was asked for"""
        requested = _int_arg(self.extra_args, MAX_PARTITION_ENTRIES_ARG)
        return max(requested or DEFAULT_MAX_PARTITION_ENTRIES, 1)

    @property
    def slices(self) -> Optional[int]:
        """Slice count requested with --slices, if any"""
        return _int_arg(self.extra_args, SLICES_ARG)

    @property
    def enabled(self) -> bool:
        """True when the encoder is expected to write a feedback file"""
        return (self.picture or self.pixel_count
                or self.skipped_pixel_count or self.per_partition)


@dataclass
class _Frame:
    index: int
    fields: Dict[str, int]
    partitions: List[Tuple[int, Dict[str, int]]] = field(
        default_factory=list)


def validate_feedback_text(text: str,
                           expected: FeedbackExpectations) -> List[str]:
    """Return the list of problems found in a feedback file, empty if none"""
    frames, errors = _parse(text)
    if not frames and not errors:
        errors.append("no frame feedback was written")

    seen = set()
    for frame in frames:
        if frame.index in seen:
            errors.append(f"frame {frame.index}: reported more than once")
        seen.add(frame.index)
        errors.extend(
            f"frame {frame.index}: {problem}"
            for problem in _check_frame(frame, expected)
        )
    missing = set(range(len(seen))) - seen
    if missing:
        errors.append(f"frame {min(missing)}: not reported")
    return errors


def _int_arg(args: List[str], name: str) -> Optional[int]:
    if name not in args:
        return None
    position = args.index(name) + 1
    if position >= len(args):
        return None
    try:
        return int(args[position])
    except ValueError:
        return None


def _parse(text: str) -> Tuple[List[_Frame], List[str]]:
    frames: List[_Frame] = []
    errors: List[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        tokens = line.split()
        if not tokens:
            continue
        try:
            kind, index = tokens[0], int(tokens[1])
            fields = {
                key: int(value)
                for key, value in (t.split("=", 1) for t in tokens[2:])
            }
        except (IndexError, ValueError):
            errors.append(f"line {line_number}: cannot parse '{line}'")
            continue

        if kind == "frame":
            frames.append(_Frame(index, fields))
        elif kind == "partition" and frames:
            frames[-1].partitions.append((index, fields))
        else:
            errors.append(f"line {line_number}: unexpected '{line}'")
    return frames, errors


def _check_frame(frame: _Frame, expected: FeedbackExpectations) -> List[str]:
    errors = []
    fields = frame.fields

    status = fields.get("status")
    if status != QUERY_STATUS_COMPLETE:
        errors.append(f"status is {status}, expected {QUERY_STATUS_COMPLETE}")
    if fields.get("bs_size", 0) <= 0:
        errors.append(f"bs_size is {fields.get('bs_size')}, expected > 0")

    if expected.picture:
        errors.extend(_check_qp(fields, expected.codec))
    if expected.pixel_count or expected.skipped_pixel_count:
        errors.extend(_check_pixel_counts(fields, expected))
    if expected.per_partition:
        errors.extend(_check_partitions(frame, expected))
    return errors


def _check_qp(fields: Dict[str, int], codec: str) -> List[str]:
    errors = []
    # The encoder only requests min/max QP where the device supports them.
    if "avgqp" not in fields:
        errors.append("avgqp is missing")

    if codec in QP_RANGE:
        low, high = QP_RANGE[codec]
        for name in ("minqp", "avgqp", "maxqp"):
            value = fields.get(name)
            if value is not None and not low <= value <= high:
                errors.append(f"{name} {value} is outside [{low}, {high}]")

    ordered = [(name, fields[name])
               for name in ("minqp", "avgqp", "maxqp") if name in fields]
    for (name, value), (next_name, next_value) in zip(ordered, ordered[1:]):
        if value > next_value:
            errors.append(
                f"{name} {value} is greater than {next_name} {next_value}")
    return errors


def _align_up(value: int) -> int:
    alignment = CODED_EXTENT_ALIGNMENT
    return (value + alignment - 1) // alignment * alignment


def _check_pixel_counts(fields: Dict[str, int],
                        expected: FeedbackExpectations) -> List[str]:
    errors = []
    names = []
    if expected.pixel_count:
        names += ["intra", "inter"]
    if expected.skipped_pixel_count:
        names.append("skipped")

    max_pixels = _align_up(expected.width) * _align_up(expected.height)
    for name in names:
        value = fields.get(name)
        if value is None:
            errors.append(f"{name} pixel count is missing")
        elif value < 0 or (max_pixels and value > max_pixels):
            errors.append(
                f"{name} pixel count {value} is outside [0, {max_pixels}]")

    # AV1 implementations may leave skipped pixels out of both counts.
    if (expected.pixel_count and "intra" in fields and "inter" in fields
            and fields["intra"] + fields["inter"]
            + fields.get("skipped", 0) == 0):
        errors.append("no pixel was reported")
    return errors


def _check_partitions(frame: _Frame,
                      expected: FeedbackExpectations) -> List[str]:
    count = frame.fields.get("pic_partition_count")
    if count is None:
        return ["pic_partition_count is missing"]
    if count < 1:
        return [f"pic_partition_count is {count}, expected >= 1"]

    errors = []
    if (expected.slices is not None and expected.codec in SLICE_CODECS
            and count != expected.slices):
        errors.append(f"pic_partition_count is {count}, "
                      f"expected {expected.slices} slices")

    reported = min(count, expected.max_partition_entries)
    if not 1 <= len(frame.partitions) <= reported:
        errors.append(f"{len(frame.partitions)} partition entries, "
                      f"expected between 1 and {reported}")

    bs_offset = frame.fields.get("bs_offset", 0)
    bs_end = bs_offset + frame.fields.get("bs_size", 0)
    next_offset = None
    for position, (index, fields) in enumerate(frame.partitions):
        if index != position:
            errors.append(f"partition {index} is at position {position}")
        status = fields.get("status", QUERY_STATUS_COMPLETE)
        if status != QUERY_STATUS_COMPLETE:
            errors.append(f"partition {index}: status is {status}, "
                          f"expected {QUERY_STATUS_COMPLETE}")
        size = fields.get("size", 0)
        offset = fields.get("offset", 0)
        if size <= 0:
            errors.append(f"partition {index}: size is {size}, expected > 0")
        if next_offset is not None and offset < next_offset:
            errors.append(f"partition {index}: offset {offset} overlaps "
                          f"the previous partition ending at {next_offset}")
        if offset < bs_offset or offset + size > bs_end:
            errors.append(f"partition {index}: ends at {offset + size}, "
                          f"outside the frame range [{bs_offset}, {bs_end}]")
        next_offset = offset + size
    return errors
