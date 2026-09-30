from io import BytesIO

from fastapi import Request
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from python_multipart import MultipartParser
from python_multipart.multipart import parse_options_header

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_PDF_PAGES = 20
MAX_EXTRACTED_CHARACTERS = 100_000


class ResumeFileError(ValueError):
    pass


async def read_pdf_request(request: Request) -> bytes:
    media_type, parameters = parse_options_header(request.headers.get("content-type"))
    if media_type != b"multipart/form-data" or b"boundary" not in parameters:
        raise ResumeFileError("CV upload must use multipart/form-data")

    content = bytearray()
    current_header_name = bytearray()
    current_header_value = bytearray()
    headers: dict[bytes, bytes] = {}
    is_file_part = False
    file_count = 0

    def on_part_begin() -> None:
        nonlocal headers, is_file_part
        headers = {}
        is_file_part = False

    def on_header_field(data: bytes, start: int, end: int) -> None:
        current_header_name.extend(data[start:end])

    def on_header_value(data: bytes, start: int, end: int) -> None:
        current_header_value.extend(data[start:end])

    def on_header_end() -> None:
        headers[bytes(current_header_name).lower()] = bytes(current_header_value)
        current_header_name.clear()
        current_header_value.clear()

    def on_headers_finished() -> None:
        nonlocal file_count, is_file_part
        _, options = parse_options_header(headers.get(b"content-disposition"))
        is_file_part = options.get(b"name") == b"file" and b"filename" in options
        if is_file_part:
            file_count += 1
            if file_count > 1:
                raise ResumeFileError("Upload exactly one CV file")
            if headers.get(b"content-type") != b"application/pdf":
                raise ResumeFileError("CV must have the application/pdf content type")

    def on_part_data(data: bytes, start: int, end: int) -> None:
        if is_file_part:
            content.extend(data[start:end])
            if len(content) > MAX_PDF_BYTES:
                raise ResumeFileError("CV must be no larger than 5 MiB")

    parser = MultipartParser(
        parameters[b"boundary"],
        {
            "on_part_begin": on_part_begin,
            "on_header_field": on_header_field,
            "on_header_value": on_header_value,
            "on_header_end": on_header_end,
            "on_headers_finished": on_headers_finished,
            "on_part_data": on_part_data,
        },
    )
    request_size = 0
    try:
        async for chunk in request.stream():
            request_size += len(chunk)
            if request_size > MAX_PDF_BYTES + MAX_MULTIPART_OVERHEAD_BYTES:
                raise ResumeFileError("CV multipart request is too large")
            parser.write(chunk)
        parser.finalize()
    except ResumeFileError:
        raise
    except Exception as exc:
        raise ResumeFileError("CV multipart request is invalid") from exc

    if file_count != 1:
        raise ResumeFileError("Upload exactly one CV file")
    if not content.startswith(b"%PDF-"):
        raise ResumeFileError("CV does not have a valid PDF header")
    return bytes(content)


def extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise ResumeFileError("Encrypted PDFs are not supported")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ResumeFileError(f"CV must contain at most {MAX_PDF_PAGES} pages")

        parts: list[str] = []
        characters = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            characters += len(text)
            if characters > MAX_EXTRACTED_CHARACTERS:
                raise ResumeFileError(
                    f"CV text must contain at most {MAX_EXTRACTED_CHARACTERS} characters"
                )
            parts.append(text)
    except ResumeFileError:
        raise
    except (PdfReadError, EOFError, ValueError, TypeError) as exc:
        raise ResumeFileError("CV could not be parsed as a PDF") from exc

    extracted = "\n".join(parts).strip()
    if not extracted:
        raise ResumeFileError("CV contains no extractable text")
    return extracted
