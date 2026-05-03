from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any, Callable

import requests

from instant_translator.translation.base import BaseTranslator, TranslationResult


class TencentTranslateTranslator(BaseTranslator):
    provider_key = "tencent_translate"
    host = "tmt.tencentcloudapi.com"
    endpoint = "https://tmt.tencentcloudapi.com/"
    service = "tmt"
    action = "TextTranslate"
    version = "2018-03-21"
    algorithm = "TC3-HMAC-SHA256"
    content_type = "application/json; charset=utf-8"
    signed_headers = "content-type;host;x-tc-action"

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        region: str,
        project_id: int,
        timeout_seconds: int = 30,
        timestamp_fn: Callable[[], int] | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.project_id = project_id
        self.timeout_seconds = timeout_seconds
        self.timestamp_fn = timestamp_fn or (lambda: int(datetime.now(tz=UTC).timestamp()))
        self.session = session or requests.Session()

    def translate(
        self,
        text: str,
        source_language: str | None,
        target_language: str,
    ) -> TranslationResult:
        payload = {
            "SourceText": text,
            "Source": source_language or "auto",
            "Target": target_language,
            "ProjectId": self.project_id,
        }
        timestamp = self.timestamp_fn()
        authorization = self._build_authorization(payload, timestamp)
        headers = {
            "Authorization": authorization,
            "Content-Type": self.content_type,
            "Host": self.host,
            "X-TC-Action": self.action,
            "X-TC-Region": self.region,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": self.version,
        }

        try:
            response = self.session.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            error = data.get("Response", {}).get("Error")
            if error:
                code = error.get("Code", "UNKNOWN_ERROR")
                return TranslationResult(error_code=self._map_tencent_error(code), error_message=error.get("Message"))
            translated_text = data["Response"]["TargetText"]
            return TranslationResult(text=translated_text)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (401, 403):
                return TranslationResult(error_code="AUTH_ERROR", error_message="认证失败，请检查密钥或权限")
            if status_code == 429:
                return TranslationResult(error_code="RATE_LIMIT", error_message="请求过于频繁，请稍后重试")
            return TranslationResult(error_code="NETWORK_ERROR", error_message="请求失败，请检查网络或服务地址")
        except requests.RequestException:
            return TranslationResult(error_code="NETWORK_ERROR", error_message="请求失败，请检查网络或服务地址")
        except (KeyError, TypeError, ValueError):
            return TranslationResult(error_code="UNKNOWN_ERROR", error_message="翻译结果解析失败")

    def _build_authorization(self, payload: dict[str, Any], timestamp: int) -> str:
        date = datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d")
        credential_scope = f"{date}/{self.service}/tc3_request"
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        canonical_headers = (
            f"content-type:{self.content_type}\n"
            f"host:{self.host}\n"
            f"x-tc-action:{self.action.lower()}\n"
        )
        canonical_request = "\n".join(
            [
                "POST",
                "/",
                "",
                canonical_headers,
                self.signed_headers,
                hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
            ]
        )
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = "\n".join(
            [
                self.algorithm,
                str(timestamp),
                credential_scope,
                hashed_canonical_request,
            ]
        )

        secret_date = hmac.new(f"TC3{self.secret_key}".encode("utf-8"), date.encode("utf-8"), hashlib.sha256).digest()
        secret_service = hmac.new(secret_date, self.service.encode("utf-8"), hashlib.sha256).digest()
        secret_signing = hmac.new(secret_service, b"tc3_request", hashlib.sha256).digest()
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        return (
            f"{self.algorithm} Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={self.signed_headers}, Signature={signature}"
        )

    @staticmethod
    def _map_tencent_error(code: str) -> str:
        lowered = code.lower()
        if "auth" in lowered or "signature" in lowered:
            return "AUTH_ERROR"
        if "limit" in lowered or "throttle" in lowered:
            return "RATE_LIMIT"
        if "language" in lowered:
            return "UNSUPPORTED_LANGUAGE"
        return "UNKNOWN_ERROR"
