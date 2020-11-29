const io = require('engine.io-client')
const port = process.env.PORT || 5000;

const socket = io('http://localhost:' + port);
let last;
function send () {
  last = new Date();
  socket.send('ping');
}

socket.on('open', () => {
  send();
});

socket.on('close', () => {
});

socket.on('message', () => {
  const latency = new Date() - last;
  console.log('latency is ' + latency + ' ms');
  setTimeout(send, 1000);
});
