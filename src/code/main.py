import argparse
import logging

from . import configs
from . import snap_operator


from typing import Iterator, Optional


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument('--source', help='Restrict to config with this source path.')
  subparsers = parser.add_subparsers(dest='command')

  # Internal commands used in scheduling and pacman hook.
  subparsers.add_parser('internal-cronrun')
  subparsers.add_parser('internal-preupdate')

  # User commands.
  subparsers.add_parser('list')
  create = subparsers.add_parser('create')
  create.add_argument('--comment', help='Comment attached to this snapshot.')
  delete = subparsers.add_parser('delete')
  delete.add_argument('target', help='Full path of the target snapshot to be removed.')

  args = parser.parse_args()
  return args


def _iterate_configs(args: argparse.Namespace) -> Iterator[configs.Config]:
  source: Optional[str] = args.source
  for config in configs.CONFIGS:
    if not source or config.source == source:
      yield config


def main():
  args = _parse_args()
  command: str = args.command
  if not command:
    print('Start with --help to see common args.')
    return

  logging.basicConfig(
      level=logging.INFO if command.startswith('internal-') else logging.WARNING)

  if command == 'delete':
    for config in _iterate_configs(args):
      snapper = snap_operator.SnapOperator(config)
      snap = snapper.find_target(args.target)
      if snap:
        snap.delete()
        snapper.btrfs_sync()
        break
    else:
      print(f'Target {args.target} not found in any configs.')
    return

  for config in _iterate_configs(args):
    if command == 'list':
      print(f'Config: source={config.source}')
    snapper = snap_operator.SnapOperator(config)
    if command == 'internal-cronrun':
      snapper.scheduled()
    elif command == 'internal-preupdate':
      snapper.on_pacman()
    elif command == 'list':
      snapper.list_backups()
    elif command == 'create':
      snapper.create(args.comment)
    else:
      raise ValueError(f'Unknown command {command}')
    snapper.btrfs_sync()


if __name__ == '__main__':
  main()
