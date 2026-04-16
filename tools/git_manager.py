"""
Git Manager — Sincronização automática com repositório Git.
"""
import subprocess
import os


def git_sync(message: str = "auto: agent task commit") -> bool:
    """
    Faz git add, commit e push do projeto.

    Returns:
        True se sucesso, False se falhou.
    """
    try:
        # Verifica se está num repo git
        check = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True, text=True, timeout=10
        )
        if check.returncode != 0:
            print("⚠️ Não é um repositório Git")
            return False

        # Add
        subprocess.run(["git", "add", "."], check=True, timeout=15)

        # Commit
        commit = subprocess.run(
            ["git", "commit", "-m", message[:200]],  # limita tamanho da mensagem
            capture_output=True, text=True, timeout=15
        )

        if "nothing to commit" in commit.stdout.lower():
            print("ℹ️  Git: nada para commitar")
            return True

        if commit.returncode != 0:
            print(f"⚠️ Git commit falhou: {commit.stderr[:200]}")
            return False

        # Push
        push = subprocess.run(
            ["git", "push"],
            capture_output=True, text=True, timeout=30
        )

        if push.returncode == 0:
            print("✅ Git sync OK")
            return True
        else:
            print(f"⚠️ Git push falhou: {push.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print("⚠️ Git timeout")
        return False

    except Exception as e:
        print(f"⚠️ Git erro: {e}")
        return False