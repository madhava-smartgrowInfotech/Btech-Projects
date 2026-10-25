"""torch must be imported before numpy/pandas on this Windows host or its DLLs fail to initialise (WinError 1114)."""
import torch  # noqa: F401
