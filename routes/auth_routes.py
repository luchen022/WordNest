"""
认证相关路由

提供基于 session 的登录/登出，并内置简单的登录失败限流。
"""
import hmac
import secrets
import time

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


auth_bp = Blueprint('auth', __name__)

# 登录失败限流记录：ip -> [失败次数, 首次失败时间]
_failed_attempts = {}


def _client_ip():
    """获取客户端 IP，用于登录失败限流。"""
    return request.remote_addr or 'unknown'


def _safe_next():
    """只允许跳转到站内相对地址，避免开放重定向。"""
    target = request.values.get('next') or ''
    if target.startswith('/') and not target.startswith('//') and '\\' not in target:
        return target
    return None


def _get_password_hash():
    """
    解析当前生效的密码哈希。

    优先级：WORDNEST_PASSWORD_HASH > WORDNEST_PASSWORD > 自动生成随机密码。
    """
    app = current_app
    cached = app.config.get('_AUTH_PASSWORD_HASH_RESOLVED')
    if cached:
        return cached

    configured_hash = app.config.get('AUTH_PASSWORD_HASH', '')
    plain_password = app.config.get('AUTH_PASSWORD', '')

    if configured_hash:
        resolved = configured_hash
    elif plain_password:
        resolved = generate_password_hash(plain_password)
    else:
        generated = secrets.token_urlsafe(12)
        resolved = generate_password_hash(generated)
        app.logger.warning(
            '未配置认证密码，已生成临时密码：%s（用户名：%s）。'
            '请设置 WORDNEST_PASSWORD 或 WORDNEST_PASSWORD_HASH 后重启。',
            generated,
            app.config.get('AUTH_USERNAME', 'admin'),
        )

    app.config['_AUTH_PASSWORD_HASH_RESOLVED'] = resolved
    return resolved


def _lockout_remaining(ip):
    """返回 (是否被锁定, 剩余秒数)。"""
    record = _failed_attempts.get(ip)
    if not record:
        return False, 0

    count, first_ts = record
    lockout_seconds = current_app.config.get('AUTH_LOCKOUT_SECONDS', 300)
    max_attempts = current_app.config.get('AUTH_MAX_ATTEMPTS', 5)
    elapsed = time.monotonic() - first_ts

    if elapsed >= lockout_seconds:
        _failed_attempts.pop(ip, None)
        return False, 0

    if count >= max_attempts:
        return True, int(lockout_seconds - elapsed)
    return False, 0


def _record_failure(ip):
    """记录一次登录失败。"""
    lockout_seconds = current_app.config.get('AUTH_LOCKOUT_SECONDS', 300)
    record = _failed_attempts.get(ip)
    now = time.monotonic()

    if not record or now - record[1] >= lockout_seconds:
        _failed_attempts[ip] = [1, now]
    else:
        record[0] += 1


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面。"""
    if not current_app.config.get('AUTH_ENABLED', True):
        return redirect(url_for('word.index'))

    if session.get('logged_in'):
        return redirect(_safe_next() or url_for('word.index'))

    if request.method == 'POST':
        ip = _client_ip()
        locked, remaining = _lockout_remaining(ip)
        if locked:
            flash(f'尝试次数过多，请在 {remaining} 秒后重试。', 'error')
            return render_template('login.html'), 429

        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        expected_username = current_app.config.get('AUTH_USERNAME', 'admin')

        username_ok = hmac.compare_digest(username, expected_username)
        password_ok = check_password_hash(_get_password_hash(), password)

        if username_ok and password_ok:
            _failed_attempts.pop(ip, None)
            session.clear()
            session.permanent = True
            session['logged_in'] = True
            session['username'] = expected_username
            return redirect(_safe_next() or url_for('word.index'))

        _record_failure(ip)
        flash('用户名或密码错误。', 'error')

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """退出登录并清除会话。"""
    session.clear()
    flash('已退出登录。', 'info')
    return redirect(url_for('auth.login'))
