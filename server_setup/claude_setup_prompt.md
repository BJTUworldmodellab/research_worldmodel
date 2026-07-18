You are Claude Code running inside a tmux session on an A100 server.

Goal: configure and verify the Relation-Aware InstructScene experiment environment.

Project root:

```text
/root/RelationAwareInstructScene
```

Expected repo:

```text
/root/RelationAwareInstructScene/repos/InstructScene
```

Do not delete user data. Do not run destructive git or filesystem commands.

Tasks:

1. Inspect the server environment, GPU, disk, Python, PyTorch, CUDA, and installed packages.
2. Read:
   - `/root/RelationAwareInstructScene/SERVER_UPLOAD_CHECKLIST.md`
   - `/root/RelationAwareInstructScene/server_setup/README.md`
3. Verify the required directories and symlinks:
   - `dataset/InstructScene -> /root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene`
   - `dataset/3D-FRONT -> /root/RelationAwareInstructScene/raw_data/3D-FRONT`
   - `out -> /root/autodl-tmp/RelationAwareInstructScene/instructscene_out`
4. Verify that `src/relation_aware_generate_sg.py` exists in the InstructScene repo.
5. Check whether these required data/checkpoint assets exist:
   - InstructScene official data and validation split
   - 3D-FRONT raw scene data
   - 3D-FUTURE model assets
   - bedroom/livingroom/diningroom sg2sc and sg diffusion checkpoints
6. If something is missing, report the exact missing path and the safest next action. Do not invent download URLs.
7. If everything needed for a smoke test exists, run the smallest safe smoke test first, not the full experiment.

Write a concise status report to:

```text
/root/RelationAwareInstructScene/logs/claude_setup_status.md
```

