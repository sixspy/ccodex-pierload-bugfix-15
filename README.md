# 港口过磅闸口（pierload）

数据工程母仓：港区地磅过磅 → 超重旁路挂起 → 裁定放行 → 闸代快照 → 提单册对账。

## 一键起环境

```bash
docker compose up -d --build
```

浏览器访问 http://localhost:11500

- 管理账号：`admin` / `admin123`
- 读写账号：`writer` / `writer123`

## 本地开发

```powershell
cd projects/13-pierload
$env:PYTHONPATH="backend"
python -m uvicorn app:app --app-dir backend --reload --port 8000
```

静态页仍由 FastAPI 托管于同一进程。

## 自测

```powershell
$env:PYTHONPATH="backend"
python -m pytest
python scripts/count_loc.py
```