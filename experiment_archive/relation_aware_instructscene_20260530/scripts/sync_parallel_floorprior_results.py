import argparse
from pathlib import Path

import paramiko


REMOTE_PATTERNS = [
    "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_*mesh*_eval_cfg1.0_1.0.txt",
    "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_*mesh*_eval_cfg1.0_1.0.json",
    "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_*mesh*_eval_cfg1.0_1.0.txt",
    "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_*mesh*_eval_cfg1.0_1.0.json",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_direct_yfix_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.txt",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_direct_yfix_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_max1.2_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.txt",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_max1.2_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.txt",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_max0.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.txt",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_max0.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_seed*_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.txt",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_seed*_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_*mesh*_eval_cfg1.0_1.0.txt",
    "/root/RelationAwareInstructScene/repos/InstructScene/out/*/generated_scenes/epoch_*/relation_aware_parsed_floor_prior_*mesh*_eval_cfg1.0_1.0.json",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", required=True)
    parser.add_argument("--out", default="results/floor_prior_remote")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host, port=args.port, username=args.user, password=args.password, timeout=20)
    sftp = ssh.open_sftp()
    try:
        pattern_cmd = " ".join(f"'{p}'" for p in REMOTE_PATTERNS)
        stdin, stdout, stderr = ssh.exec_command(f"for p in {pattern_cmd}; do ls $p 2>/dev/null || true; done")
        files = sorted(set(line.strip() for line in stdout.read().decode("utf-8", "replace").splitlines() if line.strip()))
        err = stderr.read().decode("utf-8", "replace").strip()
        if err:
            print(err)
        for remote_path in files:
            parts = remote_path.split("/")
            tag = parts[-4]
            epoch = parts[-2]
            name = parts[-1]
            local_name = f"{tag}_{epoch}_{name}"
            local_path = out_dir / local_name
            sftp.get(remote_path, str(local_path))
            print(local_path)
    finally:
        sftp.close()
        ssh.close()


if __name__ == "__main__":
    main()
