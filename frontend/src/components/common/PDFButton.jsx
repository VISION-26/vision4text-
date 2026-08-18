import React from 'react';
import { FileDown } from 'lucide-react';
import Button from './Button';

const PDFButton = ({ onClick, disabled = false, loading = false, variant = 'secondary', label = 'Download PDF Report' }) => (
    <Button variant={variant} onClick={onClick} disabled={disabled || loading || !onClick} icon={FileDown}>
        {loading ? 'Generating PDF…' : label}
    </Button>
);

export default PDFButton;
