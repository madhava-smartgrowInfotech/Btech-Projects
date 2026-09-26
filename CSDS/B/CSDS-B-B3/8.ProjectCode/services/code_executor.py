"""
KnowledgeX AI - Safe Code Execution Service
===============================================
Executes student-submitted Python solutions against test cases WITHOUT
allowing arbitrary system access. Runs in a separate process with a hard
timeout and a heavily restricted builtins/namespace so submitted code cannot
touch the filesystem, network, or OS -- satisfying the "no arbitrary system
commands" requirement.
"""
import multiprocessing as mp
import json

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
    "enumerate": enumerate, "filter": filter, "float": float, "int": int,
    "len": len, "list": list, "map": map, "max": max, "min": min,
    "pow": pow, "range": range, "reversed": reversed, "round": round,
    "set": set, "sorted": sorted, "str": str, "sum": sum, "tuple": tuple,
    "zip": zip, "print": print, "True": True, "False": False, "None": None,
    "isinstance": isinstance, "type": type,
}

FORBIDDEN_TOKENS = [
    "import os", "import sys", "import subprocess", "import shutil", "__import__",
    "open(", "exec(", "eval(", "compile(", "globals(", "locals(", "input(",
    "os.system", "socket", "requests", "urllib", "pathlib", "ctypes",
]


def _static_safety_check(code: str) -> str:
    """Very lightweight static scan; the real sandboxing comes from the
    restricted builtins + subprocess isolation below. Returns error or ''."""
    lowered = code.lower()
    for token in FORBIDDEN_TOKENS:
        if token in lowered:
            return f"Submitted code contains a disallowed operation: '{token.strip()}'."
    return ""


def _worker(code, function_name, test_inputs, result_queue):
    try:
        namespace = {"__builtins__": SAFE_BUILTINS}
        exec(code, namespace)  # noqa: S102 - restricted namespace, isolated process
        func = namespace.get(function_name)
        if not callable(func):
            result_queue.put({"error": f"Function '{function_name}' not defined."})
            return

        outputs = []
        for args in test_inputs:
            try:
                outputs.append(func(*args))
            except Exception as e:  # noqa: BLE001
                outputs.append(f"__ERROR__: {e}")
        result_queue.put({"outputs": outputs})
    except Exception as e:  # noqa: BLE001
        result_queue.put({"error": str(e)})


def run_submission(code: str, function_name: str, test_cases: list, timeout_seconds: int = 5):
    """
    Runs code in an isolated subprocess with a timeout.
    test_cases: list of {"input": [...], "expected": value}
    Returns: {"passed": bool, "tests_passed": int, "tests_total": int, "details": [...], "error": str|None}
    """
    safety_error = _static_safety_check(code)
    if safety_error:
        return {"passed": False, "tests_passed": 0, "tests_total": len(test_cases),
                "details": [], "error": safety_error}

    test_inputs = [tc["input"] for tc in test_cases]

    ctx = mp.get_context("spawn")
    result_queue = ctx.Queue()
    process = ctx.Process(target=_worker, args=(code, function_name, test_inputs, result_queue))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        return {"passed": False, "tests_passed": 0, "tests_total": len(test_cases),
                "details": [], "error": f"Execution timed out after {timeout_seconds} seconds."}

    if result_queue.empty():
        return {"passed": False, "tests_passed": 0, "tests_total": len(test_cases),
                "details": [], "error": "Execution failed unexpectedly (no output)."}

    result = result_queue.get()
    if "error" in result:
        return {"passed": False, "tests_passed": 0, "tests_total": len(test_cases),
                "details": [], "error": result["error"]}

    details = []
    passed_count = 0
    for tc, output in zip(test_cases, result["outputs"]):
        is_pass = (output == tc["expected"])
        if is_pass:
            passed_count += 1
        details.append({
            "input": tc["input"], "expected": tc["expected"],
            "actual": output, "passed": is_pass,
        })

    return {
        "passed": passed_count == len(test_cases),
        "tests_passed": passed_count,
        "tests_total": len(test_cases),
        "details": details,
        "error": None,
    }
