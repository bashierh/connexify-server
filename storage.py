"""
Persistent storage abstraction.
Uses Google Cloud Storage when GCS_BUCKET is set, otherwise local filesystem.

Layout in GCS:
  data/           – JSON data files (license_database.json, portal_users.json)
  static/         – Binary files (installers, images)
"""
import json
import os
import mimetypes

GCS_BUCKET = os.getenv("GCS_BUCKET", "")
_gcs_client = None
_gcs_bucket = None


def _get_bucket():
    """Lazy-init GCS client and bucket."""
    global _gcs_client, _gcs_bucket
    if _gcs_bucket is not None:
        return _gcs_bucket
    from google.cloud import storage as gcs
    _gcs_client = gcs.Client()
    _gcs_bucket = _gcs_client.bucket(GCS_BUCKET)
    print(f"[Storage] Using GCS bucket: {GCS_BUCKET}")
    return _gcs_bucket


def using_gcs() -> bool:
    """Return True if GCS backend is active."""
    return bool(GCS_BUCKET)


# ── JSON data files ──────────────────────────────────────────────

def load_json(filepath: str) -> dict:
    """Load a JSON file from GCS or local filesystem."""
    filename = os.path.basename(filepath)
    if GCS_BUCKET:
        try:
            bucket = _get_bucket()
            blob = bucket.blob(f"data/{filename}")
            if blob.exists():
                data = json.loads(blob.download_as_text())
                print(f"[Storage] Loaded {filename} from GCS ({len(str(data))} chars)")
                return data
            else:
                print(f"[Storage] {filename} not found in GCS, returning empty")
                return {}
        except Exception as e:
            print(f"[Storage] Error loading {filename} from GCS: {e}")
            # Fallback to local
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        return json.load(f)
                except Exception:
                    pass
            return {}
    else:
        # Local filesystem fallback
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Storage] Error loading {filepath}: {e}")
                return {}
        return {}


def save_json(filepath: str, data: dict):
    """Save a JSON file to GCS and/or local filesystem."""
    filename = os.path.basename(filepath)
    # Always save locally (acts as cache on Cloud Run too)
    try:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Storage] Error saving {filepath} locally: {e}")
    # Also save to GCS if configured
    if GCS_BUCKET:
        try:
            bucket = _get_bucket()
            blob = bucket.blob(f"data/{filename}")
            blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
            print(f"[Storage] Saved {filename} to GCS")
        except Exception as e:
            print(f"[Storage] Error saving {filename} to GCS: {e}")


# ── Binary / static files (installers, images) ──────────────────

def save_file(local_dir: str, filename: str, content: bytes):
    """Save binary file to local dir and optionally GCS static/ prefix."""
    # Save locally
    try:
        os.makedirs(local_dir, exist_ok=True)
        filepath = os.path.join(local_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
    except Exception as e:
        print(f"[Storage] Error saving {filename} locally: {e}")
    # Also save to GCS
    if GCS_BUCKET:
        try:
            bucket = _get_bucket()
            blob = bucket.blob(f"static/{filename}")
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            blob.upload_from_string(content, content_type=content_type)
            print(f"[Storage] Uploaded {filename} to GCS static/ ({len(content)} bytes)")
        except Exception as e:
            print(f"[Storage] Error uploading {filename} to GCS: {e}")


def load_file(local_dir: str, filename: str) -> bytes | None:
    """Load binary file – tries GCS first, then local."""
    if GCS_BUCKET:
        try:
            bucket = _get_bucket()
            blob = bucket.blob(f"static/{filename}")
            if blob.exists():
                return blob.download_as_bytes()
        except Exception as e:
            print(f"[Storage] Error downloading {filename} from GCS: {e}")
    # Local fallback
    filepath = os.path.join(local_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None


def list_files(local_dir: str) -> list[dict]:
    """List files in static storage. Returns [{name, size_mb}]."""
    files = {}
    # Local files
    if os.path.exists(local_dir):
        for fname in os.listdir(local_dir):
            fpath = os.path.join(local_dir, fname)
            if os.path.isfile(fpath):
                files[fname] = {"name": fname, "size_mb": round(os.path.getsize(fpath) / (1024 * 1024), 2)}
    # GCS files (may include files not yet cached locally)
    if GCS_BUCKET:
        try:
            bucket = _get_bucket()
            for blob in bucket.list_blobs(prefix="static/"):
                fname = blob.name.replace("static/", "", 1)
                if fname and '/' not in fname:
                    files[fname] = {"name": fname, "size_mb": round((blob.size or 0) / (1024 * 1024), 2)}
        except Exception as e:
            print(f"[Storage] Error listing GCS files: {e}")
    return sorted(files.values(), key=lambda f: f["name"])


def file_exists(local_dir: str, filename: str) -> bool:
    """Check if a file exists in GCS or locally."""
    if GCS_BUCKET:
        try:
            bucket = _get_bucket()
            blob = bucket.blob(f"static/{filename}")
            if blob.exists():
                return True
        except Exception:
            pass
    return os.path.exists(os.path.join(local_dir, filename))
