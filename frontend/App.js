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
    formData.append("api_key", provider === "google" ? apiKey : "");
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
    <div className="min-h-screen flex items-center justify-center bg-[#f5f5dc] p-6">
      <div className="max-w-4xl w-full bg-[#EDE8D0] shadow-lg rounded-2xl p-8">
        <h1 className="text-3xl font-bold text-[#C8B9B6] mb-6 text-center">
          AI Overview – PowerPoint Generator
        </h1>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block mb-1 font-semibold text-[#C8B9B6]">Your Text</label>
            <textarea
              className="w-full p-4 rounded-lg border border-[#C8B9B6] focus:outline-none focus:ring-2 focus:ring-[#C8B9B6]"
              placeholder="Paste your text here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              required
            />
          </div>

          <div>
            <label className="block mb-1 font-semibold text-[#C8B9B6]">Guidance (Optional)</label>
            <input
              type="text"
              className="w-full p-3 rounded-lg border border-[#C8B9B6] focus:outline-none focus:ring-2 focus:ring-[#C8B9B6]"
              placeholder="e.g., Turn into an investor pitch deck"
              value={guidance}
              onChange={(e) => setGuidance(e.target.value)}
            />
          </div>

          <div>
            <label className="block mb-1 font-semibold text-[#C8B9B6]">Select LLM Provider</label>
            <select
              className="w-full p-3 rounded-lg border border-[#C8B9B6] focus:outline-none focus:ring-2 focus:ring-[#C8B9B6]"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            >
              <option value="google">Google</option>
              <option value="gemini">Gemini</option>
            </select>
          </div>

          {provider === "google" && (
            <div>
              <label className="block mb-1 font-semibold text-[#C8B9B6]">Google API Key</label>
              <input
                type="password"
                className="w-full p-3 rounded-lg border border-[#C8B9B6] focus:outline-none focus:ring-2 focus:ring-[#C8B9B6]"
                placeholder="Enter your Google API Key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                required
              />
            </div>
          )}

          <div>
            <label className="block mb-1 font-semibold text-[#C8B9B6]">Upload PPTX Template</label>
            <input
              type="file"
              accept=".pptx,.potx"
              className="w-full"
              onChange={(e) => setTemplateFile(e.target.files[0])}
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-[#C8B9B6] hover:bg-[#B0A09B] text-white font-bold py-3 rounded-lg transition-colors"
          >
            Generate Presentation
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
