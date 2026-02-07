async function runQA() {
  const mode = document.getElementById("mode").value;
  const file = document.getElementById("fileInput").files[0];

  if (!file) {
    alert("Please upload a file");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const endpoint = mode === "image" ? "/qa/image" : "/qa/geometry";

  const res = await fetch(endpoint, {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  const errorsDiv = document.getElementById("errors");
  errorsDiv.innerHTML = "";

  data.errors.forEach(e => {
    errorsDiv.innerHTML += `<p><b>${e.type}</b>: ${e.description}</p>`;
  });

  document.getElementById("outputImage").src = data.output_url;
}
