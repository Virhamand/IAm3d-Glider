import socket
import csv
import time
from pathlib import Path


PORT = 5005


# -----------------------------
# CSV setup
# -----------------------------

# Save in Downloads folder
downloads = Path.home() / "Downloads"

file_path = downloads / "ground_telemetry.csv"

file = open(
    file_path,
    "w",
    newline=""
)

writer = csv.writer(file)

# Write column names
writer.writerow([
    "sequence",
    "time_s",
    "ax_g",
    "ay_g",
    "az_g",
    "gx_dps",
    "gy_dps",
    "gz_dps",
    "roll_deg",
    "pitch_deg"
])


# -----------------------------
# UDP setup
# -----------------------------

# Create UDP socket
sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

# Listen for telemetry
sock.bind(
    ("0.0.0.0", PORT)
)

# Check for missing signal
sock.settimeout(1.0)


# -----------------------------
# Starting values
# -----------------------------

last_sequence = None

received_packets = 0
lost_packets = 0

last_packet_time = time.monotonic()


# -----------------------------
# Dashboard
# -----------------------------

def display_telemetry(
    values,
    received,
    lost
):

    # Read packet values
    sequence = int(values[0])

    ax = float(values[2])
    ay = float(values[3])
    az = float(values[4])

    gx = float(values[5])
    gy = float(values[6])
    gz = float(values[7])

    roll = float(values[8])
    pitch = float(values[9])

    # Calculate packet loss
    total = received + lost

    if total > 0:
        loss = (lost / total) * 100
    else:
        loss = 0.0

    # Clear terminal
    print(
        "\033[2J\033[H",
        end=""
    )

    print(
        "========== GLIDER TELEMETRY =========="
    )

    print(f"\nSequence: {sequence}")

    print("\nAcceleration")
    print(f"X: {ax:.2f} g")
    print(f"Y: {ay:.2f} g")
    print(f"Z: {az:.2f} g")

    print("\nGyroscope")
    print(f"X: {gx:.2f} deg/s")
    print(f"Y: {gy:.2f} deg/s")
    print(f"Z: {gz:.2f} deg/s")

    print("\nOrientation")
    print(f"Roll:  {roll:.2f} deg")
    print(f"Pitch: {pitch:.2f} deg")

    print("\nLink")
    print("Status: CONNECTED")
    print(f"Received: {received}")
    print(f"Lost: {lost}")
    print(f"Packet Loss: {loss:.2f}%")

    print(
        "\n======================================"
    )


# -----------------------------
# Receiver loop
# -----------------------------

print("Waiting for telemetry...")


try:

    while True:

        try:

            # Receive telemetry
            data, address = sock.recvfrom(1024)

            # Save packet time
            last_packet_time = time.monotonic()


        except socket.timeout:

            # Time since last packet
            missing_time = (
                time.monotonic()
                - last_packet_time
            )

            # Clear terminal
            print(
                "\033[2J\033[H",
                end=""
            )

            print(
                "========== GLIDER TELEMETRY =========="
            )

            print("\nSTATUS: SIGNAL LOST")

            print(
                f"\nLast packet: "
                f"{missing_time:.1f} seconds ago"
            )

            print(
                f"\nReceived: "
                f"{received_packets}"
            )

            print(
                f"Lost: "
                f"{lost_packets}"
            )

            print(
                "\n======================================"
            )

            continue


        # Convert bytes to text
        packet = data.decode("utf-8")

        # Split packet
        values = packet.split(",")


        # Check packet size
        if len(values) != 10:

            print(
                "Bad packet:",
                packet
            )

            continue


        # Read sequence number
        sequence = int(values[0])

        # Count packet
        received_packets += 1


        # -------------------------
        # Packet loss detection
        # -------------------------

        if last_sequence is not None:

            expected = last_sequence + 1

            if sequence > expected:

                # Count missing packets
                lost = sequence - expected

                lost_packets += lost


        # Save sequence
        last_sequence = sequence


        # -------------------------
        # Save telemetry
        # -------------------------

        writer.writerow(values)

        # Save data immediately
        file.flush()


        # -------------------------
        # Update dashboard
        # -------------------------

        display_telemetry(
            values,
            received_packets,
            lost_packets
        )


except KeyboardInterrupt:

    print(
        "\nStopping ground station..."
    )


finally:

    # Calculate packet loss
    total_packets = (
        received_packets
        + lost_packets
    )

    if total_packets > 0:

        loss_percent = (
            lost_packets
            / total_packets
        ) * 100

    else:

        loss_percent = 0.0


    print(
        f"Received: "
        f"{received_packets}"
    )

    print(
        f"Lost: "
        f"{lost_packets}"
    )

    print(
        f"Packet loss: "
        f"{loss_percent:.2f}%"
    )


    # Close everything
    file.close()
    sock.close()

    print(
        f"Telemetry saved to: "
        f"{file_path}"
    )
