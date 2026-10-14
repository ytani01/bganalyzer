"""Read with the same SIMD code on every machine of a kind (TODO-035, TODO-046).

OpenCV, NumPy and OpenBLAS pick their code by the CPU at load time. On x86_64, AVX-512 machines
read some samples 1-4 points differently from AVX2 ones (GitHub Actions gets a different CPU each
run), so cap them at AVX2. On aarch64, cap at plain NEON (ASIMD): the Raspberry Pi 4 has nothing
more, the Pi 5 and GitHub's arm64 runners add dot product, half floats and more.

Import this before cv2 and numpy (it only sets environment variables, and only for features the
CPU has: OpenCV warns when asked to disable one it lacks). Already loaded libraries are not changed.
"""
import os
import platform


def _cpu_flags() -> set:
    try:
        with open("/proc/cpuinfo") as f:
            return {w for line in f if line.lower().startswith(("flags", "features")) for w in line.split(":", 1)[1].split()}
    except OSError:
        return set()


def caps() -> dict:
    """The environment variables that cap this machine's SIMD (empty when there is nothing to cap)."""
    flags, machine = _cpu_flags(), platform.machine().lower()
    if machine in ("x86_64", "amd64") and "avx512f" in flags:
        return {"OPENCV_CPU_DISABLE": "AVX512-SKX",
                "NPY_DISABLE_CPU_FEATURES": "X86_V4 AVX512_ICL AVX512_SPR",
                "OPENBLAS_CORETYPE": "Haswell"}
    if machine in ("aarch64", "arm64"):
        cv = [name for name, flag in (("NEON_DOTPROD", "asimddp"), ("NEON_FP16", "asimdhp"), ("NEON_BF16", "bf16"))
              if flag in flags]
        npy = [name for name, flag in (("ASIMDHP", "asimdhp"), ("ASIMDDP", "asimddp"), ("ASIMDFHM", "asimdfhm"),
                                       ("SVE", "sve")) if flag in flags]
        env = {}
        if cv:
            env["OPENCV_CPU_DISABLE"] = ",".join(cv)
        if npy:
            env["NPY_DISABLE_CPU_FEATURES"] = " ".join(npy)
        if flags & {"sve", "asimddp"}:
            env["OPENBLAS_CORETYPE"] = "ARMV8"
        return env
    return {}


def describe() -> str:
    """What the libraries ended up using (for logs)."""
    import cv2
    return f"{platform.machine()} opencv[{cv2.getCPUFeaturesLine()}] caps={caps()}"


for _var, _value in caps().items():
    os.environ.setdefault(_var, _value)
