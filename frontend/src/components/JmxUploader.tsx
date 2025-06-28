import React, { useState, useRef } from 'react';
import { Form, Button, ProgressBar, Alert } from 'react-bootstrap';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface JmxUploaderProps {
    onUploadSuccess: () => void;
}

const JmxUploader = ({ onUploadSuccess }: JmxUploaderProps) => {
    const [file, setFile] = useState<File | null>(null);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setFile(event.target.files[0]);
            setSuccess(null);
            setError(null);
            setProgress(0);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Please select a file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            setError(null);
            setSuccess(null);
            const response = await axios.post(`${API_URL}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
                    setProgress(percentCompleted);
                },
            });
            setSuccess(`File uploaded successfully: ${response.data.data.file_name}`);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
            setFile(null);
            onUploadSuccess(); // Call the callback function
        } catch (err: any) {
            setError(err.response?.data?.message || 'An error occurred during upload.');
            setProgress(0);
        }
    };

    return (
        <div className="jmx-uploader">
            {error && <Alert variant="danger">{error}</Alert>}
            {success && <Alert variant="success">{success}</Alert>}
            <Form>
                <Form.Group controlId="formFile" className="mb-2">
                    <Form.Label>Select .jmx file</Form.Label>
                    <Form.Control type="file" accept=".jmx" onChange={handleFileChange} ref={fileInputRef} />
                </Form.Group>
                {progress > 0 && <ProgressBar now={progress} label={`${progress}%`} className="mb-2" />}
                <Button variant="primary" onClick={handleUpload} disabled={!file}>
                    Upload
                </Button>
            </Form>
        </div>
    );
};

export default JmxUploader;
