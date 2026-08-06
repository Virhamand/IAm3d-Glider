import socket


class UDPSender:

    def __init__(self, ip, port):

        # Ground station address
        self.address = (ip, port)

        # Create UDP socket
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )


    def send(self, packet):

        # Convert text to bytes
        data = packet.encode("utf-8")

        # Send packet
        self.socket.sendto(
            data,
            self.address
        )


    def close(self):

        # Close socket
        self.socket.close()
