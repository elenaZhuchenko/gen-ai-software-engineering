import { useState, useCallback, type DragEvent } from 'react';
import { useImport } from '../hooks/useImport';
import { useToast } from '../components/shared/Toast';
import type { ImportSummary } from '../types/ticket';

export function ImportPage() {
  const { mutate: importFile, isPending } = useImport();
  const { toast } = useToast();

  const [file, setFile] = useState<File | null>(null);
  const [autoClassify, setAutoClassify] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState<ImportSummary | null>(null);

  const handleFile = useCallback(
    (f: File) => {
      const ext = f.name.split('.').pop()?.toLowerCase();
      if (!['csv', 'json', 'xml'].includes(ext ?? '')) {
        toast('Only CSV, JSON, and XML files are supported', 'error');
        return;
      }
      setFile(f);
      setResult(null);
    },
    [toast],
  );

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile],
  );

  function handleSubmit() {
    if (!file) return;
    importFile(
      { file, autoClassify },
      {
        onSuccess: (summary) => {
          setResult(summary);
          toast(`Imported ${summary.successful} of ${summary.total} tickets`);
          setFile(null);
        },
        onError: (err: unknown) => {
          const msg =
            (err as { response?: { data?: { detail?: string } } })?.response
              ?.data?.detail ?? 'Import failed';
          toast(msg, 'error');
        },
      },
    );
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Import Tickets
      </h1>
      <p className="text-sm text-gray-500 mb-8">
        Upload a CSV, JSON, or XML file to import tickets in bulk.
      </p>

      <div
        onDrop={onDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => document.getElementById('file-input')?.click()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : file
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 hover:border-blue-300 hover:bg-gray-50'
        }`}
      >
        <input
          id="file-input"
          type="file"
          accept=".csv,.json,.xml"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
            e.target.value = '';
          }}
        />
        {file ? (
          <div className="flex flex-col items-center gap-2">
            <svg
              className="w-10 h-10 text-green-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="font-medium text-gray-900">{file.name}</p>
            <p className="text-xs text-gray-400">
              {(file.size / 1024).toFixed(1)} KB · Click to change
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <svg
              className="w-10 h-10 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="font-medium text-gray-600">
              Drop a file here, or click to browse
            </p>
            <p className="text-xs text-gray-400">Accepts .csv · .json · .xml</p>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 mt-4">
        <input
          type="checkbox"
          id="auto-classify"
          checked={autoClassify}
          onChange={(e) => setAutoClassify(e.target.checked)}
          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
        />
        <label htmlFor="auto-classify" className="text-sm text-gray-700">
          Auto-classify imported tickets
        </label>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || isPending}
        className="mt-6 w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
      >
        {isPending ? 'Importing…' : 'Import Tickets'}
      </button>

      {result && (
        <div className="mt-8 space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-200">
              <p className="text-2xl font-bold text-gray-900">{result.total}</p>
              <p className="text-xs text-gray-500 mt-1">Total Parsed</p>
            </div>
            <div className="bg-green-50 rounded-xl p-4 text-center border border-green-200">
              <p className="text-2xl font-bold text-green-700">
                {result.successful}
              </p>
              <p className="text-xs text-green-500 mt-1">Imported</p>
            </div>
            <div
              className={`rounded-xl p-4 text-center border ${
                result.failed > 0
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <p
                className={`text-2xl font-bold ${
                  result.failed > 0 ? 'text-red-700' : 'text-gray-400'
                }`}
              >
                {result.failed}
              </p>
              <p
                className={`text-xs mt-1 ${
                  result.failed > 0 ? 'text-red-500' : 'text-gray-400'
                }`}
              >
                Failed
              </p>
            </div>
          </div>

          {result.errors.length > 0 && (
            <details className="bg-red-50 border border-red-200 rounded-xl">
              <summary className="px-4 py-3 text-sm font-medium text-red-800 cursor-pointer select-none">
                {result.errors.length} import error
                {result.errors.length !== 1 ? 's' : ''}
              </summary>
              <div className="px-4 pb-4 space-y-2">
                {result.errors.map((err, i) => (
                  <div key={i} className="text-xs text-red-700 flex gap-2">
                    <span className="font-mono font-medium">
                      Row {err.row}:
                    </span>
                    <span>{err.error}</span>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
