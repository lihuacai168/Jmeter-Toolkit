import React, { useState } from 'react';
import { Card, Row, Col } from 'react-bootstrap';
import JmxUploader from '../components/JmxUploader';
import JmxFileList from '../components/JmxFileList';

const HomePage = () => {
    const [fileListKey, setFileListKey] = useState(0);

    const handleUploadSuccess = () => {
        setFileListKey(prevKey => prevKey + 1);
    };

    return (
        <Row>
            <Col md={12} lg={6} className="mb-4">
                <Card>
                    <Card.Body>
                        <Card.Title>Upload JMX File</Card.Title>
                        <JmxUploader onUploadSuccess={handleUploadSuccess} />
                    </Card.Body>
                </Card>
            </Col>
            <Col md={12} lg={6}>
                <Card>
                    <Card.Body>
                        <Card.Title>Available JMX Files</Card.Title>
                        <JmxFileList key={fileListKey} />
                    </Card.Body>
                </Card>
            </Col>
        </Row>
    );
};

export default HomePage;
