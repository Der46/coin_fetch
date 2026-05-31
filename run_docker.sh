#!/usr/bin/env bash
set -euo pipefail

NAME="coin-fetch-container"
IMAGE="coin-fetch:latest"
WORKDIR="/coin_fetch"

# 檢查 Dockerfile 是否存在
if [[ ! -f "Dockerfile" ]]; then
  echo "錯誤：目前目錄找不到 Dockerfile。"
  echo "請在 Dockerfile 所在的專案目錄執行此 script。"
  exit 1
fi

# 檢查 fetch_rewards.py 是否存在
if [[ ! -f "fetch_rewards.py" ]]; then
  echo "錯誤：目前目錄找不到 fetch_rewards.py。"
  echo "請確認爬蟲主程式 fetch_rewards.py 位於目前專案目錄。"
  exit 1
fi

# 如果 image 不存在，就自動 build
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[$IMAGE] image 不存在，開始 build..."
  docker build -t "$IMAGE" .
else
  echo "[$IMAGE] image 已存在，略過 build。"
fi

# 顯示使用方式
show_usage() {
  echo ""
  echo "使用方式："
  echo "  ./run_docker.sh"
  echo "  ./run_docker.sh --today"
  echo "  ./run_docker.sh --date 20260529"
  echo "  ./run_docker.sh --display-date 05/29/2026"
  echo "  ./run_docker.sh --shell"
  echo "  ./run_docker.sh --rebuild"
  echo ""
}

# 檢查已存在 container 的 volume 掛載
check_existing_container_volume() {
  local container_name="$1"

  if docker ps --format '{{.Names}}' | grep -qx "$container_name"; then
    if docker exec "$container_name" bash -lc "test -d '$WORKDIR'"; then
      echo "[$container_name] $WORKDIR 目錄存在。"
    else
      echo "[$container_name] 警告：container 內找不到 $WORKDIR。"
      echo "這通常代表它當初不是用 -v \"\$(pwd)\":$WORKDIR 建立的。"
      echo ""
      echo "請執行："
      echo "  docker rm -f $container_name"
      echo "  ./run_docker.sh"
      echo ""
    fi
  else
    echo "[$container_name] 目前未執行，無法直接檢查 $WORKDIR。"
    echo "若這是舊 container，start 後也不會變更 volume 掛載。"
    echo "如果之前不是用正確 volume 建立，請執行："
    echo "  docker rm -f $container_name"
    echo "  ./run_docker.sh"
    echo ""
  fi
}

# 是否要求重建 image
REBUILD=false
SHELL_MODE=false
ARGS=()

for arg in "$@"; do
  case "$arg" in
    --rebuild)
      REBUILD=true
      ;;
    --shell)
      SHELL_MODE=true
      ;;
    --help|-h)
      show_usage
      exit 0
      ;;
    *)
      ARGS+=("$arg")
      ;;
  esac
done

# 若要求重建 image
if [[ "$REBUILD" == "true" ]]; then
  echo "[$IMAGE] 強制重建 image..."
  docker build --no-cache -t "$IMAGE" .
fi

# 如果 container 已存在，包含 stopped
if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then

  # 如果 container 正在執行中
  if docker ps --format '{{.Names}}' | grep -qx "$NAME"; then

    echo "[$NAME] 已在執行中。"
    check_existing_container_volume "$NAME"

    if [[ "$SHELL_MODE" == "true" ]]; then
      echo "使用 exec 進入 bash..."
      exec docker exec -it "$NAME" bash
    else
      echo "在既有 container 內執行 fetch_rewards.py..."
      exec docker exec -it "$NAME" python "$WORKDIR/fetch_rewards.py" "${ARGS[@]}"
    fi

  else
    echo "[$NAME] 已存在但未執行。"
    echo "注意：已存在的 container 不會自動更新 volume 掛載、workdir 或 image 設定。"
    echo ""
    echo "建議直接重建 container："
    echo "  docker rm -f $NAME"
    echo "  ./run_docker.sh"
    echo ""

    if [[ "$SHELL_MODE" == "true" ]]; then
      echo "啟動既有 container 並進入..."
      exec docker start -ai "$NAME"
    else
      echo "啟動既有 container..."
      docker start "$NAME" >/dev/null
      echo "執行 fetch_rewards.py..."
      exec docker exec -it "$NAME" python "$WORKDIR/fetch_rewards.py" "${ARGS[@]}"
    fi
  fi

else
  echo "[$NAME] 不存在，建立新容器..."

  if [[ "$SHELL_MODE" == "true" ]]; then
    echo "建立新容器並進入 bash..."
    echo "Volume: $(pwd):$WORKDIR"

    exec docker run -it \
      --name "$NAME" \
      --network=host \
      -v "$(pwd)":$WORKDIR \
      --workdir "$WORKDIR" \
      "$IMAGE" bash
  else
    echo "建立新容器並執行 fetch_rewards.py..."
    echo "Volume: $(pwd):$WORKDIR"

    exec docker run -it \
      --name "$NAME" \
      --network=host \
      -v "$(pwd)":$WORKDIR \
      --workdir "$WORKDIR" \
      "$IMAGE" python "$WORKDIR/fetch_rewards.py" "${ARGS[@]}"
  fi
fi
