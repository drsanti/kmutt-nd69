from google.protobuf.message import Message

class Vector3(Message):
    x: float
    y: float
    z: float

class Imu(Message):
    timestamp_ns: int
    frame_id: str
    acceleration: Vector3
    angular_velocity: Vector3
