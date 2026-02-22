document.getElementById("uploadForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const files = document.getElementById("files").files;
    const prompt = document.getElementById("prompt").value;
    const format = document.getElementById("format").value;

    const formData = new FormData();

    for (let file of files) {
        formData.append("files", file);
    }

    formData.append("prompt", prompt);
    formData.append("output_format", format);

    document.getElementById("status").innerText = "Processing...";

    const response = await fetch("http://localhost:8000/process", {
        method: "POST",
        body: formData
    });

    const result = await response.json();

    if (result.error) {
        document.getElementById("status").innerText = result.error;
        return;
    }

    document.getElementById("status").innerText = "Done!";

    document.getElementById("download").innerHTML =
        `<a href="http://localhost:8000${result.download_url}">
            Download File
        </a>`;
});
