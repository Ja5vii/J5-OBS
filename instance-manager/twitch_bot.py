import os
import asyncio
import logging


class TwitchBot:
    def __init__(self, manager):
        self.manager = manager
        self.logger = manager.logger
        self.nick = os.environ.get("TWITCH_BOT_NICK", "").strip().lower()
        self.token = os.environ.get("TWITCH_BOT_TOKEN", "").strip()
        self.channel = os.environ.get("TWITCH_CHANNEL", "").strip().lower().lstrip("#")
        self._reader = None
        self._writer = None
        self._running = False
        self._task = None

    def is_enabled(self):
        return bool(self.token and self.channel)

    async def start(self):
        if not self.is_enabled():
            self.logger.info("Twitch Bot disabled (TWITCH_BOT_TOKEN or TWITCH_CHANNEL not set).")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        self._running = False
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        if self._task and not self._task.done():
            self._task.cancel()

    async def send_message(self, message):
        if not self._writer or not self.channel:
            return
        try:
            msg = f"PRIVMSG #{self.channel} :{message}\r\n"
            self._writer.write(msg.encode("utf-8"))
            await self._writer.drain()
        except Exception as e:
            self.logger.error(f"TwitchBot failed to send message: {e}")

    async def _run_loop(self):
        while self._running:
            try:
                self.logger.info(f"TwitchBot connecting to #{self.channel} as {self.nick or 'justinfan1234'}...")
                oauth = self.token if self.token.startswith("oauth:") else f"oauth:{self.token}"
                nick = self.nick or "justinfan1234"

                self._reader, self._writer = await asyncio.open_connection("irc.chat.twitch.tv", 6667)
                
                # Authenticate
                self._writer.write(f"PASS {oauth}\r\n".encode("utf-8"))
                self._writer.write(f"NICK {nick}\r\n".encode("utf-8"))
                self._writer.write(f"JOIN #{self.channel}\r\n".encode("utf-8"))
                await self._writer.drain()

                self.logger.info(f"TwitchBot joined #{self.channel}")
                
                while self._running:
                    line = await self._reader.readline()
                    if not line:
                        break
                    line_str = line.decode("utf-8", errors="ignore").strip()
                    
                    # Handle Ping
                    if line_str.startswith("PING"):
                        self._writer.write("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                        await self._writer.drain()
                        continue
                    
                    if "PRIVMSG" in line_str:
                        await self._handle_message(line_str)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"TwitchBot error: {e}. Reconnecting in 10s...")
                await asyncio.sleep(10)

    async def _handle_message(self, raw_line):
        try:
            parts = raw_line.split(" :", 2)
            if len(parts) < 3:
                return
            user_part = parts[1].split("!")[0]
            text = parts[2].strip()

            if not text.startswith("!"):
                return

            cmd_parts = text.split(" ")
            cmd = cmd_parts[0].lower()

            instances = await self.manager.db.get_all_instances()
            target_inst = instances[0] if instances else None

            if cmd in ("!obs", "!stream", "!estado"):
                if not target_inst:
                    await self.send_message("No hay instancias de OBS configuradas.")
                    return
                status = target_inst.get("status", "STANDBY")
                is_live = self.manager.process_manager.is_running(target_inst["instance_id"])
                state_str = "?? ONLINE (Emitiendo)" if is_live else f"? {status}"
                await self.send_message(f"OBS [{target_inst['instance_id']}]: {state_str}")

            elif cmd in ("!brb", "!pausa"):
                if target_inst and self.manager.process_manager.is_running(target_inst["instance_id"]):
                    ws_port = target_inst.get("websocket_port")
                    ws_pw = target_inst.get("ws_password", "")
                    try:
                        import obsws_python as obsws
                        cl = obsws.ReqClient(host="127.0.0.1", port=ws_port, password=ws_pw, timeout=2)
                        cl.set_current_program_scene("BRB")
                        await self.send_message("?? Escena cambiada a: BRB")
                    except Exception as e:
                        await self.send_message(f"Error cambiando escena: {e}")

            elif cmd in ("!main", "!volver"):
                if target_inst and self.manager.process_manager.is_running(target_inst["instance_id"]):
                    ws_port = target_inst.get("websocket_port")
                    ws_pw = target_inst.get("ws_password", "")
                    try:
                        import obsws_python as obsws
                        cl = obsws.ReqClient(host="127.0.0.1", port=ws_port, password=ws_pw, timeout=2)
                        cl.set_current_program_scene("Main")
                        await self.send_message("?? Escena cambiada a: Main")
                    except Exception as e:
                        await self.send_message(f"Error cambiando escena: {e}")

        except Exception as e:
            self.logger.error(f"TwitchBot handle message error: {e}")
