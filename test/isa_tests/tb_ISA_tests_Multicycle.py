"""MultiCycle entry point using the shared ISA runner and protocol."""
from functools import partial
import sys

import tb_ISA_tests as shared
from multicycle_adapter import MultiCycleAdapter

ADAPTER = MultiCycleAdapter()
prepare_program = partial(shared.prepare_program, adapter=ADAPTER)
prepare_test = partial(shared.prepare_test, adapter=ADAPTER)
execute_test = partial(shared.execute_test, adapter=ADAPTER)
run_file_result = partial(shared.run_file_result, adapter=ADAPTER)
run_file = partial(shared.run_file, adapter=ADAPTER)
computeAllTests = partial(shared.computeAllTests, adapter=ADAPTER)
runAllTests = partial(shared.runAllTests, adapter=ADAPTER)
main = partial(shared.main, adapter=ADAPTER)

if __name__ == "__main__":
    sys.exit(main())
