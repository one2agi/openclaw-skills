#!/usr/bin/env python3
"""
manager.py — Self-Improvement Loop v5.0.0
TDD 开发：最小实现
"""
from __future__ import annotations

import os
import sys
import json
import fcntl
import argparse
import datetime
import warnings
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

LEARNINGS_DIR = os.environ.get('LEARNINGS_DIR', os.path.expanduser('~/.openclaw/workspace/.learnings'))
TYPE_TO_PREFIX: Dict[str, str] = {'learnings': 'LRN', 'errors': 'ERR', 'features': 'FEAT'}
PREFIX_TO_TYPE: Dict[str, str] = {v: k for k, v in TYPE_TO_PREFIX.items()}

# 状态常量
class EntryStatus:
    PENDING = 'pending'
    ACTIVE = 'active'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    PROMOTED = 'promoted'

ACTIVE_STATUSES = {EntryStatus.PENDING, EntryStatus.ACTIVE, EntryStatus.IN_PROGRESS}
ARCHIVE_STATUSES = {EntryStatus.RESOLVED, EntryStatus.PROMOTED}


def _not_found(entry_id: str) -> None:
    """打印未找到错误并退出。"""
    print(f"Entry not found: {entry_id}", file=sys.stderr)
    sys.exit(1)


def _find_entry_by_id(entry_id: str) -> Optional[tuple[str, List[Dict[str, Any]], int]]:
    """按 ID 查找 entry，返回 (etype, entries, index) 或 None。"""
    all_entries = _read_all_entries()
    for etype, entries in all_entries.items():
        for i, entry in enumerate(entries):
            if entry['id'] == entry_id:
                return etype, entries, i
    return None


def _lock_file(filepath: str):
    """获取文件锁，返回文件句柄。锁文件位于同目录 .locks/ 下。"""
    lock_dir = os.path.join(os.path.dirname(filepath) or '.', '.locks')
    os.makedirs(lock_dir, exist_ok=True)
    lockfile = os.path.join(lock_dir, f'{os.path.basename(filepath)}.lock')
    try:
        fh = open(lockfile, 'w')
    except PermissionError:
        raise RuntimeError(f"无法创建锁文件: {lockfile}")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    except OSError:
        fh.close()
        raise RuntimeError(f"无法获取锁: {lockfile}")
    return fh


def _unlock_file(fh):
    """释放文件锁并关闭句柄。"""
    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    fh.close()


def _atomic_write(filepath: str, lines: List[str]) -> None:
    """原子写入：先写临时文件，再 rename，确保数据完整性。"""
    tmp = filepath + f'.{os.getpid()}.tmp'
    with open(tmp, 'w') as f:
        f.writelines(lines)
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp, filepath)


def _get_jsonl_path(etype: str) -> str:
    return os.path.join(LEARNINGS_DIR, f'{etype}.jsonl')


def _ensure_dir() -> None:
    """确保学习目录和归档目录存在，必要时创建 JSONL 文件占位。"""
    os.makedirs(LEARNINGS_DIR, exist_ok=True)
    os.makedirs(os.path.join(LEARNINGS_DIR, 'archive'), exist_ok=True)
    for f in ['learnings', 'errors', 'features']:
        p = _get_jsonl_path(f)
        if not os.path.exists(p):
            Path(p).touch()


def _read_jsonl(etype: str) -> List[Dict[str, Any]]:
    """读取指定类型的 JSONL 文件，返回 entry 列表。损坏行会发出警告。"""
    fpath = _get_jsonl_path(etype)
    entries: List[Dict[str, Any]] = []
    if os.path.exists(fpath):
        with open(fpath) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        warnings.warn(f"警告：{fpath}:{line_num} JSON 损坏，已跳过")
    return entries


def _write_jsonl(etype: str, entries: List[Dict[str, Any]]) -> None:
    fpath = _get_jsonl_path(etype)
    fh = _lock_file(fpath)
    lines = [json.dumps(e, ensure_ascii=False) + '\n' for e in entries]
    _atomic_write(fpath, lines)
    _unlock_file(fh)


def _append_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    etype = entry['type']
    fpath = _get_jsonl_path(etype)
    fh = _lock_file(fpath)
    try:
        line = json.dumps(entry, ensure_ascii=False) + '\n'
        with open(fpath, 'a') as f:
            f.write(line)
    finally:
        _unlock_file(fh)
    return entry


def _read_all_entries() -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for etype in ['learnings', 'errors', 'features']:
        result[etype] = _read_jsonl(etype)
    return result


def _generate_id(prefix: str) -> str:
    """生成唯一 ID，格式：{PREFIX}-{YYYYMMDD}-{NNN}。线程安全。"""
    today = datetime.datetime.now().strftime('%Y%m%d')
    fpath = _get_jsonl_path(PREFIX_TO_TYPE.get(prefix, ''))
    fh = _lock_file(fpath)
    count = 0
    if os.path.exists(fpath):
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        e = json.loads(line)
                        if e['id'].startswith(f'{prefix}-{today}'):
                            count += 1
                    except json.JSONDecodeError:
                        pass
    nnn = f'{count + 1:03d}'
    _unlock_file(fh)
    return f'{prefix}-{today}-{nnn}'


# ============== 命令实现 ==============

def cmd_add(args: argparse.Namespace) -> None:
    _ensure_dir()
    if args.json:
        with open(args.json) as f:
            data = json.load(f)
    else:
        data = {
            'type': args.type,
            'category': args.category,
            'pattern_key': args.pattern_key or '',
            'what_happened': args.what,
            'root_cause': getattr(args, 'root_cause', '') or '',
            'how_to_avoid': args.avoid or '',
            'tags': [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else [],
            'source': args.source,
        }

    prefix = TYPE_TO_PREFIX[data['type']]
    data['id'] = _generate_id(prefix)
    data['logged_at'] = datetime.datetime.now().isoformat()
    data['status'] = EntryStatus.PENDING
    data['notified'] = False
    data['notification_count'] = 0
    data['updated_at'] = None

    entry = _append_entry(data)
    if args.json_output:
        print(json.dumps({'success': True, 'entry': entry}, ensure_ascii=False, indent=2))
    else:
        print(f"Added: {entry['id']}")


def cmd_list(args: argparse.Namespace) -> None:
    _ensure_dir()
    all_entries = _read_all_entries()
    for etype, entries in all_entries.items():
        if args.type and etype != args.type:
            continue
        filtered = entries
        if args.status:
            filtered = [e for e in filtered if e.get('status') == args.status]
        if args.pattern_key:
            filtered = [e for e in filtered if args.pattern_key in e.get('pattern_key', '')]
        if args.count_only:
            print(f"{etype}: {len(filtered)}")
            continue
        for entry in filtered:
            ts = entry.get('logged_at', '')[:10]
            status = entry.get('status', 'pending')
            what = entry.get('what_happened', '')[:50]
            print(f"[{entry['id']}] {ts} [{status}] {what}...")


def cmd_get(args: argparse.Namespace) -> None:
    _ensure_dir()
    all_entries = _read_all_entries()
    for entries in all_entries.values():
        for entry in entries:
            if entry['id'] == args.id:
                print(json.dumps(entry, ensure_ascii=False, indent=2))
                return
    _not_found(args.id)


def cmd_update(args: argparse.Namespace) -> None:
    _ensure_dir()
    result = _find_entry_by_id(args.id)
    if result is None:
        _not_found(args.id)
    etype, entries, i = result
    if args.status:
        entries[i]['status'] = args.status
    if args.pattern_key is not None:
        entries[i]['pattern_key'] = args.pattern_key
    entries[i]['updated_at'] = datetime.datetime.now().isoformat()
    _write_jsonl(etype, entries)
    print(json.dumps({'success': True, 'entry': entries[i]}, ensure_ascii=False, indent=2))


def cmd_notify(args: argparse.Namespace) -> None:
    _ensure_dir()
    result = _find_entry_by_id(args.id)
    if result is None:
        _not_found(args.id)
    etype, entries, i = result
    entries[i]['notified'] = True
    entries[i]['notification_count'] = entries[i].get('notification_count', 0) + 1
    entries[i]['updated_at'] = datetime.datetime.now().isoformat()
    _write_jsonl(etype, entries)
    print(json.dumps({'success': True, 'entry': entries[i]}, ensure_ascii=False, indent=2))


def _entry_to_raw_md(entry: Dict[str, Any]) -> str:
    """Render a JSON entry as Markdown for AI analysis."""
    sections = []
    if entry.get('category'):
        sections.append(f"### Category\n{entry.get('category')}")
    sections.append(f"### What Happened\n{entry.get('what_happened', '')}")
    if entry.get('root_cause'):
        sections.append(f"### Root Cause\n{entry.get('root_cause', '')}")
    if entry.get('how_to_avoid'):
        sections.append(f"### How To Avoid\n{entry.get('how_to_avoid', '')}")
    if entry.get('tags'):
        sections.append(f"### Tags\n{', '.join(entry.get('tags', []))}")
    if entry.get('skill_candidate'):
        sections.append(f"### Suggested Skill\n{entry.get('skill_candidate')}")
    return '\n\n'.join(sections)


def cmd_scan(args: argparse.Namespace) -> None:
    _ensure_dir()
    all_entries = _read_all_entries()
    groups: Dict[str, Dict[str, Any]] = {}
    for etype, entries in all_entries.items():
        for entry in entries:
            if entry.get('status') not in ACTIVE_STATUSES:
                continue
            key = entry.get('pattern_key') or entry.get('category', '')
            if not key:
                continue
            if key not in groups:
                groups[key] = {'name': key, 'source': 'pattern_key' if entry.get('pattern_key') else 'category', 'entries': []}
            groups[key]['entries'].append(entry)

    patterns = []
    for name, group in groups.items():
        count = len(group['entries'])
        first = group['entries'][0]
        first['raw_md'] = _entry_to_raw_md(first)
        should_notify = (
            count >= args.threshold and
            (not first.get('notified', False) or first.get('notification_count', 0) < count)
        )
        max_entries = getattr(args, 'max_entries', 10)
        if max_entries == 0:
            max_entries = len(group['entries'])
        for entry in group['entries'][:max_entries]:
            entry['raw_md'] = _entry_to_raw_md(entry)

        patterns.append({
            'name': name, 'count': count, 'threshold': args.threshold,
            'should_notify': should_notify, 'source': group['source'],
            'first_entry': first,
            'entries': group['entries'][:max_entries],
        })

    if args.trigger_only:
        patterns = [p for p in patterns if p['should_notify']]

    print(json.dumps({'patterns': patterns, 'meta': {'threshold': args.threshold, 'scanned_at': datetime.datetime.now().isoformat()}}, ensure_ascii=False, indent=2))


def cmd_archive(args: argparse.Namespace) -> None:
    _ensure_dir()
    all_entries = _read_all_entries()
    today = datetime.datetime.now().strftime('%Y-%m')
    archive_file = os.path.join(LEARNINGS_DIR, 'archive', f'{today}.jsonl')
    os.makedirs(os.path.dirname(archive_file), exist_ok=True)
    total_archived = 0
    for etype, entries in all_entries.items():
        to_archive = [e for e in entries if e.get('status') in ARCHIVE_STATUSES]
        to_keep = [e for e in entries if e.get('status') not in ARCHIVE_STATUSES]
        if to_archive:
            fh = _lock_file(archive_file)
            try:
                with open(archive_file, 'a') as f:
                    for entry in to_archive:
                        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            finally:
                _unlock_file(fh)
            total_archived += len(to_archive)
        if to_keep != entries:
            _write_jsonl(etype, to_keep)
    if args.dry_run:
        print(f"[DRY RUN] Would archive {total_archived} entries to {archive_file}")
    else:
        print(f"Archived {total_archived} entries to {archive_file}")


def cmd_stat(args: argparse.Namespace) -> None:
    _ensure_dir()
    all_entries = _read_all_entries()
    for etype, entries in all_entries.items():
        total = len(entries)
        by_status: Dict[str, int] = {}
        for entry in entries:
            s = entry.get('status', 'unknown')
            by_status[s] = by_status.get(s, 0) + 1
        print(f"\n{etype}: {total} total")
        for s, count in sorted(by_status.items()):
            print(f"  {s}: {count}")


# ============== Evolve 子函数 ==============

def _aggregate_patterns(
    all_entries: Dict[str, List[Dict[str, Any]]],
    threshold: int
) -> Dict[str, Dict[str, Any]]:
    """聚合 entries 按 pattern_key，返回达到阈值的 pattern 数据。"""
    pattern_counts: Dict[str, Dict[str, Any]] = {}
    for etype, entries in all_entries.items():
        for entry in entries:
            pattern_key = entry.get('pattern_key', '')
            if not pattern_key:
                continue
            if pattern_key not in pattern_counts:
                pattern_counts[pattern_key] = {'learnings': [], 'errors': [], 'features': [], 'total': 0}
            pattern_counts[pattern_key][etype].append(entry)
            pattern_counts[pattern_key]['total'] += 1

    # 过滤低于阈值的
    return {pk: data for pk, data in pattern_counts.items() if data['total'] >= threshold}


def _generate_patch(pattern_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """为单个 pattern 生成 patch。"""
    decision_rules = []
    for etype, entries in data.items():
        if etype == 'total':
            continue
        for entry in entries:
            if entry.get('root_cause'):
                decision_rules.append({
                    'type': 'failure_lesson',
                    'source': entry.get('root_cause', ''),
                    'avoid': entry.get('how_to_avoid', ''),
                    'what': entry.get('what_happened', '')[:200],
                    'entry_id': entry.get('id', '')
                })
            elif entry.get('how_to_avoid'):
                decision_rules.append({
                    'type': 'improvement',
                    'action': entry.get('how_to_avoid', ''),
                    'what': entry.get('what_happened', '')[:200],
                    'entry_id': entry.get('id', '')
                })

    skill_md = f"""## Decision Rule: {pattern_key}

**Trigger**: 匹配 pattern `{pattern_key}`

"""
    for rule in decision_rules:
        if rule['type'] == 'failure_lesson':
            skill_md += f"""### 失败教训
- **发生了什么**: {rule['what']}
- **根因**: {rule['source']}
- **如何避免**: {rule['avoid']}

"""

    return {
        'pattern_key': pattern_key,
        'count': data['total'],
        'entries_count': data['total'],
        'decision_rules': decision_rules,
        'skill_md': skill_md.strip(),
    }


def _apply_patches_to_skill(skill_path: str, patches: List[Dict[str, Any]], create_backup: bool) -> None:
    """将 patches 追加到 SKILL.md。"""
    if create_backup:
        backup_dir = os.path.join(LEARNINGS_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if os.path.exists(skill_path):
            backup_path = os.path.join(backup_dir, f'SKILL_{timestamp}.md')
            shutil.copy(skill_path, backup_path)
            print(f"Backup created: {backup_path}")

    existing = ""
    if os.path.exists(skill_path):
        with open(skill_path) as f:
            existing = f.read()

    new_content = existing.rstrip() + "\n\n"
    for patch in patches:
        new_content += f"\n{patch['skill_md']}\n"

    with open(skill_path, 'w') as f:
        f.write(new_content)

    print(f"Applied {len(patches)} patches to {skill_path}")


def cmd_evolve(args: argparse.Namespace) -> None:
    """分析 learnings/errors/features，生成 SKILL.md patches"""
    threshold = args.threshold
    all_entries = _read_all_entries()

    # 聚合 pattern_key 出现次数
    pattern_counts = _aggregate_patterns(all_entries, threshold)

    # 过滤特定 pattern
    if args.pattern:
        pattern_counts = {pk: data for pk, data in pattern_counts.items() if pk == args.pattern}

    # 生成 patches
    patches = [_generate_patch(pk, data) for pk, data in pattern_counts.items()]

    result = {
        'patches': patches,
        'patterns_found': len(patches),
        'threshold': threshold,
    }

    # Preview 模式
    if args.preview:
        for patch in patches:
            print(f"## Pattern: {patch['pattern_key']}")
            print(f"**Count**: {patch['count']}")
            print()
            print(patch['skill_md'])
            print()
            print("---")
            print()
        return

    # Apply 模式
    if args.apply:
        if args.dry_run:
            print("Dry-run: would apply the following patches:")
            for patch in patches:
                print(f"  - {patch['pattern_key']} ({patch['count']} entries)")
            return

        if not patches:
            print("No patches to apply.")
            return

        agent_dir = os.path.dirname(LEARNINGS_DIR)
        skill_path = os.path.join(agent_dir, 'SKILL.md')
        _apply_patches_to_skill(skill_path, patches, args.backup)

        # 标记 entries 为 promoted
        for patch in patches:
            for rule in patch.get('decision_rules', []):
                entry_id = rule.get('entry_id')
                if entry_id:
                    fake_args = argparse.Namespace(id=entry_id, status=EntryStatus.PROMOTED, pattern_key=None)
                    cmd_update(fake_args)
        return

    # 默认：JSON 输出
    if args.json_output or not sys.stdout.isatty():
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for patch in patches:
            print(f"Pattern: {patch['pattern_key']}")
            print(f"  Count: {patch['count']}")
            print(f"  Decision rules: {len(patch['decision_rules'])}")
            print()


def cmd_self_review(args: argparse.Namespace) -> None:
    """Self-review: agent 任务完成后自检，发现问题写入 learnings/errors"""

    if args.analyze:
        pattern = args.pattern
        result = {
            'pattern': pattern,
            'analysis': {},
            'suggestions': [],
            'improvements': []
        }

        all_entries = _read_all_entries()
        relevant_entries = []

        for etype, entries in all_entries.items():
            for entry in entries:
                if pattern and entry.get('pattern_key') == pattern:
                    relevant_entries.append(entry)
                elif not pattern:
                    relevant_entries.append(entry)

        if relevant_entries:
            result['analysis'] = {
                'total_entries': len(relevant_entries),
                'patterns': {}
            }

            for entry in relevant_entries:
                pk = entry.get('pattern_key', 'unknown')
                if pk not in result['analysis']['patterns']:
                    result['analysis']['patterns'][pk] = {'count': 0, 'entries': []}
                result['analysis']['patterns'][pk]['count'] += 1
                result['analysis']['patterns'][pk]['entries'].append(entry.get('id', ''))

            for pk, data in result['analysis']['patterns'].items():
                if data['count'] >= 2:
                    result['suggestions'].append({
                        'type': 'evolve',
                        'pattern': pk,
                        'reason': f"Pattern '{pk}' appears {data['count']} times"
                    })

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 自检模式
    input_data = args.input
    findings = []

    if input_data == '-':
        input_data = sys.stdin.read()

    if input_data:
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            data = {'raw': input_data}

        errors = data.get('errors', [])
        actions = data.get('actions', [])

        for error in errors:
            findings.append({
                'type': 'error',
                'source': 'self_review',
                'category': 'error',
                'what_happened': str(error)[:500],
                'pattern_key': f'self-review.error.{hash(error) % 10000}'
            })

        for action in actions:
            action_result = str(action.get('result', '')).lower()
            if 'failed' in action_result or 'error' in action_result:
                findings.append({
                    'type': 'error',
                    'source': 'self_review',
                    'category': 'error',
                    'what_happened': f"Action failed: {action.get('command', 'unknown')}",
                    'pattern_key': 'self-review.action.failed'
                })

    result = {
        'findings': findings,
        'findings_count': len(findings),
        'patterns_detected': len(set(f.get('pattern_key', '') for f in findings))
    }

    if args.write and findings:
        for finding in findings:
            entry = {
                'type': finding['type'],
                'category': finding['category'],
                'pattern_key': finding.get('pattern_key', ''),
                'what_happened': finding.get('what_happened', ''),
                'source': finding.get('source', 'self_review'),
            }
            _append_entry(entry)

    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_pending(args: argparse.Namespace) -> None:
    """Manage .pending_notifications/ directory"""
    pending_dir = os.path.join(LEARNINGS_DIR, '.pending_notifications')
    os.makedirs(pending_dir, exist_ok=True)

    if args.list:
        files = sorted(os.listdir(pending_dir))
        if files:
            for f in files:
                print(f)
        else:
            print("(empty)")
        return

    if args.clean:
        for f in os.listdir(pending_dir):
            os.remove(os.path.join(pending_dir, f))
        print(f"Cleaned {pending_dir}")
        return

    if args.write:
        pattern_key = args.write
        content = sys.stdin.read()
        outfile = os.path.join(pending_dir, f'{pattern_key}.analysis.json')
        with open(outfile, 'w') as f:
            f.write(content)
        print(f"Wrote {outfile}")


def main() -> None:
    global LEARNINGS_DIR
    parser = argparse.ArgumentParser(prog='manager.py', description='Self-Improvement Loop v5.0.0')
    parser.add_argument('--learnings-dir', default=LEARNINGS_DIR)
    parser.add_argument('--json-output', action='store_true')
    subparsers = parser.add_subparsers(dest='cmd', required=True)

    p = subparsers.add_parser('add')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--type', choices=['learnings', 'errors', 'features'])
    g.add_argument('--json', help='从 JSON 文件读取')
    p.add_argument('--category')
    p.add_argument('--pattern-key', default='')
    p.add_argument('--what')
    p.add_argument('--root-cause', default='')
    p.add_argument('--avoid', '--how-to-avoid', dest='avoid', default='')
    p.add_argument('--tags', default='')
    p.add_argument('--source', default='human_correction')

    p = subparsers.add_parser('list')
    p.add_argument('--type')
    p.add_argument('--status')
    p.add_argument('--pattern-key')
    p.add_argument('--count-only', action='store_true')

    p = subparsers.add_parser('get')
    p.add_argument('id')

    p = subparsers.add_parser('update')
    p.add_argument('id')
    p.add_argument('--status')
    p.add_argument('--pattern-key')

    p = subparsers.add_parser('notify')
    p.add_argument('id')

    p = subparsers.add_parser('scan')
    p.add_argument('--threshold', type=int, default=2)
    p.add_argument('--trigger-only', action='store_true')
    p.add_argument('--max-entries', type=int, default=10,
                   help='Max entries per pattern to return (default 10, 0=all)')

    p = subparsers.add_parser('archive')
    p.add_argument('--dry-run', action='store_true')

    p = subparsers.add_parser('stat')

    p = subparsers.add_parser('pending')
    p.add_argument('--list', action='store_true', help='List pending files')
    p.add_argument('--clean', action='store_true', help='Clean pending directory')
    p.add_argument('--write', metavar='PATTERN_KEY', help='Write analysis JSON from stdin')

    p = subparsers.add_parser('evolve')
    p.add_argument('--threshold', type=int, default=2,
                   help='Minimum count to trigger patch generation')
    p.add_argument('--pattern', help='Only generate patch for specific pattern')
    p.add_argument('--preview', action='store_true',
                   help='Show human-readable markdown preview of patches')
    p.add_argument('--apply', action='store_true',
                   help='Apply patches to agent SKILL.md')
    p.add_argument('--backup', action='store_true',
                   help='Create backup before applying patches')
    p.add_argument('--dry-run', action='store_true',
                   help='Show what would be applied without modifying files')

    p = subparsers.add_parser('self-review')
    p.add_argument('--input', default='',
                   help='Input data (use - for stdin)')
    p.add_argument('--write', action='store_true',
                   help='Write findings to learnings/errors')
    p.add_argument('--check-patterns', action='store_true',
                   help='Check for repeated patterns in existing entries')
    p.add_argument('--analyze', action='store_true',
                   help='Analyze patterns and suggest improvements')
    p.add_argument('--pattern',
                   help='Specific pattern to analyze')

    args = parser.parse_args()
    LEARNINGS_DIR = args.learnings_dir

    commands = {
        'add': cmd_add, 'list': cmd_list, 'get': cmd_get, 'update': cmd_update,
        'notify': cmd_notify, 'scan': cmd_scan, 'archive': cmd_archive, 'stat': cmd_stat,
        'pending': cmd_pending, 'evolve': cmd_evolve, 'self-review': cmd_self_review
    }
    commands[args.cmd](args)


if __name__ == '__main__':
    main()