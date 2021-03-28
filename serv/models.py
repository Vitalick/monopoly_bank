from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() if i else word for i, word in enumerate(string.split('_')))


RoomIdT = int
ClientIdT = int


class MsgTypes(str, Enum):
    error = 'error'
    available_rooms = 'available_rooms'
    update_room = 'update_room'
    connect_to_room = 'connect_to_room'
    connect_to_room_for_listen = 'connect_to_room_for_listen'
    connected_to_room = 'connected_to_room'
    connected_to_room_for_listen = 'connected_to_room_for_listen'
    disconnect_from_room = 'disconnect_from_room'
    disconnect_from_room_for_listen = 'disconnect_from_room_for_listen'
    disconnected_from_room = 'disconnected_from_room'
    disconnected_from_room_for_listen = 'disconnected_from_room_for_listen'
    user2user_money = 'user2user_money'
    user2bank_money = 'user2bank_money'
    bank2user_money = 'bank2user_money'
    undefined_message = 'undefined_message'


class Player(BaseModel):
    room_id: Optional[RoomIdT]
    client_id: Optional[ClientIdT]
    username: str
    money: int
    admin: bool = False

    class Config:
        alias_generator = to_camel
        extra = 'allow'


MONEY_DEFAULT: int = 1500


class Message(BaseModel):
    msg_type: MsgTypes = MsgTypes.undefined_message
    room_id: RoomIdT = None
    username: str = None
    to_username: str = None
    players: list[Player] = []
    rooms: list[RoomIdT] = None
    amount: int = 0
    text: str = ''

    class Config:
        alias_generator = to_camel
        extra = 'allow'
