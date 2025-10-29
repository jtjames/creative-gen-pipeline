"""Manual smoke tests for the Dropbox storage helper."""
from storage import DropboxStorage


def run():
    storage = DropboxStorage()
    print(f"Root path: {storage.root_path}")

    sample_paths = []
    try:
        for idx, path in enumerate(storage.list_paths("")):
            sample_paths.append(path)
            if idx >= 4:
                break
    except RuntimeError as exc:
        print(f"Listing failed: {exc}")
    else:
        print("Sample paths:", sample_paths or "<none>")

    test_path = "smoke-tests/health-check.txt"
    artifact = storage.upload_bytes(
        path=test_path,
        data=b"creative automation hello",
    )
    print("Uploaded artifact:", artifact)
    link = storage.generate_temporary_link(test_path)
    print("Temporary link:", link)


if __name__ == "__main__":
    run()
