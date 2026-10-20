"""One-file local conversion process. Never accepts a URL or enables plugins."""

import json
import resource
import sys

from markitdown import MarkItDown

from service.extraction import extract_invoice


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
    result = MarkItDown(enable_plugins=False).convert_local(sys.argv[1])
    markdown = result.text_content
    if len(markdown) > 100_000:
        raise ValueError("Converted document is too large")
    print(
        json.dumps(
            {
                "markdown": markdown,
                "title": result.title,
                "extraction": extract_invoice(markdown),
            }
        )
    )


if __name__ == "__main__":
    main()
