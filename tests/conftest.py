"""Shared test doubles for the offline test suite."""

import json


class FakeResponse:
    def __init__(self, data=None, status_code=200, content=b"", text=None):
        self._data = data
        self.status_code = status_code
        self.content = content
        if text is not None:
            self._text = text
        elif data is None:
            self._text = content.decode("utf-8", "replace")
        else:
            self._text = json.dumps(data, ensure_ascii=False)

    def json(self):
        if isinstance(self._data, Exception):
            raise self._data
        return self._data

    @property
    def text(self):
        return self._text


class FakeSession:
    """Small requests.Session substitute with queued responses."""

    def __init__(self, post_responses=None, get_responses=None):
        self.post_responses = list(post_responses or [])
        self.get_responses = list(get_responses or [])
        self.posts = []
        self.gets = []

    def post(self, url, headers=None, data=None, timeout=None, allow_redirects=None):
        self.posts.append(
            {
                "url": url,
                "headers": headers,
                "data": data,
                "timeout": timeout,
                "allow_redirects": allow_redirects,
            }
        )
        if not self.post_responses:
            raise AssertionError(f"Unexpected POST to {url}")
        response = self.post_responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def get(self, url, timeout=None, allow_redirects=None):
        self.gets.append(
            {"url": url, "timeout": timeout, "allow_redirects": allow_redirects}
        )
        if not self.get_responses:
            raise AssertionError(f"Unexpected GET to {url}")
        response = self.get_responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def create_task_response(task_id="task-1", token="token-1", bind_id="bind-1"):
    return FakeResponse(
        {
            "ret": 0,
            "data": {
                "tasks": [
                    {
                        "id": task_id,
                        "token": token,
                        "bind_id": bind_id,
                        "status": "queued",
                    }
                ]
            },
        }
    )


def completed_tts_response(url="https://cdn.example/audio.mp3", status="succeed"):
    return _tts_response([url], status)


def completed_tts_response_multi(urls, status="succeed"):
    return _tts_response(list(urls), status)


def _tts_response(urls, status):
    return FakeResponse(
        {
            "ret": 0,
            "data": {
                "tasks": [
                    {
                        "id": "task-1",
                        "status": status,
                        "payload": json.dumps(
                            {
                                "audio_subtitles": [
                                    {
                                        "speech_url": url,
                                        "text": f"segment-{index}",
                                    }
                                    for index, url in enumerate(urls, 1)
                                ]
                            }
                        ),
                    }
                ]
            },
        }
    )


def completed_stt_response():
    payload = {
        "utterances": [
            {
                "text": "Xin chào",
                "start_time": 0,
                "end_time": 1200,
                "translation_text": "Hello",
                "words": [
                    {
                        "text": "Xin",
                        "start_time": 0,
                        "end_time": 400,
                        "blank_duration": 0,
                    }
                ],
            }
        ]
    }
    return FakeResponse(
        {
            "ret": 0,
            "data": {
                "tasks": [
                    {
                        "id": "task-1",
                        "status": "succeed",
                        "payload": json.dumps(payload),
                    }
                ]
            },
        }
    )
