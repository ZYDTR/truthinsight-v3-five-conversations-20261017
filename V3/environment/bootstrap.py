"""Boot the isolated API and seed one real single-Agent Workflow."""

from __future__ import annotations

import ast
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid


HARNESS = Path("/harness")
CONFIG = json.loads((HARNESS / "config.json").read_text())
RUN_ID = CONFIG["run_id"]


def _credential_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in Path("/credentials.env").read_text().splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        if not key.startswith("CCSDK_OPENAI_COMPAT_") and key != "CCSDK_MODEL_PROXY_PROVIDER":
            continue
        try:
            value = ast.literal_eval(value)
        except Exception:
            pass
        values[key] = str(value)
    return values


def _configure_environment() -> None:
    values = _credential_env()
    values.update(
        {
            "HOST": "0.0.0.0",
            "PORT": "8001",
            "DATABASE_URL": (
                f"postgres://probe:{CONFIG['database_password']}@{RUN_ID}-pg:5432/"
                f"{CONFIG['database']}"
            ),
            "REDIS_URL": f"redis://{RUN_ID}-redis:6379/0",
            "REDIS_PASSWORD": "",
            "IS_OPEN_SSO": "OFF",
            "SECRET_KEY": CONFIG["jwt_secret"],
            "DEFAULT_ADMIN_USERNAME": "probe_admin",
            "DEFAULT_ADMIN_PASSWORD": "isolated-test-password",
            "DEFAULT_ADMIN_ROLE": "super_admin",
            "CRYPTO_BASE_KEY": 'P7YxQwbK3tJnMrVfL8zSgHe5R2NdAa6Z',
            "AGENT_RUNTIME_STATE_DIR": "/app/runtime_state",
            "AGENT_RUNTIME_STATE_HOST_DIR": CONFIG["state_host"],
            "AGENT_RUNTIME_WORKSPACE_DIR": "/app/runtime_state/worker_data",
            "AGENT_RUNTIME_WORKSPACE_HOST_DIR": CONFIG["state_host"] + "/worker_data",
            "SKILL_STORAGE_TYPE": "local",
            "SKILL_LOCAL_STORAGE_ROOT": "/app/skills",
            "AGENT_RUNTIME_SKILL_HOST_ROOT": CONFIG["skills_host"],
            "AGENT_RUNTIME_SKILL_MOUNT_DIR": "/runtime_assets/skills",
            "AGENT_RUNTIME_WORKER_CONNECT_MODE": "docker_network",
            "AGENT_RUNTIME_DOCKER_NETWORK": RUN_ID + "-net",
            "AGENT_RUNTIME_ANTHROPIC_BASE_URL": (
                f"http://{RUN_ID}-api:8001/api/agent-runtime/internal/anthropic-proxy"
            ),
            "AGENT_RUNTIME_ARTIFACT_API_BASE_URL": f"http://{RUN_ID}-api:8001/api",
            "CCSDK_WORKER_IMAGE": RUN_ID + "-worker:candidate",
            "CCSDK_WORKER_BASE_IMAGE": CONFIG["worker_base_image"],
            "CCSDK_BUILD_WORKER_BASE_IMAGE": "false",
            "CCSDK_CLAUDE_MODEL": CONFIG["model_name"],
            "CCSDK_OPENAI_COMPAT_FALLBACK_MODEL": "",
            "CCSDK_CLAUDE_FALLBACK_MODEL": "",
            "CCSDK_WORKER_MAX_CONCURRENCY": "2",
            "CCSDK_DEFAULT_MAX_TURNS": "500",
            "CCSDK_MAX_TURNS_LIMIT": "500",
            "CCSDK_UNSAFE_ALLOW_ALL_TOOLS": "false",
            "CCSDK_CONTAINER_CPUS": "1",
            "CCSDK_CONTAINER_MEMORY": "4g",
            "CCSDK_DEBUG_ENABLE_WEAKER_NESTED_SANDBOX": "true",
            "CCSDK_DEBUG_ALLOW_ALL_UNIX_SOCKETS": "true",
            "AGENT_RUNTIME_IDLE_STOP_ENABLED": "0",
            "AGENT_RUNTIME_IDLE_STOP_DRY_RUN": "1",
            "AGENT_RUNTIME_ENABLE_LOCAL_CLAUDE_SETTINGS": "false",
            "AGENT_RUNTIME_MODEL_PROXY_TIMEOUT_SECONDS": "1200",
            "AGENT_RUNTIME_WORKFLOW_AGENT_STALL_TIMEOUT_MS": "900000",
            "AGENT_RUNTIME_WORKFLOW_CLAUDE_API_TIMEOUT_MS": "1200000",
            "AGENT_RUNTIME_WORKFLOW_CLAUDE_STREAM_IDLE_TIMEOUT_MS": "900000",
            "MINIO_ENDPOINT": RUN_ID + "-unused-minio:9000",
            "MINIO_ACCESS_KEY": "isolated-unused",
            "MINIO_SECRET_KEY": "isolated-unused",
            "MINIO_SECURE": "false",
            "XX_JOB_ADDR": "",
            "XX_JOB_ACCESS_TOKEN": "",
            "XX_JOB_EXECUTOR_NAME": "",
            "APP_SERVICE_ADDR": "",
            "LOG_DIR": "/harness/logs",
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOST_UID": "0",
            "HOST_GID": "0",
            "PATH": "/harness/bin:" + os.getenv("PATH", "/usr/local/bin:/usr/bin:/bin"),
        }
    )
    os.environ.update(values)
    sys.path.insert(0, "/app")


_configure_environment()


async def seed():
    from aerich import Command
    from tortoise import Tortoise
    from app.db.config import TORTOISE_ORM
    from app.core.security import create_access_token, get_password_hash
    from app.models.user import User
    from app.models.role import Role
    from app.models.system_config import SystemConfig
    from app.models.user_report_usage import UserReportUsage
    from app.services.agent_runtime.runtime_store import ensure_user, atomic_write_json
    cmd=Command(TORTOISE_ORM,app="models",location="/app/migrations")
    await cmd.init(); upgraded=await cmd.upgrade()
    (HARNESS/'migrations.json').write_text(json.dumps(upgraded))
    role,_=await Role.get_or_create(identifier="super_admin",defaults={"name":"super_admin"})
    users={}
    for name in ['probe','chemistry','physics','astronomy','earth','neuro']:
        username='tibv31_'+name
        u=await User.create(username=username,hashed_password=get_password_hash(CONFIG['user_password']),role=role)
        await UserReportUsage.create(user_id=u,used_count=0,max_allowed_count=None)
        code='user-'+str(u.id); root=ensure_user(code); path=root/'user.json'; meta=json.loads(path.read_text());meta['current_container_code']=RUN_ID;atomic_write_json(path,meta)
        users[name]={'user_id':str(u.id),'user_code':code,'username':username,'token':create_access_token(subject=json.dumps({'username':username}),expires_delta=timedelta(days=14))}
    settings={
        'CCSDK_CLAUDE_MODEL':CONFIG['model_name'],
        'AGENT_RUNTIME_CONVERSATION_MAIN_TOOLS':json.dumps(['Read','Glob','Grep','Edit','Write','Bash','SendMessage','StructuredOutput','Agent']),
        'AGENT_RUNTIME_CONVERSATION_RESEARCH_AGENT_TOOLS':json.dumps(['Read','Glob','Grep','Edit','Write','Bash','SendMessage','StructuredOutput']),
        'AGENT_RUNTIME_CONVERSATION_DISALLOWED_TOOLS':json.dumps(['WebSearch','WebFetch','Workflow']),
        'AGENT_RUNTIME_CONVERSATION_MAX_CONCURRENT_SUBAGENTS':'4',
        'AGENT_RUNTIME_MODEL_PROXY_TIMEOUT_SECONDS':'1200',
        'AGENT_RUNTIME_WORKFLOW_AGENT_STALL_TIMEOUT_MS':'900000',
        'AGENT_RUNTIME_WORKFLOW_CLAUDE_API_TIMEOUT_MS':'1200000',
        'AGENT_RUNTIME_WORKFLOW_CLAUDE_STREAM_IDLE_TIMEOUT_MS':'900000',
    }
    for key,value in settings.items():await SystemConfig.update_or_create(key=key,defaults={'value':value})
    (HARNESS/'private/users.json').write_text(json.dumps(users));(HARNESS/'private/users.json').chmod(0o600)
    (HARNESS/'settings.safe.json').write_text(json.dumps(settings,indent=2))
    await Tortoise.close_connections()
if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'serve'
    if mode=='seed':asyncio.run(seed())
    elif mode=='digest':
        from app.services.agent_runtime.docker_manager import worker_source_digest
        print(worker_source_digest())
    elif mode=='serve':
        import uvicorn
        uvicorn.run('app.main:app',host='0.0.0.0',port=8001,workers=1,timeout_graceful_shutdown=35)
