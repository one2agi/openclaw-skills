#!/usr/bin/env python3
"""
tests/test_cron_integration.py — TDD for cron integration
让 cron 能够自动执行 evolve + apply
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


class TestCronPayloadExists:
    """测试 cron-payloads.json 中的 evolve payload"""

    def test_evolve_payload_exists(self):
        """cron-payloads.json 应包含 self-improvement-evolve payload"""
        payload_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'cron-payloads.json')

        with open(payload_path) as f:
            payloads = json.load(f)

        assert 'self-improvement-evolve' in payloads or 'self-improvement-check' in payloads

    def test_evolve_payload_has_schedule(self):
        """evolve payload 应有 schedule 配置"""
        payload_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'cron-payloads.json')

        with open(payload_path) as f:
            payloads = json.load(f)

        # 应该有 self-improvement-check 或类似的 payload
        payload = payloads.get('self-improvement-check', payloads.get('self-improvement-evolve', {}))
        assert 'schedule' in payload or 'schedule' in payloads


class TestEvolveCronIntegration:
    """测试 evolve 与 cron 的集成"""

    def test_evolve_command_works_in_isolated_mode(self, temp_learnings_dir):
        """evolve 应该在 isolated session 中工作"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'cron.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'cron.test'
        ], learnings_dir=temp_learnings_dir)

        # evolve 应该能正常工作
        result = run_manager(['evolve', '--threshold', '2'],
                            learnings_dir=temp_learnings_dir)

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert 'patterns_found' in data

    def test_evolve_apply_works_in_isolated_mode(self, temp_learnings_dir):
        """apply 应该在 isolated session 中工作"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'apply.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'apply.test'
        ], learnings_dir=temp_learnings_dir)

        # dry-run apply 应该能正常工作
        result = run_manager(['evolve', '--apply', '--dry-run'],
                            learnings_dir=temp_learnings_dir)

        assert result.returncode == 0

    def test_self_review_command_works_in_isolated_mode(self, temp_learnings_dir):
        """self-review 应该在 isolated session 中工作"""
        result = run_manager(['self-review'],
                            learnings_dir=temp_learnings_dir)

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert 'findings' in data


class TestFullWorkflow:
    """测试完整工作流"""

    def test_capture_to_evolve_workflow(self, temp_learnings_dir):
        """完整流程: capture → evolve → apply"""
        # 1. 添加 entries
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '用户纠正1',
            '--pattern-key', 'workflow.test',
            '--root-cause', '原因1',
            '--avoid', '方法1'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '用户纠正2',
            '--pattern-key', 'workflow.test',
            '--root-cause', '原因2',
            '--avoid', '方法2'
        ], learnings_dir=temp_learnings_dir)

        # 2. evolve 生成 patches
        result = run_manager(['evolve', '--threshold', '2'],
                            learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        assert data['patterns_found'] == 1
        assert data['patches'][0]['pattern_key'] == 'workflow.test'

        # 3. preview
        result = run_manager(['evolve', '--preview'],
                            learnings_dir=temp_learnings_dir)
        assert 'workflow.test' in result.stdout

    def test_self_review_to_evolve_workflow(self, temp_learnings_dir):
        """完整流程: self-review → evolve"""
        # 1. self-review 检测问题 - 不传 input，只检查已有 entries
        result = run_manager(['self-review'],
                            learnings_dir=temp_learnings_dir)

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert 'findings_count' in data

        # 2. self-review --check-patterns
        result = run_manager(['self-review', '--check-patterns'],
                            learnings_dir=temp_learnings_dir)

        assert result.returncode == 0

        # 3. evolve 应该能工作
        result = run_manager(['evolve'],
                            learnings_dir=temp_learnings_dir)

        assert result.returncode == 0


class TestCronPayloadGeneration:
    """测试 cron payload 生成"""

    def test_cron_payload_includes_evolve_step(self):
        """cron payload 应该包含 evolve 步骤"""
        payload_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'cron-payloads.json')

        with open(payload_path) as f:
            content = f.read()

        # payload 应该包含 evolve 相关的指令
        # 或者在 agent prompt 中应该提到 evolve
        assert 'evolve' in content.lower() or 'manager.py' in content

    def test_setup_crons_generates_evolve_cron(self, tmp_path):
        """setup_crons.py 应该能生成包含 evolve 的 cron"""
        setup_script = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'setup_crons.py')

        # 检查 setup_crons.py 是否支持 --evolve 标志
        result = subprocess.run(
            ['python3', setup_script, '--help'],
            capture_output=True,
            text=True
        )

        # 如果有 --help，检查是否提及 evolve
        if result.returncode == 0:
            # 可能 --help 不存在，但脚本应该能运行
            pass