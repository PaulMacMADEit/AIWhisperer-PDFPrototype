function Spinner({ config }) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    const spinner = new Spin.Spinner({
      lines: 13,
      color: "#ffffff",
      ...config,
    });
    spinner.spin(ref.current);
    return () => spinner.stop();
  }, [ref]);

  return <span ref={ref} />;
}

function Result({ filename, extractedText, fullTranscript, table }) {
  const handleDownload = () => {
    window.location.href = `/download_csv/${encodeURIComponent(filename)}`;
  };

  return (
    <div className="flex flex-col items-center space-y-8 w-full">
      <h2 className="text-xl font-semibold">Here is the output for: {filename}</h2>
      <div className="flex justify-center mb-4">
        <button
          onClick={handleDownload}
          className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded text-sm"
        >
          Download CSV
        </button>
      </div>
      <div className="w-full space-y-8">
        <div className="w-full">
          <h3 className="text-lg font-semibold mb-2 text-center">Table Data</h3>
          <div className="h-64 overflow-y-auto border border-gray-300 rounded-lg flex items-center justify-center">
            <pre className="p-4 bg-gray-100 whitespace-pre-wrap text-xs font-mono w-full text-center">
              {table ? JSON.stringify(table, null, 2) : "No table data available"}
            </pre>
          </div>
        </div>
        <div className="w-full">
          <h3 className="text-lg font-semibold mb-2 text-center">AI Extracted Data</h3>
          <div className="h-64 overflow-y-auto border border-gray-300 rounded-lg flex items-center justify-center">
            <pre className="p-4 bg-gray-100 whitespace-pre-wrap text-xs font-mono w-full text-center">
              {extractedText || "No extracted data available"}
            </pre>
          </div>
        </div>
        <div className="w-full">
          <h3 className="text-lg font-semibold mb-2 text-center">Full Transcript</h3>
          <div className="h-64 overflow-y-auto border border-gray-300 rounded-lg flex items-center justify-center">
            <pre className="p-4 bg-gray-100 whitespace-pre-wrap text-xs font-mono w-full text-center">
              {fullTranscript !== null ? fullTranscript : "No full transcript available"}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

function Form({ onSubmit, onFileSelect, selectedFile, selectedModel, handleModelChange }) {
  return (
    <form className="flex flex-col space-y-4 items-center">
      <img src="logo.png" alt="Logo" className="w-56 h-29" />
      <div className="text-2xl font-semibold text-gray-700"> The Travel Package Analyzer </div>
      <input
        accept="application/pdf,image/*"
        type="file"
        name="file"
        onChange={onFileSelect}
        className="block w-full text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 cursor-pointer"
      />
      {selectedFile && (
        <p className="text-sm text-gray-600">Selected file: {selectedFile.name}</p>
      )}
      <div>
        <button
          type="button"
          onClick={onSubmit}
          disabled={!selectedFile}
          className="bg-indigo-400 disabled:bg-zinc-500 hover:bg-indigo-600 text-white font-bold py-2 px-4 rounded text-sm"
        >
          Upload
        </button>
      </div>
      <div className="mt-4">
        <select
          value={selectedModel}
          onChange={handleModelChange}
          className="mt-1 block w-full p-2 border border-gray-300 rounded"
        >
          <option value="OpenAI-GPT4">OpenAI-GPT4</option>
          <option value="Anthropic-Sonnet3.5">Anthropic-Sonnet3.5</option>
          <option value="Google-Gemini1.5">Google-Gemini1.5</option>
        </select>
        <p className="mt-2 text-sm text-gray-600">Selected Model: {selectedModel}</p>
      </div>
    </form>
  );
}

function App() {
  const [selectedFile, setSelectedFile] = React.useState();
  const [uploadStatus, setUploadStatus] = React.useState(null);
  const [extractedText, setExtractedText] = React.useState(null);
  const [fullTranscript, setFullTranscript] = React.useState(null);
  const [selectedModel, setSelectedModel] = React.useState("OpenAI-GPT4");

  const handleModelChange = (event) => {
    setSelectedModel(event.target.value);
  };

  const handleSubmission = async () => {
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("model", selectedModel);

    try {
      const resp = await fetch("/parse", {
        method: "POST",
        body: formData,
      });

      if (resp.status !== 200) {
        throw new Error("An error occurred: " + resp.status);
      }
      const body = await resp.json();
      setUploadStatus(`File "${body.filename}" uploaded successfully!`);
      setExtractedText({ filename: body.filename, text: body.text, table: body.table });
      await fetchFullTranscript(body.filename);
    } catch (error) {
      setUploadStatus(`Error: ${error.message}`);
    }
  };

  const fetchFullTranscript = async (filename) => {
    try {
      const encodedFilename = encodeURIComponent(filename);
      const resp = await fetch(`/full_transcript/${encodedFilename}`);
      if (resp.status !== 200) {
        throw new Error("An error occurred: " + resp.status);
      }
      const body = await resp.json();
      setFullTranscript(body.text);
    } catch (error) {
      console.error("Error fetching full transcript:", error);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-4xl p-8">
        <main className="rounded-xl bg-white p-8 shadow-lg">
          {!extractedText ? (
            <>
              <Form
                onSubmit={handleSubmission}
                onFileSelect={(e) => setSelectedFile(e.target.files[0])}
                selectedFile={selectedFile}
                selectedModel={selectedModel}
                handleModelChange={handleModelChange}
              />
              {uploadStatus && (
                <p className="mt-4 text-center text-green-600">{uploadStatus}</p>
              )}
            </>
          ) : (
            <Result
              filename={extractedText.filename}
              extractedText={extractedText.text}
              fullTranscript={fullTranscript}
              table={extractedText.table}
            />
          )}
        </main>
      </div>
    </div>
  );
}

const container = document.getElementById("react");
ReactDOM.createRoot(container).render(<App />);