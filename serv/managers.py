from typing import Optional

from fastapi import WebSocket

from .models import Player, Message, MsgTypes, MONEY_DEFAULT, ClientIdT, RoomIdT


class ConnectionManager:
    def __init__(self):
        self.ws_dict: dict[ClientIdT, WebSocket] = {}
        self.client_room_check: dict[ClientIdT, RoomIdT] = {}
        # self.rooms: dict[RoomIdT, list[ClientIdT]] = {}
        self.players: list[Player] = []

    async def connect(self, websocket: WebSocket, client_id: ClientIdT):
        await websocket.accept()
        self.ws_dict.update({client_id: websocket})
        await self.send_personal_message(self.available_rooms_msg, client_id)

    async def disconnect(self, client_id: ClientIdT):
        print(f'DISCONNECT {client_id}')
        del self.ws_dict[client_id]
        if room_id := await self.disconnect_from_room(client_id):
            await self.send_room_updates(room_id)

    def get_player_by_id(self, client_id: ClientIdT):
        user_list = list(filter(lambda x: x.client_id == client_id, self.players))
        if not len(user_list):
            return
        return user_list[0]

    def get_player_by_username(self, username: str, room_id: RoomIdT):
        user_list = list(filter(lambda x: x.username == username and x.room_id == room_id, self.players))
        if not len(user_list):
            return
        return user_list[0]

    @property
    def available_rooms(self):
        return set(filter(lambda x: x, map(lambda x: x.room_id, self.players)))

    @property
    def available_rooms_msg(self):
        msg = Message()
        msg.msg_type = MsgTypes.available_rooms.value
        msg.rooms = self.available_rooms
        return msg

    async def check_room(self, client_id: ClientIdT, room_id: RoomIdT = None):
        self.client_room_check.update({client_id: room_id})
        if room_id:
            await self.send_personal_message(self.room_info_msg(room_id), client_id)

    async def connect_to_room(self, client_id: ClientIdT, username: str, room_id: RoomIdT, just_listen: bool = False):
        await self.disconnect_from_room(client_id)
        if just_listen:
            await self.check_room(client_id, room_id)
            return True
        root_user = False
        if room_id not in self.available_rooms:
            root_user = True
        if players := list(filter(lambda x: x.room_id == room_id and x.username == username, self.players)):
            player = players[0]
            if player.client_id:
                return False
            i = self.players.index(player)
            self.players[i].client_id = client_id
        else:
            self.players.append(
                Player(username=username, room_id=room_id, client_id=client_id, money=MONEY_DEFAULT, admin=root_user))
        # self.rooms.update({room_id: [*self.rooms.get(room_id, []), client_id]})
        await self.send_all_without_room(self.available_rooms_msg)
        await self.send_room_updates(room_id)
        return True

    async def disconnect_from_room(self, client_id: ClientIdT):
        res = self.client_room_check.get(client_id)
        if res:
            await self.check_room(client_id)
        if players := list(filter(lambda x: x.client_id == client_id and x.room_id, self.players)):
            player = players[0]
            room_id: int = player.room_id
            i = self.players.index(player)
            self.players[i].client_id = None
            # self.rooms.update({room_id: list(filter(lambda x: x != client_id, self.rooms.get("room_id", [])))})
            await self.send_all_without_room(self.available_rooms_msg)
            await self.send_room_updates(room_id)
            return room_id
        return res if res else False

    def players_in_room(self, room_id: RoomIdT = None):
        return list(filter(lambda x: x and (not room_id or x.room_id == room_id), self.players))

    def clients_without_room(self):
        players_in_room = list(filter(lambda x: x, map(lambda x: x.client_id, self.players_in_room())))
        return list(filter(lambda x: x not in players_in_room, self.ws_dict.keys()))

    def clients_in_room(self, room_id: RoomIdT):
        return list(map(lambda x: x[0], filter(lambda x: x[1] == room_id, self.client_room_check.items())))

    def room_info_msg(self, room_id: RoomIdT):
        msg = Message()
        msg.msg_type = MsgTypes.update_room.value
        msg.players = self.players_in_room(room_id)
        return msg

    async def send_room_updates(self, room_id: RoomIdT):
        await self.send_to_room(self.room_info_msg(room_id), room_id)

    async def request_processing(self, client_id: ClientIdT, message_raw: str):
        message: Message = Message.parse_raw(message_raw)
        response = Message()
        without_response = False
        if message.msg_type == MsgTypes.connect_to_room.value:
            if await self.connect_to_room(client_id, message.username, message.room_id):
                response.msg_type = MsgTypes.connected_to_room.value
                response.room_id = message.room_id
            else:
                response.msg_type = MsgTypes.error.value
                response.text = 'Этот пользователь уже в комнате'
        elif message.msg_type == MsgTypes.disconnect_from_room.value:
            if await self.disconnect_from_room(client_id):
                response.msg_type = MsgTypes.disconnected_from_room.value
            else:
                response.msg_type = MsgTypes.error.value
                response.text = 'Вы ещё не в комнате'
        elif message.msg_type == MsgTypes.connect_to_room_for_listen.value:
            await self.connect_to_room(client_id, message.username, message.room_id, True)
            response.msg_type = MsgTypes.connected_to_room_for_listen.value
            response.room_id = message.room_id
        elif message.msg_type == MsgTypes.user2user_money.value:
            if message.amount <= 0:
                response.msg_type = 'error'
                response.text = 'Сумма меньше или равна нулю'
                await self.send_personal_message(response, client_id)
            player_from = self.get_player_by_id(client_id)
            without_response = True
            if not player_from:
                response.msg_type = 'error'
                response.text = 'Вы не находитесь в комнате'
                await self.send_personal_message(response, client_id)
            elif player_from.money < message.amount:
                response.msg_type = 'error'
                response.text = 'У Вас недостаточно средств'
                await self.send_personal_message(response, client_id)
            elif not player_from.room_id:
                response.msg_type = 'error'
                response.text = 'Игрок не находится в комнате'
                await self.send_personal_message(response, client_id)
            player_to = self.get_player_by_username(message.to_username, player_from.room_id)
            if not player_to:
                response.msg_type = 'error'
                response.text = 'Игрок получатель не найден'
                await self.send_personal_message(response, client_id)
            i_from = self.players.index(player_from)
            i_to = self.players.index(player_to)
            self.players[i_from].money -= message.amount
            self.players[i_to].money += message.amount
            await self.send_room_updates(player_from.room_id)
        elif message.msg_type == MsgTypes.bank2user_money.value:
            player_from = self.get_player_by_id(client_id)
            without_response = True
            if not player_from:
                response.msg_type = 'error'
                response.text = 'Вы не находитесь в комнате'
                await self.send_personal_message(response, client_id)
            elif not player_from.admin:
                response.msg_type = 'error'
                response.text = 'Вы не являетесь банком комнаты'
                await self.send_personal_message(response, client_id)
            elif not player_from.room_id:
                response.msg_type = 'error'
                response.text = 'Игрок не находится в комнате'
                await self.send_personal_message(response, client_id)
            player_to = self.get_player_by_username(message.to_username, player_from.room_id)
            if not player_to:
                response.msg_type = 'error'
                response.text = 'Игрок получатель не найден'
                await self.send_personal_message(response, client_id)
            i_to = self.players.index(player_to)
            self.players[i_to].money += message.amount
            await self.send_room_updates(player_from.room_id)
        elif message.msg_type == MsgTypes.user2bank_money.value:
            if message.amount <= 0:
                response.msg_type = 'error'
                response.text = 'Сумма меньше или равна нулю'
                await self.send_personal_message(response, client_id)
            player_from = self.get_player_by_id(client_id)
            without_response = True
            if not player_from:
                response.msg_type = 'error'
                response.text = 'Вы не находитесь в комнате'
                await self.send_personal_message(response, client_id)
            elif player_from.money < message.amount:
                response.msg_type = 'error'
                response.text = 'У Вас недостаточно средств'
                await self.send_personal_message(response, client_id)
            elif not player_from.room_id:
                response.msg_type = 'error'
                response.text = 'Игрок не находится в комнате'
                await self.send_personal_message(response, client_id)
            i_from = self.players.index(player_from)
            self.players[i_from].money -= message.amount
            await self.send_room_updates(player_from.room_id)
        else:
            response.msg_type = 'undefined_message'
        if not without_response:
            await self.send_personal_message(response, client_id)

    async def send_personal_message(self, message: Message, client_id: int):
        data = message.json(exclude_defaults=True, by_alias=True)
        websocket = self.ws_dict[client_id]
        print(f'SEND TO {client_id} data: {data}')
        await websocket.send_text(data)

    async def send_to_room(self, message: Message, room_id: RoomIdT):
        for client_id in set(map(lambda x: x.client_id,
                                 filter(lambda x: x.client_id, self.players_in_room(room_id)))) | set(
            self.clients_in_room(
                room_id)):
            if client_id:
                await self.send_personal_message(message, client_id)

    async def send_all_without_room(self, message: Message):
        for client_id in self.clients_without_room():
            if client_id:
                await self.send_personal_message(message, client_id)

    async def broadcast(self, message: str):
        for connection in self.ws_dict.values():
            await connection.send_text(message)


manager = ConnectionManager()
