"""
Giao diện dòng lệnh (CLI) của ToolNet CapCut TTS.
"""

import argparse
import json
import sys

from toolnet_capcut_tts import __version__
from toolnet_capcut_tts.client import CapCutClient
from toolnet_capcut_tts.action import build_tts_action, parse_provider_params
from toolnet_capcut_tts.models import DeviceConfig, SubtitleResult


def save_json(obj: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(obj, fp, ensure_ascii=False, indent=2)
        fp.write("\n")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="toolnet-capcut-tts",
        description="ToolNet CapCut TTS - tạo request và gọi CapCut common_task cho TTS/STT",
    )
    ap.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    ap.add_argument(
        "mode",
        choices=[
            "upload-audio",
            "tts-new",
            "tts-action",
            "tts-srt",
            "tts-query",
            "stt-new",
            "stt-query",
            "stt-file",
            "translate",
            "list-voices",
            "list-languages",
        ],
        help="Chế độ cần thực thi",
    )
    ap.add_argument("--device-json", help="Ghi đè device/query bằng file JSON")
    ap.add_argument("--base-url", help="API origin được phép (mặc định CAPCUT_BASE_URL hoặc endpoint quan sát được)")
    ap.add_argument("--payload-sign", help="Chữ ký payload TTS native; nếu bỏ trống, SDK dùng helper ký tương thích")
    ap.add_argument("--dry-run", action="store_true", help="In request mà không gửi HTTP")
    ap.add_argument("--out", help="Ghi response JSON ra file")

    ap.add_argument("--text", action="append", help="Đoạn text TTS; có thể lặp lại")
    ap.add_argument("--text-file", help="File text TTS, mỗi dòng một đoạn")
    ap.add_argument("--srt-file", help="File SRT đầu vào cho mode tts-srt")
    ap.add_argument("--output-dir", default="tts-srt-output", help="Thư mục chứa các MP3 theo từng cue")
    ap.add_argument("--part", action=argparse.BooleanOptionalAction, default=True,
                    help="Tạo một MP3 cho mỗi cue SRT (mặc định; dùng --no-part để gộp một MP3)")
    ap.add_argument("--audio-out", default="tts-output.mp3", help="Đường dẫn MP3 gộp khi dùng --no-part")
    ap.add_argument("--voice", default="BV074_streaming", help="Voice type hoặc tên hiển thị")
    ap.add_argument("--resource-id", default=None, help="Resource ID của voice (tự resolve nếu bỏ trống)")
    ap.add_argument("--seg-id", help="Segment ID của Lyra draft cho tts-action")
    ap.add_argument("--speaker", help="Speaker ID cho envelope tts-action")
    ap.add_argument("--provider-params-json", help="JSON object hoặc @file cho provider params")
    ap.add_argument("--extension-json", help="JSON object hoặc @file cho extension")
    ap.add_argument("--options-json", help="Tùy chọn bổ sung dạng JSON object hoặc @file")
    ap.add_argument("--emotion", help="Emotion cho envelope tts-action")

    ap.add_argument("--audio-vid", help="Vid media đã upload cho STT")
    ap.add_argument("--audio-md5", help="MD5 media nguồn cho STT")
    ap.add_argument("--audio-file", help="File MP3/M4A/MP4 cần upload trước khi STT")
    ap.add_argument("--duration-ms", type=int, help="Thời lượng audio tính bằng mili giây")
    ap.add_argument("--language", default=None, help="Mã ngôn ngữ nguồn cho STT (mặc định zh-CN); bỏ trống khi list-voices để xem tất cả")
    ap.add_argument("--translation-language", default="vi-VN", help="Mã ngôn ngữ đích cho dịch STT")
    ap.add_argument("--use-translation", action="store_true", help="Bật dịch trong STT")
    ap.add_argument("--srt-out", help="Ghi utterance STT hoàn tất thành file SubRip UTF-8 (.srt)")
    ap.add_argument("--no-wait", action="store_true", help="Với stt-file/translate, trả về ngay sau khi tạo task")
    ap.add_argument("--language-category", default="tts_catalog_languages",
                    help="Nhóm mã ngôn ngữ cho mode list-languages")

    ap.add_argument("--task-id", help="Task ID cho mode query")
    ap.add_argument("--token", help="Task token cho mode query")
    ap.add_argument("--bind-id", default="", help="Task bind ID")
    return ap


def main(args_list=None) -> None:
    ap = build_parser()
    args = ap.parse_args(args_list)

    # Device configuration loading
    device = DeviceConfig()
    if args.device_json:
        device = DeviceConfig.from_json_file(args.device_json)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    client = CapCutClient(device=device, base_url=args.base_url)

    # 1. List voices and languages
    if args.mode == "list-voices":
        voices = client.list_voices(lang=args.language)
        voice_dicts = [
            {
                "display_name": v.display_name,
                "voice_type": v.voice_type,
                "resource_id": v.resource_id,
                "lang": v.lang,
            }
            for v in voices
        ]
        out_data = {"voices": voice_dicts}
        print(json.dumps(out_data, ensure_ascii=False, indent=2))
        if args.out:
            save_json(out_data, args.out)
        return

    if args.mode == "list-languages":
        codes = client.list_languages(category=args.language_category)
        out_data = {
            "category": args.language_category,
            "languages": codes,
            "categories": client.list_language_categories(),
        }
        print(json.dumps(out_data, ensure_ascii=False, indent=2))
        if args.out:
            save_json(out_data, args.out)
        return

    # 2. Upload Audio & STT File combined mode
    file_mode = args.mode in {"stt-file", "translate"}
    translate_mode = args.mode == "translate"
    if args.mode in {"upload-audio", "stt-file", "translate"}:
        if not args.audio_file:
            print("Error: --audio-file is required for upload-audio, stt-file, and translate", file=sys.stderr)
            sys.exit(1)
        upload_info = client.upload_audio(args.audio_file)
        upload_dict = upload_info.to_dict()

        if args.mode == "upload-audio":
            if args.out:
                save_json(upload_dict, args.out)
            print(json.dumps(upload_dict, ensure_ascii=False, indent=2))
            return

        # stt-file flow continues to stt-new
        args.audio_vid = upload_info.vid
        args.audio_md5 = upload_info.md5
        if not args.duration_ms and upload_info.duration_ms:
            args.duration_ms = upload_info.duration_ms
        args.mode = "stt-new"
        if translate_mode:
            args.use_translation = True
        print("Upload complete:")
        print(json.dumps(upload_dict, ensure_ascii=False, indent=2))

    # 3. Dry-run or Execute API requests
    url, headers, body_text = None, None, None

    if args.mode == "tts-srt":
        if not args.srt_file:
            ap.error("tts-srt requires --srt-file")
        if args.dry_run:
            try:
                cues = SubtitleResult.from_srt(args.srt_file)
            except Exception as exc:
                ap.error(str(exc))
            print(json.dumps({"mode": "tts-srt", "cue_count": len(cues.utterances),
                              "texts": [cue.text for cue in cues.utterances],
                              "part": args.part,
                              "output": args.output_dir if args.part else args.audio_out,
                              "sent": False}, ensure_ascii=False, indent=2))
            return
        try:
            result = client.generate_speech_from_srt(
                args.srt_file, output_dir=args.output_dir, voice=args.voice,
                resource_id=args.resource_id,
                part=args.part, audio_path=args.audio_out,
            )
        except Exception as exc:
            print(f"SRT TTS failed: {exc}", file=sys.stderr)
            sys.exit(1)
        summary = {key: value for key, value in result.items() if key != "tts"}
        tasks = (result["tts"].get("data") or {}).get("tasks") or []
        summary["tts_status"] = tasks[0].get("status") if tasks else None
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.out:
            save_json(summary, args.out)
        return

    if args.mode == "tts-action":
        if not args.text or not args.seg_id:
            print("Error: tts-action requires --text and --seg-id", file=sys.stderr)
            sys.exit(1)
        action_options = parse_provider_params(args.options_json) or {}
        if not isinstance(action_options, dict):
            ap.error("--options-json must contain a JSON object")
        action_options.update({
            "text": args.text[0], "seg_id": args.seg_id,
            "speaker": args.speaker,
            "emotion": args.emotion,
            "provider_params_json": args.provider_params_json,
            "extension_json": args.extension_json,
        })
        action_options = {key: value for key, value in action_options.items() if value is not None}
        action = build_tts_action(**action_options)
        print(json.dumps(action, ensure_ascii=False, indent=2))
        if args.out:
            save_json(action, args.out)
        return

    if args.mode == "tts-new":
        texts = args.text or []
        if args.text_file:
            with open(args.text_file, "r", encoding="utf-8") as fp:
                texts.extend([line.strip() for line in fp if line.strip()])
        if not texts:
            print("Error: need --text or --text-file", file=sys.stderr)
            sys.exit(1)
        url, headers, body_text = client.build_tts_new_request(
            texts, args.voice, args.resource_id, payload_sign=args.payload_sign,
        )

    elif args.mode == "stt-new":
        if not args.audio_vid or not args.audio_md5:
            print("Error: need --audio-vid and --audio-md5", file=sys.stderr)
            sys.exit(1)
        url, headers, body_text = client.build_stt_new_request(
            args.audio_vid,
            args.audio_md5,
            args.duration_ms or 10000,
            args.language or "zh-CN",
            args.translation_language,
            args.use_translation,
        )

    elif args.mode in {"tts-query", "stt-query"}:
        if not args.task_id or not args.token:
            print("Error: need --task-id and --token", file=sys.stderr)
            sys.exit(1)
        url, headers, body_text = client.build_query_request(
            args.task_id, args.token, mode=args.mode, bind_id=args.bind_id
        )
    else:
        print(f"Error: unknown mode {args.mode}", file=sys.stderr)
        sys.exit(1)

    req_dump = {"url": url, "headers": headers, "body": json.loads(body_text)}

    if args.dry_run:
        print(json.dumps(req_dump, ensure_ascii=False, indent=2))
        return

    if client.session is None:
        print("Error: pip install requests is required to execute API requests", file=sys.stderr)
        sys.exit(1)

    try:
        if args.mode in {"tts-query", "stt-query"}:
            response_data = (client.query_tts_task if args.mode == "tts-query" else client.query_stt_task)(
                args.task_id, args.token, bind_id=args.bind_id
            )
        elif args.mode == "tts-new":
            response_data = client.create_tts_task(
                texts, args.voice, args.resource_id, payload_sign=args.payload_sign,
            )
        else:
            response_data = client.create_stt_task(
                args.audio_vid, args.audio_md5, args.duration_ms or 10000,
                args.language or "zh-CN", args.translation_language, args.use_translation,
            )
            if (file_mode or args.srt_out) and not args.no_wait:
                tasks = (response_data.get("data") or {}).get("tasks") or []
                if not tasks:
                    raise RuntimeError(f"No STT task returned from API: {response_data}")
                task = tasks[0]
                task_id, token = task.get("id"), task.get("token")
                if not task_id or not token:
                    raise RuntimeError(f"STT create response omitted task id/token: {response_data}")
                import time
                started = time.monotonic()
                while time.monotonic() - started < 120:
                    response_data = client.query_stt_task(
                        task_id, token,
                        bind_id=task.get("bind_id") or (response_data.get("data") or {}).get("bind_id") or "",
                    )
                    queried = (response_data.get("data") or {}).get("tasks") or []
                    status = str(queried[0].get("status", "")).lower() if queried else ""
                    if status in {"success", "succeed", "succeeded", "completed", "done"}:
                        break
                    if status in {"failed", "failure", "error"}:
                        raise RuntimeError(f"STT task failed: {response_data}")
                    time.sleep(2)
                else:
                    raise RuntimeError("STT task did not complete within 120 seconds")
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(response_data, ensure_ascii=False, indent=2))
    if args.out:
        save_json(response_data, args.out)
    if args.srt_out:
        try:
            tasks = (response_data.get("data") or {}).get("tasks") or []
            if tasks:
                status = str(tasks[0].get("status", "")).lower()
                if status and status not in {"success", "succeed", "succeeded", "completed", "done"}:
                    raise ValueError(f"STT task is not complete (status={status}); no SRT was written")
            client.write_srt(
                response_data,
                args.srt_out,
                use_translation=args.use_translation,
            )
        except Exception as exc:
            print(f"Could not write SRT: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"SRT written: {args.srt_out}")


if __name__ == "__main__":
    main()
