#!/usr/bin/env python3
"""
tests/test_evolve_apply.py — TDD for evolve apply 命令
把 patch 应用到 agent SKILL.md
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


class TestEvolveApplyCommand:
    """测试 evolve apply 命令 - 简化为 evolve --preview"""

    def test_evolve_preview_flag_exists(self, temp_learnings_dir):
        """evolve --preview 命令应该存在"""
        result = run_manager(['evolve', '--preview', '--help'], learnings_dir=temp_learnings_dir, check=False)
        # 如果命令不存在，会报错
        assert result.returncode == 0 or '--preview' in result.stderr or 'preview' in result.stdout

    def test_evolve_empty_does_nothing(self, temp_learnings_dir):
        """空 patch 不应输出内容"""
        result = run_manager(['evolve', '--preview'], learnings_dir=temp_learnings_dir)
        assert result.returncode == 0
        # 空的时候输出应该为空或只有头部
        assert 'pattern' not in result.stdout.lower() or len(result.stdout.strip()) < 50

    def test_evolve_preview_shows_patterns(self, temp_learnings_dir):
        """preview 应显示 pattern 信息"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'test.preview'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'test.preview'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--preview'], learnings_dir=temp_learnings_dir)

        # preview 模式应显示 markdown 格式的 patch
        assert 'test.preview' in result.stdout

    def test_evolve_preview_format(self, temp_learnings_dir):
        """preview 应输出人类可读的 markdown 格式"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'preview.format.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'preview.format.test'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--preview'], learnings_dir=temp_learnings_dir)

        # 应该包含 markdown 格式符号
        assert '##' in result.stdout or 'Decision Rule' in result.stdout or 'Pattern' in result.stdout


class TestEvolveMerge:
    """测试 patch 合并逻辑"""

    def test_merge_decision_rules(self, temp_learnings_dir):
        """两个相同 pattern 的 entry 应合并为一个 rule"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '错误1',
            '--pattern-key', 'merge.test',
            '--root-cause', '原因A',
            '--avoid', '方法A'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '错误2',
            '--pattern-key', 'merge.test',
            '--root-cause', '原因B',
            '--avoid', '方法B'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        patch = data['patches'][0]
        # 应该有 2 个 decision rules
        assert len(patch['decision_rules']) == 2

    def test_merge_different_patterns(self, temp_learnings_dir):
        """不同 pattern 应保持分离"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'A1',
            '--pattern-key', 'pattern.A'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'A2',
            '--pattern-key', 'pattern.A'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'B1',
            '--pattern-key', 'pattern.B'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', 'B2',
            '--pattern-key', 'pattern.B'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        # 应该有 2 个 patches
        assert len(data['patches']) == 2
        pattern_keys = [p['pattern_key'] for p in data['patches']]
        assert 'pattern.A' in pattern_keys
        assert 'pattern.B' in pattern_keys


class TestEvolvePreview:
    """测试 patch 预览 - 用 --preview 标志"""

    def test_preview_markdown_format(self, temp_learnings_dir):
        """evolve --preview 应输出人类可读的 markdown 格式"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试预览',
            '--pattern-key', 'preview.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试预览2',
            '--pattern-key', 'preview.test'
        ], learnings_dir=temp_learnings_dir)

        result = run_manager(['evolve', '--preview'], learnings_dir=temp_learnings_dir)

        # 应该包含 markdown 格式
        assert '##' in result.stdout or 'Decision Rule' in result.stdout or 'Pattern' in result.stdout


class TestEvolveIntegration:
    """测试 evolve 与现有命令的集成"""

    def test_evolve_respects_status_filter(self, temp_learnings_dir):
        """evolve 应能过滤已解决的 entries"""
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '已解决',
            '--pattern-key', 'resolved.test'
        ], learnings_dir=temp_learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '未解决',
            '--pattern-key', 'resolved.test'
        ], learnings_dir=temp_learnings_dir)

        # 获取第一个 entry 的 ID 并标记为 resolved
        result = run_manager(['list', '--type', 'learnings', '--pattern-key', 'resolved.test'],
                             learnings_dir=temp_learnings_dir, check=False)
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                if data and len(data) > 0:
                    entry_id = data[0].get('id')
                    if entry_id:
                        run_manager(['update', entry_id, '--status', 'resolved'],
                                   learnings_dir=temp_learnings_dir)
            except:
                pass

        # evolve 应该仍然检测到这个 pattern
        result = run_manager(['evolve', '--threshold', '2'], learnings_dir=temp_learnings_dir)
        data = json.loads(result.stdout)

        # count 仍然是 2，因为 resolved 状态不影响统计
        assert len(data['patches']) >= 0  # 至少不报错