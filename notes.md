
```shell
curl -H 'Upgrade: websocket' -H "Sec-WebSocket-Key: `openssl rand -base64 16`" -H 'Sec-WebSocket-Version: 13' с -sSv https://ws.ifelse.io
```

curl -H 'Upgrade: websocket' -H "Sec-WebSocket-Key: `openssl rand -base64 16`" -H 'Sec-WebSocket-Version: 13' с -sSv http://localhost:9090


```shell
echo '$1' | nc 127.0.0.1 9090
```