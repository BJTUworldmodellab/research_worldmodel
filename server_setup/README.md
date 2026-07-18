# A100 服务器配置说明

这个目录用于把新租的 A100 机器配置成 Relation-Aware InstructScene 实验环境。

推荐镜像：

```text
PyTorch 2.1.0 / Python 3.10 / Ubuntu 22.04 / CUDA 12.1
```

## 需要你提供的信息

真正登录服务器配置前，需要这些信息：

```text
SSH host:
SSH port:
SSH user: root
登录方式: 密码或私钥
数据来源: 本地上传 / 旧服务器复制 / 网盘链接 / 已经在新机器上
checkpoint 来源: 本地上传 / 旧服务器复制 / 网盘链接 / 已经在新机器上
```

不要把密码直接写进仓库文件里。可以在终端交互输入。

## 本地上传

在 Windows PowerShell 里把变量改成你的服务器信息：

```powershell
$SERVER="root@<server-host>"
$PORT="<ssh-port>"
$REMOTE="/root/RelationAwareInstructScene"

ssh -p $PORT $SERVER "mkdir -p $REMOTE"
scp -P $PORT -r server_setup scripts docs results SERVER_UPLOAD_CHECKLIST.md $SERVER":"$REMOTE/
scp -P $PORT results\relation_aware_generate_sg.py $SERVER":/root/RelationAwareInstructScene/relation_aware_generate_sg.py"
scp -P $PORT results\run_mesh_visual_eval.sh $SERVER":/root/RelationAwareInstructScene/run_mesh_visual_eval.sh"
```

如果要把本地 archive 也传上去：

```powershell
ssh -p $PORT $SERVER "mkdir -p /root/RelationAwareInstructScene/archive"
scp -P $PORT -r experiment_archive\relation_aware_instructscene_20260530 $SERVER":/root/RelationAwareInstructScene/archive/"
```

## 服务器初始化

登录服务器后运行：

```bash
cd /root/RelationAwareInstructScene
bash server_setup/setup_relation_scene_server.sh
```

如果 InstructScene repo 还没有 clone，先设置仓库地址：

```bash
export INSTRUCTSCENE_REPO_URL="<InstructScene Git URL>"
bash server_setup/setup_relation_scene_server.sh
```

如果 repo 已经存在于 `/root/RelationAwareInstructScene/repos/InstructScene`，脚本会直接使用现有 repo。

## 必须补齐的数据

完整实验不能只靠当前仓库，还需要：

```text
/root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene
/root/RelationAwareInstructScene/raw_data/3D-FRONT
/root/RelationAwareInstructScene/raw_data/3D-FRONT/3D-FUTURE-model
```

以及 InstructScene 官方 checkpoint：

```text
bedroom_sg2scdiffusion_objfeat epoch 1999
bedroom_sgdiffusion_vq_objfeat epoch 1999
livingroom_sg2scdiffusion_objfeat epoch 1999
livingroom_sgdiffusion_vq_objfeat epoch 1459
diningroom_sg2scdiffusion_objfeat epoch 1999
diningroom_sgdiffusion_vq_objfeat epoch 1239
```

## 检查

服务器初始化后运行：

```bash
bash server_setup/check_relation_scene_server.sh
```

这个检查只验证环境、目录、软链接和关键文件是否在位，不会替你下载第三方数据。

