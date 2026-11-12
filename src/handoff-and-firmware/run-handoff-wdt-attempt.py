"""Use the fixed wait diagnostic with the pinned r3 adapter and host guards."""
import importlib.util
from pathlib import Path
from golden_handoff_wdt_profile import QEMU, QEMU_SHA, SCRIPT_NAME, HELPER_NAME, SCRIPT_SHA, HELPER_SHA, BOOT_ARGS

base = Path(__file__).parent
spec = importlib.util.spec_from_file_location('full_runner', base / 'run-full-attempt.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
if SCRIPT_SHA is None or HELPER_SHA is None:
    raise SystemExit('Root-service wait diagnostic is not admitted')
if runner.digest(base / SCRIPT_NAME) != SCRIPT_SHA or runner.digest(base / HELPER_NAME) != HELPER_SHA:
    raise SystemExit('Admitted wait-diagnostic source changed')
runner.QEMU, runner.QEMU_SHA = QEMU, QEMU_SHA
runner.HANDOFF_SCRIPT_NAME, runner.ADT_HELPER_NAME = SCRIPT_NAME, HELPER_NAME
runner.PRESERVE_EXISTING_BOOT_ARGS = True
runner.DEFAULT_HANDOFF_PC = runner.REQUIRED_HANDOFF_PC = 0xe0a00000
runner.REQUESTED_BOOT_ARGS = BOOT_ARGS
raise SystemExit(runner.main())
