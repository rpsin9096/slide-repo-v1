"""FocusGate v3.0 — High-Throughput Performance & Concurrency Subsystem.

Provides zero-copy circular ring buffers and sub-second multi-actor
barrier synchronization primitives.
"""

from core.perf.ring_buffer import AtomicEventRingBuffer
from core.perf.wave_barrier import HighThroughputWaveBarrier, BarrierConvergenceReceipt

__all__ = [
    "AtomicEventRingBuffer",
    "HighThroughputWaveBarrier",
    "BarrierConvergenceReceipt"
]
