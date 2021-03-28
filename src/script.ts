import { Message } from './interfaces'

const clientId:number = Date.now()
document.querySelector('#ws-id').textContent = clientId.toString()
const ws:WebSocket = new WebSocket(`ws://localhost:8000/ws/${clientId}`)

ws.onmessage = function (event) {
  const messages = document.getElementById('messages')
  const message = document.createElement('li')
  const msgObj: Message = JSON.parse(event.data)
  const content = document.createTextNode(msgObj.msgType)
  message.appendChild(content)
  messages.appendChild(message)
}

// function sendMessage (event) {
//   const input = document.getElementById('messageText')
//   ws.send(input.value)
//   input.value = ''
//   event.preventDefault()
// }
