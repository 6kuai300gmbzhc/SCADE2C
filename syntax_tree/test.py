from typing import Optional
import logging
import os
import subprocess
import sys
import time
import unittest
import syntax_tree.testdata.analyse_out as analyse_out
from pathlib import Path





template_dir="./template"
def run_command(command: list,log_path_stdout,log_path_stderr,cwd=".",encoding="utf-8"):
    print(" ".join(command))
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding=encoding
    )
    if log_path_stdout is not None:
        with open(log_path_stdout,"a",encoding="utf-8") as f:
            f.write(result.stdout+"\n")
    if log_path_stderr is not None:
        with open(log_path_stderr,"a",encoding="utf-8") as f:
            f.write(result.stderr+"\n")
    if result.stderr:
        raise Exception(result.stderr)


main_node_dict={
    "t":"t4::t",
    "ABC_N":"ABC_N::ABC_N",
    "templateTest":"a::templateTest",
    "Automaton":"Automaton",
    "control_block":"pbtb::pbtb",
    "aircraft_brake_system":"aircraft_brake_system::brake_system",
    "cruise_control":"System::SystemSimul_",
    "Fighter":"World::Fighter::Fighter",
    "RollControl":"RollControl_::RollControl_",
    "flight_control":"FlightControlSimulation::World",
    "pilot":"Pilot::Pilot",
    "wind_model":"main_",


    "test_model2": "test_model2::test_model2",
    "test_model": "test_model::test_model",
    "test_lustre": "test_lustre::test_lustre",
    "test_Int": "test_Int::test_Int",
    "test_clash": "test_clash::test_clash",
    "testPilote": "testPilote::testPilote",
    "testCapt": "testCapt::testCapt",
    "testBoite": "testBoite::testBoite",
    "remplissage": "remplissage::remplissage",
    "polymorphic_pack": "polymorphic_pack::polymorphic_pack",
    "pilote": "pilote::pilote",
    "packs": "packs::packs",
    "packed_cst": "packed_cst::packed_cst",
    "packageTableau": "packageTableau::packageTableau",
    "pack1": "pack1::pack1",
    "pack": "pack::pack",
    "p": "p::p",
    "newpacks": "newpacks::newpacks",
    "complex": "complex::complex",
    "Condact": "Condact::Condact",
    "consensus": "main",
    "dadic": "dadic::dadic",
    "modelInst": "modelInst::modelInst",
    "Xr_test": "Xr_test",
    "test_bool":"test_bool_"
}
class ScadeException(AssertionError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
class CException(AssertionError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


import sys
import os


def create_empty_file(file_path):
    """创建空文件（用于清空日志）"""
    with open(file_path, "w") as f:
        pass


def get_main_node(file, main_node_dict):
    """从字典中获取主节点名称，若不存在则使用文件名"""
    return main_node_dict[file] if file in main_node_dict.keys() else file


def get_exec_name(main_node):
    """从主节点名称中提取可执行文件名"""
    return main_node if "::" not in main_node else main_node.split("::")[-1]


def count_scade_lines(scade_file_path: str) -> int:
    with open(scade_file_path, "rb") as f:
        raw_bytes = f.read()

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw_bytes.decode(encoding)
            return len(text.splitlines())
        except UnicodeDecodeError:
            continue

    return len(raw_bytes.decode("utf-8", errors="ignore").splitlines())


def run_scade_compile(file_path, file, main_node, log_stdout, log_stderr):
    """运行SCADE编译命令，并返回耗时"""
    scade_input = f"{file_path}/{file}.scade"
    output_dir = f"{file_path}/kcg"
    start_time = time.perf_counter()
    try:
        run_command(
            [sys.executable, "-m", "syntax_tree.main",
             "-i", scade_input,
             "-m", main_node,
             "-o", output_dir,
             "-t"],
            log_stdout,
            log_stderr
        )
    except Exception:
        raise
    return round(time.perf_counter() - start_time, 6)


def run_kcg_compile(file_path, log_stdout, log_stderr):
    """运行KCG C代码编译"""
    wsl_command = f"cd {file_path}/kcg && ./kcg_compile.sh"
    run_command(
        ["wsl", "-d", "ubuntu", "bash", "-c", wsl_command],
        log_stdout,
        log_stderr
    )
def run_coverage(file_path, log_stdout, log_stderr):
    """运行覆盖率测试"""
    wsl_command = f"cd {file_path}/kcg && ./kcg_coverage.sh"
    run_command(
        ["wsl", "-d", "ubuntu", "bash", "-c", wsl_command],
        log_stdout,
        log_stderr
    )


def run_executable(file_path, exec_name, log_stdout, log_stderr):
    """运行生成的可执行文件"""
    wsl_command = f"cd {file_path}/kcg && ./{exec_name}.exec"
    run_command(
        ["wsl", "-d", "ubuntu", "bash", "-c", wsl_command],
        log_stdout,
        log_stderr
    )


def run_and_compile(test_dir, file="aa"):
    """主函数：协调各个编译和执行步骤"""
    file_path = f"{test_dir}/{file}"
    log_stdout = f"{file_path}/stdout.txt"
    log_stderr = f"{file_path}/stderr.txt"
    scade_file_path = Path(file_path) / f"{file}.scade"
    line_count = count_scade_lines(str(scade_file_path))

    # 1. 清空日志文件
    create_empty_file(log_stdout)
    create_empty_file(log_stderr)

    # 2. 获取主节点和可执行文件名
    main_node = get_main_node(file, main_node_dict)
    exec_name = get_exec_name(main_node)

    # 3. 运行SCADE编译
    try:
        duration_seconds = run_scade_compile(file_path, file, main_node, log_stdout, log_stderr)
    except Exception as e:
        raise ScadeException("scade编译不通过")

    # 4. 运行KCG C编译
    try:
        run_kcg_compile(file_path, log_stdout, log_stderr)
    except Exception as e:
        raise CException("c编译不通过")

    # 5. 运行生成的可执行文件
    try:
        run_executable(file_path, exec_name, log_stdout, log_stderr)
    except Exception as e:
        raise RuntimeError("可执行文件运行失败")

    return line_count, round(duration_seconds, 6)

def run_and_test_coverage(test_dir, file="aa"):
    file_path = f"{test_dir}/{file}"
    log_stdout = f"{file_path}/stdout.txt"
    log_stderr = f"{file_path}/stderr.txt"
    scade_file_path = Path(file_path) / f"{file}.scade"
    line_count = count_scade_lines(str(scade_file_path))

    # 1. 清空日志文件
    create_empty_file(log_stdout)
    create_empty_file(log_stderr)

    # 2. 获取主节点和可执行文件名
    main_node = get_main_node(file, main_node_dict)
    exec_name = get_exec_name(main_node)

    # 3. 运行SCADE编译
    try:
        duration_seconds = run_scade_compile(file_path, file, main_node, log_stdout, log_stderr)
    except Exception as e:
        raise ScadeException("scade编译不通过")
    try:
        run_coverage(file_path, log_stdout, log_stderr)
    except Exception as e:
        raise ScadeException("可执行文件运行失败")

    return line_count, round(duration_seconds, 6)


class CountingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successes = []          # 额外记录通过用例

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(str(test))
forbade_test_set={
}
forbade_fail_test_set={
}
class MyTestCase(unittest.TestCase):
    passed_subtests = []  # 新增：记录通过的子测试文件名
    failed_subtests = []
    case_metrics = []
    test_dir = "./from_lustre"
    test_fail_dir="./test_fail"
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)



    def test_all_coverage(self):
        files = [f for f in os.listdir(self.test_dir)
                 if os.path.isdir(os.path.join(self.test_dir, f))]

        for path in files:
            if path in forbade_test_set:continue
            with self.subTest(file=path):
                try:
                    line_count, duration_seconds = run_and_test_coverage(self.test_dir, path)
                    MyTestCase.case_metrics.append((path, line_count, duration_seconds))
                    # 如果 test_one 没抛异常，说明通过了
                    MyTestCase.passed_subtests.append(path)
                except Exception as e:
                    MyTestCase.failed_subtests.append(path)
                    self.logger.error(f"{path} failed: {e}")
                    raise  # 让 unittest 记录失败
    def test_all(self):
        # try:
        #     run_command([sys.executable, "-m", "syntax_tree.Lustre_Complie"],None,None)
        # except Exception as e:
        #     ...
        files = [f for f in os.listdir(self.test_dir)
                 if os.path.isdir(os.path.join(self.test_dir, f))]

        for path in files:
            if path in forbade_test_set:continue
            with self.subTest(file=path):
                try:
                    line_count, duration_seconds = run_and_compile(self.test_dir, path)
                    MyTestCase.case_metrics.append((path, line_count, duration_seconds))
                    # 如果 test_one 没抛异常，说明通过了
                    MyTestCase.passed_subtests.append(path)
                except Exception as e:
                    MyTestCase.failed_subtests.append(path)
                    self.logger.error(f"{path} failed: {e}")
                    raise  # 让 unittest 记录失败
    def test_one_coverage(self,path="StateMachine_1"):
        try:
            line_count, duration_seconds = run_and_test_coverage(self.test_dir, path)
            MyTestCase.case_metrics.append((path, line_count, duration_seconds))
            # 如果 test_one 没抛异常，说明通过了
            MyTestCase.passed_subtests.append(path)
        except Exception as e:
            self.logger.error(f"{path} failed: {e}")
            MyTestCase.failed_subtests.append(path)
            raise  # 让 unittest 记录失败
    def test_one(self,path="activate_merge"):
        try:
            line_count, duration_seconds = run_and_compile(self.test_dir, path)
            MyTestCase.case_metrics.append((path, line_count, duration_seconds))
            # 如果 test_one 没抛异常，说明通过了
            MyTestCase.passed_subtests.append(path)
        except Exception as e:
            self.logger.error(f"{path} failed: {e}")
            MyTestCase.failed_subtests.append(path)
            raise  # 让 unittest 记录失败

    def test_fail_one(self,path="aircraft_brake_system"):
        try:
            run_and_compile(self.test_fail_dir, path)
            MyTestCase.failed_subtests.append(path)
            self.logger.error(f"{path} success, hence failed")
            raise
        except ScadeException as e:
            MyTestCase.passed_subtests.append(path)
        except CException as e:
            MyTestCase.failed_subtests.append(path)
            self.logger.error(f"{path} c failed: {e}")
            raise

if __name__ == '__main__':

    suite=unittest.TestSuite()
    suite.addTest(MyTestCase("test_all"))
    # suite.addTest(MyTestCase("test_one"))
    runner = unittest.TextTestRunner(resultclass=CountingResult, verbosity=2)
    result = runner.run(suite)

    passed_subtest_count = len(MyTestCase.passed_subtests)


    with open("./test_result.txt", "w", encoding="utf-8") as f:
        f.write('\n===== 统计 =====\n')
        f.write(f'run    : {passed_subtest_count + len(result.failures) + len(result.errors) + len(result.skipped)}\n')
        f.write(f'passed : {passed_subtest_count}\n')
        f.write(f'failed : {len(result.failures)}\n')
        f.write(f'errors : {len(result.errors)}\n')
        f.write('===== 每个测试用例的 .scade 行数与 SCADE 编译耗时 =====\n')
        for case_name, line_count, duration_seconds in MyTestCase.case_metrics:
            f.write(f'{case_name}: ({line_count}, {duration_seconds:.6f}s)\n')
        f.write('===== 通过的子测试（文件名） =====\n')
        for ok in MyTestCase.passed_subtests:
            f.write(ok + '\n')
        f.write('===== 未通过的子测试（文件名） =====\n')
        for ok in MyTestCase.failed_subtests:
            f.write(ok + '\n')