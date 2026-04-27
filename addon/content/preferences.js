// Zotron Preference Pane
// Uses Zotero.HTTP.request() (not fetch!) for test buttons

var PREF = "extensions.zotron.";

var OCR_CONFIGS = {
  glm:    { url: "https://open.bigmodel.cn/api/paas/v4/layout_parsing",                                    model: "glm-ocr" },
  qwen:   { url: "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",    model: "qwen-vl-ocr" },
  custom: { url: "",                                                                                         model: "" },
};

var EMB_CONFIGS = {
  ollama:    { url: "http://localhost:11434",                                            model: "qwen3-embedding:4b" },
  zhipu:     { url: "https://open.bigmodel.cn/api/paas/v4/embeddings",                  model: "embedding-3" },
  dashscope: { url: "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",     model: "text-embedding-v4" },
  doubao:    { url: "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal",  model: "doubao-embedding-vision-251215" },
  openai:    { url: "https://api.openai.com/v1/embeddings",                             model: "text-embedding-3-small" },
};

function sp(key, val) { try { Zotero.Prefs.set(PREF + key, val, true); } catch(e) {} }
function gp(key) { try { var v = Zotero.Prefs.get(PREF + key, true); return (v === undefined || v === null || v === "undefined") ? "" : v; } catch(e) { return ""; } }
function se(id, val) { var el = document.getElementById(id); if (el) el.value = val || ""; }
function setStatus(id, msg, color) { var el = document.getElementById(id); if (el) { el.textContent = msg; el.style.color = color; } }

function applyOCR() {
  var p = gp("ocr.provider") || "glm";
  var c = OCR_CONFIGS[p]; if (!c) return;
  sp("ocr.apiUrl", c.url); sp("ocr.model", c.model);
  se("zotron-ocr-apiurl", c.url); se("zotron-ocr-model", c.model);
}

function applyEmb() {
  var p = gp("embedding.provider") || "ollama";
  var c = EMB_CONFIGS[p]; if (!c) return;
  sp("embedding.apiUrl", c.url); sp("embedding.model", c.model);
  se("zotron-emb-apiurl", c.url); se("zotron-emb-model", c.model);
}

function testOCR() {
  var url = gp("ocr.apiUrl");
  var keyEl = document.getElementById("zotron-ocr-apikey");
  var key = keyEl ? keyEl.value : gp("ocr.apiKey");
  if (!key) { setStatus("zotron-ocr-status", "请先填写 API Key", "#e74c3c"); return; }
  setStatus("zotron-ocr-status", "测试中...", "#f39c12");
  var model = gp("ocr.model") || "glm-ocr";
  Zotero.HTTP.request("POST", url, {
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + key },
    body: JSON.stringify({ model: model }),
    timeout: 10000,
    successCodes: false,
  }).then(function(xhr) {
    if (xhr.status === 401 || xhr.status === 403) {
      setStatus("zotron-ocr-status", "API Key 无效 (" + xhr.status + ")", "#e74c3c");
    } else {
      setStatus("zotron-ocr-status", "连接成功 (HTTP " + xhr.status + ")", "#27ae60");
    }
  }).catch(function(e) {
    setStatus("zotron-ocr-status", "连接失败: " + (e.message || e), "#e74c3c");
  });
}

function testEmb() {
  var provider = gp("embedding.provider") || "ollama";
  var url = gp("embedding.apiUrl");
  var keyEl = document.getElementById("zotron-emb-apikey");
  var key = keyEl ? keyEl.value : gp("embedding.apiKey");
  var model = gp("embedding.model");
  if (provider !== "ollama" && !key) { setStatus("zotron-emb-status", "请先填写 API Key", "#e74c3c"); return; }
  setStatus("zotron-emb-status", "测试中...", "#f39c12");

  var reqUrl, body, headers;
  if (provider === "ollama") {
    reqUrl = url + "/api/embeddings";
    body = JSON.stringify({ model: model, prompt: "test" });
    headers = { "Content-Type": "application/json" };
  } else if (provider === "doubao") {
    reqUrl = url;
    body = JSON.stringify({ model: model, input: [{ type: "text", text: "test" }] });
    headers = { "Content-Type": "application/json", "Authorization": "Bearer " + key };
  } else {
    reqUrl = url;
    body = JSON.stringify({ model: model, input: "test" });
    headers = { "Content-Type": "application/json", "Authorization": "Bearer " + key };
  }

  Zotero.HTTP.request("POST", reqUrl, {
    headers: headers,
    body: body,
    timeout: 10000,
    successCodes: false,
  }).then(function(xhr) {
    if (xhr.status === 401 || xhr.status === 403) {
      setStatus("zotron-emb-status", "API Key 无效 (" + xhr.status + ")", "#e74c3c");
    } else if (xhr.status >= 200 && xhr.status < 300) {
      try {
        var data = JSON.parse(xhr.responseText);
        var dim = provider === "ollama"
          ? (data.embedding ? data.embedding.length : "?")
          : (data.data && data.data[0] ? data.data[0].embedding.length : "?");
        setStatus("zotron-emb-status", "连接成功 — 向量维度: " + dim, "#27ae60");
      } catch(e) {
        setStatus("zotron-emb-status", "连接成功 (HTTP " + xhr.status + ")", "#27ae60");
      }
    } else {
      setStatus("zotron-emb-status", "请求失败 (HTTP " + xhr.status + ")", "#e74c3c");
    }
  }).catch(function(e) {
    setStatus("zotron-emb-status", "连接失败: " + (e.message || e), "#e74c3c");
  });
}

function init() {
  // Clean undefined prefs
  var keys = ["ocr.apiKey", "ocr.apiUrl", "ocr.model", "embedding.apiKey", "embedding.apiUrl", "embedding.model"];
  for (var i = 0; i < keys.length; i++) { if (!gp(keys[i])) sp(keys[i], ""); }

  applyOCR();
  applyEmb();

  var ocrSel = document.getElementById("zotron-ocr-provider");
  var embSel = document.getElementById("zotron-emb-provider");
  if (ocrSel) ocrSel.addEventListener("command", function() { sp("ocr.provider", ocrSel.value); applyOCR(); });
  if (embSel) embSel.addEventListener("command", function() { sp("embedding.provider", embSel.value); applyEmb(); });

  // Bind text inputs to save on change (Zotero 7 HTML prefs don't auto-bind)
  var bindings = [
    ["zotron-ocr-apikey", "ocr.apiKey"],
    ["zotron-ocr-apiurl", "ocr.apiUrl"],
    ["zotron-ocr-model", "ocr.model"],
    ["zotron-emb-apikey", "embedding.apiKey"],
    ["zotron-emb-apiurl", "embedding.apiUrl"],
    ["zotron-emb-model", "embedding.model"],
  ];
  for (var b of bindings) {
    (function(elId, prefKey) {
      var el = document.getElementById(elId);
      if (el) {
        // Load saved value into field
        var saved = gp(prefKey);
        if (saved) el.value = saved;
        // Save on change
        el.addEventListener("change", function() { sp(prefKey, el.value); });
      }
    })(b[0], b[1]);
  }

  var ocrBtn = document.getElementById("zotron-ocr-test");
  var embBtn = document.getElementById("zotron-emb-test");
  if (ocrBtn) ocrBtn.addEventListener("click", testOCR);
  if (embBtn) embBtn.addEventListener("click", testEmb);
}

if (document.getElementById("zotron-ocr-provider")) { init(); }
else { setTimeout(init, 300); }
