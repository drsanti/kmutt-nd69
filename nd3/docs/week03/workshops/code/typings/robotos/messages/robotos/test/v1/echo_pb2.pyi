from google.protobuf.message import Message

class EchoRequest(Message):
    text: str
    sequence: int

class EchoResponse(Message):
    text: str
    sequence: int
