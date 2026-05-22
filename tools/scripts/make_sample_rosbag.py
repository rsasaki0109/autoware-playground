#!/usr/bin/env python3
"""Generate a tiny synthetic rosbag2 dataset for smoke / real-path testing.

Usage:
  python3 tools/scripts/make_sample_rosbag.py <output_dir> [--messages N]

The resulting bag contains a small number of std_msgs/String messages on
/chatter. It is large enough for `ros2 bag info` and `ros2 bag play` to
behave normally but small enough to ship in CI when needed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_writer(out_dir: Path):
    import rosbag2_py

    storage_options = rosbag2_py.StorageOptions(uri=str(out_dir), storage_id="sqlite3")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )
    writer = rosbag2_py.SequentialWriter()
    writer.open(storage_options, converter_options)

    try:
        topic = rosbag2_py.TopicMetadata(
            id=0,
            name="/chatter",
            type="std_msgs/msg/String",
            serialization_format="cdr",
        )
    except TypeError:
        # Older rosbag2 (pre-Jazzy) does not accept `id`.
        topic = rosbag2_py.TopicMetadata(
            name="/chatter",
            type="std_msgs/msg/String",
            serialization_format="cdr",
        )
    writer.create_topic(topic)
    return writer


def write_bag(out_dir: Path, *, messages: int = 10) -> None:
    if out_dir.exists():
        raise SystemExit(f"refusing to overwrite existing path: {out_dir}")
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    from rclpy.serialization import serialize_message
    from std_msgs.msg import String

    writer = _build_writer(out_dir)
    for i in range(messages):
        msg = String()
        msg.data = f"hello {i}"
        timestamp_ns = (i + 1) * 100_000_000  # 100 ms apart
        writer.write("/chatter", serialize_message(msg), timestamp_ns)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", help="Directory to write the bag into")
    parser.add_argument(
        "--messages",
        type=int,
        default=10,
        help="Number of /chatter messages to write (default: 10)",
    )
    args = parser.parse_args(argv)
    write_bag(Path(args.output_dir), messages=args.messages)
    print(f"wrote sample rosbag to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
