import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Upload, FileText, AlertCircle, CheckCircle, Loader2, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { sseService, type JobStatusUpdate } from '@/services/sse';
import { authService } from '@/services/authService';

interface UploadFormData {
  file: File | null;
  documentType: 'biblical' | 'theological' | '';
  category: string;
}

interface UploadResponse {
  documentId: string;
  filename: string;
  documentType: string;
  processingStatus: string;
  uploadedAt: string;
  jobId: string;
}

const MAX_FILE_SIZE = 52428800; // 50MB in bytes
const ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.txt', '.md', '.json'];
const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'text/markdown',
  'text/x-markdown',
  'application/json'
];

// Enhanced validation rules to match backend
const MIME_TYPE_MAPPINGS = {
  '.pdf': ['application/pdf'],
  '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  '.txt': ['text/plain'],
  '.md': ['text/markdown', 'text/plain', 'text/x-markdown'],
  '.json': ['application/json', 'text/plain']
};

export const DocumentUpload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<{
    message: string;
    type?: string;
    code?: string;
    status?: number;
  } | null>(null);
  const [success, setSuccess] = useState<UploadResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusUpdate | null>(null);
  const [sseConnected, setSseConnected] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors }
  } = useForm<UploadFormData>({
    defaultValues: {
      file: null,
      documentType: '',
      category: ''
    }
  });

  const selectedFile = watch('file');
  const documentType = watch('documentType');

  // Cleanup SSE connection on component unmount
  useEffect(() => {
    return () => {
      sseService.cleanup();
    };
  }, []);

  // SSE connection handler
  const connectToJobStatus = useCallback((jobId: string) => {
    const token = authService.getToken();
    if (!token) {
      setError({ message: 'Authentication token not found', type: 'auth_error', code: 'missing_token' });
      return;
    }

    setSseConnected(true);
    setJobStatus({ status: 'queued', progress: 0.0, step: 'initializing' });

    sseService.connect(jobId, token, {
      onMessage: (update: JobStatusUpdate) => {
        console.log('Received job status update:', update);
        setJobStatus(update);
        
        // Handle final states
        if (update.status === 'completed') {
          setSseConnected(false);
        } else if (update.status === 'failed' || update.status === 'error') {
          setSseConnected(false);
          if (update.message) {
            setError({ 
              message: `Job processing failed: ${update.message}`, 
              type: 'job_error', 
              code: update.status 
            });
          }
        }
      },
      onError: (error) => {
        console.error('SSE connection error:', error);
        setSseConnected(false);
        setError({ 
          message: 'Real-time connection lost. Job is still processing in the background.', 
          type: 'sse_error', 
          code: 'connection_lost' 
        });
      },
      onOpen: () => {
        console.log('SSE connection established');
      },
      onClose: () => {
        console.log('SSE connection closed');
        setSseConnected(false);
      },
      reconnectAttempts: 3,
      reconnectDelay: 2000
    });
  }, []);

  const validateFile = useCallback((file: File): string | null => {
    // Check if file has a name
    if (!file.name || file.name.trim() === '') {
      return 'File must have a valid filename';
    }

    // Check file size - empty file
    if (file.size === 0) {
      return 'File is empty and cannot be uploaded';
    }

    // Check file size - too large
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is ${(MAX_FILE_SIZE / 1024 / 1024).toFixed(1)}MB. Your file is ${(file.size / 1024 / 1024).toFixed(1)}MB`;
    }

    // Check file extension
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!fileExtension || fileExtension === '.') {
      return 'File has no extension';
    }
    
    if (!ALLOWED_FILE_TYPES.includes(fileExtension)) {
      return `File type ${fileExtension} not allowed. Supported types: ${ALLOWED_FILE_TYPES.join(', ')}`;
    }

    // Enhanced MIME type validation to match backend
    const expectedMimeTypes = MIME_TYPE_MAPPINGS[fileExtension as keyof typeof MIME_TYPE_MAPPINGS];
    if (expectedMimeTypes && file.type && !expectedMimeTypes.includes(file.type)) {
      return `MIME type ${file.type} doesn't match file extension ${fileExtension}`;
    }

    // Fallback check for general MIME type
    if (file.type && !ALLOWED_MIME_TYPES.includes(file.type)) {
      return `File type not supported. Please upload: PDF, DOCX, TXT, MD, or JSON files`;
    }

    return null;
  }, []);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setError(null);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const validationError = validateFile(file);
      
      if (validationError) {
        setError({ message: validationError, type: 'validation_error', code: 'client_validation_failed' });
        return;
      }

      setValue('file', file);
    }
  }, [validateFile, setValue]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validationError = validateFile(file);
      
      if (validationError) {
        setError({ message: validationError, type: 'validation_error', code: 'client_validation_failed' });
        e.target.value = '';
        return;
      }

      setValue('file', file);
    }
  }, [validateFile, setValue]);

  const uploadFile = async (data: UploadFormData, useStreaming: boolean = false): Promise<UploadResponse> => {
    if (!data.file || !data.documentType) {
      throw new Error('File and document type are required');
    }

    const { apiService } = await import('@/services/api');

    if (useStreaming) {
      // Use streaming upload for real-time progress
      return await apiService.uploadDocumentWithStream(
        data.file,
        data.documentType,
        data.category || undefined,
        (event) => {
          console.log('Stream event:', event);
          // Handle stream events (validation_complete, storage_complete, etc.)
          if (event.event === 'upload_complete') {
            setUploadProgress(100);
          }
        }
      );
    } else {
      // Use regular upload with XMLHttpRequest progress
      return await apiService.uploadDocument(
        data.file,
        data.documentType,
        data.category || undefined,
        (progress) => {
          setUploadProgress(progress.percentage);
        }
      );
    }
  };

  const onSubmit = async (data: UploadFormData) => {
    if (!data.file || !data.documentType) {
      setError({ message: 'Please select a file and document type', type: 'validation_error', code: 'missing_required_fields' });
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    setJobStatus(null);
    setSseConnected(false);
    setUploadProgress(0);

    try {
      const result = await uploadFile(data);
      setSuccess(result);
      
      // Connect to SSE for real-time job status updates
      if (result.jobId) {
        connectToJobStatus(result.jobId);
      }
      
      reset();
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      if (error && typeof error === 'object' && error.type && error.code) {
        // Enhanced error from backend
        setError({
          message: error.message || 'Upload failed',
          type: error.type,
          code: error.code,
          status: error.status
        });
      } else {
        // Basic error
        setError({ 
          message: error instanceof Error ? error.message : 'Upload failed',
          type: 'unknown_error',
          code: 'upload_failed'
        });
      }
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Upload Document</CardTitle>
        <CardDescription>
          Upload biblical or theological documents for processing. Supported formats: PDF, DOCX, TXT, MD, JSON (max 50MB)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Drag and Drop Zone */}
          <div
            className={cn(
              "relative border-2 border-dashed rounded-lg p-8 text-center transition-colors",
              dragActive ? "border-primary bg-primary/10" : "border-gray-300 hover:border-gray-400",
              selectedFile && "border-green-500 bg-green-50"
            )}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept={ALLOWED_FILE_TYPES.join(',')}
              onChange={handleFileSelect}
              disabled={uploading}
            />
            
            {selectedFile ? (
              <div className="space-y-2">
                <FileText className="mx-auto h-12 w-12 text-green-600" />
                <p className="text-sm font-medium text-green-700">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(1)}MB
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <p className="text-sm font-medium">Drop your file here, or click to select</p>
                <p className="text-xs text-gray-500">
                  PDF, DOCX, TXT, MD, JSON up to 50MB
                </p>
              </div>
            )}
          </div>

          {/* Document Type Selection */}
          <div className="space-y-2">
            <Label htmlFor="documentType">Document Type *</Label>
            <Select
              value={documentType}
              onValueChange={(value: 'biblical' | 'theological') => setValue('documentType', value)}
              disabled={uploading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select document type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="biblical">Biblical Text</SelectItem>
                <SelectItem value="theological">Theological Commentary</SelectItem>
              </SelectContent>
            </Select>
            {errors.documentType && (
              <p className="text-sm text-red-600">{errors.documentType.message}</p>
            )}
          </div>

          {/* Optional Category */}
          <div className="space-y-2">
            <Label htmlFor="category">Category (Optional)</Label>
            <Input
              id="category"
              {...register('category')}
              placeholder="e.g., Commentary, Study Guide, Reference"
              disabled={uploading}
            />
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Uploading... {uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-1">
                  <p className="font-medium">{error.message}</p>
                  {error.type && error.code && (
                    <p className="text-xs text-red-700">
                      Error Code: <code className="bg-red-100 px-1 rounded">{error.code}</code>
                      {error.status && ` (${error.status})`}
                    </p>
                  )}
                  {error.type === 'validation_error' && (
                    <p className="text-xs text-red-700">
                      Please check your file meets the requirements and try again.
                    </p>
                  )}
                  {error.type === 'storage_error' && (
                    <p className="text-xs text-red-700">
                      There was a problem saving your file. Please try again.
                    </p>
                  )}
                  {error.type === 'auth_error' && (
                    <p className="text-xs text-red-700">
                      Please log out and log back in, then try again.
                    </p>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Success Display */}
          {success && (
            <Alert variant="default" className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                <div className="space-y-1">
                  <p className="font-medium">Upload successful!</p>
                  <p className="text-sm">
                    Document ID: <code className="bg-white px-1 rounded">{success.documentId}</code>
                  </p>
                  <p className="text-sm">Status: {success.processingStatus}</p>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Real-time Job Status Display */}
          {jobStatus && (
            <Alert variant="default" className="border-blue-200 bg-blue-50">
              <Activity className={cn(
                "h-4 w-4",
                sseConnected ? "text-blue-600 animate-pulse" : "text-blue-600"
              )} />
              <AlertDescription className="text-blue-800">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">Processing Status</p>
                    <span className={cn(
                      "text-xs px-2 py-1 rounded-full",
                      jobStatus.status === 'completed' && "bg-green-100 text-green-800",
                      jobStatus.status === 'processing' && "bg-yellow-100 text-yellow-800",
                      jobStatus.status === 'queued' && "bg-blue-100 text-blue-800",
                      jobStatus.status === 'failed' && "bg-red-100 text-red-800",
                      jobStatus.status === 'error' && "bg-red-100 text-red-800"
                    )}>
                      {jobStatus.status.charAt(0).toUpperCase() + jobStatus.status.slice(1)}
                    </span>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>Progress: {Math.round(jobStatus.progress * 100)}%</span>
                      <span>Step: {jobStatus.step}</span>
                    </div>
                    <Progress value={jobStatus.progress * 100} className="h-2" />
                  </div>
                  
                  {jobStatus.message && (
                    <p className="text-sm">{jobStatus.message}</p>
                  )}
                  
                  {sseConnected && (
                    <div className="flex items-center space-x-1 text-xs text-blue-600">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span>Real-time updates connected</span>
                    </div>
                  )}
                  
                  {jobStatus.timestamp && (
                    <p className="text-xs text-gray-500">
                      Last update: {new Date(jobStatus.timestamp).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={!selectedFile || !documentType || uploading}
            className="w-full"
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload Document
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default DocumentUpload;