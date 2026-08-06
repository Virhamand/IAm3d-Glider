def create_packet(
    sequence,
    timestamp,
    ax, ay, az,
    gx, gy, gz,
    roll, pitch
):

    # Create telemetry message
    packet = (
        f"{sequence},"
        f"{timestamp:.3f},"
        f"{ax:.3f},{ay:.3f},{az:.3f},"
        f"{gx:.2f},{gy:.2f},{gz:.2f},"
        f"{roll:.2f},{pitch:.2f}"
    )

    return packet
