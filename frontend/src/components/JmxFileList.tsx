import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Table, Button, Alert, Spinner, Toast, ToastContainer, Form, Row, Col, ProgressBar, InputGroup } from 'react-bootstrap';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface JmxFile {
    name: string;
    size: number;
    modified: number;
}

interface ToastMessage {
    id: number;
    title: string;
    body: string;
    variant: 'success' | 'danger';
}

interface JmxFileListProps {
    onUploadSuccess: () => void;
}

const JmxFileList = ({ onUploadSuccess }: JmxFileListProps) => {
    const [files, setFiles] = useState<JmxFile[]>([]);
    const [filteredFiles, setFilteredFiles] = useState<JmxFile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    // Upload related state
    const [file, setFile] = useState<File | null>(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Search related state
    const [searchQuery, setSearchQuery] = useState<string>('');

    const fetchFiles = useCallback(async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_URL}/files?file_type=jmx`);
            setFiles(response.data.data.files);
            setError(null);
        } catch (err: any) {
            setError(err.response?.data?.message || 'Could not fetch JMX files.');
        } finally {
            setLoading(false);
        }
    }, []);

    // Filter files based on search criteria
    const filterFiles = useCallback(() => {
        let filtered = files;

        // Filter by filename (fuzzy search)
        if (searchQuery.trim()) {
            const searchTerm = searchQuery.trim().toLowerCase();
            filtered = filtered.filter(file =>
                file.name.toLowerCase().includes(searchTerm)
            );
        }

        setFilteredFiles(filtered);
    }, [files, searchQuery]);

    // Apply filters when files or search criteria change
    useEffect(() => {
        filterFiles();
    }, [filterFiles]);

    useEffect(() => {
        fetchFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const addToast = (title: string, body: string, variant: 'success' | 'danger') => {
        const newToast: ToastMessage = { id: Date.now(), title, body, variant };
        setToasts(prev => [...prev, newToast]);
    };

    const handleExecute = async (fileName: string) => {
        try {
            const response = await axios.post(`${API_URL}/execute`, { file_name: fileName });
            addToast('Success', `Task ${response.data.data.task_id} started for ${fileName}.`, 'success');
        } catch (err: any) {
            const errorMessage = err.response?.data?.message || 'Execution failed';
            addToast('Error', `Failed to start test for ${fileName}: ${errorMessage}`, 'danger');
        }
    };

    const handleDownload = (fileName: string) => {
        window.open(`${API_URL}/download/jmx/${fileName}`, '_blank');
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setFile(event.target.files[0]);
            setUploadError(null);
            setUploadProgress(0);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setUploadError('Please select a file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            setUploadError(null);
            const response = await axios.post(`${API_URL}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
                    setUploadProgress(percentCompleted);
                },
            });
            addToast('Success', `File uploaded successfully: ${response.data.data.file_name}`, 'success');
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
            setFile(null);
            setUploadProgress(0);
            onUploadSuccess();
            fetchFiles(); // Refresh the list
        } catch (err: any) {
            setUploadError(err.response?.data?.message || 'An error occurred during upload.');
            setUploadProgress(0);
        }
    };

    const handleSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(event.target.value);
    }, []);

    const handleSearchClear = useCallback(() => {
        setSearchQuery('');
    }, []);

    if (loading) {
        return <div className="text-center"><Spinner animation="border" /></div>;
    }

    if (error) {
        return <Alert variant="danger">{error}</Alert>;
    }

    return (
        <div className="jmx-file-list">
            <Row className="mb-2 align-items-center">
                <Col md={2}>
                    <h5 className="mb-0">Available JMX Files</h5>
                </Col>
                <Col md={3}>
                    <InputGroup size="sm">
                        <Form.Control
                            type="text"
                            placeholder="Search files..."
                            value={searchQuery}
                            onChange={handleSearchChange}
                        />
                        {searchQuery && (
                            <Button
                                variant="outline-secondary"
                                onClick={handleSearchClear}
                                style={{ borderLeft: 'none' }}
                                title="Clear search"
                            >
                                ✕
                            </Button>
                        )}
                    </InputGroup>
                </Col>
                <Col md={2}>
                    <Form.Control
                        type="file"
                        accept=".jmx"
                        onChange={handleFileChange}
                        ref={fileInputRef}
                        size="sm"
                        placeholder="Upload JMX File"
                    />
                </Col>
                <Col md={1}>
                    <Button variant="primary" size="sm" onClick={handleUpload} disabled={!file}>
                        Upload
                    </Button>
                </Col>
                <Col md={1}>
                    <Button variant="secondary" size="sm" onClick={() => fetchFiles()}>Refresh</Button>
                </Col>
                <Col md={2}>
                    {uploadProgress > 0 && (
                        <ProgressBar now={uploadProgress} style={{ height: '31px' }} />
                    )}
                </Col>
                <Col md={2}>
                    <span className="text-muted">
                        {filteredFiles.length} of {files.length} files
                    </span>
                </Col>
            </Row>
            {uploadError && <Alert variant="danger" className="mb-2 py-1">{uploadError}</Alert>}
            <div style={{ height: '750px', overflowY: 'auto' }}>
                <Table striped bordered hover size="sm" className="mb-0">
                <thead>
                    <tr>
                        <th style={{ width: '80px' }}>ID</th>
                        <th>File Name</th>
                        <th>Size</th>
                        <th>Last Modified</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredFiles.length > 0 ? filteredFiles.map((file, index) => (
                        <tr key={file.name}>
                            <td style={{ width: '80px', textAlign: 'center' }}>{index + 1}</td>
                            <td>{file.name}</td>
                            <td>{`${(file.size / 1024).toFixed(2)} KB`}</td>
                            <td>{new Date(file.modified * 1000).toLocaleString()}</td>
                            <td>
                                <Button variant="success" onClick={() => handleExecute(file.name)}>
                                    Execute
                                </Button>{' '}
                                <Button variant="info" onClick={() => handleDownload(file.name)}>
                                    Download
                                </Button>
                            </td>
                        </tr>
                    )) : (
                        <tr>
                            <td colSpan={5} className="text-center">No JMX files found.</td>
                        </tr>
                    )}
                </tbody>
                </Table>
            </div>
            <ToastContainer position="top-end" className="p-3" style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 9999 }}>
                {toasts.map(toast => (
                    <Toast key={toast.id} onClose={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} delay={5000} autohide bg={toast.variant}>
                        <Toast.Header>
                            <strong className="me-auto">{toast.title}</strong>
                            <small>now</small>
                        </Toast.Header>
                        <Toast.Body className={toast.variant === 'success' ? 'text-white' : ''}>{toast.body}</Toast.Body>
                    </Toast>
                ))}
            </ToastContainer>
        </div>
    );
};

export default JmxFileList;
