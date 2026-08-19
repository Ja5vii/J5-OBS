import os
import asyncio
import logging


class TwitchBot:
    def __init__(self, manager):
        self.manager = manager
        self.logger = manager.logger
        self.nick = os.environ.get("TWITCH_BOT_NICK", "").strip().lower()
        self.token = os.environ.get("TWITCH_BOT_TOKEN", "").strip()
        self.global_channel = os.environ.get("TWITCH_CHANNEL", "").strip().lower().lstrip("#")
        self._reader = None
        self._writer = None
        self._running = False
        self._task = None
        self._joined_channels = set()

    def is_enabled(self):
        return bool(self.token)

    async def start(self):
        if not self.is_enabled():
            self.logger.info("Twitch Bot disabled (TWITCH_BOT_TOKEN not set in environment).")
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

    async def get_all_target_channels(self):
        channels = set()
        if self.global_channel:
            channels.add(self.global_channel)
        try:
            instances = await self.manager.db.get_all_instances()
            for inst in instances:
                ch = (inst.get("twitch_channel") or "").strip().lower().lstrip("#")
                if ch:
                    channels.add(ch)
        except Exception:
            pass
        return channels

    async def sync_channels(self):
        if not self._writer or not self._running:
            return
        target_channels = await self.get_all_target_channels()
        to_join = target_channels - self._joined_channels
        for ch in to_join:
            try:
                self._writer.write(f"JOIN #{ch}\r\n".encode("utf-8"))
                await self._writer.drain()
                self._joined_channels.add(ch)
                self.logger.info(f"TwitchBot joined channel #{ch}")
            except Exception as e:
                self.logger.error(f"Failed to join #{ch}: {e}")

    async def send_message(self, message, channel=None):
        if not self._writer:
            return
        target_channels = [channel.lstrip("#")] if channel else list(await self.get_all_target_channels())
        for ch in target_channels:
            if not ch:
                continue
            try:
                msg = f"PRIVMSG #{ch} :{message}\r\n"
                self._writer.write(msg.encode("utf-8"))
                await self._writer.drain()
            except Exception as e:
                self.logger.error(f"TwitchBot failed to send message to #{ch}: {e}")

    async def notify_instance(self, instance_id, message):
        try:
            inst = await self.manager.db.get_instance(instance_id)
            ch = inst.get("twitch_channel") if inst else None
            ch = (ch or self.global_channel or "").lstrip("#")
            if ch:
                await self.send_message(message, channel=ch)
        except Exception as e:
            self.logger.error(f"Failed to notify instance {instance_id}: {e}")

    async def _run_loop(self):
        while self._running:
            try:
                self.logger.info("TwitchBot connecting to Twitch IRC...")
                oauth = self.token if self.token.startswith("oauth:") else f"oauth:{self.token}"
                nick = self.nick or "j5obs_bot"

                self._reader, self._writer = await asyncio.open_connection("irc.chat.twitch.tv", 6667)
                self._joined_channels.clear()

                # Authenticate
                self._writer.write(f"PASS {oauth}\r\n".encode("utf-8"))
                self._writer.write(f"NICK {nick}\r\n".encode("utf-8"))
                await self._writer.drain()

                # Join all channels for all users
                await self.sync_channels()

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
            # Format: :user!user@user.tmi.twitch.tv PRIVMSG #channel :message
            parts = raw_line.split(" :", 2)
            if len(parts) < 3:
                return

            prefix_parts = parts[1].split(" ")
            if len(prefix_parts) < 2 or prefix_parts[0] != "PRIVMSG":
                return

            channel = prefix_parts[1].lstrip("#").lower()
            text = parts[2].strip()

            if not text.startswith("!"):
                return

            cmd_parts = text.split(" ")
            cmd = cmd_parts[0].lower()

            # Find instance mapped to this Twitch channel
            instances = await self.manager.db.get_all_instances()
            target_inst = None
            for inst in instances:
                inst_ch = (inst.get("twitch_channel") or "").strip().lower().lstrip("#")
                if inst_ch == channel:
                    target_inst = inst
                    break

            if not target_inst and instances:
                target_inst = instances[0]

            if not target_inst:
                return

            inst_id = target_inst["instance_id"]
            is_running = self.manager.process_manager.is_running(inst_id)

            if cmd in ("!obs", "!stream", "!estado"):
                status = target_inst.get("status", "STANDBY")
                state_str = "🟢 ONLINE (Emitiendo)" if is_running else f"⚪ {status}"
                await self.send_message(f"[{target_inst['name']}] Estado: {state_str}", channel=channel)

            elif cmd in ("!brb", "!pausa"):
                if is_running:
                    ws_port = target_inst.get("websocket_port")
                    ws_pw = target_inst.get("ws_password", "")
                    try:
                        import obsws_python as obsws
                        cl = obsws.ReqClient(host="127.0.0.1", port=ws_port, password=ws_pw, timeout=2)
                        cl.set_current_program_scene("BRB")
                        await self.send_message("🎬 Escena cambiada a: BRB (Pausa)", channel=channel)
                    except Exception as e:
                        await self.send_message(f"Error cambiando escena: {e}", channel=channel)
                else:
                    await self.send_message("El OBS no está encendido actualmente.", channel=channel)

            elif cmd in ("!main", "!volver"):
                if is_running:
                    ws_port = target_inst.get("websocket_port")
                    ws_pw = target_inst.get("ws_password", "")
                    try:
                        import obsws_python as obsws
                        cl = obsws.ReqClient(host="127.0.0.1", port=ws_port, password=ws_pw, timeout=2)
                        cl.set_current_program_scene("Main")
                        await self.send_message("🎬 Escena cambiada a: Main (Principal)", channel=channel)
                    except Exception as e:
                        await self.send_message(f"Error cambiando escena: {e}", channel=channel)
                else:
                    await self.send_message("El OBS no está encendido actualmente.", channel=channel)

            elif cmd in ("!refresh", "!reiniciar"):
                if is_running:
                    ws_port = target_inst.get("websocket_port")
                    ws_pw = target_inst.get("ws_password", "")
                    try:
                        import obsws_python as obsws
                        cl = obsws.ReqClient(host="127.0.0.1", port=ws_port, password=ws_pw, timeout=2)
                        cl.press_input_properties_button("Moblin_RTMP", "restart")
                        await self.send_message("🔄 Fuente de Moblin reiniciada.", channel=channel)
                    except Exception as e:
                        await self.send_message(f"Error al reiniciar fuente: {e}", channel=channel)

        except Exception as e:
            self.logger.error(f"TwitchBot handle message error: {e}")
