const https = require("https");
const fs = require("fs");
const path = require("path");
const os = require("os");

const PORT = 3000;
const ROOT_DIR = __dirname;
const CERT_DIR = path.join(os.homedir(), ".office-addin-dev-certs");

const certFile = path.join(CERT_DIR, "localhost.crt");
const keyFile = path.join(CERT_DIR, "localhost.key");

if (!fs.existsSync(certFile) || !fs.existsSync(keyFile)) {
  console.error("SSL Certificates not found in " + CERT_DIR);
  process.exit(1);
}

const options = {
  key: fs.readFileSync(keyFile),
  cert: fs.readFileSync(certFile)
};

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml"
};

const server = https.createServer(options, (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");

  let reqPath = req.url.split("?")[0];
  if (reqPath === "/" || reqPath === "") {
    reqPath = "/index.html";
  }

  const filePath = path.join(ROOT_DIR, reqPath);

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": contentType });
    fs.createReadStream(filePath).pipe(res);
  } else {
    // If an icon is requested that does not exist, return an empty 204 or transparent 1x1 png
    if (reqPath.startsWith("/assets/")) {
      res.writeHead(200, { "Content-Type": "image/png" });
      res.end();
      return;
    }
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("404 Not Found: " + reqPath);
  }
});

server.listen(PORT, () => {
  console.log(`Office Add-in HTTPS Server running at https://localhost:${PORT}/`);
  console.log(`Taskpane URL: https://localhost:${PORT}/index.html`);
});
