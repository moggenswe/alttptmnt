// Shows the download button with the zip's size and date. downloads/version.json is written by
// tools/build_site.py when the site is built for hosting; opened from the zip itself there is no download to offer,
// so the button stays hidden.
fetch("downloads/version.json")
  .then(response => (response.ok ? response.json() : Promise.reject(response.status)))
  .then(version => {
    const megabytes = (version.size / 1048576).toFixed(1);
    for (const box of document.querySelectorAll(".download")) {
      box.querySelector(".download-meta").textContent =
        `zip, ${megabytes} MB · updated ${version.date} · version ${version.commit}`;
      box.hidden = false;
    }
  })
  .catch(() => {});
