import React, { useState, useEffect } from 'react';
import './App.css';
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2, Sparkles, TrendingUp, ShieldAlert, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
    const [file, setFile] = useState(null);
    const [jobId, setJobId] = useState(null);
    const [status, setStatus] = useState(null); // 'idle', 'uploading', 'processing', 'completed', 'failed'
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && selectedFile.name.endsWith('.csv')) {
            setFile(selectedFile);
            setError(null);
        } else {
            setError('Please select a valid CSV file.');
            setFile(null);
        }
    };

    const uploadFile = async () => {
        if (!file) return;
        setStatus('uploading');
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/jobs/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            setJobId(data.id);
            setStatus('processing');
        } catch (err) {
            setError(err.message);
            setStatus('failed');
        }
    };

    useEffect(() => {
        let interval;
        if (status === 'processing' && jobId) {
            interval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/jobs/${jobId}/status`);
                    const data = await response.json();

                    if (data.job.status === 'completed') {
                        setStatus('completed');
                        fetchResults(jobId);
                        clearInterval(interval);
                    } else if (data.job.status === 'failed') {
                        setStatus('failed');
                        setError(data.job.error_message || 'Processing failed');
                        clearInterval(interval);
                    }
                } catch (err) {
                    console.error('Polling error:', err);
                }
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [status, jobId]);

    const fetchResults = async (id) => {
        try {
            const response = await fetch(`/api/jobs/${id}/results`);
            const data = await response.json();
            setResults(data);
        } catch (err) {
            setError('Failed to fetch results');
        }
    };

    const reset = () => {
        setFile(null);
        setJobId(null);
        setStatus('idle');
        setResults(null);
        setError(null);
    };

    return (
        <div className="App">
            <nav className="navbar">
                <div className="nav-content">
                    <div className="logo">
                        <Sparkles className="logo-icon" size={28} />
                        <span>TransactionProcessingAI</span>
                    </div>
                    <div className="nav-links">
                        <a href="#" className="active">Dashboard</a>
                        <a href="http://localhost:8000/docs" target="_blank">API Docs</a>
                    </div>
                </div>
            </nav>

            <main className="container">
                <AnimatePresence mode="wait">
                    {!jobId && status !== 'uploading' && (
                        <motion.div
                            key="upload"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="upload-section glass-card"
                        >
                            <div className="section-header">
                                <h1>Transaction Pipeline</h1>
                                <p>Upload your financial records for AI-powered cleaning, anomaly detection, and smart categorization.</p>
                            </div>

                            <div className={`dropzone ${file ? 'has-file' : ''}`}>
                                <input type="file" id="fileInput" accept=".csv" onChange={handleFileChange} />
                                <label htmlFor="fileInput">
                                    <div className="dropzone-content">
                                        {file ? (
                                            <div className="file-info">
                                                <FileText size={48} className="file-icon" />
                                                <span className="file-name">{file.name}</span>
                                                <span className="file-size">{(file.size / 1024).toFixed(2)} KB</span>
                                            </div>
                                        ) : (
                                            <>
                                                <Upload size={48} className="upload-icon" />
                                                <span className="upload-text">Drag & drop your CSV file or <strong>browse</strong></span>
                                                <span className="upload-hint">Only .csv files supported</span>
                                            </>
                                        )}
                                    </div>
                                </label>
                            </div>

                            {error && <div className="error-badge"><AlertCircle size={18} /> {error}</div>}

                            <button
                                className="btn-primary"
                                onClick={uploadFile}
                                disabled={!file}
                            >
                                Start Processing <ChevronRight size={20} />
                            </button>
                        </motion.div>
                    )}

                    {status === 'uploading' || status === 'processing' ? (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.05 }}
                            className="loading-section glass-card"
                        >
                            <div className="loader-container">
                                <div className="pulsing-circle">
                                    <Loader2 className="spinning" size={40} />
                                </div>
                            </div>
                            <h2>{status === 'uploading' ? 'Uploading Data...' : 'AI is analyzing your transactions...'}</h2>
                            <p>This usually takes 15-30 seconds depending on the file size and Gemini API speed.</p>
                            <div className="job-meta">Job ID: <span className="id-tag">{jobId || 'Generating...'}</span></div>
                        </motion.div>
                    ) : null}

                    {status === 'completed' && results && (
                        <motion.div
                            key="results"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="results-container"
                        >
                            <div className="results-header">
                                <div className="header-left">
                                    <div className="status-badge success">
                                        <CheckCircle2 size={16} /> Completed
                                    </div>
                                    <h1>Analysis Results</h1>
                                </div>
                                <button className="btn-secondary" onClick={reset}>Upload New File</button>
                            </div>

                            <div className="results-grid">
                                <div className="card-summary glass-card">
                                    <div className="card-icon-title">
                                        <Sparkles className="icon-purple" />
                                        <h3>AI Narrative Summary</h3>
                                    </div>
                                    <p className="narrative-text">{results.ai_summary?.narrative}</p>
                                    <div className={`risk-indicator ${results.ai_summary?.risk_level}`}>
                                        Risk Level: <strong>{results.ai_summary?.risk_level?.toUpperCase()}</strong>
                                    </div>
                                </div>

                                <div className="stats-grid">
                                    <div className="stat-card glass-card">
                                        <TrendingUp className="icon-blue" />
                                        <div className="stat-info">
                                            <span className="stat-label">Total Spend (INR)</span>
                                            <span className="stat-value">₹{parseFloat(results.ai_summary?.total_spend_inr).toLocaleString()}</span>
                                        </div>
                                    </div>
                                    <div className="stat-card glass-card">
                                        <ShieldAlert className="icon-orange" />
                                        <div className="stat-info">
                                            <span className="stat-label">Anomalies Detected</span>
                                            <span className="stat-value">{results.ai_summary?.anomaly_count}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="top-merchants glass-card">
                                    <h3>Top Merchants</h3>
                                    <div className="merchant-list">
                                        {results.ai_summary?.top_merchants.map((m, i) => (
                                            <div key={i} className="merchant-item">
                                                <span className="rank">{i + 1}</span>
                                                <span className="name">{m}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="anomalies-section glass-card">
                                    <h3>Flagged Anomalies</h3>
                                    <div className="anomaly-table-container">
                                        <table className="anomaly-table">
                                            <thead>
                                                <tr>
                                                    <th>ID</th>
                                                    <th>Merchant</th>
                                                    <th>Amount</th>
                                                    <th>Reason</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {results.anomalies.map((a, i) => (
                                                    <tr key={i}>
                                                        <td><code>{a.txn_id}</code></td>
                                                        <td>{a.merchant}</td>
                                                        <td>{a.amount} {a.currency}</td>
                                                        <td className="reason">{a.anomaly_reason}</td>
                                                    </tr>
                                                ))}
                                                {results.anomalies.length === 0 && (
                                                    <tr><td colSpan="4" className="empty-state">No anomalies found.</td></tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {status === 'failed' && (
                        <motion.div
                            key="error"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="error-section glass-card"
                        >
                            <AlertCircle size={64} className="icon-red" />
                            <h2>Processing Failed</h2>
                            <p>{error}</p>
                            <button className="btn-primary" onClick={reset}>Try Again</button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>
        </div>
    );
}

export default App;
