import sys, runpy
sys.path.insert(0, "recognizer")
import dice
calls = []
orig = dice._pip_found
def wrap(*a, **k):
    calls.append(1); return orig(*a, **k)
dice._pip_found = wrap
sys.argv = ["evaluate.py"] + sys.argv[1:]
try:
    runpy.run_path("recognizer/evaluate.py", run_name="__main__")
finally:
    print("_pip_found calls:", len(calls))
