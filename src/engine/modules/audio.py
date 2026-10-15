import array
from pathlib import Path

import pygame


class Mixer:
    """
        Singleton owner of music playback.

        Wraps ``pygame.mixer.music`` so the rest of the engine has one place to
        load a song, play it, seek it and read an amplitude envelope from it.
        The mixer never decides *when* playback should jump: callers hand it a
        target position in seconds and :meth:`follow` locks playback to it,
        which is what keeps the editor timeline and the music in sync.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        self.path: Path | None = None
        self.length = 0.0
        self.paused = False
        self.volume = 1.0
        self.waveform: list[float] = []
        self.waveform_resolution = 500

    # Internal
    def _init_hardware(self, frequency=44100, size=-16, channels=2, buffer=512):
        """Open the audio device if it is not open yet.\n
            :param frequency: Playback sample rate in hertz
            :type frequency: int
            :param size: Sample size, negative for signed samples
            :type size: int
            :param channels: Number of output channels
            :type channels: int
            :param buffer: Mix buffer size, smaller means lower latency
            :type buffer: int
        """
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency, size, channels, buffer)

    def _analyse(self, path: Path):
        """Build the downsampled amplitude envelope used by timelines.\n
            :param path: Audio file to read
            :type path: Path
        """
        self.waveform = []

        try:
            sound = pygame.mixer.Sound(str(path))
            channels = max(1, (pygame.mixer.get_init() or (0, 0, 2))[2])
            samples = array.array('h')
            samples.frombytes(sound.get_raw())

            frames = len(samples) // channels
            window = max(1, frames // self.waveform_resolution)
            self.waveform = [
                self._window_peak(samples, frame, window, channels)
                for frame in range(0, frames, window)
            ][:self.waveform_resolution]

            del sound, samples

        except Exception:
            self.waveform = []

    def _window_peak(self, samples, frame, window, channels) -> float:
        """Peak absolute amplitude of one window, normalised to 0..1.\n
            :param samples: Interleaved sample buffer
            :type samples: array
            :param frame: First frame of the window
            :type frame: int
            :param window: Window length in frames
            :type window: int
            :param channels: Samples per frame
            :type channels: int
            :return: Peak amplitude between 0 and 1
            :rtype: float
        """
        start = frame * channels
        chunk = samples[start:start + window * channels:channels]

        if not chunk:
            return 0.0

        return max(max(chunk), -min(chunk)) / 32768

    # Query
    def get_length(self) -> float:
        """Duration of the loaded song in seconds, 0 when nothing is loaded."""
        return self.length

    def get_position(self) -> float:
        """Current playback head in seconds."""
        return pygame.mixer.music.get_pos() / 1000

    def get_waveform(self, points: int) -> list[float]:
        """Sample the amplitude envelope at ``points`` evenly spaced columns.\n
            :param points: How many amplitudes to return
            :type points: int
            :return: Normalised amplitudes between 0 and 1
            :rtype: list
        """
        if not self.waveform:
            return [0.0] * points

        count = len(self.waveform)
        step = count / points

        return [
            self.waveform[min(count - 1, int(index * step))]
            for index in range(points)
        ]

    def is_playing(self) -> bool:
        """Whether the song is currently sounding."""
        return bool(pygame.mixer.music.get_busy()) and not self.paused

    def has_song(self) -> bool:
        """Whether a song is loaded and ready."""
        return self.path is not None and self.length > 0

    # Playback
    def load(self, path: str | Path) -> bool:
        """Load a song, analyse its envelope and reset playback state.\n
            :param path: Audio file to load
            :type path: str | Path
            :return: Whether the file loaded successfully
            :rtype: bool
        """
        self._init_hardware()

        file = Path(path)
        if not file.exists():
            return False

        try:
            pygame.mixer.music.load(str(file))
        except pygame.error:
            return False

        self.path = file
        self.paused = False
        self.length = float(pygame.mixer.music.get_length())

        self._analyse(file)

        return True

    def play(self, start=0.0):
        """Start playback, optionally partway into the song.\n
            :param start: Position to start from, in seconds
            :type start: float
        """
        if not self.has_song():
            return

        self._init_hardware()

        self.paused = False
        pygame.mixer.music.play(0, min(max(start, 0.0), self.length))

    def seek(self, position: float):
        """Jump the playback head to ``position`` seconds.\n
            :param position: Position inside the song, in seconds
            :type position: float
        """
        if not self.has_song():
            return

        pygame.mixer.music.set_pos(min(max(position, 0.0), self.length))

    def follow(self, target: float, tolerance=0.12):
        """Lock playback to ``target`` seconds, seeking only when it drifts.\n
            Playback is started from ``target`` when it is stopped so a seeked
            editor timeline keeps its place instead of restarting the song.

            :param target: Desired playback position, in seconds
            :type target: float
            :param tolerance: Drift allowed before a seek is issued
            :type tolerance: float
        """
        if not self.has_song():
            return

        position = min(max(target, 0.0), self.length)

        if self.length - position < 0.05:
            self.stop()
        elif not self.is_playing():
            self.play(start=position)
        elif abs(self.get_position() - position) > tolerance:
            self.seek(position)

    def pause(self):
        """Pause playback, keeping the current position."""
        if not pygame.mixer.music.get_busy():
            return

        pygame.mixer.music.pause()
        self.paused = True

    def unpause(self):
        """Resume playback after a pause."""
        if not pygame.mixer.music.get_busy():
            return

        self.paused = False
        pygame.mixer.music.unpause()

    def stop(self):
        """Stop playback and rewind the playback head."""
        pygame.mixer.music.stop()
        self.paused = False

    def set_volume(self, volume: float):
        """Set the output volume.\n
            :param volume: Volume between 0 and 1
            :type volume: float
        """
        self.volume = min(max(volume, 0.0), 1.0)
        pygame.mixer.music.set_volume(self.volume)


mixer = Mixer()


def get_mixer() -> Mixer:
    """Return the global :class:`Mixer` instance."""
    return mixer


__all__ = [
    'Mixer',
    'mixer',
    'get_mixer',
]
