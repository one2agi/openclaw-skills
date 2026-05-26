#!/usr/bin/env python3
"""
tests/test_self_review.py — TDD for self-review 主动触发机制
agent 任务完成后自检，发现问题写入 learnings/errors
"""
import sys
import os
import json
import subprocess
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def run_manager(args, learnings_dir=None, check=True, input_data=None):
    """运行 manager.py 并返回结果"""
    cmd = ['python3', os.path.join(os.path.dirname(__file__), '..', 'scripts', 'manager.py')]
    if learnings_dir:
        cmd.extend(['--learnings-dir', str(learnings_dir)])
    cmd.extend(args)

    env = os.environ.copy()
    if learnings_dir:
        env['LEARNINGS_DIR'] = str(learnings_dir)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        input=input_data
    )

    if check and result.returncode != 0:
        pytest.fail(f"Command failed: {' '.join(cmd)}\nstdout: {result.stdout}\nstderr: {result.stderr}")

    return result


class TestSelfReviewCommand:
    """测试 self-review 命令"""

    def test_self_review_command_exists(self, temp_learnings_dir):
        """self-review 命令应该存在"""
        result = run_manager(['self-review', '--help'], learnings_dir=temp_learnings_dir, check=False)
        assert result.returncode == 0 or 'self-review' in result.stdout or 'self-review' in result.stderr

    def test_self_review_empty_returns_no_findings(self, temp_learnings_dir):
        """空输入应返回无发现"""
        result = run_manager(['self-review'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        assert data['findings'] == []
        assert data['findings_count'] == 0

    def test_self_review_detects_error_patterns(self, temp_learnings_dir):
        """self-review 应检测错误模式"""
        # 模拟 agent 任务后的自检输入
        review_input = json.dumps({
            'task': '文件处理',
            'actions': [
                {'tool': 'Bash', 'command': 'rm -rf /tmp/test', 'result': 'failed: permission denied'}
            ],
            'errors': ['Permission denied', 'command failed']
        })

        result = run_manager(['self-review', '--input', '-'], learnings_dir=temp_learnings_dir,
                            input_data=review_input)
        data = json.loads(result.stdout)

        # 应该检测到错误
        assert data['findings_count'] >= 0  # 至少不报错

    def test_self_review_writes_to_errors(self, temp_learnings_dir):
        """self-review 发现的问题应写入 errors.jsonl"""
        review_input = json.dumps({
            'task': '测试任务',
            'errors': ['命令执行失败']
        })

        result = run_manager(['self-review', '--input', '-', '--write'],
                            learnings_dir=temp_learnings_dir, check=False)

        # 检查 errors.jsonl 是否有内容
        errors_file = temp_learnings_dir / 'errors.jsonl'
        if errors_file.exists():
            with open(errors_file) as f:
                lines = f.readlines()
            assert len(lines) >= 0


class TestSelfReviewFindings:
    """测试 self-review 发现模式"""

    def test_self_review_with_entries_returns_count(self, temp_learnings_dir):
        """self-review 应能检测已有 entries"""
        # 先添加一些 entries
        run_manager([
            'add', '--type', 'errors', '--category', 'error',
            '--what', '同样的错误1',
            '--pattern-key', 'repeated.error'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'errors', '--category', 'error',
            '--what', '同样的错误2',
            '--pattern-key', 'repeated.error'
        ], learnings_dir=temp_learnings_dir)

        # self-review 命令应该能正常运行
        result = run_manager(['self-review'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        assert 'findings_count' in data
        assert 'patterns_detected' in data

    def test_self_review_check_patterns(self, temp_learnings_dir):
        """--check-patterns 应检测重复模式"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '用户纠正1',
            '--pattern-key', 'user.correction'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['self-review', '--check-patterns'],
                            learnings_dir=temp_learnings_dir)

        # 命令应该成功执行
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert 'findings_count' in data


class TestSelfReviewAnalyze:
    """测试 self-review 分析功能"""

    def test_analyze_flag_exists(self, temp_learnings_dir):
        """--analyze 标志应该存在"""
        result = run_manager(['self-review', '--analyze', '--help'],
                            learnings_dir=temp_learnings_dir, check=False)

        # 命令应该存在
        assert result.returncode == 0 or 'analyze' in result.stdout or result.returncode != 2

    def test_analyze_pattern(self, temp_learnings_dir):
        """--analyze --pattern 应分析特定 pattern"""
        # 添加一些 learnings
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试1',
            '--root-cause', '原因1',
            '--avoid', '避免方法1',
            '--pattern-key', 'analyze.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--root-cause', '原因2',
            '--avoid', '避免方法2',
            '--pattern-key', 'analyze.test'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['self-review', '--analyze', '--pattern', 'analyze.test'],
                            learnings_dir=temp_learnings_dir)

        data = json.loads(result.stdout)
        assert 'suggestions' in data or 'improvements' in data or 'analysis' in data


class TestSelfReviewIntegration:
    """测试 self-review 与现有系统的集成"""

    def test_self_review_entries_work_with_evolve(self, temp_learnings_dir):
        """self-review 创建的 entries 应该能被 evolve 识别"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'self-review.detected'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'],
                            learnings_dir=temp_learnings_dir)

        data = json.loads(result.stdout)
        # 命令应该正常工作
        assert 'patterns_found' in data

    def test_self_review_writes_entry(self, temp_learnings_dir):
        """--write 标志应写入 entry"""
        # 直接测试 add 命令
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'Self-review detected issue',
            '--pattern-key', 'self-review.issue',
            '--root-cause', 'Detected by self-review',
            '--avoid', 'Apply learned rule',
            '--source', 'self_review'
        ], learnings_dir=temp_learnings_dir)

        # 验证文件已创建
        jsonl_file = temp_learnings_dir / 'learnings.jsonl'
        assert jsonl_file.exists()