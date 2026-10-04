"""Create the diagnostic input sequence used for the first playable map."""

from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python gameplay_smoke.py OUTPUT_IN_BUILD")
    destination = Path(sys.argv[1])
    events: list[tuple[int, int, str]] = []

    def hold(first: int, last: int, buttons: str) -> None:
        events.append((first, last, buttons))

    def pulse(first: int, last_first: int, interval: int) -> None:
        for frame in range(first, last_first + 1, interval):
            hold(frame, frame + 1, "A")

    pulse(1000, 11950, 45)  # Intro, title, menu, Birch, naming.
    hold(12001, 12120, "RIGHT")
    hold(12121, 12280, "DOWN")  # Leave the moving truck.
    pulse(12310, 15000, 45)
    pulse(15020, 17990, 45)
    hold(18001, 18300, "UP")  # Climb to the bedroom.
    pulse(18320, 18980, 45)
    hold(19001, 19025, "LEFT")
    hold(19026, 19048, "UP")  # Face the wall clock.
    pulse(19070, 19490, 35)
    hold(19501, 19505, "UP")  # Choose YES in the clock prompt.
    hold(19530, 19531, "A")
    pulse(19600, 25960, 45)
    hold(26001, 26030, "RIGHT")
    hold(26031, 26055, "UP")  # Return downstairs.
    hold(26056, 26300, "DOWN")
    pulse(26320, 28970, 45)
    hold(29001, 29100, "RIGHT")
    hold(29101, 29300, "DOWN")
    hold(30001, 30014, "LEFT")
    hold(30015, 30100, "DOWN")  # Leave the house after the TV event.

    assert all(left[1] < right[0] for left, right in zip(events, events[1:]))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(f"{first} {last} {buttons}\n" for first, last, buttons in events),
        encoding="ascii",
    )
    print(f"{len(events)} input ranges written to {destination}")


if __name__ == "__main__":
    main()
