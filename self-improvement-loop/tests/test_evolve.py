#!/usr/bin/env python3
"""
tests/test_evolve.py — TDD for manager.py evolve 命令
Red-Green-Refactor 循环
"""
import sys
import os
import json
import subprocess
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def run_manager(args, learnings_dir=None, check=True):
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
        env=env
    )

    if check and result.returncode != 0:
        pytest.fail(f"Command failed: {' '.join(cmd)}\nstdout: {result.stdout}\nstderr: {result.stderr}")

    return result


class TestEvolveCommand:
    """测试 evolve 命令"""

    def test_evolve_exists(self, temp_learnings_dir):
        """evolve 命令应该存在"""
        result = run_manager(['evolve', '--help'], learnings_dir=temp_learnings_dir, check=False)
        # 如果命令不存在，会报 "unknown argument: --help" 或者帮助输出包含 evolve
        assert 'evolve' in result.stdout.lower() or result.returncode != 2

    def test_evolve_empty_returns_no_patch(self, temp_learnings_dir):
        """空 learnings 应返回无 patch"""
        result = run_manager(['evolve'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        assert data['patches'] == []
        assert data['patterns_found'] == 0

    def test_evolve_single_entry_no_patch(self, temp_learnings_dir):
        """只有一条 entry 不应生成 patch (需要 count >= 2)"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '用户纠正了一次',
            '--pattern-key', 'hook.correction.forgot-to-verify'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        # count=1 < threshold=2，不应生成 patch
        assert data['patches'] == []

    def test_evolve_double_entry_generates_patch(self, temp_learnings_dir):
        """两条相同 pattern 的 entry 应生成 patch"""
        # 添加两条相同 pattern_key 的 entry
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '用户纠正: 忘记验证输出',
            '--pattern-key', 'hook.correction.forgot-to-verify',
            '--root-cause', '没有在完成后检查结果',
            '--avoid', '完成后主动验证输出'
        ], learnings_dir=temp_learnings_dir)

        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '用户纠正: 又忘记验证',
            '--pattern-key', 'hook.correction.forgot-to-verify',
            '--root-cause', '没有验证习惯',
            '--avoid', '建立验证检查表'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        assert len(data['patches']) == 1
        patch = data['patches'][0]
        assert patch['pattern_key'] == 'hook.correction.forgot-to-verify'
        assert patch['count'] == 2
        assert 'decision_rules' in patch or 'skill_md' in patch

    def test_evolve_includes_decision_rules(self, temp_learnings_dir):
        """生成的 patch 应包含 decision rules"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试纠正',
            '--pattern-key', 'test.pattern.001'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试纠正2',
            '--pattern-key', 'test.pattern.001'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        patch = data['patches'][0]
        # patch 应该包含可合并为 SKILL.md 的内容
        assert 'content' in patch or 'skill_md' in patch

    def test_evolve_different_patterns_separate_patches(self, temp_learnings_dir):
        """不同 pattern_key 应生成不同 patches"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'pattern A 第1次',
            '--pattern-key', 'pattern.A'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'pattern A 第2次',
            '--pattern-key', 'pattern.A'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'pattern B 第1次',
            '--pattern-key', 'pattern.B'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        # pattern.A 有 2 条 >= threshold，pattern.B 只有 1 条
        assert len(data['patches']) == 1
        assert data['patches'][0]['pattern_key'] == 'pattern.A'

    def test_evolve_threshold_parameter(self, temp_learnings_dir):
        """threshold 参数应过滤结果"""
        # 添加 3 条相同 pattern
        for i in range(3):
            run_manager([
                'add', '--type', 'learnings', '--category', 'correction',
                '--what', f'条目{i}',
                '--pattern-key', 'threshold.test'
            ], learnings_dir=temp_learnings_dir)

        # threshold=3 时，count=3 应该通过
        result = run_manager(['evolve', '--threshold', '3'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert len(data['patches']) == 1

        # threshold=4 时，count=3 不应该通过
        result = run_manager(['evolve', '--threshold', '4'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)
        assert len(data['patches']) == 0

    def test_evolve_includes_entries_for_context(self, temp_learnings_dir):
        """patch 应包含相关 entries 用于上下文分析"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '纠正1',
            '--pattern-key', 'context.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '纠正2',
            '--pattern-key', 'context.test'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        patch = data['patches'][0]
        assert 'entries' in patch or 'entries_count' in patch
        assert patch.get('entries_count', 0) == 2 or len(patch.get('entries', [])) == 2


class TestEvolveOutput:
    """测试 evolve 输出格式"""

    def test_evolve_returns_json(self, temp_learnings_dir):
        """evolve 应返回有效 JSON"""
        result = run_manager(['evolve'], learnings_dir=temp_learnings_dir)

        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert 'patches' in data
        except json.JSONDecodeError:
            pytest.fail(f"Output is not valid JSON: {result.stdout}")

    def test_evolve_patch_has_required_fields(self, temp_learnings_dir):
        """patch 应包含必要字段"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'required.fields.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'required.fields.test'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        patch = data['patches'][0]
        assert 'pattern_key' in patch
        assert 'count' in patch
        assert patch['count'] == 2


class TestEvolveWithErrors:
    """测试 errors.jsonl 的进化"""

    def test_evolve_includes_errors(self, temp_learnings_dir):
        """evolve 应包含 errors.jsonl 中的数据"""
        run_manager([
            'add', '--type', 'errors', '--category', 'error',
            '--what', '命令执行失败',
            '--pattern-key', 'cmd.error.exec'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'errors', '--category', 'error',
            '--what', '命令又失败',
            '--pattern-key', 'cmd.error.exec'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        # errors 的 pattern 也应该被检测到
        pattern_keys = [p['pattern_key'] for p in data['patches']]
        assert 'cmd.error.exec' in pattern_keys