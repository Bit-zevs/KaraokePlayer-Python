from __future__ import annotations

import json

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket


class NetworkKaraokeSync(QObject):
    """Tiny LAN sync for karaoke parties.

    Host sends JSON snapshots: song title, position and playback state.
    Clients with the same songs loaded follow the host.
    """

    state_received = Signal(dict)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._server: QTcpServer | None = None
        self._client: QTcpSocket | None = None
        self._clients: list[QTcpSocket] = []
        self._last_snapshot: dict = {}

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._broadcast_last_snapshot)

    def host(self, port: int = 45454) -> None:
        self.disconnect_sync()

        self._server = QTcpServer(self)
        self._server.newConnection.connect(self._accept_clients)

        if not self._server.listen(QHostAddress.SpecialAddress.Any, port):
            self.error_occurred.emit(
                f"Не удалось запустить сетевую синхронизацию на порту {port}."
            )
            self._server = None
            return

        self._timer.start()
        self.status_changed.emit(f"Сетевой режим: ведущий, порт {port}")

    def join(self, host: str, port: int = 45454) -> None:
        self.disconnect_sync()

        self._client = QTcpSocket(self)
        self._client.readyRead.connect(lambda socket=self._client: self._read_from_socket(socket))
        self._client.connected.connect(
            lambda: self.status_changed.emit(
                f"Сетевой режим: зритель, подключено к {host}:{port}"
            )
        )
        self._client.errorOccurred.connect(
            lambda *_: self.error_occurred.emit("Не удалось подключиться к ведущему.")
        )
        self._client.connectToHost(host, port)

    def set_snapshot(self, snapshot: dict) -> None:
        self._last_snapshot = snapshot
        if self._server is not None:
            self._broadcast_last_snapshot()

    def disconnect_sync(self) -> None:
        self._timer.stop()

        for socket in self._clients:
            socket.disconnectFromHost()
            socket.deleteLater()
        self._clients.clear()

        if self._client is not None:
            self._client.disconnectFromHost()
            self._client.deleteLater()
            self._client = None

        if self._server is not None:
            self._server.close()
            self._server.deleteLater()
            self._server = None

        self.status_changed.emit("Сетевой режим выключен")

    def _accept_clients(self) -> None:
        if self._server is None:
            return

        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            self._clients.append(socket)
            socket.disconnected.connect(lambda socket=socket: self._remove_client(socket))
            self.status_changed.emit(f"Подключился зритель: {socket.peerAddress().toString()}")
            self._send(socket, self._last_snapshot)

    def _remove_client(self, socket: QTcpSocket) -> None:
        if socket in self._clients:
            self._clients.remove(socket)
        socket.deleteLater()

    def _broadcast_last_snapshot(self) -> None:
        if not self._last_snapshot:
            return

        for socket in list(self._clients):
            if socket.state() == QTcpSocket.SocketState.ConnectedState:
                self._send(socket, self._last_snapshot)

    def _send(self, socket: QTcpSocket, payload: dict) -> None:
        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        socket.write(data)
        socket.flush()

    def _read_from_socket(self, socket: QTcpSocket) -> None:
        while socket.canReadLine():
            raw = bytes(socket.readLine()).decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if isinstance(payload, dict):
                self.state_received.emit(payload)