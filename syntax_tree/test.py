import logging
import os
import subprocess
import sys
import unittest
import syntax_tree.testdata.analyse_out as analyse_out
from pathlib import Path




test_dir = "./test"
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
    "templateTest":"a::templateTest"
}
def test_one(file="aa"):
    file_path = f"{test_dir}/{file}"
    log_stdout= f"{file_path}/stdout.txt"
    log_stderr=f"{file_path}/stderr.txt"
    with open(log_stdout,"w") as f:pass
    with open(log_stderr,"w") as f:pass
    main_node = main_node_dict[file] if file in main_node_dict.keys() else file
    try:
        run_command([sys.executable, "-m", "syntax_tree.main", "-i", f"{file_path}/{file}.scade", "-m", f"{main_node}", "-o", f"{file_path}/kcg","-t"],
                log_stdout,log_stderr)
    except Exception as e:
        raise AssertionError("scade编译不通过")
    try:
        #f"{file_path}/{file}.exec < {file_path}/kcg/test_data_{file}_scade.in > {file_path}/{file}_out.txt && "
        #f"cp -r {template_dir}/. {file_path}/kcg && "
        run_command(["wsl", "-d", "ubuntu", "bash", "-c",


                 f"cd {file_path}/kcg && ./kcg_compile.sh && ./{file}.exec"],log_stdout,log_stderr)
    except Exception as e:
        raise AssertionError("c编译不通过")
    c_file_path=f"{file_path}/kcg/test_data_{file}_c_out.txt"
    # lustre_file_path=f"{file_path}/{file}_out.txt"
    # is_ok,reason=analyse_out.anaylyse_and_compare(c_file_path,lustre_file_path)
    # with open(log_stderr,"a") as f:
    #     f.write(reason)
    # if not is_ok:
    #     raise AssertionError(reason)



class CountingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successes = []          # 额外记录通过用例

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(str(test))
forbade_test_set={

}
class MyTestCase(unittest.TestCase):
    passed_subtests = []  # 新增：记录通过的子测试文件名
    failed_subtests = []

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def test_all(self):
        # try:
        #     run_command([sys.executable, "-m", "syntax_tree.Lustre_Complie"],None,None)
        # except Exception as e:
        #     ...
        files = [f for f in os.listdir(test_dir)
                 if os.path.isdir(os.path.join(test_dir, f))]

        for path in files:
            if path in forbade_test_set:continue
            with self.subTest(file=path):
                try:
                    test_one(path)
                    # 如果 test_one 没抛异常，说明通过了
                    MyTestCase.passed_subtests.append(path)
                except Exception as e:
                    MyTestCase.failed_subtests.append(path)
                    self.logger.error(f"{path} failed: {e}")
                    raise  # 让 unittest 记录失败

    def test_one(self,path="templateTest"):
        try:
            test_one(path)
            # 如果 test_one 没抛异常，说明通过了
            MyTestCase.passed_subtests.append(path)
        except Exception as e:
            self.logger.error(f"{path} failed: {e}")
            MyTestCase.failed_subtests.append(path)
            raise  # 让 unittest 记录失败


if __name__ == '__main__':

    suite=unittest.TestSuite()
    suite.addTest(MyTestCase("test_one"))
    runner = unittest.TextTestRunner(resultclass=CountingResult, verbosity=2)
    result = runner.run(suite)

    passed_subtest_count = len(MyTestCase.passed_subtests)


    with open("./test_result.txt", "w") as f:
        f.write('\n===== 统计 =====\n')
        f.write(f'run    : {passed_subtest_count + len(result.failures) + len(result.errors) + len(result.skipped)}\n')
        f.write(f'passed : {passed_subtest_count}\n')
        f.write(f'failed : {len(result.failures)}\n')
        f.write(f'errors : {len(result.errors)}\n')
        f.write('===== 通过的子测试（文件名） =====\n')
        for ok in MyTestCase.passed_subtests:
            f.write(ok + '\n')
        f.write('===== 未通过的子测试（文件名） =====\n')
        for ok in MyTestCase.failed_subtests:
            f.write(ok + '\n')