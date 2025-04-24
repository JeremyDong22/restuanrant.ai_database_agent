# Docker使用指南 - DB Agent应用

## 项目Docker配置说明

本项目使用Docker进行容器化，以便于部署和运行。Docker配置文件包括：

- `Dockerfile`: 定义了应用的构建步骤和运行环境
- `.dockerignore`: 排除不需要包含在Docker镜像中的文件
- `docker-run.sh`: 构建和运行Docker容器的便捷脚本
- `docker-debug.sh`: 用于调试目的的脚本，进入容器内部

## 前提条件

确保您的系统已安装Docker。如果尚未安装，请参考[Docker官方文档](https://docs.docker.com/get-docker/)进行安装。

## 使用方法

### 1. 设置环境变量

应用依赖以下环境变量：

```bash
# 设置Supabase数据库连接URI（必需）
export SUPABASE_DB_URI="postgresql://username:password@host:port/database"

# 设置Flask环境（可选，默认为development）
export FLASK_ENV="development"  # 或 "production"
```

### 2. 使用脚本构建和运行

最简单的方法是使用提供的脚本：

```bash
./docker-run.sh
```

此脚本会自动构建镜像并启动容器，将应用暴露在8080端口（默认）。

### 3. 手动构建和运行

如果您想手动执行Docker命令：

```bash
# 构建镜像
docker build -t dbagent .

# 运行容器
docker run -d \
  --name dbagent \
  -p 8080:5000 \
  -e SUPABASE_DB_URI=${SUPABASE_DB_URI} \
  -e FLASK_ENV=${FLASK_ENV:-"development"} \
  dbagent
```

## 容器管理

```bash
# 查看容器日志
docker logs -f dbagent

# 停止容器
docker stop dbagent

# 删除容器
docker rm dbagent

# 删除镜像
docker rmi dbagent
```

## 调试

如果您遇到问题，可以使用交互模式运行容器进行调试：

```bash
# 使用调试脚本
./docker-debug.sh

# 或手动运行
docker run -it --rm \
  -p 8080:5000 \
  -e SUPABASE_DB_URI=${SUPABASE_DB_URI} \
  -e FLASK_ENV="development" \
  dbagent /bin/bash
```

在容器内部，您可以运行：
```bash
# 使用 Flask 开发服务器
python3 app.py

# 或使用 Gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

## 注意事项

- 确保`SUPABASE_DB_URI`环境变量已正确设置，否则应用将无法连接到数据库
- 默认情况下，应用在容器内部使用5000端口，并映射到主机的8080端口
- **macOS用户注意**：macOS的AirPlay Receiver服务默认占用5000端口，因此我们在宿主机上使用8080端口
- 如果8080端口也被占用，可以通过设置环境变量修改端口：`export PORT=自定义端口 && ./docker-run.sh` 