"""
queue.py — Cola de reproducción.
Maneja el orden de las canciones, shuffle y modos de loop.
"""
 
import random
 
LOOP_NONE   = "none"    # sin repetición
LOOP_ONE    = "one"     # repetir canción
LOOP_ALL    = "all"     # repetir lista
 
 
class Queue:
    def __init__(self):
        self._original: list[dict] = []   # lista canónica
        self._order:    list[int]  = []   # índices en el orden actual
        self._pos:      int        = -1   # posición actual en _order
 
        self.shuffle: bool = False
        self.loop:    str  = LOOP_NONE
 
    # ── Carga ─────────────────────────────────────────────────────────────────
 
    def set_songs(self, songs: list[dict], start_index: int = 0):
        """Carga una nueva lista. songs: lista de dicts de DB."""
        self._original = list(songs)
        self._rebuild_order(start_index)
 
    def _rebuild_order(self, start_index: int = 0):
        n = len(self._original)
        if n == 0:
            self._order = []
            self._pos = -1
            return
 
        start_index = max(0, min(start_index, n - 1))
 
        if self.shuffle:
            self._order = list(range(n))
            self._order.remove(start_index)
            random.shuffle(self._order)
            self._order.insert(0, start_index)
            self._pos = 0
        else:
            self._order = list(range(n))
            self._pos = start_index
 
    # ── Navegación ────────────────────────────────────────────────────────────
 
    def current(self) -> dict | None:
        if not self._order or self._pos < 0:
            return None
        return self._original[self._order[self._pos]]
 
    def next(self) -> dict | None:
        if not self._order:
            return None
        if self.loop == LOOP_ONE:
            return self.current()
        next_pos = self._pos + 1
        if next_pos >= len(self._order):
            if self.loop == LOOP_ALL:
                next_pos = 0
            else:
                return None   # fin de lista
        self._pos = next_pos
        return self.current()
 
    def prev(self) -> dict | None:
        if not self._order:
            return None
        if self.loop == LOOP_ONE:
            return self.current()
        prev_pos = self._pos - 1
        if prev_pos < 0:
            if self.loop == LOOP_ALL:
                prev_pos = len(self._order) - 1
            else:
                prev_pos = 0
        self._pos = prev_pos
        return self.current()
 
    def jump_to_song(self, song_id: int) -> dict | None:
        """Salta directamente a la canción con ese id de DB."""
        for i, idx in enumerate(self._order):
            if self._original[idx]["id"] == song_id:
                self._pos = i
                return self.current()
        return None
 
    # ── Shuffle ───────────────────────────────────────────────────────────────
 
    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        # _order[_pos] es el índice real en _original
        start = self._order[self._pos] if self._pos >= 0 and self._order else 0
        self._rebuild_order(start)
        return self.shuffle
 
    def set_shuffle(self, value: bool):
        if value != self.shuffle:
            self.toggle_shuffle()
 
    # ── Loop ──────────────────────────────────────────────────────────────────
 
    def cycle_loop(self) -> str:
        # Cicla solo entre NONE y ONE (LOOP_ALL eliminado de la UI)
        if self.loop == LOOP_NONE:
            self.loop = LOOP_ONE
        else:
            self.loop = LOOP_NONE
        return self.loop
 
    def set_loop(self, mode: str):
        if mode in (LOOP_NONE, LOOP_ONE, LOOP_ALL):
            self.loop = mode
 
    # ── Utilidades ────────────────────────────────────────────────────────────
 
    @property
    def count(self) -> int:
        return len(self._original)
 
    @property
    def pos(self) -> int:
        return self._pos
 
    def all_songs(self) -> list[dict]:
        return [self._original[i] for i in self._order]
