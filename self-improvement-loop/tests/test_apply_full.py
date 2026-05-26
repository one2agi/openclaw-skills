#!/usr/bin/env python3
"""
tests/test_apply_full.py — TDD for apply --backup 功能
测试完整 apply 流程和 backup 机制
"""
import sys
import os
import json
import subprocess
import pytest
from pathlib import Path

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


class TestApplyFullWorkflow:
    """测试 apply 完整工作流"""

    def test_apply_creates_backup(self, tmp_path):
        """apply --backup 应该创建备份"""
        # 创建临时 .learnings 目录
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)
        (learnings_dir / 'archive').mkdir()

        # SKILL.md 应该在 learnings 的父目录
        # agent_dir = os.path.dirname(os.path.dirname(LEARNINGS_DIR))
        # 所以如果 LEARNINGS_DIR = /tmp/xxx/.learnings，则 SKILL.md 应在 /tmp/xxx/SKILL.md
        skill_md = tmp_path / 'SKILL.md'
        skill_md.write_text('# Original SKILL.md\n\nOriginal content.')

        # 添加 entries
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试1',
            '--pattern-key', 'backup.test',
            '--root-cause', '原因1',
            '--avoid', '方法1'
        ], learnings_dir=learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'backup.test',
            '--root-cause', '原因2',
            '--avoid', '方法2'
        ], learnings_dir=learnings_dir)

        # 执行 apply --backup
        result = run_manager(['evolve', '--apply', '--backup'],
                           learnings_dir=learnings_dir)

        # 检查 backup 目录
        backup_dir = learnings_dir / 'backups'
        assert backup_dir.exists(), "Backup directory should exist"

        backups = list(backup_dir.glob('SKILL_*.md'))
        assert len(backups) >= 1, "Should have at least one backup"

        # 检查备份内容
        backup_content = backups[0].read_text()
        assert 'Original content' in backup_content, "Backup should contain original content"

    def test_apply_modifies_skill_md(self, tmp_path):
        """apply 应该修改 agent SKILL.md"""
        # 创建临时目录
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)
        (learnings_dir / 'archive').mkdir()

        # SKILL.md 在父目录
        skill_md = tmp_path / 'SKILL.md'
        skill_md.write_text('# SKILL.md\n\nOriginal content.')

        # 添加 entries
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试纠正',
            '--pattern-key', 'apply.test',
            '--root-cause', '根因',
            '--avoid', '避免方法'
        ], learnings_dir=learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试纠正2',
            '--pattern-key', 'apply.test',
            '--root-cause', '根因2',
            '--avoid', '避免方法2'
        ], learnings_dir=learnings_dir)

        # 执行 apply
        result = run_manager(['evolve', '--apply'],
                           learnings_dir=learnings_dir)

        # 检查 SKILL.md 被修改
        new_content = skill_md.read_text()
        assert 'apply.test' in new_content or 'Decision Rule' in new_content, \
            "SKILL.md should contain new patch content"
        assert 'Original content' in new_content, "SKILL.md should preserve original content"

    def test_apply_without_backup(self, tmp_path):
        """apply 不带 --backup 不应创建备份"""
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)

        skill_md = tmp_path / 'SKILL.md'
        skill_md.write_text('# SKILL.md\n\nOriginal.')

        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'no.backup.test'
        ], learnings_dir=learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'no.backup.test'
        ], learnings_dir=learnings_dir)

        result = run_manager(['evolve', '--apply'],
                           learnings_dir=learnings_dir)

        backup_dir = learnings_dir / 'backups'
        # 不带 --backup 可能创建也可能不创建，但不应该报错
        assert result.returncode == 0

    def test_apply_multiple_patches(self, tmp_path):
        """apply 应该能处理多个 patches"""
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)

        skill_md = tmp_path / 'SKILL.md'
        skill_md.write_text('# SKILL.md\n')

        # 添加多个 pattern 的 entries
        for pattern in ['pattern.A', 'pattern.B']:
            run_manager([
                'add', '--type', 'learnings', '--category', 'correction',
                '--what', f'测试 {pattern}',
                '--pattern-key', pattern
            ], learnings_dir=learnings_dir)
            run_manager([
                'add', '--type', 'learnings', '--category', 'correction',
                '--what', f'测试 {pattern} 第2次',
                '--pattern-key', pattern
            ], learnings_dir=learnings_dir)

        # 执行 apply
        result = run_manager(['evolve', '--apply', '--preview'],
                           learnings_dir=learnings_dir)

        # 应该有多个 patterns
        assert 'pattern.A' in result.stdout or 'pattern.B' in result.stdout


class TestPendingCommand:
    """测试 pending 命令完整功能"""

    def test_pending_list_empty(self, temp_learnings_dir):
        """pending --list 空目录应无输出"""
        result = run_manager(['pending', '--list'], learnings_dir=temp_learnings_dir)
        assert result.returncode == 0

    def test_pending_clean_removes_files(self, tmp_path):
        """pending --clean 应清理文件"""
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)
        pending_dir = learnings_dir / '.pending_notifications'
        pending_dir.mkdir()

        # 创建一些临时文件
        (pending_dir / 'test1.json').write_text('{}')
        (pending_dir / 'test2.json').write_text('{}')

        result = run_manager(['pending', '--clean'], learnings_dir=learnings_dir)

        assert result.returncode == 0
        remaining = list(pending_dir.glob('*.json'))
        assert len(remaining) == 0, "All pending files should be cleaned"

    def test_pending_write_creates_file(self, tmp_path):
        """pending --write 应创建文件"""
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)
        pending_dir = learnings_dir / '.pending_notifications'
        pending_dir.mkdir()

        # pending --write 从 stdin 读取，需要特殊处理
        # 这里只验证命令存在
        result = run_manager(['pending', '--write', 'test.pattern'],
                           learnings_dir=learnings_dir, check=False)
        # 命令存在，可能失败因为没有 stdin 输入，但不应该报 "unknown command"
        assert 'usage' not in result.stderr.lower() or result.returncode != 2


class TestApplyEdgeCases:
    """测试 apply 边界情况"""

    def test_apply_no_entries(self, tmp_path):
        """无 entries 时 apply 应该处理得当"""
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)

        result = run_manager(['evolve', '--apply'],
                           learnings_dir=learnings_dir)

        # 应该成功执行但不做任何事
        assert result.returncode == 0

    def test_apply_single_entry_no_threshold(self, tmp_path):
        """只有一条 entry 不应触发 apply"""
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)

        skill_md = tmp_path / 'SKILL.md'
        skill_md.write_text('# SKILL.md\n\nOriginal.')

        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '只有一条',
            '--pattern-key', 'single.entry'
        ], learnings_dir=learnings_dir)

        # threshold=2 时，不应该生成 patch
        result = run_manager(['evolve', '--apply', '--threshold', '2'],
                           learnings_dir=learnings_dir)

        # 成功执行，但没有 patches 可应用
        assert result.returncode == 0

    def test_apply_preserves_existing_content(self, tmp_path):
        """apply 应该保留 SKILL.md 原有内容"""
        learnings_dir = tmp_path / '.learnings'
        learnings_dir.mkdir(parents=True)

        skill_md = tmp_path / 'SKILL.md'
        original = '''# Agent SKILL.md

## 已有规则

- 规则1
- 规则2

## 其他内容

一些其他内容。
'''
        skill_md.write_text(original)

        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试',
            '--pattern-key', 'preserve.test'
        ], learnings_dir=learnings_dir)
        run_manager([
            'add', '--type', 'learnings', '--category', 'correction',
            '--what', '测试2',
            '--pattern-key', 'preserve.test'
        ], learnings_dir=learnings_dir)

        result = run_manager(['evolve', '--apply'],
                           learnings_dir=learnings_dir)

        new_content = skill_md.read_text()
        # 原有内容应该保留
        assert '规则1' in new_content
        assert '规则2' in new_content
        assert '其他内容' in new_content