from __future__ import annotations
from typing import Any, Optional, Callable
import asyncio
import math


class AudioTrack:
    def __init__(self, title: str = "", author: str = "", duration: float = 0,
                 url: str = "", thumbnail: str = "", identifier: str = "", source: str = ""):
        self.title = title
        self.author = author
        self.duration = duration
        self.url = url
        self.thumbnail = thumbnail
        self.identifier = identifier
        self.source = source

    def __repr__(self) -> str:
        return f"AudioTrack({self.title})"


class AudioPlaylist:
    def __init__(self, name: str = "", tracks: list[AudioTrack] = None, url: str = ""):
        self.name = name
        self.tracks = tracks or []
        self.selected_track = self.tracks[0] if self.tracks else None
        self.url = url

    def __repr__(self) -> str:
        return f"AudioPlaylist({self.name}, {len(self.tracks)} tracks)"


class GuildAudioState:
    def __init__(self):
        self.queue: list[AudioTrack] = []
        self.current_track: AudioTrack | None = None
        self.volume: float = 100.0
        self.repeat: bool = False
        self.autoplay: bool = False
        self.pitch: float = 1.0
        self.speed: float = 1.0
        self.rotation: float = 0.0
        self.mono: float = 0.0
        self.voice_client: Any = None
        self.playing: bool = False
        self.paused: bool = False
        self._on_track_end: Callable | None = None

    def build_ffmpeg_options(self) -> tuple[str, str]:
        filters = []
        before = ""
        if self.pitch != 1.0 or self.speed != 1.0:
            tempo = self.speed
            pitch_adjust = math.log2(self.pitch) * 12
            if abs(tempo - 1.0) > 0.01:
                filters.append(f"atempo={tempo}")
            if abs(pitch_adjust) > 0.5:
                filters.append(f"asetrate=44100*{2**(pitch_adjust/12)},atempo=1.0")
        if self.rotation != 0.0:
            filters.append(f"aphaser=in={self.rotation}")
        if self.mono > 0.0:
            filters.append(f"pan=mono|c0={self.mono}*FL+{1-self.mono}*FR")
        vol = self.volume / 100.0
        if vol != 1.0:
            before = f"-filter:a volume={vol}"
        if filters:
            af = ",".join(filters)
            if before:
                before = f"{before},{af}"
            else:
                before = f"-filter:a {af}"
        return before, ""


class AudioManager:
    def __init__(self):
        self.guild_states: dict[int, GuildAudioState] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def get_state(self, guild_id: int) -> GuildAudioState:
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = GuildAudioState()
        return self.guild_states[guild_id]

    def connect(self, guild_id: int, channel) -> None:
        state = self.get_state(guild_id)
        state.voice_client = channel.guild.voice_client

    def disconnect(self, guild_id: int) -> None:
        state = self.get_state(guild_id)
        if state.voice_client and state.voice_client.is_connected():
            state.voice_client.stop()
            asyncio.run_coroutine_threadsafe(state.voice_client.disconnect(), self._loop)
        state.voice_client = None
        state.current_track = None
        state.playing = False
        state.paused = False

    def _after_playback(self, guild_id: int, error=None) -> None:
        state = self.get_state(guild_id)
        if error:
            state.playing = False
            return
        state.playing = False
        state.paused = False
        if state.repeat and state.current_track:
            self._play_next(guild_id, requeue=True)
        else:
            self._play_next(guild_id)

    def _play_next(self, guild_id: int, requeue: bool = False) -> None:
        state = self.get_state(guild_id)
        if requeue and state.current_track:
            state.queue.insert(0, state.current_track)
        if state.queue:
            track = state.queue.pop(0)
            self.play(guild_id, track)
        else:
            state.current_track = None
            if state._on_track_end:
                cb = state._on_track_end
                state._on_track_end = None
                if self._loop:
                    self._loop.call_soon_threadsafe(cb)

    def play(self, guild_id: int, track: AudioTrack) -> None:
        import discord
        state = self.get_state(guild_id)
        if not state.voice_client or not state.voice_client.is_connected():
            return
        state.current_track = track
        state.playing = True
        state.paused = False
        before, _ = state.build_ffmpeg_options()
        try:
            source = discord.FFmpegPCMAudio(track.url, before_options=before or None)
            def after(error=None):
                self._after_playback(guild_id, error)
            state.voice_client.play(source, after=after)
        except Exception:
            state.playing = False
            self._play_next(guild_id)

    def pause(self, guild_id: int) -> None:
        state = self.get_state(guild_id)
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.pause()
            state.paused = True

    def resume(self, guild_id: int) -> None:
        state = self.get_state(guild_id)
        if state.voice_client and state.voice_client.is_paused():
            state.voice_client.resume()
            state.paused = False

    def stop(self, guild_id: int) -> None:
        state = self.get_state(guild_id)
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.stop()
        state.playing = False
        state.paused = False
        state.current_track = None

    def skip(self, guild_id: int) -> AudioTrack | None:
        state = self.get_state(guild_id)
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.stop()
        if state.queue:
            state.current_track = state.queue.pop(0)
            self.play(guild_id, state.current_track)
            return state.current_track
        state.current_track = None
        state.playing = False
        return None

    def add_track(self, guild_id: int, track: AudioTrack) -> None:
        state = self.get_state(guild_id)
        state.queue.append(track)

    def clear_queue(self, guild_id: int) -> None:
        state = self.get_state(guild_id)
        state.queue.clear()

    def remove_track(self, guild_id: int, index: int) -> AudioTrack | None:
        state = self.get_state(guild_id)
        if 0 <= index < len(state.queue):
            return state.queue.pop(index)
        return None

    def set_volume(self, guild_id: int, volume: float) -> None:
        state = self.get_state(guild_id)
        state.volume = max(0, min(1000, volume))
        state.voice_client = None

    def set_repeat(self, guild_id: int, repeat: bool) -> None:
        state = self.get_state(guild_id)
        state.repeat = repeat

    def set_autoplay(self, guild_id: int, autoplay: bool) -> None:
        state = self.get_state(guild_id)
        state.autoplay = autoplay

    def set_pitch(self, guild_id: int, val: float) -> None:
        state = self.get_state(guild_id)
        state.pitch = max(0.5, min(2.0, val))

    def set_speed(self, guild_id: int, val: float) -> None:
        state = self.get_state(guild_id)
        state.speed = max(0.5, min(2.0, val))

    def set_rotation(self, guild_id: int, val: float) -> None:
        state = self.get_state(guild_id)
        state.rotation = val

    def set_mono(self, guild_id: int, val: bool) -> None:
        state = self.get_state(guild_id)
        state.mono = 1.0 if val else 0.0

    def get_tracks_from_source(self, query: str) -> AudioTrack | AudioPlaylist | None:
        if query.startswith("http"):
            title = query.split("/")[-1][:80] if "/" in query else "Track"
            track = AudioTrack(
                title=title,
                author="Unknown",
                duration=0,
                url=query,
                source="url",
            )
            return track
        track = AudioTrack(
            title=query,
            author="Search",
            duration=0,
            source="search",
        )
        return track
