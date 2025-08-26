import React, { useState } from "react";

function App() {
  const [text, setText] = useState("");
  const [guidance, setGuidance] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState("google");
  const [templateFile, setTemplateFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("text", text);
    formData.append("guidance", guidance);
    formData.append("llm_provider", provider);
    formData.append("api_key", apiKey);
    formData.append("template", templateFile);

    const res = await fetch("https://<YOUR_BACKEND_URL>/generate-presentation", {
      method: "POST",
      body: formData
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "generated_presentation.pptx";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } else {
      alert("Failed to generate presentation.");
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Your Text, Your Style – PPT Generator</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          className="w-full p-2 border"
          placeholder="Paste your text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          required
        />
        <input
          type="text"
          className="w-full p-2 border"
          placeholder="Guidance (optional)"
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
        />
        <select className="w-full p-2 border" value={provider} onChange={(e) => setProvider(e.target.value)}>
          <option value="google">Google</option>
        </select>
        <input
          type="password"
          className="w-full p-2 border"
          placeholder="Google API Key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          required
        />
        <input type="file" accept=".pptx,.potx" onChange={(e) => setTemplateFile(e.target.files[0])} required />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Generate PPT</button>
      </form>
    </div>
  );
}

export default App;
