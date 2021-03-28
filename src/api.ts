/* tslint:disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type MsgTypes =
  | "error"
  | "available_rooms"
  | "update_room"
  | "connect_to_room"
  | "connect_to_room_for_listen"
  | "connected_to_room"
  | "connected_to_room_for_listen"
  | "disconnect_from_room"
  | "disconnect_from_room_for_listen"
  | "disconnected_from_room"
  | "disconnected_from_room_for_listen"
  | "user2user_money"
  | "user2bank_money"
  | "bank2user_money"
  | "undefined_message";

export interface Message {
  msgType?: MsgTypes & string;
  roomId?: number;
  username?: string;
  toUsername?: string;
  players?: Player[];
  rooms?: number[];
  amount?: number;
  text?: string;
  [k: string]: unknown;
}
export interface Player {
  roomId?: number;
  clientId?: number;
  username: string;
  money: number;
  admin?: boolean;
  [k: string]: unknown;
}
