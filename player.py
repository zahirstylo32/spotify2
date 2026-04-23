"""
player.py — Motor de reproducción (pygame.mixer)
Maneja play/pause/stop/seek/volumen y notifica eventos a la UI
mediante callbacks.
"""
 
import pygame
import threading
import time
 
# Inicializar mixer con buena calidad
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
pygame.mixer.init()
pygame.init()
 
# Evento personalizado que pygame lanza al terminar una pista
SONG_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(SONG_END)
 
 
class Player:
    def __init__(self, on_song_end=None, on_tick=None):
        """
        on_song_end: callable() — llamado cuando termina la canción.
        on_tick:     callable(pos_seg, dur_seg) — llamado cada ~200 ms.
        """
        self._on_song_end = on_song_end
        self._on_tick = on_tick
 
        self._path: str | None = None
        self._duration: float = 0.0
        self._paused: bool = False
        self._playing: bool = False
        self._volume: float = 0.7
        self._seek_offset: float = 0.0   # segundos ya reproducidos antes de un seek
 
        pygame.mixer.music.set_volume(self._volume)
 
        # Hilo de polling para eventos y tick
        self._stop_thread = False
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
 
    # ── Controles ─────────────────────────────────────────────────────────────
 
    def load(self, path: str, duration: float = 0.0):
        """Carga una canción sin reproducirla.
        Usa stop() interno sin disparar el evento SONG_END."""
        # Desregistrar evento temporalmente para que el stop no
        # desencadene otro _on_song_end mientras cargamos la siguiente
        pygame.mixer.music.set_endevent(0)
        pygame.mixer.music.stop()
        self._playing = False
        self._paused = False
        self._seek_offset = 0.0
        self._path = path
        self._duration = duration
        pygame.mixer.music.load(path)
        # Volver a registrar el evento
        pygame.mixer.music.set_endevent(SONG_END)
 
    def play(self):
        if not self._path:
            return
        if self._paused:
            pygame.mixer.music.unpause()
            self._paused = False
        else:
            pygame.mixer.music.play(start=self._seek_offset)
        self._playing = True
 
    def pause(self):
        if self._playing and not self._paused:
            pygame.mixer.music.pause()
            self._paused = True
 
    def stop(self):
        pygame.mixer.music.set_endevent(0)
        pygame.mixer.music.stop()
        pygame.mixer.music.set_endevent(SONG_END)
        self._playing = False
        self._paused = False
        self._seek_offset = 0.0
 
    def seek(self, seconds: float):
        """Salta a la posición indicada en segundos."""
        seconds = max(0.0, min(seconds, self._duration))
        self._seek_offset = seconds
        if self._playing and not self._paused:
            pygame.mixer.music.play(start=seconds)
        else:
            # Carga en pausa: basta con actualizar el offset
            pass
 
    def set_volume(self, vol: float):
        """vol entre 0.0 y 1.0"""
        self._volume = max(0.0, min(1.0, vol))
        pygame.mixer.music.set_volume(self._volume)
 
    @property
    def volume(self) -> float:
        return self._volume
 
    @property
    def is_playing(self) -> bool:
        return self._playing and not self._paused
 
    @property
    def is_paused(self) -> bool:
        return self._paused
 
    def position(self) -> float:
        """Posición actual en segundos."""
        if not self._playing:
            return self._seek_offset
        raw = pygame.mixer.music.get_pos() / 1000.0   # ms → s
        if raw < 0:
            return self._seek_offset
        return self._seek_offset + raw
 
    # ── Hilo interno ──────────────────────────────────────────────────────────
 
    def _poll_loop(self):
        while not self._stop_thread:
            for event in pygame.event.get():
                if event.type == SONG_END and self._playing:
                    self._playing = False
                    self._seek_offset = 0.0
                    if self._on_song_end:
                        self._on_song_end()
 
            if self._playing and not self._paused and self._on_tick:
                pos = self.position()
                self._on_tick(pos, self._duration)
 
            time.sleep(0.2)
 
    def destroy(self):
        self._stop_thread = True
        pygame.mixer.music.stop()
        pygame.mixer.quit()