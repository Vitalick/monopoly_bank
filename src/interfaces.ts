/* tslint:disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface Message {
  msgType?: string;
  roomId?: number;
  username?: string;
  toUsername?: number;
  players?: Player[];
  freePlayers?: Player[];
  rooms?: number[];
  amount?: number;
  text?: string;
}
export interface Player {
  roomId?: number;
  username: string;
  money?: number;
}
