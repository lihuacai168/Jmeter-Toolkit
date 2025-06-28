import React, { useState } from 'react';
import { Card, Row, Col } from 'react-bootstrap';
import JmxFileList from '../components/JmxFileList';

const HomePage = () => {
    const [fileListKey, setFileListKey] = useState(0);

    const handleUploadSuccess = () => {
        setFileListKey(prevKey => prevKey + 1);
    };

    return (
        <Row>
            <Col md={12}>
                <Card>
                    <Card.Body>
                        <JmxFileList key={fileListKey} onUploadSuccess={handleUploadSuccess} />
                    </Card.Body>
                </Card>
            </Col>
        </Row>
    );
};

export default HomePage;
