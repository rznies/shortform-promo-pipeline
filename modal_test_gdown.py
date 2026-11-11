import modal

app = modal.App("test-gdown")
image = modal.Image.debian_slim().pip_install("gdown")

@app.function(image=image, timeout=300)
def test_download():
    import gdown, os
    url = "https://drive.google.com/uc?id=12RYcCkQtgzBYXU0fRdLIhg830UnIdDSh"
    out = "/tmp/test.mp4"
    gdown.download(url, out, quiet=False)
    size = os.path.getsize(out) / (1024 * 1024)
    return f"Downloaded {size:.2f} MB in Modal cloud!"

@app.local_entrypoint()
def main():
    print(test_download.remote())
