import sys; sys.path.insert(0,'recognizer'); import evaluate
for n in sys.argv[1:]: print(n, evaluate.run(f"samples/{n}.truth.json")[2])
